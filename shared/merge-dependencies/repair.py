#!/usr/bin/env python3
"""Find a minimum-cardinality root removal in a finite offline catalog."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import sys

import resolve as fmt
import exhaustive as checker


def repair(data, max_steps=10000, max_trials=10000):
    """Try removed-root subsets in cardinality then canonical lexical order.

    Stop on the first unknown result, so no smaller unproved subset can be
    skipped while claiming a minimum. Search states are shared across trials.
    """
    for label, value in [('max_steps', max_steps), ('max_trials', max_trials)]:
        if type(value) is not int or not 1 <= value <= 1000000:
            raise fmt.Invalid(label + ' must be an integer from 1 to 1000000')
    packages, roots = fmt.validate(data)
    normalized = {'packages': packages, 'roots': roots}
    digest = hashlib.sha256(json.dumps(normalized, sort_keys=True,
                                      separators=(',', ':')).encode()).hexdigest()
    base = {'method': 'minimum-root-removal-v1', 'catalog_sha256': digest,
            'max_steps': max_steps, 'max_trials': max_trials}
    names = sorted(roots)
    steps = trials = 0
    exhausted_sizes = []
    for size in range(len(names) + 1):
        for removed in itertools.combinations(names, size):
            remaining = {p: s for p, s in roots.items() if p not in removed}
            # Even the empty-root trial consumes a trial but needs no search.
            if trials == max_trials or (remaining and steps == max_steps):
                return dict(base, status='inconclusive', steps=steps, trials=trials,
                            fully_rejected_removal_sizes=exhausted_sizes,
                            reason='trial or shared search budget exhausted')
            trials += 1
            candidate = {'packages': packages, 'roots': remaining}
            result = (fmt.solve(candidate, max_steps - steps) if remaining
                      else {'status': 'resolved', 'selected': {}, 'steps': 0})
            steps += result['steps']
            if result['status'] == 'inconclusive':
                return dict(base, status='inconclusive', steps=steps, trials=trials,
                            fully_rejected_removal_sizes=exhausted_sizes,
                            unresolved_removed=list(removed), reason=result['reason'])
            if result['status'] == 'resolved':
                selected = result['selected']
                # Separate iterative edge checker, independent of solver search
                # and accepts(), validates the returned reachable witness.
                if checker.assignment(packages, remaining, selected) != selected:
                    raise fmt.Invalid('solver returned an invalid assignment')
                return dict(base, status='repaired' if size else 'compatible',
                            minimum_removed_count=size,
                            removed={p: roots[p] for p in removed},
                            remaining_roots=remaining, selected=selected,
                            fully_rejected_removal_sizes=exhausted_sizes,
                            steps=steps, trials=trials)
        exhausted_sizes.append(size)
    raise AssertionError('empty root set must be compatible')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('catalog', help='workspace catalog JSON, or demo')
    parser.add_argument('--max-steps', type=int, default=10000)
    parser.add_argument('--max-trials', type=int, default=10000)
    args = parser.parse_args(argv)
    try:
        path = (Path(__file__).parent / 'examples/requests-conflict.json'
                if args.catalog == 'demo' else args.catalog)
        result = repair(fmt.load(path), args.max_steps, args.max_trials)
        code = 3 if result['status'] == 'inconclusive' else 0
    except (fmt.Invalid, checker.Invalid, OSError, ValueError, TypeError, RecursionError) as exc:
        result, code = {'status': 'invalid', 'error': str(exc)}, 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return code


if __name__ == '__main__':
    sys.exit(main())
