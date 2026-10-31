import argparse
import contextlib
import io
import json
import tempfile
import unittest
from concurrent.futures import Future
from pathlib import Path
from unittest.mock import patch

from fbench import cli
from fbench.provenance import file_hash, make_manifest
from fbench.score import Job, score_binary, target_addresses


class InlineExecutor:
    def __init__(self, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def submit(self, fn, job):
        f = Future()
        f.set_result(fn(job))
        return f


class RunIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        binary = self.root / 'data/binaries/O0/p/bin'
        cfg = self.root / 'data/pipeline_data/source_cfgs/O0/p/bin.json'
        binary.parent.mkdir(parents=True)
        cfg.parent.mkdir(parents=True)
        binary.write_bytes(b'binary')
        cfg.write_text('{}')
        self.binary, self.cfg = binary, cfg
        self.program = self.root / 'cli'
        self.program.write_bytes(b'cli')
        self.env = {'fission': {'sha256': file_hash(self.program)}, 'layer': 'nir',
                    'metrics': ['ged']}
        self.args = argparse.Namespace(data=str(self.root / 'data'), opt=[], project=[],
            match=None, limit=None, metrics=['ged'], layer='nir', binary_timeout=60,
            fission_cli=str(self.program), jobs=1, force=False, results=str(self.root / 'results'))

    def manifest(self):
        return make_manifest([('O0', 'p', 'bin', self.binary, self.cfg)], self.env)

    def test_manifest_changes_with_input_and_options(self):
        original = self.manifest()
        self.assertEqual(original, self.manifest())
        self.cfg.write_text('{"changed": true}')
        self.assertNotEqual(original['run_id'], self.manifest()['run_id'])
        self.cfg.write_text('{}')
        self.binary.write_bytes(b'different')
        self.assertNotEqual(original['run_id'], self.manifest()['run_id'])
        self.binary.write_bytes(b'binary')
        self.env['metrics'] = ['byte_match']
        self.assertNotEqual(original['run_id'], self.manifest()['run_id'])

    def test_audit_includes_missing_and_stem_fallback(self):
        (self.binary.parent / 'other').write_bytes(b'no cfg')
        (self.binary.parent / 'tool.exe').write_bytes(b'executable')
        (self.cfg.parent / 'tool.json').write_text('{}')
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            self.assertEqual(cli.cmd_audit(self.args), 0)
        counts = json.loads(stream.getvalue())['counts']
        self.assertEqual(counts, {'exact': 1, 'stem': 1, 'missing': 1})

    def test_score_rejects_changed_input_before_decompilation(self):
        old = file_hash(self.binary)
        self.binary.write_bytes(b'changed')
        job = Job('O0', 'p', 'bin', str(self.binary), str(self.cfg), str(self.root / 'r.json'),
                  str(self.program), run_id='a' * 64, binary_sha256=old,
                  cfg_sha256=file_hash(self.cfg), cli_sha256=file_hash(self.program))
        with patch('fbench.score._score') as worker:
            result = score_binary(job)
        worker.assert_not_called()
        self.assertEqual(result['status'], 'error')
        self.assertIn('input changed', result['error'])

    def test_ambiguous_function_identity_fails_closed(self):
        self.assertEqual(target_addresses({1: {'f', 'unrelated'}}, {'f'}), {1: 'f'})
        with self.assertRaisesRegex(ValueError, 'multiple addresses'):
            target_addresses({1: {'f'}, 2: {'f'}}, {'f'})
        with self.assertRaisesRegex(ValueError, 'share address'):
            target_addresses({1: {'f', 'g'}}, {'f', 'g'})

    def test_resume_isolated_and_failed_rows_retried(self):
        calls = []
        def fake_score(job):
            calls.append(job)
            rec = {'opt': job.opt, 'project': job.project, 'binary': job.binary,
                   'status': 'ok', 'targets': 1, 'produced': 1, 'functions': {'f': {'ged': 0}},
                   'seconds': 0, 'provenance': {'run_id': job.run_id,
                     'binary_sha256': job.binary_sha256, 'cfg_sha256': job.cfg_sha256}}
            out = Path(job.out_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(rec))
            return rec
        with patch('fbench.cli.find_fission_cli', return_value=str(self.program)), \
             patch('fbench.cli.environment', return_value=self.env), \
             patch('fbench.cli.fission_version', return_value='test'), \
             patch('fbench.cli.score_binary', side_effect=fake_score), \
             patch('fbench.cli.ProcessPoolExecutor', InlineExecutor):
            self.assertEqual(cli.cmd_run(self.args), 0)
            self.assertEqual(cli.cmd_run(self.args), 0)
            self.assertEqual(len(calls), 1)
            out = Path(calls[0].out_path)
            rec = json.loads(out.read_text())
            rec['status'] = 'error'
            out.write_text(json.dumps(rec))
            self.assertEqual(cli.cmd_run(self.args), 0)
            self.assertEqual(len(calls), 2)
            self.binary.write_bytes(b'new binary')
            self.assertEqual(cli.cmd_run(self.args), 0)
            self.assertEqual(len(calls), 3)
            self.assertNotEqual(calls[0].run_id, calls[2].run_id)

    def test_report_refuses_missing_or_foreign_results(self):
        self.env['fission']['version'] = 'test'
        manifest = self.manifest()
        root = self.root / 'results/runs' / manifest['run_id']
        root.mkdir(parents=True)
        (root / 'manifest.json').write_text(json.dumps(manifest))
        args = argparse.Namespace(results=str(self.root / 'results'), run_id=manifest['run_id'], layer='nir')
        with patch('fbench.cli.DOCS', self.root / 'docs'):
            self.assertEqual(cli.cmd_report(args), 2)
            out = root / 'binaries/O0/p/bin.nir.json'
            out.parent.mkdir(parents=True)
            out.write_text(json.dumps({'opt':'O0','project':'p','binary':'bin','status':'ok',
                'targets':1,'produced':1,'functions':{'f':{'ged':0}},
                'provenance':{'run_id':'f'*64, 'binary_sha256':manifest['inputs'][0]['binary_sha256'],
                              'cfg_sha256':manifest['inputs'][0]['cfg_sha256']}}))
            self.assertEqual(cli.cmd_report(args), 2)
            rec = json.loads(out.read_text())
            rec['provenance']['run_id'] = manifest['run_id']
            out.write_text(json.dumps(rec))
            self.assertEqual(cli.cmd_report(args), 0)
            summary = json.loads((self.root / 'docs/data/summary.json').read_text())
            self.assertEqual(summary['total']['union'], 100.0)
            self.assertEqual(summary['run_id'], manifest['run_id'])
            rec['functions'] = {'f': {}}
            out.write_text(json.dumps(rec))
            self.assertEqual(cli.cmd_report(args), 2)


if __name__ == '__main__':
    unittest.main()
