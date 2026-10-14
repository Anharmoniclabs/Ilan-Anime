"""Cemí production CLI. Dataset images are user-approved and local only."""
from __future__ import annotations
import argparse
import hashlib
import json
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import yaml
from PIL import Image, UnidentifiedImageError

ROOT = Path(__file__).resolve().parent.parent
EXT = {'.png', '.jpg', '.jpeg', '.webp'}


def config(path):
    return yaml.safe_load(Path(path).read_text(encoding='utf-8'))


def characters(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))['characters']


def approved_items(manifest):
    entries = json.loads(Path(manifest).read_text(encoding='utf-8'))
    if not isinstance(entries, list):
        raise ValueError('Manifest must be a JSON list')
    return entries


def build_dataset(args):
    src = Path(args.manifest).resolve().parent
    out = Path(args.out).resolve()
    entries = approved_items(args.manifest)
    if not entries:
        raise ValueError('No approved training images; no dataset created')
    if out == src or src in out.parents and (src / 'metadata.jsonl').exists():
        raise ValueError('Output must be a distinct dataset folder')
    style = config(args.style)
    names = set()
    records = []
    for i, e in enumerate(entries):
        if not e.get('approved', False):
            raise ValueError(f'Image #{i} is not approved; explicitly approve all training images')
        if e.get('origin') not in ('author_original','author_approved_refinement'):
            raise ValueError(f'Image #{i} must declare origin author_original or author_approved_refinement')
        raw_path = Path(e['file'])
        if raw_path.is_absolute() or '..' in raw_path.parts:
            raise ValueError('Only safe relative image paths are accepted')
        source = (src / raw_path).resolve()
        if src not in source.parents or not source.is_file() or source.suffix.lower() not in EXT:
            raise ValueError(f'Unsupported/missing image: {raw_path}')
        if not e.get('caption') or len(e['caption'].strip()) < 16:
            raise ValueError(f'Caption missing/too short for {raw_path}')
        with Image.open(source) as im:
            im.verify()
        with Image.open(source) as im:
            w, h = im.size
            if min(w,h) < 512:
                raise ValueError(f'{raw_path} too small: {w}x{h} (minimum side 512)')
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if digest in names:
            raise ValueError(f'Duplicate image pixels/file bytes: {raw_path}')
        names.add(digest)
        filename = f'{i:04d}{source.suffix.lower()}'
        caption = f"{style['trigger']}, {e['caption'].strip()}"
        records.append((source, filename, {'file_name':filename,'text':caption}, digest, e))
    out.mkdir(parents=True, exist_ok=True)
    for source, name, _, _, _ in records:
        shutil.copyfile(source, out / name)
    with (out/'metadata.jsonl').open('w',encoding='utf-8') as f:
        for _,_,rec,_,_ in records:
            f.write(json.dumps(rec,ensure_ascii=False)+'\n')
    with (out/'provenance.json').open('w',encoding='utf-8') as f:
        json.dump([{'file_name':name,'sha256':dig,'origin':ent['origin'],'source':str(source)} for source,name,_,dig,ent in records],f,indent=2)
    print(f'Prepared {len(records)} approved images at {out}; provenance local, DO NOT publish without author approval.')


