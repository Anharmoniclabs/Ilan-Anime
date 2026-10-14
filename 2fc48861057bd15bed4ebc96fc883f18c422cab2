import unittest
from episode import split_fx, drawing_at, intake


class EpisodeTests(unittest.TestCase):
    def test_nested_effect_arguments_survive_import(self):
        fx = split_fx('AIRBRUSH_RIBBONS(blue,gold; count 40; 2s); STREAK_CEL')
        self.assertEqual(fx, [dict(name='AIRBRUSH_RIBBONS', args='blue,gold; count 40; 2s'),
                              dict(name='STREAK_CEL', args='')])

    def test_malformed_effect_fails(self):
        with self.assertRaises(ValueError): split_fx('PRESS(0.9; FILM_GRAIN')

    def test_hold_and_loop_boundaries(self):
        track = [[0,3], [2,6], [1,3]]
        self.assertEqual([drawing_at(track, f) for f in (0,2,3,8,9,11,12,40)],
                         [0,0,2,2,1,1,1,1])
        self.assertEqual(drawing_at(track, 12, loop=True), 0)
        self.assertEqual(drawing_at(track, 15, loop=True), 2)

    def test_episode_timeline_and_repaired_import(self):
        data = intake()
        self.assertEqual(len(data['shots']), 128)
        self.assertEqual(sum(s['frames'] for s in data['shots']), 27120)
        shot = next(s for s in data['shots'] if s['id']=='S14-08')
        press = next(f for f in shot['fx'] if f['name']=='PRESS')
        self.assertIn('ONLY the tapping hand keeps color', press['args'])


if __name__ == '__main__': unittest.main()
