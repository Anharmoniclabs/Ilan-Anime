import copy
import json
from pathlib import Path
import unittest

from vintage_motion import positions, validate


class VintageTravel(unittest.TestCase):
    def setUp(self):
        self.spec=json.loads((Path(__file__).parent/'river-opening/vintage-90s/shot.json').read_text())

    def test_tracking_does_not_cancel_boat_travel(self):
        validate(self.spec)
        first,last=positions(self.spec,0),positions(self.spec,191)
        self.assertEqual(last['camera_x']-first['camera_x'],104)
        self.assertEqual(last['boat_world_x']-first['boat_world_x'],220)
        self.assertEqual(last['boat_screen_x']-first['boat_screen_x'],116)
        xs=[positions(self.spec,n)['boat_screen_x'] for n in range(192)]
        self.assertTrue(all(b>a for a,b in zip(xs,xs[1:])))

    def test_canoes_stay_inside_picture_for_entire_pan(self):
        for n in range(192):
            p=positions(self.spec,n)
            self.assertGreaterEqual(p['boat_screen_x'],0)
            self.assertLessEqual(p['boat_screen_x']+self.spec['fleet_width'],1280)
        broken=copy.deepcopy(self.spec);broken['boat_travel']=400
        with self.assertRaises(ValueError):validate(broken)

    def test_camera_cannot_pan_past_painted_background(self):
        self.spec['camera_pan']=200
        with self.assertRaises(ValueError):validate(self.spec)


if __name__=='__main__':unittest.main()