def train_command(args):
    dataset = Path(args.dataset).resolve()
    trainer = Path(args.trainer).resolve()
    if not trainer.is_file():
        raise ValueError('Provide the official diffusers train_text_to_image_lora_sdxl.py script using --trainer')
    if not (dataset/'metadata.jsonl').is_file():
        raise ValueError('First run dataset prepare; metadata.jsonl missing')
    with (dataset/'metadata.jsonl').open(encoding='utf-8') as f:
        rows = [json.loads(line) for line in f if line.strip()]
    if not rows or any('text' not in r or not (dataset/r['file_name']).is_file() for r in rows):
        raise ValueError('ImageFolder metadata invalid')
    style = config(args.style)
    out = str(Path(args.out).resolve())
    cmd = ['accelerate','launch',str(trainer), '--pretrained_model_name_or_path',style['base_model'],
           '--train_data_dir',str(dataset), '--resolution',str(args.resolution),
           '--train_batch_size','1','--gradient_accumulation_steps',str(args.grad_accum),
           '--learning_rate',str(args.lr),'--lr_scheduler','constant','--lr_warmup_steps','0',
           '--mixed_precision','fp16','--rank',str(args.rank),'--max_train_steps',str(args.steps),
           '--checkpointing_steps',str(args.checkpoint_steps),'--seed',str(args.seed),
           '--output_dir',out,'--report_to','tensorboard', '--gradient_checkpointing']
    print(shlex.join(cmd))
    if args.run:
        subprocess.run(cmd,check=True)


def prompt(args):
    style = config(args.style)
    cast = characters(args.characters)
    if args.character.upper() not in cast:
        raise ValueError(f'Unknown character: {args.character}. Options: {", ".join(cast)}')
    c = cast[args.character.upper()]
    description = ', '.join([c['name'],c['look'],c['build'],c['outfit'],c['expression']])
    prompt_text = f"{style['positive_prefix']}, {description}, {args.scene}; single consistent character, no writing or logos"
    output = {'shot_id':args.shot_id,'character_id':args.character.upper(),
              'prompt':prompt_text, 'negative_prompt':style['negative'],
              'seed':args.seed,'width':args.width,'height':args.height,
              'style_id':style['style_id'],'reference_image':args.reference or None,
              'stage':'concept-keyframe', 'lora_weight':args.lora_weight,
              'continuity':c['continuity']}
    result = json.dumps(output,indent=2,ensure_ascii=False)
    if args.out:
        Path(args.out).parent.mkdir(parents=True,exist_ok=True)
        Path(args.out).write_text(result+'\n',encoding='utf-8')
    print(result)


def render(args):
    shot = json.loads(Path(args.shot).read_text(encoding='utf-8'))
    if not args.lora or not Path(args.lora).is_file():
        raise ValueError('An actual trained LoRA file must be supplied with --lora')
    if shot.get('reference_image'):
        raise ValueError('A reference was requested; this text2image renderer does not enforce reference identity. Use an SDXL IP-Adapter/ControlNet workflow instead.')
    try:
        import torch
        from diffusers import StableDiffusionXLPipeline
    except ImportError as exc:
        raise RuntimeError('Install the CUDA PyTorch build and requirements-gpu.txt first') from exc
    if not torch.cuda.is_available():
        raise RuntimeError('This SDXL render path requires CUDA GPU. Use a cloud CUDA runtime.')
    model = config(args.style)['base_model']
    pipe = StableDiffusionXLPipeline.from_pretrained(model,torch_dtype=torch.float16,use_safetensors=True)
    pipe.load_lora_weights(str(Path(args.lora).parent),weight_name=Path(args.lora).name)
    pipe = pipe.to('cuda')
    try:
        pipe.enable_xformers_memory_efficient_attention()
    except (AttributeError,ImportError,ValueError):
        pass
    pipe.fuse_lora(lora_scale=float(shot.get('lora_weight',0.8)))
    gen = torch.Generator(device='cuda').manual_seed(int(shot['seed']))
    img = pipe(prompt=shot['prompt'],negative_prompt=shot['negative_prompt'],
               width=int(shot['width']),height=int(shot['height']),generator=gen,
               num_inference_steps=args.steps,guidance_scale=args.guidance).images[0]
    dest = Path(args.out)
    dest.parent.mkdir(parents=True,exist_ok=True)
    img.save(dest)
    (dest.with_suffix('.json')).write_text(json.dumps({'shot':shot,'base_model':model,
             'lora':str(args.lora),'steps':args.steps,'guidance_scale':args.guidance},indent=2),encoding='utf-8')
    print(f'Keyframe saved: {dest}. Not temporally consistent animation by itself.')


