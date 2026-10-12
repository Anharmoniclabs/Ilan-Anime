"""Local HTTP contract tests; synthetic PNGs do NOT prove visual generation."""
import copy
import json
from pathlib import Path
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import unittest
from production.asset_registry import AssetRegistry
from production.comfy.local import (Client, ComfyError, ConnectionPaused, graph,
    prepare, submit, poll, preflight, safe_path, digest)
from production.comfy.launch import command

PNG = b'\x89PNG\r\n\x1a\nsynthetic-transport-fixture'

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    def send(self, body, status=200):
        self.send_response(status); self.end_headers()
        self.wfile.write(body if isinstance(body, bytes) else json.dumps(body).encode())
    def do_GET(self):
        s = self.server
        if self.path == '/object_info': self.send(s.info)
        elif self.path == '/queue': self.send({'queue_running': [], 'queue_pending': [s.prompt] if s.prompt else []})
        elif self.path.startswith('/history'):
            self.send({'prompt-1': {'prompt': s.prompt, 'status': {'completed': True, 'status_str': s.result},
                         'outputs': {'9': {'images': [{'filename': 'image.png', 'subfolder': 'ilan', 'type': 'output'}]}}}} if s.complete else {})
        elif self.path.startswith('/view?'): self.send(PNG)
        elif self.path == '/redirect':
            self.send_response(302); self.send_header('Location', 'https://platform.comfy.org'); self.end_headers()
        else: self.send({}, 404)
    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get('Content-Length', 0)))
        s = self.server
        if self.path == '/upload/image': self.send({'name': 'reference.png', 'subfolder': '', 'type': 'input'})
        elif self.path == '/prompt':
            s.posts += 1
            data = json.loads(raw)
            s.prompt = [0, 'prompt-1', data['prompt'], data['extra_data']]
            if s.lose_ack:
                self.connection.shutdown(2); self.connection.close(); return
            self.send({'prompt_id': 'prompt-1', 'number': 0, 'node_errors': {}})
        else: self.send({}, 404)

class ComfyLocalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / 'production').mkdir()
        (self.root / 'production/art_direction.json').write_text(json.dumps({'modes': {'STORY_FRAME': {}}, 'canonical_document': 'art.md'}))
        (self.root / 'art.md').write_text('author style')
        (self.root / 'ref.png').write_bytes(PNG)
        shots = self.root / 'projects/cemi_episode_01/data/shots'; shots.mkdir(parents=True)
        (shots / 'S01-11.json').write_text('{}')
        self.continuity = {'character_ids': ['beheto'], 'costume_ids': ['river'], 'prop_ids': ['drum'], 'time': 'moonless night', 'location': 'river'}
        self.registry = AssetRegistry(self.root)
        self.registry.register(asset_id='reference', path='ref.png', kind='reference', mode='reference', shots=['S01-11'],
            provenance={'creator': 'artist', 'origin': 'test', 'license': 'test', 'source_assets': [], 'notes': 'Synthetic fixture'}, continuity=self.continuity)
        self.registry.transition('reference', 1, 'submitted')
        for kind, target, who in [('technical', 'technical-approved', 'reviewer'), ('author', 'author-approved', 'luis-m-minier')]:
            # Reuse the exact approval structure validated by the existing registry tests.
            from tests.test_asset_registry import AssetRegistryTests
            approval = AssetRegistryTests.approval(kind, approver_id=who, digest=digest(PNG))
            approval['asset_id'] = 'reference'
            self.registry.transition('reference', 1, target, approval)
        self.registry.transition('reference', 1, 'canonical')
        self.spec = {'job_id': 'test-shot', 'shots': ['S01-11'], 'art_mode': 'STORY_FRAME',
            'reference': {'asset_id': 'reference', 'version': 1}, 'seed': 42,
            'positive': 'scripted action', 'negative': 'drift', 'checkpoint': 'local.safetensors',
            'license': 'test only', 'continuity': self.continuity}
        self.path = self.root / 'production/comfy-runs/test-shot/job.json'
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.server.info = {n['class_type']: {'input': {'required': {}}, 'python_module': 'nodes'} for n in graph(self.spec, 'ref.png').values()}
        self.server.info['CheckpointLoaderSimple']['input']['required'] = {'ckpt_name': [['local.safetensors']]}
        self.server.posts = 0; self.server.prompt = None; self.server.complete = True
        self.server.result = 'success'; self.server.lose_ack = False
        thread = threading.Thread(target=self.server.serve_forever, daemon=True); thread.start()
        self.addCleanup(self.server.server_close); self.addCleanup(self.server.shutdown)
        self.client = Client(f'http://127.0.0.1:{self.server.server_port}')

    def prepared(self): return prepare(self.root, self.spec, self.path)

    def test_http_end_to_end_exploratory_and_idempotent_collect(self):
        self.prepared(); self.assertEqual(submit(self.root, self.path, self.client)['state'], 'queued')
        result = poll(self.root, self.path, self.client)
        self.assertEqual('awaiting-review', result['state']); self.assertEqual(1, len(result['outputs']))
        state = AssetRegistry(self.root).verify(check_files=True)
        self.assertEqual('exploratory', state['states'][('test-shot.000', 1)])
        self.assertEqual({}, state['final_uses'])
        poll(self.root, self.path, self.client)
        self.assertEqual(1, self.server.posts)
        with self.assertRaises(ComfyError): submit(self.root, self.path, self.client)

    def test_ack_lost_reconciles_without_second_post(self):
        self.prepared(); self.server.lose_ack = True
        with self.assertRaises(ConnectionPaused): submit(self.root, self.path, self.client)
        self.assertEqual('paused', json.loads(self.path.read_text())['state'])
        with self.assertRaises(ComfyError): poll(self.root, self.path, self.client)
        result = poll(self.root, self.path, self.client, 'APPROVE RESUME test-shot')
        self.assertEqual('awaiting-review', result['state']); self.assertEqual(1, self.server.posts)

    def test_missing_history_is_paused_not_resubmitted(self):
        self.prepared(); submit(self.root, self.path, self.client)
        self.server.complete = False; self.server.prompt = None
        with self.assertRaises(ComfyError): poll(self.root, self.path, self.client)
        self.assertEqual('paused', json.loads(self.path.read_text())['state']); self.assertEqual(1, self.server.posts)

    def test_execution_error_never_registers_output(self):
        self.prepared(); submit(self.root, self.path, self.client); self.server.result = 'error'
        self.assertEqual('failed', poll(self.root, self.path, self.client)['state'])
        self.assertEqual(1, len(AssetRegistry(self.root).summary()['assets']))

    def test_unknown_nodes_and_paid_nodes_rejected(self):
        with self.assertRaises(ComfyError): preflight({'1': {'class_type': 'CloudGenerate', 'inputs': {}}}, {})
        self.server.info['KSampler']['api_node'] = True
        self.prepared()
        with self.assertRaises(ComfyError): submit(self.root, self.path, self.client)
        self.assertEqual(0, self.server.posts)

    def test_missing_checkpoint_stops_before_prompt(self):
        self.spec['checkpoint'] = 'missing.safetensors'; self.prepared()
        with self.assertRaisesRegex(ComfyError, 'Unavailable model'): submit(self.root, self.path, self.client)
        self.assertEqual(0, self.server.posts)

    def test_changed_or_rejected_source_stops_submit(self):
        self.prepared(); self.registry.transition('reference', 1, 'rejected')
        with self.assertRaises(ComfyError): submit(self.root, self.path, self.client)
        self.assertEqual(0, self.server.posts)

    def test_unapproved_source_stops_prepare(self):
        self.registry.transition('reference', 1, 'rejected')
        with self.assertRaises(ComfyError): self.prepared()

    def test_no_remote_endpoint_proxy_credentials_or_redirect(self):
        for url in ['https://platform.comfy.org', 'http://localhost:8188', 'http://user:pw@127.0.0.1', 'http://127.0.0.1/x']:
            with self.assertRaises(ComfyError): Client(url)
        with self.assertRaises(ComfyError): self.client.request('/redirect')

    def test_lora_and_controlnet_graph_wiring(self):
        self.spec.update(lora='style.safetensors', controlnet='pose.safetensors')
        g = graph(self.spec, 'ref.png', 'pose.png')
        self.assertEqual(['2', 0], g['7']['inputs']['model'])
        self.assertEqual(['12', 0], g['7']['inputs']['positive'])
        self.assertEqual('pose.png', g['11']['inputs']['image'])
        with self.assertRaises(ComfyError): self.prepared()

    def test_paths_and_changed_spec(self):
        for name in ['../escape', '/tmp/escape', '.hidden/a']:
            with self.assertRaises(ComfyError): safe_path(self.root, name)
        self.prepared(); job = json.loads(self.path.read_text()); job['spec']['seed'] = 24
        self.path.write_text(json.dumps(job))
        with self.assertRaisesRegex(ComfyError, 'specification changed'): submit(self.root, self.path, self.client)

    def test_launch_flags(self):
        root = self.root / 'ComfyUI'; (root / 'comfy').mkdir(parents=True)
        (root / 'main.py').write_text('')
        (root / 'comfy/cli_args.py').write_text('--offline --disable-all-custom-nodes')
        args = command(root, 'python', cpu=True)
        self.assertIn('--offline', args); self.assertIn('--cpu', args)
        self.assertIn('--disable-all-custom-nodes', args); self.assertNotIn('0.0.0.0', args)

if __name__ == '__main__': unittest.main()
