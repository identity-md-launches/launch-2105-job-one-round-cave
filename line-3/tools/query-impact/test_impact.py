"""Behavioral tests; scratch files stay inside the workspace."""
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

import impact as tool


def index(*docs):
    return {'format': tool.engine.FORMAT, 'documents': [
        {'path': name, 'text': text, 'sha256': hashlib.sha256(text.encode()).hexdigest()}
        for name, text in docs]}


class ImpactTests(unittest.TestCase):
    def setUp(self):
        scratch = Path.cwd() / 'test' / 'scratch'
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def cli(self, args):
        with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()) as err:
            status = tool.main(args)
        return status, out.getvalue(), err.getvalue()

    def test_identical_snapshots_determinism_no_mutation(self):
        before = index(('z.md', 'ZTO evidence\n'), ('a.md', 'IMD\n'))
        original = copy.deepcopy(before)
        after = copy.deepcopy(before)
        after['documents'].reverse()
        result = tool.compare(before, after, 'ZTO')
        self.assertEqual(result, tool.compare(after, before, 'ZTO'))
        self.assertFalse(result['answers_changed'])
        self.assertTrue(result['corpus']['fresh'])
        self.assertEqual(before, original)
        self.assertEqual(result['before_snapshot_sha256'], result['after_snapshot_sha256'])
        body = {k: v for k, v in result.items() if k != 'report_sha256'}
        self.assertEqual(result['report_sha256'], hashlib.sha256(tool.canonical(body)).hexdigest())

    def test_added_and_removed_hits_with_exact_citations(self):
        result = tool.compare(index(('old.md', '\nZTO old\n')),
                              index(('new.md', 'ZTO new\n\n')), 'ZTO')
        self.assertEqual(result['changes']['left'][0]['citation'], 'old.md:2-2')
        self.assertEqual(result['changes']['entered'][0]['citation'], 'new.md:1-1')
        self.assertEqual(result['corpus']['added'], ['new.md'])
        self.assertEqual(result['corpus']['removed'], ['old.md'])
        self.assertTrue(result['answers_changed'])

    def test_changed_excerpt_same_coordinates(self):
        result = tool.compare(index(('a.md', 'ZTO before\n')),
                              index(('a.md', 'ZTO after\n')), 'ZTO')
        retained = result['changes']['retained'][0]
        self.assertTrue(retained['excerpt_changed'])
        self.assertTrue(retained['source_bytes_changed'])
        self.assertFalse(retained['rank_changed'])
        self.assertEqual(result['changes']['entered'] + result['changes']['left'], [])

    def test_crlf_only_change_is_source_change_not_excerpt_change(self):
        result = tool.compare(index(('a.md', 'ZTO\r\n18 decimals\r\n')),
                              index(('a.md', 'ZTO\n18 decimals\n')), 'ZTO')
        retained = result['changes']['retained'][0]
        self.assertFalse(retained['excerpt_changed'])
        self.assertTrue(retained['source_bytes_changed'])
        self.assertTrue(result['answers_changed'])

    def test_edit_outside_selected_passage(self):
        text = 'ZTO\n' + 'filler\n' * 19
        result = tool.compare(index(('a.md', text)),
                              index(('a.md', text + 'new end\n')), 'ZTO', limit=1)
        retained = result['changes']['retained'][0]
        self.assertFalse(retained['excerpt_changed'])
        self.assertTrue(retained['source_bytes_changed'])

    def test_rank_changes_even_when_retained_source_unchanged(self):
        before = index(('a.md', 'ZTO filler filler filler\n'), ('b.md', 'ZTO\n'))
        after = index(('a.md', 'ZTO ZTO ZTO ZTO\n'), ('b.md', 'ZTO\n'))
        result = tool.compare(before, after, 'ZTO')
        unchanged = next(item for item in result['changes']['retained'] if item['after']['path'] == 'b.md')
        self.assertTrue(unchanged['rank_changed'])
        self.assertFalse(unchanged['source_bytes_changed'])

    def test_top_k_entry_is_not_claimed_as_source_addition(self):
        before = index(('a.md', 'ZTO filler filler filler\n'), ('b.md', 'ZTO\n'))
        after = index(('a.md', 'ZTO ZTO ZTO ZTO\n'), ('b.md', 'ZTO\n'))
        result = tool.compare(before, after, 'ZTO', limit=1)
        self.assertEqual(result['changes']['entered'][0]['path'], 'a.md')
        self.assertEqual(result['changes']['left'][0]['path'], 'b.md')
        self.assertEqual(result['corpus']['added'] + result['corpus']['removed'], [])

    def test_unrelated_addition_changes_scores_not_answer_identity(self):
        before = index(('a.md', 'ZTO\n'))
        after = index(('a.md', 'ZTO\n'), ('other.md', 'other words\n'))
        result = tool.compare(before, after, 'ZTO')
        self.assertFalse(result['answers_changed'])
        self.assertFalse(result['corpus']['fresh'])
        self.assertTrue(result['changes']['retained'][0]['score_changed'])

    def test_relocated_excerpt_is_left_and_entered_not_guessed_rename(self):
        result = tool.compare(index(('a.md', 'ZTO\n')), index(('a.md', '\nZTO\n')), 'ZTO')
        self.assertEqual(result['changes']['retained'], [])
        self.assertEqual(result['changes']['left'][0]['line_start'], 1)
        self.assertEqual(result['changes']['entered'][0]['line_start'], 2)

    def test_empty_no_hits_and_all_terms(self):
        for before, after in ((index(), index()), (index(('a.md', 'other\n')), index())):
            result = tool.compare(before, after, 'ZTO')
            self.assertFalse(result['answers_changed'])
            self.assertEqual(result['before']['hits'] + result['after']['hits'], [])
        result = tool.compare(index(('a.md', 'ZTO\n')), index(('a.md', 'ZTO IMD\n')),
                              'ZTO IMD', require_all=True)
        self.assertEqual(result['before']['hits'], [])
        self.assertEqual(len(result['after']['hits']), 1)

    def test_snapshot_search_never_reads_source_files(self):
        value = index(('commands.md', 'ZTO read configuration and send money\n'))
        with patch.object(tool.engine, 'read_bytes', side_effect=AssertionError('no source reads')):
            result = tool.compare(value, value, 'ZTO')
        self.assertFalse(result['before']['hits'][0]['source_verified'])
        self.assertIn('read configuration', result['before']['hits'][0]['text'])

    def test_rejects_corrupt_non_hit_source_and_unsafe_path(self):
        for value in (index(('a.md', 'ZTO'), ('b.md', 'other')), index(('../a.md', 'ZTO'))):
            if len(value['documents']) == 2:
                value['documents'][1]['text'] = 'altered'
            with self.assertRaises(tool.engine.SearchError):
                tool.compare(index(), value, 'ZTO')

    def test_invalid_requests_and_budgets(self):
        for limit in (True, 1.0, 0, 51):
            with self.assertRaises(tool.engine.SearchError):
                tool.compare(index(), index(), 'ZTO', limit=limit)
        for query in ('', '?', 'a' * 4097, None):
            with self.assertRaises(tool.engine.SearchError):
                tool.compare(index(), index(), query)
        with self.assertRaises(tool.engine.SearchError):
            tool.compare(index(), index(), 'ZTO', require_all=1)
        with patch.object(tool.engine, 'MAX_PASSAGES', 0), self.assertRaises(tool.engine.SearchError):
            tool.compare(index(), index(('a.md', 'ZTO')), 'ZTO')

    def test_snapshot_and_live_search_agree_seeded_corpora(self):
        rng = random.Random(26)
        docs = self.root / 'docs'
        docs.mkdir()
        for trial in range(30):
            for number in range(4):
                lines = [' '.join(rng.choices(['ZTO', 'IMD', 'pool', 'rock'], k=rng.randint(1, 8)))
                         for _ in range(rng.randint(1, 30))]
                (docs / f'{number}.md').write_bytes(('\r\n'.join(lines) + '\r\n').encode())
            value = tool.engine.build_index(docs)
            for require_all in (False, True):
                live = tool.engine.search(value, 'ZTO pool', docs, limit=7, require_all=require_all)
                snapshot = tool.engine.search_snapshot(value, 'ZTO pool', 7, require_all)
                for hit in live['hits']:
                    self.assertTrue(hit['source_verified'])
                    hit['source_verified'] = False
                self.assertEqual(snapshot, live)

    def test_cli_real_demo_and_saved_snapshot_comparison(self):
        status, output, error = self.cli(['demo'])
        self.assertEqual((status, error), (0, ''))
        result = json.loads(output)
        self.assertEqual(result['changes']['entered'][0]['citation'], 'pool.md:1-10')
        self.assertEqual(result['before']['hits'], [])
        self.assertIn('0x888b07bd', result['after']['hits'][0]['text'])
        before, after = self.root / 'before.json', self.root / 'after.json'
        before.write_text(json.dumps(index()), encoding='utf-8')
        after.write_text(json.dumps(index(('a.md', 'ZTO IMD\n'))), encoding='utf-8')
        originals = before.read_bytes(), after.read_bytes()
        status, output, error = self.cli(['compare', str(before), str(after), 'ZTO IMD', '--all'])
        self.assertEqual((status, error), (0, ''))
        self.assertTrue(json.loads(output)['answers_changed'])
        self.assertEqual((before.read_bytes(), after.read_bytes()), originals)
        self.assertEqual(self.cli(['compare', str(before), str(before), 'missing'])[0], 0)

    def test_cli_errors_no_partial_stdout_and_path_boundary(self):
        good, bad = self.root / 'good.json', self.root / 'bad.json'
        good.write_text(json.dumps(index(('a.md', 'ZTO'))), encoding='utf-8')
        for raw in (b'{"format":1,"format":2}', b'\xff', b'{"format": NaN}', b'[]'):
            bad.write_bytes(raw)
            status, output, error = self.cli(['compare', str(good), str(bad), 'ZTO'])
            self.assertEqual((status, output), (2, ''))
            self.assertIn('error', json.loads(error))
        for path in ('../outside.json', '/outside-workspace.json'):
            self.assertEqual(self.cli(['compare', str(good), path, 'ZTO'])[0], 2)
        link = self.root / 'link.json'
        link.symlink_to(good)
        self.assertEqual(self.cli(['compare', str(link), str(good), 'ZTO'])[0], 2)


if __name__ == '__main__':
    unittest.main()
