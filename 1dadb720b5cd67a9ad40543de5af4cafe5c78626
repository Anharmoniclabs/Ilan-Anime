from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

from studio import episode
from studio.paths import load_json, write_json


class EpisodeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'ref.png'
        Image.new('RGB', (160, 90), 'navy').save(self.source)
        self.script = self.root / 'source.json'
        write_json(self.script, {'shots': [{'id':'S01-01', 'frames':144, 'start_frame':0,
                                          'script':'One paddle stroke.', 'keyframes':['ref.png']}]})
        for name, value in [('ROOT',self.root),('PROJECT',self.root),('EPISODE',self.script)]:
            p=patch.object(episode,name,value); p.start(); self.addCleanup(p.stop)
        self.out=self.root/'queue'
        episode.initialize(self.out)

    def test_one_submission_then_review_gate(self):
        submitted=[]
        def submit(path): submitted.append(path)
        def export(job,target): target.write_bytes(b'test-only')
        result=episode.run(self.out,submit=submit,importer=lambda p:None,exporter=export)
        self.assertEqual(result['state'],'awaiting_motion_review')
        self.assertEqual(len(submitted),1)
        with self.assertRaises(episode.EpisodeError):
            episode.run(self.out,submit=lambda p:self.fail('submitted twice'))

    def test_unknown_remote_outcome_is_sticky(self):
        def fail(path): raise TimeoutError('unknown outcome')
        with self.assertRaises(TimeoutError):
            episode.run(self.out,submit=fail)
        self.assertEqual(episode.summary(self.out)['state'],'paused')
        with self.assertRaises(episode.EpisodeError):
            episode.run(self.out,submit=lambda p:self.fail('retry'))

    def test_changed_reference_stops_before_network(self):
        Image.new('RGB',(160,90),'red').save(self.source)
        result=episode.run(self.out,submit=lambda p:self.fail('network called'))
        self.assertEqual(result['state'],'paused')

    def test_partial_episode_cannot_be_assembled(self):
        with self.assertRaises(episode.EpisodeError): episode.assemble(self.out)

    def test_initialization_is_idempotent(self):
        original=(self.out/'episode.json').read_bytes()
        episode.initialize(self.out)
        self.assertEqual(original,(self.out/'episode.json').read_bytes())

    def test_changed_script_stops(self):
        write_json(self.script,{'shots':[]})
        with self.assertRaises(episode.EpisodeError):
            episode.run(self.out,submit=lambda p:self.fail('network called'))

    def test_uncertain_local_output_is_not_overwritten(self):
        target=self.out/'jobs/S01-01'
        target.mkdir(parents=True)
        with self.assertRaises(episode.EpisodeError):
            episode.run(self.out,submit=lambda p:self.fail('network called'))
        self.assertEqual(episode.summary(self.out)['state'],'paused')

    def candidate(self):
        episode.run(self.out,submit=lambda p:None,importer=lambda p:None,
                    exporter=lambda job,target:target.write_bytes(b'draft-candidate'))

    def test_independent_review_advances_draft_without_author_approval(self):
        self.candidate()
        def reviewer(directory,row):
            return {'decision':'approve','evidence':['Inspected actual frames'],
                    'repair_notes':[],'reviewer_thread_id':'test-reviewer',
                    'output_sha256':row['output_sha256']}
        result=episode.review(self.out,reviewer=reviewer)
        self.assertEqual(result['state'],'ready')
        row=load_json(self.out/'episode.json')['shots'][0]
        self.assertEqual(row['state'],'draft_ready')
        self.assertNotIn('author_approval',row)

    def test_rejected_motion_stops_automation(self):
        self.candidate()
        def reviewer(directory,row):
            return {'decision':'reject','evidence':['Paddle deforms at frame 10'],
                    'repair_notes':['Repair paddle geometry'],'reviewer_thread_id':'test-reviewer',
                    'output_sha256':row['output_sha256']}
        self.assertEqual(episode.review(self.out,reviewer=reviewer)['state'],'needs_repair')
        with patch.object(episode,'run',side_effect=AssertionError('continued after rejection')):
            self.assertEqual(episode.auto(self.out)['state'],'needs_repair')

    def test_review_is_bound_to_exact_output(self):
        self.candidate()
        with self.assertRaises(episode.EpisodeError):
            episode.review(self.out,reviewer=lambda d,r:{'decision':'approve','evidence':['test'],
                           'reviewer_thread_id':'test-reviewer','output_sha256':'wrong'})
        self.assertEqual(episode.summary(self.out)['state'],'paused')


if __name__=='__main__': unittest.main()