def assemble(args):
    if args.fps < 1 or args.fps > 60:
        raise ValueError('fps must be in [1,60]')
    frames = Path(args.frames)
    if not frames.is_dir() or not list(frames.glob('*.png')):
        raise ValueError('No PNG frames in input folder')
    if not shutil.which('ffmpeg'):
        raise ValueError('ffmpeg executable not found')
    out = Path(args.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(['ffmpeg','-y','-framerate',str(args.fps),'-pattern_type','glob',
                    '-i',str(frames/'*.png'),'-c:v','libx264','-pix_fmt','yuv420p',
                    '-movflags','+faststart',str(out)],check=True)
    print(f'MP4 assembled: {out}. Frame timing depends on filenames sorted by ffmpeg glob.')


def main(argv=None):
    p = argparse.ArgumentParser(description='Cemí SDXL LoRA style + animation preproduction')
    sub = p.add_subparsers(dest='command',required=True)
    d = sub.add_parser('prepare',help='Validate and copy approved images into HF imagefolder dataset')
    d.add_argument('--manifest',required=True)
    d.add_argument('--out',default='data/style_train')
    d.add_argument('--style',default=str(ROOT/'configs/style.yaml'))
    d.set_defaults(func=build_dataset)
    t = sub.add_parser('train-command',help='Print or run SDXL LoRA training command with official trainer')
    t.add_argument('--trainer',required=True)
    t.add_argument('--dataset',default='data/style_train')
    t.add_argument('--style',default=str(ROOT/'configs/style.yaml'))
    t.add_argument('--out',default='models/cemi-style-v1')
    t.add_argument('--resolution',type=int,default=1024)
    t.add_argument('--steps',type=int,default=1500)
    t.add_argument('--grad-accum',type=int,default=4)
    t.add_argument('--lr',type=float,default=1e-4)
    t.add_argument('--rank',type=int,default=16)
    t.add_argument('--checkpoint-steps',type=int,default=250)
    t.add_argument('--seed',type=int,default=20261009)
    t.add_argument('--run',action='store_true',help='Launch real GPU training; default only prints')
    t.set_defaults(func=train_command)
    s = sub.add_parser('shot',help='Create JSON prompt/shot manifest for reproducible generations')
    s.add_argument('--character',required=True)
    s.add_argument('--scene',required=True)
    s.add_argument('--shot-id',required=True)
    s.add_argument('--style',default=str(ROOT/'configs/style.yaml'))
    s.add_argument('--characters',default=str(ROOT/'configs/characters.json'))
    s.add_argument('--reference',help='Optional character reference art (metadata only; render requires separate adapter workflow)')
    s.add_argument('--seed',type=int,default=20261009)
    s.add_argument('--width',type=int,default=1024)
    s.add_argument('--height',type=int,default=1024)
    s.add_argument('--lora-weight',type=float,default=0.8)
    s.add_argument('--out')
    s.set_defaults(func=prompt)
    r = sub.add_parser('render',help='Render one text-to-image keyframe with a trained SDXL LoRA on CUDA')
    r.add_argument('--shot',required=True)
    r.add_argument('--lora',required=True)
    r.add_argument('--style',default=str(ROOT/'configs/style.yaml'))
    r.add_argument('--out',required=True)
    r.add_argument('--steps',type=int,default=30)
    r.add_argument('--guidance',type=float,default=6.0)
    r.set_defaults(func=render)
    a = sub.add_parser('assemble',help='Combine ordered PNG animation frames into MP4')
    a.add_argument('--frames',required=True)
    a.add_argument('--fps',type=int,default=12)
    a.add_argument('--out',required=True)
    a.set_defaults(func=assemble)
    args = p.parse_args(argv)
    try:
        args.func(args)
    except (ValueError,FileNotFoundError,UnidentifiedImageError,RuntimeError,subprocess.CalledProcessError) as exc:
        p.exit(2,f'ERROR: {exc}\n')

if __name__=='__main__':
    main()
