import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from production.host_handoff import HandoffRegistry
from production.runtime import Ledger, LedgerError
from studio import picture
from studio.paths import sha256, write_json

ROOT = Path(__file__).resolve().parents[1]


class PictureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in (picture.TEMPLATE, 'production/roles.json'):
            dst = self.root / name
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes((ROOT / name).read_bytes())
        roles = json.loads((self.root / 'production/roles.json').read_text())
        for role in roles.values():
            p = self.root / role['skill']; p.parent.mkdir(parents=True, exist_ok=True); p.write_text('Fixture skill')
        for name in (picture.SCRIPT, 'production/art_direction.json', 'art.png'):
            p = self.root / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_text('{}')
        ep, rows, arts, cursor = [], [], [], 0
        departments = {'character': {'action': 'write'}, 'props': {'action': 'pen contact'},
                      'environment_fx': {'action': 'torch', 'script_fx': 'light'}, 'camera': {'script_mode': 'fixed'}}
        for i in range(128):
            shot = f'S{i // 16:02}-{i % 16:02}'
            frames = 210 if i < 127 else 450
            e = {'id': shot, 'frames': frames, 'start_frame': cursor, 'end_frame': cursor + frames, 'script': 'Current action'}
            art = {'shot': shot, 'path': 'art.png', 'sha256': sha256(self.root / 'art.png')}
            ep.append(e); arts.append(art)
            rows.append({'shot': shot, 'frames': frames, 'start_frame': cursor, 'end_frame_exclusive': cursor + frames,
                         'artwork': art, 'action_contract': {'departments': departments}, 'draft': None, 'status': 'missing'})
            cursor += frames
        write_json(self.root / picture.EPISODE, {'shots': ep})
        write_json(self.root / picture.ART, {'shots': arts})
        write_json(self.root / picture.TIMELINE, {'shots': rows, 'fps': 24})

    def test_catalog_covers_episode_without_creating_workers(self):
        p = picture.plan(self.root)
        self.assertEqual(128, len(p['shots']))
        self.assertEqual(21, len(p['stages']))
        self.assertFalse(p['canonical_delivery_allowed'])
        self.assertEqual([], list(self.root.glob('production/runs/*/ledger.json')))
        self.assertEqual(p, picture.plan(self.root))

    def test_stage_contracts_and_independent_skills_reach_ledger(self):
        ledger = picture.start('S00-00', root=self.root)
        self.assertEqual(['script-timing'], ledger.ready())
        keys = ledger._task('keys')
        self.assertIn('layout', keys['depends_on'])
        self.assertIn('registered key drawings', keys['completion_contract']['required_artifact_kinds'])
        self.assertEqual(['write'], keys['full_scene_action']['character'])
        self.assertTrue(keys['require_host_bindings'])
        self.assertNotIn('mix', ledger._task('edit')['depends_on'])
        self.assertIn('draft-review', ledger.data['tasks'])
        self.assertFalse(any(t['requires_author_approval'] for t in ledger.data['tasks'].values()))
        self.assertEqual(ledger.data, picture.start('S00-00', root=self.root).data)

    def test_final_template_is_not_weakened(self):
        t = json.loads((self.root / picture.TEMPLATE).read_text()); original = copy.deepcopy(t)
        picture.profile(t)
        self.assertEqual(original, t)
        self.assertTrue(next(s for s in t['stages'] if s['id'] == 'qa')['requires_author_approval'])

    def test_changed_art_blocks_dispatch_before_reserving_task(self):
        ledger = picture.start('S00-00', root=self.root)
        (self.root / 'art.png').write_text('changed')
        with self.assertRaisesRegex(picture.PictureError, 'Artwork changed'):
            picture.handoff(ledger.run, 'script-timing', root=self.root)
        self.assertEqual('pending', Ledger(self.root, ledger.run)._task('script-timing')['state'])

    def test_real_host_handoff_has_reference_and_both_skills(self):
        ledger = picture.start('S00-00', root=self.root)
        job = picture.handoff(ledger.run, 'script-timing', root=self.root)
        self.assertEqual(['art.png'], job['reference_images'])
        self.assertNotEqual(job['skill'], job['reviewer_skill'])
        self.assertIn('completion_contract', job['prompt'])
        with self.assertRaises(ValueError):
            picture.handoff(ledger.run, 'script-timing', root=self.root)

    def test_paused_shot_does_not_block_other_shot_or_resume_itself(self):
        first = picture.start('S00-00', root=self.root); first.pause('missing actual drawings')
        second = picture.start('S00-01', root=self.root)
        self.assertEqual(['script-timing'], second.ready())
        self.assertTrue(picture.start('S00-00', root=self.root).data['paused'])

    def test_partial_planning_recovers_without_resetting_tasks(self):
        original = Ledger.add
        def interrupted(ledger, task):
            if task['id'] == 'asset-register':
                raise RuntimeError('simulated planning interruption')
            return original(ledger, task)
        with patch.object(Ledger, 'add', interrupted), self.assertRaises(RuntimeError):
            picture.start('S00-00', root=self.root)
        ledger = picture.start('S00-00', root=self.root)
        self.assertEqual(21, len(ledger.data['tasks']))
        self.assertEqual(21, sum(e['action'] == 'add' for e in ledger.data['events']))

    def test_failed_handoff_preparation_does_not_reserve_worker(self):
        ledger = picture.start('S00-00', root=self.root)
        with patch.object(picture, 'write_json', side_effect=OSError('disk unavailable')):
            with self.assertRaises(OSError):
                picture.handoff(ledger.run, 'script-timing', root=self.root)
        current = Ledger(self.root, ledger.run)
        self.assertEqual('pending', current._task('script-timing')['state'])
        self.assertFalse(any(e['action'] == 'dispatch' for e in current.data['events']))

    def test_interrupted_reservation_recovers_saved_job_without_redispatch(self):
        ledger = picture.start('S00-00', root=self.root)
        dispatch = Ledger.dispatch

        def interrupted(instance, task_id, alias):
            dispatch(instance, task_id, alias)
            raise OSError('interrupted after reservation persisted')

        with patch.object(Ledger, 'dispatch', interrupted):
            with self.assertRaises(OSError):
                picture.handoff(ledger.run, 'script-timing', root=self.root)
        job_path = ledger.run_dir / 'handoff-jobs/script-timing.json'
        self.assertTrue(job_path.is_file())
        self.assertEqual('running', Ledger(self.root, ledger.run)._task('script-timing')['state'])
        with self.assertRaises(ValueError):
            picture.handoff(ledger.run, 'script-timing', root=self.root)
        job = picture.handoff(ledger.run, 'script-timing', root=self.root, recover=True)
        self.assertEqual('script-timing', job['task'])
        self.assertIn('completion_contract', job['prompt'])
        self.assertEqual(['art.png'], job['reference_images'])
        current = Ledger(self.root, ledger.run)
        self.assertEqual(1, sum(e['action'] == 'dispatch' for e in current.data['events']))

    def test_recovery_never_offers_a_bound_worker_again(self):
        ledger = picture.start('S00-00', root=self.root)
        picture.handoff(ledger.run, 'script-timing', root=self.root)
        HandoffRegistry(self.root, ledger.run).bind_creator(
            'script-timing', 'synthetic-test-host', 'actual-fixture-worker')
        with self.assertRaises(ValueError):
            picture.handoff(ledger.run, 'script-timing', root=self.root, recover=True)
        current = Ledger(self.root, ledger.run)
        self.assertEqual(1, sum(e['action'] == 'dispatch' for e in current.data['events']))

    def test_recovery_requires_inspection_when_a_result_exists(self):
        ledger = picture.start('S00-00', root=self.root)
        picture.handoff(ledger.run, 'script-timing', root=self.root)
        result = self.root / ledger._task('script-timing')['output_dir'] / 'result.json'
        result.write_text('{"status": "blocked", "blockers": ["saved work requires inspection"]}')
        with self.assertRaises(ValueError):
            picture.handoff(ledger.run, 'script-timing', root=self.root, recover=True)

    def test_unrelated_timeline_relink_and_catalog_refresh_preserve_active_packet(self):
        ledger = picture.start('S00-00', root=self.root)
        packet_path = ledger.run_dir / 'picture-packet.json'
        packet = json.loads(packet_path.read_text())
        timeline_path = self.root / picture.TIMELINE
        timeline = json.loads(timeline_path.read_text())
        timeline['shots'][1]['status'] = 'reviewed-draft-fixture'
        timeline['shots'][1]['draft'] = {'path': 'unrelated-shot-review.mp4'}
        write_json(timeline_path, timeline)
        picture.verify_packet(self.root, packet)
        picture.plan(self.root, refresh=True)
        self.assertEqual(ledger.data, picture.start('S00-00', root=self.root).data)
        self.assertEqual(packet, json.loads(packet_path.read_text()))
        job = picture.handoff(ledger.run, 'script-timing', root=self.root)
        self.assertEqual('script-timing', job['task'])

    def test_selected_shot_changes_fail_packet_verification(self):
        ledger = picture.start('S00-00', root=self.root)
        packet = json.loads((ledger.run_dir / 'picture-packet.json').read_text())

        def change_script(data):
            data['shots'][0]['script'] = 'Changed current action'

        def change_contract(data):
            data['shots'][0]['action_contract']['departments']['character']['action'] = 'Changed contact'

        def change_art_selection(data):
            data['shots'][0]['path'] = 'alternate.png'
            data['shots'][0]['sha256'] = sha256(self.root / 'alternate.png')

        (self.root / 'alternate.png').write_text('different fixture image')
        for source, mutation in ((picture.EPISODE, change_script),
                                 (picture.TIMELINE, change_contract),
                                 (picture.ART, change_art_selection)):
            p = self.root / source
            original = p.read_bytes()
            try:
                data = json.loads(original)
                mutation(data)
                write_json(p, data)
                with self.subTest(source=source), self.assertRaises(ValueError):
                    picture.verify_packet(self.root, packet)
            finally:
                p.write_bytes(original)

    def test_packet_pins_repair_reports_and_art_direction(self):
        repair = 'repair-report.md'
        (self.root / repair).write_text('original contact repair instructions')
        ledger = picture.start('S00-00', root=self.root, repairs=[repair])
        packet = json.loads((ledger.run_dir / 'picture-packet.json').read_text())
        for source in (repair, 'production/art_direction.json'):
            p = self.root / source
            original = p.read_bytes()
            try:
                p.write_text('changed instructions')
                with self.subTest(source=source), self.assertRaises(ValueError):
                    picture.verify_packet(self.root, packet)
            finally:
                p.write_bytes(original)

    def test_corrupt_timing_and_escaping_references_rejected(self):
        p = self.root / picture.EPISODE; d = json.loads(p.read_text()); d['shots'][1]['start_frame'] += 1; write_json(p, d)
        with self.assertRaisesRegex(picture.PictureError, 'Timing mismatch'):
            picture.plan(self.root)
        with self.assertRaises(picture.PictureError):
            picture.path(self.root, '../outside')


if __name__ == '__main__':
    unittest.main()
