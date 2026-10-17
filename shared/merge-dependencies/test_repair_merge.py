"""Integration checks for the merged-catalog repair proposal."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

import repair_merge


class RepairMergeTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).parent / 'examples'
        self.paths = [root / f'{part}.json' for part in ('base', 'ours', 'theirs')]
        self.texts = [p.read_text() for p in self.paths]

    def test_real_requests_merge_proposes_minimum_removal(self):
        before = [p.read_bytes() for p in self.paths]
        result = repair_merge.check(*self.texts)
        self.assertEqual(result['status'], 'repair_proposed')
        self.assertEqual(result['checked_merge']['status'], 'unsatisfiable')
        proposal = result['repair']
        self.assertEqual(proposal['minimum_removed_count'], 1)
        self.assertEqual(proposal['removed'], {'idna': '>=3.10'})
        self.assertEqual(proposal['selected']['idna'], '2.10')
        self.assertEqual(proposal['fully_rejected_removal_sizes'], [0])
        self.assertEqual(before, [p.read_bytes() for p in self.paths])

    def test_repair_budget_keeps_result_inconclusive(self):
        result = repair_merge.check(*self.texts, max_trials=1)
        self.assertEqual(result['status'], 'inconclusive')
        self.assertEqual(result['repair']['status'], 'inconclusive')

    def test_text_conflict_skips_repair(self):
        base, ours, theirs = self.texts
        result = repair_merge.check(base, ours.replace('requests', 'Requests'),
                                    theirs.replace('requests', 'REQUESTS'))
        self.assertEqual(result['status'], 'text_conflict')
        self.assertIsNone(result['repair'])

    def test_repair_budget_validated_even_without_a_proposal(self):
        with self.assertRaises(ValueError):
            repair_merge.check(*self.texts, max_trials=0)

    def test_demo_exit_and_json(self):
        p = subprocess.run([sys.executable, '-B', str(Path(__file__).parent / 'repair_merge.py'),
                            'demo'], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(json.loads(p.stdout)['status'], 'repair_proposed')


if __name__ == '__main__':
    unittest.main()
