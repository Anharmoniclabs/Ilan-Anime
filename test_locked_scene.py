import tempfile
import unittest
import json
import subprocess
from pathlib import Path

from camera_motion import track, command
from locked_scene import check_regions, check_camera, cell, render


class LayoutLocks(unittest.TestCase):
    def test_no_intrusion(self):
        with self.assertRaisesRegex(ValueError,'overlap'):
            check_regions([{'rect':[0,0,40,40]},{'rect':[30,30,40,40]}],[100,100])
        check_regions([{'rect':[0,0,40,40]},{'rect':[40,0,40,40]}],[100,100])

    def test_bounds_and_stretch_are_rejected(self):
        for region in [{'rect':[80,0,40,40]}, {'rect':[0,0,40,40],'scale_x':2}, {'rect':[0,0,0,10]}]:
            with self.assertRaises(ValueError): check_regions([region],[100,100])

    def test_camera_cannot_cut_subject(self):
        keys=track([{'at':0},{'at':1,'zoom':1.2}])
        with self.assertRaisesRegex(ValueError,'clips'):
            check_camera(keys,[[.01,.01,.98,.98]],60)
        check_camera(keys,[[.3,.3,.4,.4]],60)

    def test_intermediate_camera_samples_checked(self):
        keys=track([{'at':0},{'at':.5,'zoom':2,'x':.25},{'at':1}])
        with self.assertRaises(ValueError): check_camera(keys,[[.6,.4,.1,.1]],61)

    def test_sheet_with_wrong_aspect_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'wide.png'
            command(['ffmpeg','-v','error','-f','lavfi','-i','color=red:s=200x100','-frames:v','1',str(source)])
            with self.assertRaisesRegex(ValueError,'aspect'):
                cell(source,1,1,0,[100,100],Path(tmp)/'cel.png')

    def test_actual_composite_changes_only_its_region(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            for name,size,color in [('plate','160x90','black'),('a','32x32','red'),('b','32x32','blue')]:
                command(['ffmpeg','-v','error','-f','lavfi','-i',f'color={color}:s={size}',
                         '-frames:v','1',str(base/(name+'.png'))])
            spec=dict(plate='plate.png',duration=2/30,fps=30,regions=[dict(name='test',rect=[64,24,32,32],
                      cels=['a.png','b.png'],timeline=[0,1],feather=2)])
            path=base/'spec.json'; path.write_text(json.dumps(spec))
            render(path,base/'result')
            raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(base/'result/scene.mp4'),'-f','rawvideo','-pix_fmt','rgb24','-'])
            length=160*90*3
            self.assertEqual(len(raw),length*2)
            a,b=raw[:length],raw[length:]
            center=(40*160+80)*3
            self.assertGreater(a[center],200); self.assertGreater(b[center+2],200)
            for y in range(0,16):
                self.assertEqual(a[y*160*3:(y+1)*160*3],b[y*160*3:(y+1)*160*3])


if __name__=='__main__': unittest.main()
