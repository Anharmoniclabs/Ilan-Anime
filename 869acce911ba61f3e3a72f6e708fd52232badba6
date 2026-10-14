import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

import camera_motion as camera


class CameraMathTest(unittest.TestCase):
    def test_easing_endpoints_and_monotonicity(self):
        for kind in camera.EASINGS:
            if kind == 'hold':
                continue
            values = [camera.ease(i/100, kind) for i in range(101)]
            self.assertAlmostEqual(values[0], 0)
            self.assertAlmostEqual(values[-1], 1)
            self.assertTrue(all(a <= b+1e-12 for a, b in zip(values, values[1:])), kind)
        self.assertLess(camera.ease(.001, 'smoother'), .000001)

    def test_camera_hits_keys_without_drift(self):
        keys = camera.track([{'at':0,'x':.4,'zoom':2}, {'at':.4,'x':.6,'zoom':1.5}, {'at':1,'x':.5,'zoom':1}])
        for key in keys:
            s = camera.sample(keys, key['at'])
            self.assertAlmostEqual(s['zoom'], key['zoom'])
            self.assertAlmostEqual(s['x'], key['x'])
        first = camera.sample(keys,.2)
        camera.sample(keys,.9)
        self.assertEqual(camera.sample(keys,.2), first)

    def test_bounds_prevent_outside_artwork(self):
        keys = camera.track([{'at':0,'x':0,'y':1,'zoom':1}, {'at':1,'x':1,'y':0,'zoom':2}])
        for i in range(100):
            value = camera.sample(keys,i/99)
            half = .5/value['zoom']
            self.assertGreaterEqual(value['x']-half, -1e-9)
            self.assertLessEqual(value['y']+half, 1+1e-9)
        self.assertTrue(camera.sample(keys,0)['clamped'])

    def test_hold_changes_at_the_exact_key(self):
        keys = camera.track([{'at':0,'zoom':1,'ease':'hold'}, {'at':.5,'zoom':2}, {'at':1,'zoom':2}])
        self.assertEqual(camera.sample(keys,.4999)['zoom'],1)
        self.assertEqual(camera.sample(keys,.5)['zoom'],2)

    def test_rejects_invalid_tracks(self):
        for bad in ([{'at':0},{'at':0},{'at':1}], [{'at':.1},{'at':1}], [{'at':0,'zoom':0},{'at':1}],
                    [{'at':0,'x':float('nan')},{'at':1}], [{'at':0,'ease':'typo'},{'at':1}]):
            with self.assertRaises(ValueError):
                camera.track(bad)


class RenderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.source = cls.root/'marker.mp4'
        camera.command(['ffmpeg','-v','error','-f','lavfi','-i',
                        'color=c=0x18324a:s=320x180:r=12:d=1,drawbox=x=145:y=80:w=30:h=20:color=red:t=fill',
                        '-c:v','libx264','-pix_fmt','yuv420p',str(cls.source)])

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def render(self, name, shots, size=None, fps=30):
        spec = {'fps':fps,'size':size or [320,180], 'shots':shots}
        path = self.root/(name+'.json')
        path.write_text(json.dumps(spec))
        dest = self.root/name
        result = camera.render(path,dest)
        return result,dest

    def shot(self, **kwargs):
        return {'source':str(self.source),'duration':1,**kwargs}

    def test_pan_moves_smoothly_on_held_artwork(self):
        result,out = self.render('pan',[self.shot(preset='pan-right')])
        raw = subprocess.check_output(['ffmpeg','-v','error','-i',str(out/'camera.mp4'),'-f','rawvideo','-pix_fmt','rgb24','-'])
        frame_size = 320*180*3
        centers = []
        for offset in range(0,len(raw),frame_size):
            frame=raw[offset:offset+frame_size]
            xs=[]
            for i in range(0,len(frame),3):
                if frame[i]>170 and frame[i+1]<80 and frame[i+2]<80:
                    xs.append((i//3)%320)
            self.assertTrue(xs)
            centers.append(sum(xs)/len(xs))
        self.assertEqual(len(centers),30)
        self.assertGreater(centers[0]-centers[-1],40)
        self.assertTrue(all(a >= b-.25 for a,b in zip(centers,centers[1:])))
        self.assertGreater(len(set(round(x,1) for x in centers)),20)
        self.assertEqual(result['shots'][0]['clamped_frames'],0)
        with self.assertRaisesRegex(ValueError,'Output exists'):
            camera.render(self.root/'pan.json',out)

    def test_mixed_cut_and_dissolve_preserve_frame_count(self):
        result,out=self.render('edit',[self.shot(),self.shot(preset='push-in'),
                                      self.shot(preset='pull-back',transition={'type':'dissolve','seconds':.2})])
        self.assertEqual(result['frames'],84)
        self.assertAlmostEqual(camera.probe(out/'camera.mp4')['duration'],2.8,places=2)
        camera.command(['ffmpeg','-v','error','-xerror','-i',str(out/'camera.mp4'),'-f','null','-'])

    def test_4k_output_dimensions(self):
        result,out=self.render('uhd',[self.shot(duration=2/30)],size=[3840,2160])
        self.assertEqual(result['frames'],2)
        self.assertEqual(result['size'],[3840,2160])
        info=camera.probe(out/'camera.mp4')
        self.assertEqual((info['width'],info['height']),(3840,2160))

    def test_rejects_trim_and_overlapping_transitions(self):
        invalid=[self.shot(start=.8,duration=.5)]
        with self.assertRaisesRegex(ValueError,'past the source'):
            camera.validate({'shots':invalid},self.root)
        invalid=[self.shot(),self.shot(transition={'type':'dissolve','seconds':.8}),self.shot(transition={'type':'dissolve','seconds':.3})]
        with self.assertRaisesRegex(ValueError,'too long'):
            camera.validate({'shots':invalid},self.root)

    def test_aspect_ratio_change_must_be_explicit(self):
        spec={'size':[320,320],'shots':[self.shot()]}
        with self.assertRaisesRegex(ValueError,'Aspect ratios'):
            camera.validate(spec,self.root)
        for fit in ('contain','cover'):
            changed=copy.deepcopy(spec);changed['shots'][0]['fit']=fit
            camera.validate(changed,self.root)


if __name__=='__main__':
    unittest.main()
