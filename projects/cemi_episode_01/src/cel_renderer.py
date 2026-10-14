"""Deterministic, local 2D cel animation. No network calls or paid video service.

Run from any directory: python src/cel_renderer.py --shot current --width 1280
The final-episode gate intentionally refuses incomplete shots.
"""
from pathlib import Path
import argparse, json, math, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
FPS = 24
W, H = 1280, 720
RES = Image.Resampling.BICUBIC
PI = math.pi

def smooth(a, b, x):
    t = max(0., min(1., (x-a)/(b-a)))
    return t*t*(3-2*t)

def plate(name):
    return Image.open(ROOT/'assets'/name).convert('RGBA').resize((W,H), RES)

def polygon_mask(points):
    m=Image.new('L',(W,H)); ImageDraw.Draw(m).polygon([(round(x*W/1672),round(y*H/941)) for x,y in points],fill=255)
    return m.filter(ImageFilter.GaussianBlur(.45*W/1280))

def cutout(img, points):
    out=img.copy();out.putalpha(polygon_mask(points));return out

def mesh(img, handles=(), water=0., frame=0):
    """Inverse piecewise bilinear mesh; per-handle influence has finite support.
    Handles: x, y, radius, dx, dy in original 1672x941 art coordinates.
    Background pins are obtained automatically outside each handle radius.
    """
    def src(x,y):
        u,v=x*1672/W,y*941/H; dx=dy=0.
        for cx,cy,r,hx,hy in handles:
            q=math.hypot((u-cx),(v-cy))/r
            if q<1:
                a=(1-q*q)**2
                dx+=hx*a;dy+=hy*a
        if water:
            strength=smooth(400,900,v)*water
            dx+=strength*math.sin(v/19-frame*.29)
            dy+=strength*.14*math.sin(u/67+frame*.2)
        return x-dx*W/1672,y-dy*H/941
    tiles=[];step=max(12,round(W/48))
    for y in range(0,H,step):
        for x in range(0,W,step):
            r,b=min(W,x+step),min(H,y+step)
            tiles.append(((x,y,r,b),(*src(x,y),*src(x,b),*src(r,b),*src(r,y))))
    return img.transform((W,H),Image.Transform.MESH,tiles,RES)

def shift(img,x,y):
    return img.transform((W,H),Image.Transform.AFFINE,(1,0,-x*W/1672,0,1,-y*H/941),RES)

def over(bg,fg): return Image.alpha_composite(bg,fg)

BELL=[(770,131),(790,118),(816,133),(832,167),(867,181),(898,216),(912,253),(905,289),(884,355),(877,406),(876,465),(885,537),(907,611),(914,659),(903,684),(880,703),(836,720),(779,726),(713,719),(650,703),(588,683),(537,663),(508,669),(487,651),(491,632),(449,611),(408,579),(374,545),(353,515),(342,486),(348,465),(371,440),(421,405),(479,365),(530,316),(584,258),(621,203),(654,180),(702,168),(753,166)]
LEAD=[(0,790),(55,739),(83,702),(88,634),(116,620),(137,575),(170,555),(208,531),(212,501),(239,473),(272,464),(313,457),(351,473),(385,500),(414,515),(420,494),(453,461),(472,441),(502,425),(540,421),(578,433),(605,449),(610,424),(633,390),(672,363),(710,355),(746,361),(770,388),(772,423),(792,450),(807,486),(845,494),(851,527),(835,568),(805,610),(758,658),(703,704),(654,740),(593,782),(522,825),(450,858),(354,885),(256,908),(148,921),(54,918),(15,897),(0,842)]
MID=[(849,407),(873,389),(903,374),(910,326),(933,287),(948,244),(968,222),(998,211),(1026,230),(1037,250),(1047,243),(1061,224),(1082,214),(1110,220),(1131,242),(1138,222),(1157,194),(1170,180),(1206,178),(1231,194),(1228,219),(1253,229),(1272,247),(1293,256),(1310,278),(1340,293),(1351,310),(1332,321),(1307,305),(1274,284),(1251,307),(1257,330),(1238,367),(1196,397),(1134,424),(1061,449),(996,467),(930,473),(879,468),(860,447)]
FAR=[(1337,226),(1361,218),(1372,193),(1374,175),(1389,156),(1407,153),(1424,162),(1427,178),(1429,157),(1440,144),(1455,142),(1470,156),(1473,164),(1482,152),(1496,148),(1501,130),(1506,110),(1528,106),(1544,127),(1547,155),(1567,172),(1577,191),(1586,207),(1590,222),(1571,221),(1557,204),(1554,224),(1533,246),(1494,264),(1450,276),(1400,276),(1361,267),(1342,248)]

