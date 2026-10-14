import base64
import copy
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from unittest.mock import patch
import studio


class StudioTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old = studio.ROOT
        studio.ROOT = Path(self.temp.name)
        studio.load()
        self.image = studio.ROOT / 'reference.png'
        studio.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=blue:s=160x90','-frames:v','1',str(self.image)])
        self.p = studio.action('upload', {'data':base64.b64encode(self.image.read_bytes()).decode(),'name':'Hero.png'})
        self.s = self.p['shots'][0]
        self.id = self.s['id']
        self.p['characters'] = 'Short silver hair, navy coat, red scarf'
        self.p['world'] = 'Rainy rooftop at blue hour'
        self.s.update(start='Crouches and plants the left foot.', action='Leaps right with the torso rotating.', end='Lands right and absorbs impact.')
        self.p = studio.action('save',self.p)
        self.s = self.p['shots'][0]

    def tearDown(self):
        studio.ROOT = self.old
        self.temp.cleanup()

    def clip(self, moving):
        path = studio.ROOT / ('moving.mp4' if moving else 'still.mp4')
        studio.run(['ffmpeg','-v','error','-f','lavfi','-i',('testsrc2=s=160x90:r=16' if moving else 'color=c=blue:s=160x90:r=16'),'-t','2','-c:v','libx264','-pix_fmt','yuv420p',str(path)])
        return path

    def import_clip(self, moving=True):
        path = self.clip(moving)
        return studio.action('import', {'id':self.id,'data':base64.b64encode(path.read_bytes()).decode()})

    def test_actual_frames_and_frozen_warning(self):
        p = self.import_clip(False)
        t = p['shots'][0]['takes'][0]
        self.assertEqual(t['frame_count'],32)
        result = studio.action('framezip',{'id':self.id})
        with zipfile.ZipFile(studio.file_path(result['url'])) as archive:
            self.assertEqual(len([n for n in archive.namelist() if n.endswith('.png')]),32)
        self.assertTrue(t['motion_warning'])
        self.assertTrue((studio.file_path(t['folder'])/'contact.jpg').exists())
        p = self.import_clip(True)
        t = p['shots'][0]['takes'][1]
        self.assertFalse(t['motion_warning'])
        self.assertEqual(t['frame_count'],32)

    def test_export_requires_review_and_normalizes_dimensions(self):
        self.import_clip()
        with self.assertRaisesRegex(ValueError,'Review and approve'):
            studio.action('export',{})
        with self.assertRaisesRegex(ValueError,'four quality'):
            studio.action('approve',{'id':self.id})
        p = studio.action('approve', {'id':self.id,**dict.fromkeys(studio.CHECKS,True)})
        result = studio.action('export',{})
        info = studio.probe(studio.file_path(result['export']))
        self.assertEqual((info['width'],info['height']),(1280,720))
        self.assertAlmostEqual(info['seconds'],2,places=1)
        p['world'] = 'Daylight'
        result = studio.action('save',p)
        self.assertFalse(result['shots'][0]['takes'][0]['approved'])

    def test_submission_receipts_and_duplicate_prevention(self):
        queue = dict(request_id='abc',status_url='https://queue.fal.run/status',response_url='https://queue.fal.run/result')
        with patch.dict(studio.os.environ,{'FAL_KEY':'test-only'}), patch.object(studio,'api',return_value=queue) as api:
            p = studio.action('render', {'id':self.id})
            payload = api.call_args.args[1]
            self.assertEqual(payload['interpolator_model'],'none')
            self.assertIn('visible articulated body action',payload['prompt'])
            with self.assertRaisesRegex(ValueError,'already has a pending'):
                studio.action('render', {'id':self.id})
            self.assertEqual(api.call_count,1)
            receipt = json.loads((studio.file_path(p['shots'][0]['takes'][0]['folder'])/'take.json').read_text())
            self.assertEqual(receipt['request_id'],'abc')

    def test_unknown_outcome_never_retries(self):
        with patch.dict(studio.os.environ,{'FAL_KEY':'test-only'}), patch.object(studio,'api',side_effect=TimeoutError) as api:
            with self.assertRaisesRegex(ValueError,'uncertain'):
                studio.action('render', {'id':self.id})
            self.assertEqual(studio.load()['shots'][0]['takes'][0]['status'],'unknown')
            with self.assertRaisesRegex(ValueError,'already has a pending'):
                studio.action('render', {'id':self.id})
            self.assertEqual(api.call_count,1)

    def test_prompt_requires_direction_and_path_is_contained(self):
        bad = copy.deepcopy(self.s)
        bad['action'] = ''
        with self.assertRaisesRegex(ValueError,'body action'):
            studio.prompt(self.p,bad)
        with self.assertRaisesRegex(ValueError,'Invalid workspace'):
            studio.file_path('../outside')
        with self.assertRaisesRegex(ValueError,'Unexpected queue'):
            studio.api('https://example.com/steal-key')

    def test_invalid_project_save_is_atomic(self):
        before = studio.load()
        self.p['shots'][0]['seconds']='1000'
        with self.assertRaisesRegex(ValueError,'2–10'):
            studio.action('save',self.p)
        self.assertEqual(studio.load(),before)


if __name__ == '__main__':
    unittest.main()
