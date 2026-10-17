import copy
import importlib.util
import itertools
import json
from pathlib import Path
import random
import subprocess
import sys
import unittest

spec = importlib.util.spec_from_file_location('root_repair', Path(__file__).with_name('repair.py'))
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


class RepairTests(unittest.TestCase):
    def conflict(self):
        return {'packages': {'a': {'1': {'x': '==1'}},
                             'b': {'1': {'x': '==2'}},
                             'c': {'1': {'x': '==2'}},
                             'x': {'1': {}, '2': {}}},
                'roots': {'a': '*', 'b': '*', 'c': '*'}}

    def test_minimum_cardinality_not_just_irreducible(self):
        result = r.repair(self.conflict())
        self.assertEqual(result['minimum_removed_count'], 1)
        self.assertEqual(result['removed'], {'a': '*'})
        self.assertEqual(result['selected'], {'b': '1', 'c': '1', 'x': '2'})
        self.assertEqual(result['fully_rejected_removal_sizes'], [0])

    def test_compatible(self):
        data = self.conflict()
        data['roots'] = {'a': '*'}
        result = r.repair(data)
        self.assertEqual(result['status'], 'compatible')
        self.assertEqual(result['removed'], {})
        self.assertEqual(result['minimum_removed_count'], 0)

    def test_all_roots_removed_and_cycles(self):
        data = {'packages': {'a': {'1': {'a': '==2'}}}, 'roots': {'a': '*'}}
        result = r.repair(data)
        self.assertEqual(result['remaining_roots'], {})
        self.assertEqual(result['selected'], {})
        self.assertEqual(result['minimum_removed_count'], 1)

    def test_missing_roots(self):
        result = r.repair({'packages': {}, 'roots': {'a': '*', 'b': '*'}})
        self.assertEqual(result['minimum_removed_count'], 2)
        self.assertEqual(result['trials'], 4)

    def test_removed_root_can_still_be_transitive(self):
        data = {'packages': {'a': {'1': {'b': '==1'}}, 'b': {'1': {}, '2': {}}},
                'roots': {'a': '*', 'b': '==2'}}
        # Canonical a-removal wins the tie; force it to be impossible on its own.
        data['packages']['b']['2'] = {'missing': '*'}
        result = r.repair(data)
        self.assertEqual(result['removed'], {'b': '==2'})
        self.assertEqual(result['selected'], {'a': '1', 'b': '1'})
        self.assertEqual(result['trials'], 3)

    def test_shared_budgets_and_exact_boundary(self):
        data = self.conflict()
        complete = r.repair(data)
        self.assertEqual(r.repair(data, complete['steps'], complete['trials']),
                         dict(complete, max_steps=complete['steps'], max_trials=complete['trials']))
        for kwargs in ({'max_steps': 1}, {'max_trials': 1},
                       {'max_steps': complete['steps'] - 1}):
            result = r.repair(data, **kwargs)
            self.assertEqual(result['status'], 'inconclusive')
            self.assertNotIn('minimum_removed_count', result)
            self.assertLessEqual(result['steps'], result['max_steps'])
            self.assertLessEqual(result['trials'], result['max_trials'])

    def test_empty_roots_need_no_search_budget(self):
        result = r.repair({'packages': {}, 'roots': {'a': '*'}}, max_steps=1)
        self.assertEqual(result['status'], 'repaired')
        self.assertEqual(result['steps'], 1)

    def test_normalization_digest_and_immutability(self):
        data = {'packages': {'A_B': {'1': {}}}, 'roots': {'a.b': '*'}}
        before = copy.deepcopy(data)
        first = r.repair(data)
        second = r.repair({'packages': {'a-b': {'1': {}}}, 'roots': {'A-B': '*'}})
        self.assertEqual(first, second)
        self.assertEqual(data, before)
        self.assertEqual(first, r.repair(data))

    def test_invalid_input_and_budgets(self):
        for value in (True, 0, -1, 1000001, 1.5):
            for key in ('max_steps', 'max_trials'):
                with self.assertRaises(r.fmt.Invalid):
                    r.repair(self.conflict(), **{key: value})
        for data in ({'packages': {}, 'roots': {}},
                     {'packages': {}, 'roots': {'a': '~1'}}):
            with self.assertRaises(r.fmt.Invalid):
                r.repair(data)

    def test_bad_solver_witness_rejected(self):
        original = r.fmt.solve
        try:
            r.fmt.solve = lambda *args: {'status': 'resolved', 'selected': {}, 'steps': 1}
            with self.assertRaises(r.fmt.Invalid):
                r.repair(self.conflict())
        finally:
            r.fmt.solve = original

    def test_seeded_independent_oracle(self):
        rng = random.Random(2404)
        for _ in range(250):
            names = ['a', 'b', 'c', 'd']
            packages = {p: {v: {q: rng.choice(['==1', '==2', '*', '!=1'])
                                      for q in names + ['missing'] if rng.random() < .17}
                            for v in ['1', '2'] if rng.random() < .8} for p in names}
            roots = {p: rng.choice(['*', '==1', '==2'])
                     for p in rng.sample(names, rng.randint(1, 4))}
            data = {'packages': packages, 'roots': roots}
            result = r.repair(data)
            expected = None
            for size in range(len(roots) + 1):
                for removed in itertools.combinations(sorted(roots), size):
                    kept = {p: s for p, s in roots.items() if p not in removed}
                    trial = (r.checker.exhaustive({'packages': packages, 'roots': kept})
                             if kept else {'status': 'resolved'})
                    if trial['status'] == 'resolved':
                        expected = removed
                        break
                if expected is not None:
                    break
            self.assertEqual(list(result['removed']), list(expected))
            self.assertEqual(result['minimum_removed_count'], len(expected))
            self.assertEqual(r.checker.assignment(packages, result['remaining_roots'],
                                                 result['selected']), result['selected'])

    def test_real_snapshot_cli_and_budget_codes(self):
        command = [sys.executable, '-B', str(Path(__file__).with_name('repair.py')), 'demo']
        run = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        result = json.loads(run.stdout)
        self.assertEqual(result['minimum_removed_count'], 1)
        self.assertEqual(result['removed'], {'idna': '>=3.10'})
        limited = subprocess.run(command + ['--max-trials', '1'], capture_output=True, text=True)
        self.assertEqual(limited.returncode, 3)
        invalid = subprocess.run(command + ['--max-steps', '0'], capture_output=True, text=True)
        self.assertEqual(invalid.returncode, 2)


if __name__ == '__main__':
    unittest.main()
