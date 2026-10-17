"""Filesystem checks for explicit conflict finishing; standard library only."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('conflict_finish', HERE / 'finish.py')
f = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(f)


class FinishTests(unittest.TestCase):
    def setUp(self):
        scratch = Path.cwd() / 'test' / 'scratch'
        scratch.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.inputs = [self.root / side for side in ('base', 'ours', 'theirs')]
        for folder in self.inputs:
            folder.mkdir()
            (folder / 'clash.txt').write_bytes(b'first\r\nbase\r\n')
            (folder / 'remove.txt').write_bytes(b'old\n')
            (folder / 'keep.txt').write_bytes(b'keep\n')
        (self.inputs[1] / 'clash.txt').write_bytes(b'first\r\nours\r\n')
        (self.inputs[2] / 'clash.txt').write_bytes(b'first\r\ntheirs\r\n')
        (self.inputs[1] / 'remove.txt').write_bytes(b'edited\n')
        (self.inputs[2] / 'remove.txt').unlink()
        (self.inputs[1] / 'addition.txt').write_bytes('café\n'.encode())
        self.packet = self.root / 'packet.json'
        self.decisions = self.root / 'decisions.json'
        self.output = self.root / 'finished'
        self.pin()
        self.write_decisions({
            'clash.txt': {'candidate': 'first\r\nours and theirs\r\n',
                          'reason': 'Combined both edited lines after review.'},
            'remove.txt': {'candidate': 'edited\n',
                           'reason': 'Kept the correction despite the deletion.'}})

    def pin(self):
        self.packet.write_text(json.dumps(f.r.tree.from_directories(self.inputs)), encoding='utf-8')
        self.digest = hashlib.sha256(self.packet.read_bytes()).hexdigest()

    def write_decisions(self, choices):
        self.decisions.write_text(json.dumps({
            'schema': 'conflict-finish/v1', 'packet_sha256': self.digest,
            'decisions': choices}), encoding='utf-8')

    def run_finish(self, **changes):
        args = dict(packet_path=self.packet, inputs=self.inputs,
                    decisions_path=self.decisions, output=self.output,
                    expected_sha256=self.digest)
        args.update(changes)
        return f.finish(**args)

    def test_stages_all_explicit_resolutions_and_preserves_inputs(self):
        before = {path: path.read_bytes() for folder in self.inputs for path in folder.rglob('*') if path.is_file()}
        receipt = self.run_finish()
        self.assertEqual((self.output / 'clash.txt').read_bytes(), b'first\r\nours and theirs\r\n')
        self.assertEqual((self.output / 'remove.txt').read_bytes(), b'edited\n')
        self.assertEqual((self.output / 'addition.txt').read_bytes(), 'café\n'.encode())
        self.assertEqual((self.output / 'keep.txt').read_bytes(), b'keep\n')
        self.assertEqual(before, {path: path.read_bytes() for path in before})
        self.assertEqual(set(receipt['resolutions']), {'clash.txt', 'remove.txt'})
        self.assertEqual(receipt['manifest'], f.r.tree.manifest(f.r.tree.snapshot(self.output, [0])))
        self.assertEqual(receipt['packet_sha256'], self.digest)

    def test_missing_extra_and_implicit_change_refused(self):
        choices = json.loads(self.decisions.read_text())['decisions']
        for altered in ({'clash.txt': choices['clash.txt']},
                        {**choices, 'keep.txt': {'candidate': 'changed', 'reason': 'No.'}}):
            self.write_decisions(altered)
            with self.assertRaises(ValueError):
                self.run_finish()
            self.assertFalse(self.output.exists())

    def test_stale_source_and_rehashed_packet_refused(self):
        (self.inputs[0] / 'keep.txt').write_text('changed\n')
        with self.assertRaises(f.export.Refused):
            self.run_finish()
        (self.inputs[0] / 'keep.txt').write_text('keep\n')
        packet = json.loads(self.packet.read_text())
        packet['files'][0]['candidate'] = 'injected'
        self.packet.write_text(json.dumps(packet))
        self.digest = hashlib.sha256(self.packet.read_bytes()).hexdigest()
        self.write_decisions(json.loads(self.decisions.read_text())['decisions'])
        with self.assertRaises(f.export.Refused):
            self.run_finish()
        self.assertFalse(self.output.exists())

    def test_wrong_pin_and_decision_packet_hash_refused(self):
        with self.assertRaises(ValueError):
            self.run_finish(expected_sha256='0' * 64)
        decisions = json.loads(self.decisions.read_text())
        decisions['packet_sha256'] = '0' * 64
        self.decisions.write_text(json.dumps(decisions))
        with self.assertRaises(ValueError):
            self.run_finish()

    def test_bad_decision_schema_and_text_refused(self):
        good = json.loads(self.decisions.read_text())['decisions']
        bad = dict(good)
        bad['clash.txt'] = {'candidate': 'x\x00y', 'reason': 'Chosen'}
        for choices in (bad, {**good, 'clash.txt': {'candidate': '', 'reason': ''}},
                        {**good, 'clash.txt': {'candidate': 3, 'reason': 'Chosen'}},
                        {**good, 'clash.txt': {'candidate': '', 'reason': 'Chosen', 'extra': 1}}):
            self.write_decisions(choices)
            with self.assertRaises(ValueError):
                self.run_finish()
            self.assertFalse(self.output.exists())

    def test_explicit_delete_and_existing_output(self):
        choices = json.loads(self.decisions.read_text())['decisions']
        choices['remove.txt'] = {'candidate': None, 'reason': 'Deletion accepted after review.'}
        self.write_decisions(choices)
        receipt = self.run_finish()
        self.assertIn('remove.txt', receipt['omitted'])
        self.assertFalse((self.output / 'remove.txt').exists())
        with self.assertRaises(ValueError):
            self.run_finish()

    def test_file_directory_collision_must_be_resolved(self):
        for folder in self.inputs:
            (folder / 'slot').write_text('base\n')
        (self.inputs[1] / 'slot').write_text('ours\n')
        (self.inputs[2] / 'slot').unlink()
        (self.inputs[2] / 'slot').mkdir()
        (self.inputs[2] / 'slot' / 'child.txt').write_text('child\n')
        self.pin()
        report = f.r.tree.from_directories(self.inputs)
        choices = {entry['path']: {'candidate': None, 'reason': 'Resolve path collision.'}
                   for entry in report['files'] if entry['status'].endswith('conflict')}
        choices['slot']['candidate'] = 'selected\n'
        choices['slot/child.txt']['candidate'] = 'child\n'
        self.write_decisions(choices)
        with self.assertRaisesRegex(ValueError, 'collision'):
            self.run_finish()
        choices['slot/child.txt']['candidate'] = None
        self.write_decisions(choices)
        self.run_finish()
        self.assertEqual((self.output / 'slot').read_text(), 'selected\n')

    def test_workspace_boundary_symlink_and_rollback(self):
        link = self.root / 'link'
        link.symlink_to(self.inputs[0], target_is_directory=True)
        for target in (self.inputs[0] / 'nested', link / 'new', Path('/tmp/outside-finish')):
            with self.assertRaises(ValueError):
                self.run_finish(output=target)
        self.decisions.unlink()
        self.decisions.symlink_to(self.packet)
        with self.assertRaises(ValueError):
            self.run_finish()
        self.decisions.unlink()
        self.write_decisions({
            'clash.txt': {'candidate': 'resolved\n', 'reason': 'Reviewed both versions.'},
            'remove.txt': {'candidate': None, 'reason': 'Reviewed deletion.'}})
        original = Path.open
        def fail(path, mode='r', *args, **kwargs):
            if path.is_relative_to(self.output) and mode == 'xb':
                raise OSError('simulated write failure')
            return original(path, mode, *args, **kwargs)
        with patch.object(Path, 'open', fail):
            with self.assertRaises(OSError):
                self.run_finish()
        self.assertFalse(self.output.exists())

    def test_cli_real_files(self):
        command = [sys.executable, '-B', str(HERE / 'finish.py'), str(self.packet),
                   *map(str, self.inputs), str(self.decisions), str(self.output),
                   '--expected-sha256', self.digest]
        result = subprocess.run(command, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['schema'], 'conflict-finish-receipt/v1')


if __name__ == '__main__':
    unittest.main()
