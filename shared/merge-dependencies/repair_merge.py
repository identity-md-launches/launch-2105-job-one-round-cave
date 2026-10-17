#!/usr/bin/env python3
"""Review a text merge, verify dependency compatibility, and propose a root repair."""
import argparse
import json
import sys

import check_merge as first
import repair
import second_check


def check(base, ours, theirs, max_steps=10000, max_assignments=10000,
          max_repair_steps=10000, max_trials=10000):
    for label, value in [('max_repair_steps', max_repair_steps), ('max_trials', max_trials)]:
        if type(value) is not int or not 1 <= value <= 1000000:
            raise ValueError(label + ' must be an integer from 1 to 1000000')
    checked = second_check.check(base, ours, theirs, max_steps, max_assignments)
    status = checked['status']
    result = {'format': 'dependency-merge-repair/v1', 'status': status,
              'checked_merge': checked, 'repair': None,
              'limits': [
                  'Review and proposal only; no catalog is changed or package installed.',
                  'Minimum means fewest removed roots in this finite catalog.',
                  'The caller must decide whether a proposed removal is acceptable.',
                  'Search budgets or disagreement cannot authorize a repair.']}
    if status == 'unsatisfiable':
        data = first.parse(checked['review']['merge']['merged'])
        proposal = repair.repair(data, max_repair_steps, max_trials)
        result['repair'] = proposal
        if proposal['status'] == 'inconclusive':
            result['status'] = 'inconclusive'
        elif proposal['status'] == 'repaired' and proposal['minimum_removed_count'] > 0:
            result['status'] = 'repair_proposed'
        else:
            result['status'] = 'disagreement'
    return result


def demo(**limits):
    texts = [first.review.engine.read_text(first.HERE / 'examples' / (n + '.json'))
             for n in ('base', 'ours', 'theirs')]
    return check(*texts, **limits)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('demo', 'check'):
        p = sub.add_parser(name)
        if name == 'check':
            for branch in ('base', 'ours', 'theirs'):
                p.add_argument(branch)
        p.add_argument('--max-steps', type=int, default=10000)
        p.add_argument('--max-assignments', type=int, default=10000)
        p.add_argument('--max-repair-steps', type=int, default=10000)
        p.add_argument('--max-trials', type=int, default=10000)
    args = parser.parse_args(argv)
    try:
        limits = {key: getattr(args, key) for key in
                  ('max_steps', 'max_assignments', 'max_repair_steps', 'max_trials')}
        if args.command == 'demo':
            result = demo(**limits)
        else:
            texts = [first.review.engine.read_text(p) for p in
                     (args.base, args.ours, args.theirs)]
            result = check(*texts, **limits)
        code = {'resolved': 0, 'repair_proposed': 1, 'text_conflict': 1,
                'invalid_catalog': 2, 'inconclusive': 3, 'disagreement': 4}[result['status']]
        if args.command == 'demo' and result['status'] == 'repair_proposed':
            code = 0
        print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
        return code
    except (ValueError, OSError, TypeError, RecursionError):
        print(json.dumps({'status': 'invalid', 'error': 'Invalid workspace inputs or budgets.'}),
              file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