class Rig:
    def __init__(self):
        self.bellbg=plate('bg/bell_clean.png')
        self.bell=cutout(plate('keyframes/S01-05B.png'),BELL)
        self.drum=plate('keyframes/S01-11.png')
        self.riverbg=plate('bg/river_clean.png')
        source=plate('keyframes/S01-12.png')
        self.boats=[cutout(source,p) for p in (LEAD,MID,FAR)]
        # Keep the original root bank on top to retain its exact paint texture.
        self.foreground=cutout(source,[(1120,941),(1293,777),(1427,704),(1511,690),(1580,476),(1672,344),(1672,941)])

    def bell_frame(self,f):
        q=f//3*3;t=q/FPS
        angle=17*math.cos(t*PI*2/1.8)*math.exp(-t*.12)
        cel=self.bell.rotate(angle,RES,center=(804*W/1672,136*H/941))
        bg=self.bellbg.copy()
        # Flame is a localized deformation, separate from the prop clock.
        bg=mesh(bg,[(267,347,95,4*math.sin(q*1.7),7*math.cos(q*.8))])
        return over(bg,cel)

    def drum_frame(self,f):
        q=f//2*2;t=q/FPS
        # Anticipation -> press -> settle. The palms barely travel once in contact.
        press=smooth(.6,3.2,t);settle=smooth(5.4,8.5,t)
        lean=-1+press*1.6-settle*.22
        breath=math.sin(t*PI)*.7
        handles=[(957,178,230,-12*lean,28*lean+breath),
                 (1162,306,165,-5*lean,16*lean),
                 (788,332,145,3*lean,13*lean),
                 (790,448,110,0,3*press),
                 (970,457,115,0,3*press),
                 (1490,170,140,1.2*math.sin(t*2),2*math.sin(t*2))]
        out=mesh(self.drum,handles,water=1.1,frame=q)
        fx=Image.new('RGBA',(W,H));d=ImageDraw.Draw(fx)
        if t>2:
            for i in range(3):
                age=t-2-i*.45
                if 0<age<4:
                    r=(85+age*145)*W/1672;cy=820*H/941
                    alpha=int(82*(1-age/4))
                    d.arc((W*.52-r,cy-r*.20,W*.52+r,cy+r*.20),5,171,fill=(140,193,216,alpha),width=max(1,W//900))
        return over(out,fx)

    def current_frame(self,f):
        q=f//2*2;t=q/FPS
        # Water, bodies, hulls and foam each have their own drawing clock.
        out=mesh(self.riverbg,water=2.0,frame=q)
        for i in (2,1,0):
            amp=(1,.65,.4)[i]
            cyc=math.sin(t*2.3+i*.7)
            handles=[]
            if i==0:
                handles=[(289,573,150,9*cyc,5*cyc),(471,655,125,12*cyc,8*cyc),
                         (121,705,100,-10*cyc,-12*cyc),(539,510,155,4*cyc,2*cyc),
                         (695,412,140,5*cyc,2*cyc)]
            if i==1:
                handles=[(1194,212,100,6*cyc,5*cyc),(1250,255,75,6*cyc,8*cyc)]
            boat=mesh(self.boats[i],handles)
            # Paddles slow while the hull continues to accelerate with the current.
            dx=-amp*(2*t+25*smooth(3,12,t));dy=amp*(.95*t+7*smooth(3,12,t))+1.5*math.sin(t*2+i)
            boat=shift(boat,dx,dy)
            out=over(out,boat)
        fx=Image.new('RGBA',(W,H));d=ImageDraw.Draw(fx)
        # Drawn foam bank: short broken strokes re-exposed on 2s, not particles.
        turn=PI*.5*smooth(2,8,t)
        for k in range(14):
            x=930+(k%4)*135;y=500+(k//4)*97
            phase=((q//2+k*3)%16)/16
            x-=phase*42;y+=phase*17
            length=17+(k%3)*6
            ang=turn+(-.3 if k%2 else .15)
            coords=[]
            for j in range(7):
                a=j/6-.5
                xx=a*length; yy=math.sin(j*PI/6)*3
                coords.append(((x+xx*math.cos(ang)-yy*math.sin(ang))*W/1672,(y+xx*math.sin(ang)+yy*math.cos(ang))*H/941))
            d.line(coords,fill=(99,160,195,100),width=max(1,W//850))
        out=over(out,fx)
        return over(out,self.foreground)

def render_audio(mode,duration,path):
    sr=48000;n=int(sr*duration);t=np.arange(n)/sr
    rng=np.random.default_rng(27120)
    noise=rng.normal(0,1,n)
    # Smooth the water bed. Deliberately quiet and unclipped.
    noise=np.convolve(noise,np.ones(13)/13,mode='same')*.025
    if mode=='bell':
        s=noise*.15
        for hit in [.1,1.0,1.9,2.8]:
            u=np.maximum(0,t-hit);env=(t>=hit)*np.exp(-u*10)
            for freq,amp in [(740,.08),(1193,.05),(2387,.025),(3511,.02)]:
                s+=amp*np.sin(2*PI*freq*u)*env
    else:
        swell=np.minimum(1,np.maximum(0,(t-1.8)/1.4))*np.exp(-np.maximum(0,t-4)*.22)
        sub=(np.sin(2*PI*57*t)+.25*np.sin(2*PI*113*t))*.055*swell
        water=noise*(.4+.8*np.minimum(1,np.maximum(0,t-10)/14))
        s=sub+water
    stereo=np.column_stack((s,np.roll(s,110)*.92))
    pcm=(np.clip(stereo,-.95,.95)*32767).astype('<i2')
    with wave.open(str(path),'wb') as w:
        w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr);w.writeframes(pcm.tobytes())

def loop_audio():
    sr=48000;t=np.arange(384000)/sr
    # Integer cycles guarantee a seam-free exact eight-second repeat.
    s=.017*np.sin(2*PI*71*t)+.006*np.sin(2*PI*143*t)+.003*np.sin(2*PI*287*t)
    p=ROOT/'assets/audio/loop_8s_48000.wav';p.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(p),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes((s*32767).astype('<i2').tobytes())

def render(mode,width):
    global W,H
    W=width;H=width*9//16
    rig=Rig();duration=5 if mode=='bell' else 24
    stem='Bell_motion_test' if mode=='bell' else 'Cemi_SC0_Current_Turns_motion_test'
    out=ROOT/'renders'/f'{stem}.mp4';out.parent.mkdir(parents=True,exist_ok=True)
    wav=ROOT/'renders'/f'{stem}.wav';render_audio(mode,duration,wav)
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','24','-i','pipe:0','-i',str(wav),'-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart','-shortest',str(out)]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    lastq=None;im=None
    for f in range(duration*FPS):
        rate=3 if mode=='bell' else 2;q=f//rate*rate
        if q!=lastq:
            if mode=='bell':im=rig.bell_frame(f)
            elif f<240:im=rig.drum_frame(f)
            else:im=rig.current_frame(f-240)
            lastq=q
        p.stdin.write(im.convert('RGB').tobytes())
        if f in ([0,18,42,90] if mode=='bell' else [0,72,180,240,384,570]):
            im.convert('RGB').save(ROOT/'qa'/f'{mode}_{f:04}.jpg',quality=90)
        if f%120==0:print(f'{mode}: {f}/{duration*FPS}',flush=True)
    p.stdin.close()
    if p.wait()!=0:raise RuntimeError('ffmpeg export failed')
    loop_audio();print(out,flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--shot',choices=['bell','current'],default='current');ap.add_argument('--width',type=int,default=1280)
    args=ap.parse_args()
    if args.width%16:ap.error('width must be divisible by 16')
    render(args.shot,args.width)
