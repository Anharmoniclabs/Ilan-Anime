import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from cemi_pipeline.cli import main

class PipelineTests(unittest.TestCase):
    def test_shot_no_random_text(self):
        with tempfile.TemporaryDirectory() as td:
            shot = Path(td)/'shot.json'
            main(['shot','--character','JC','--shot-id','x1','--scene','listening on rooftop','--out',str(shot)])
            data=json.loads(shot.read_text())
            self.assertEqual(data['character_id'],'JC')
            self.assertIn('wall writing',data['negative_prompt'])
            self.assertIn('cemistyle',data['prompt'])

    def test_preparation_enforces_approval(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            Image.new('RGB',(600,600),(50,60,70)).save(root/'a.png')
            entry={'file':'a.png','approved':False,'origin':'author_original','caption':'a mature original colored illustration'}
            manifest=root/'manifest.json'
            manifest.write_text(json.dumps([entry]))
            with self.assertRaises(SystemExit):
                main(['prepare','--manifest',str(manifest),'--out',str(root/'train')])
            entry['approved']=True
            manifest.write_text(json.dumps([entry]))
            main(['prepare','--manifest',str(manifest),'--out',str(root/'train')])
            text=(root/'train'/'metadata.jsonl').read_text()
            self.assertIn('cemistyle',text)
            self.assertTrue((root/'train'/'provenance.json').exists())

    def test_manifest_rejects_traversal(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            manifest=root/'manifest.json'
            manifest.write_text(json.dumps([{'file':'../escape.png','approved':True,'origin':'author_original','caption':'legitimate original portrait with warm colors'}]))
            with self.assertRaises(SystemExit):
                main(['prepare','--manifest',str(manifest),'--out',str(root/'train')])

    def test_character_bible_is_distinct(self):
        from cemi_pipeline.cli import characters, ROOT
        data=characters(ROOT/'configs/characters.json')
        self.assertIn('close-cropped',data['MANNY']['look'])
        self.assertIn('short curly',data['JC']['look'])
        self.assertNotEqual(data['JC']['build'],data['MANNY']['build'])

    def test_hand_ink_reference_is_not_filtered_out(self):
        from cemi_pipeline.cli import config, ROOT
        s = config(ROOT/'configs/style.yaml')
        self.assertEqual(s['style_id'], 'cemi_option_b_v2_handink')
        self.assertIn('crosshatching', s['positive_prefix'])
        self.assertIn('ink', s['positive_prefix'].lower())
        self.assertIn('wall writing', s['negative'])
        self.assertNotIn('excessive hatch marks', s['negative'])
        self.assertIn('watercolor', s['positive_prefix'])

if __name__=='__main__':
    unittest.main()
