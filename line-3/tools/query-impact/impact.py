#!/usr/bin/env python3
"""Explain how a query's exact cited results differ between offline snapshots."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

_path = Path(__file__).absolute().parents[1] / 'corpus-freshness' / 'freshness.py'
_spec = importlib.util.spec_from_file_location('impact_freshness', _path)
freshness = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(freshness)
engine = freshness.engine
FORMAT = 'evidence-query-impact/v1'


def canonical(value):
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(',', ':'), allow_nan=False).encode('utf-8')
    except (TypeError, ValueError, UnicodeError, RecursionError):
        raise engine.SearchError('value cannot be encoded as canonical JSON') from None


def snapshot_hash(index):
    """Bind all source bytes, independent of JSON formatting/document order."""
    engine.validate_index(index)
    normalized = {'format': index['format'],
                  'documents': sorted(index['documents'], key=lambda doc: doc['path'])}
    return hashlib.sha256(canonical(normalized)).hexdigest()


def key(hit):
    # Coordinate identity only. Relocated text is deliberately not guessed at.
    return hit['path'], hit['line_start'], hit['line_end']


def reference(rank, hit):
    return {'rank': rank, 'path': hit['path'], 'line_start': hit['line_start'],
            'line_end': hit['line_end'], 'citation': hit['citation']}


def answer_identity(result):
    return [{name: hit[name] for name in
             ('path', 'line_start', 'line_end', 'text', 'sha256')}
            for hit in result['hits']]


def compare(before, after, query, limit=5, require_all=False):
    """Read neither corpus nor network; search both hash-validated snapshots."""
    if not isinstance(query, str) or len(query) > 4096 or not engine.tokens(query):
        raise engine.SearchError('query must contain a word or address and be at most 4096 characters')
    if type(limit) is not int or not 1 <= limit <= 50:
        raise engine.SearchError('limit must be an integer between 1 and 50')
    if type(require_all) is not bool:
        raise engine.SearchError('require_all must be boolean')
    # Validate both in full before producing any output, including non-hit files.
    before_hash, after_hash = snapshot_hash(before), snapshot_hash(after)
    old_result = engine.search_snapshot(before, query, limit, require_all)
    new_result = engine.search_snapshot(after, query, limit, require_all)
    old = {key(hit): (rank, hit) for rank, hit in enumerate(old_result['hits'], 1)}
    new = {key(hit): (rank, hit) for rank, hit in enumerate(new_result['hits'], 1)}
    entered = [reference(*new[k]) for k in new if k not in old]
    left = [reference(*old[k]) for k in old if k not in new]
    retained = []
    for k in new:
        if k not in old:
            continue
        old_rank, old_hit = old[k]
        new_rank, new_hit = new[k]
        retained.append({
            'before': reference(old_rank, old_hit),
            'after': reference(new_rank, new_hit),
            'rank_changed': old_rank != new_rank,
            'excerpt_changed': old_hit['text'] != new_hit['text'],
            'source_bytes_changed': old_hit['sha256'] != new_hit['sha256'],
            'score_changed': old_hit['score'] != new_hit['score'],
            'matched_terms_changed': old_hit['matched_terms'] != new_hit['matched_terms'],
        })
    corpus = freshness.compare(before, after)
    body = {
        'format': FORMAT,
        'request': {'query': query, 'limit': limit, 'require_all': require_all},
        'before_snapshot_sha256': before_hash,
        'after_snapshot_sha256': after_hash,
        'verification_scope': 'embedded UTF-8 bytes only; no live source or truth check',
        'answers_changed': canonical(answer_identity(old_result)) != canonical(answer_identity(new_result)),
        'corpus': corpus,
        'changes': {'entered': entered, 'left': left, 'retained': retained},
        'before': old_result,
        'after': new_result,
    }
    body['report_sha256'] = hashlib.sha256(canonical(body)).hexdigest()
    return body


def demo():
    root = _path.parent.parent / 'evidence-search' / 'examples' / 'docs'
    complete = engine.build_index(root)
    # A controlled completeness comparison using only real inherited documents.
    # This does not claim the omitted-document corpus ever existed on chain.
    partial = {'format': engine.FORMAT, 'documents': [
        doc for doc in complete['documents'] if doc['path'] != 'pool.md']}
    return compare(partial, complete, 'ZTO pool tick spacing', require_all=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    run = commands.add_parser('compare', help='compare cited query results in two index JSON files')
    run.add_argument('before_index')
    run.add_argument('after_index')
    run.add_argument('query')
    run.add_argument('--limit', type=int, default=5)
    run.add_argument('--all', action='store_true')
    commands.add_parser('demo', help='show the impact of including the historical ZTO pool document')
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            result = demo()
        else:
            result = compare(engine.load_index(args.before_index),
                             engine.load_index(args.after_index), args.query,
                             args.limit, args.all)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (engine.SearchError, OSError) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
