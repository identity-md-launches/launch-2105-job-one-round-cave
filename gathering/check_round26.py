"""Run every line tool's documented checks without changing line files."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


TOOLS = {
    1: ('threeway', 'merge-review', 'tree-review', 'review-recheck',
        'candidate-export', 'conflict-finish'),
    2: ('state-witness', 'header-anchor', 'code-witness', 'proof-set',
        'pool-state', 'header-chain'),
    3: ('evidence-search', 'corpus-freshness', 'search-receipt',
        'evidence-bundle', 'corpus-change-receipt', 'query-impact'),
    4: ('offline-resolver', 'conflict-core', 'exhaustive-audit', 'root-repair'),
}


def fingerprints():
    return {p.as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for n in range(1, 5) for folder in (Path(f'line-{n}'), Path(f'dist/line-{n}'))
            for p in sorted(folder.rglob('*')) if p.is_file()}


def run(args, expected=0, timeout=180):
    proc = subprocess.run([sys.executable, '-B', *args], text=True,
                          capture_output=True, timeout=timeout)
    result = {'command': 'python3 -B ' + ' '.join(args), 'exit': proc.returncode,
              'expected_exit': expected, 'stdout': proc.stdout[-1000:],
              'stderr': proc.stderr[-1000:]}
    if proc.returncode != expected:
        raise AssertionError(result)
    return result


def main():
    before = fingerprints()
    suites = []
    scratch = Path('test/scratch')
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch, prefix='gathering26-') as temp:
        copied = Path(temp) / 'offline-resolver'
        shutil.copytree('line-4/tools/offline-resolver', copied)
        for n, names in TOOLS.items():
            for name in names:
                folder = f'line-{n}/tools/{name}'
                test_folder = str(copied) if name == 'offline-resolver' else folder
                result = run(['-m', 'unittest', 'discover', '-s', test_folder,
                              '-p', 'test_*.py'])
                count = re.search(r'Ran (\d+) tests?', result['stderr'])
                result['tool'] = folder
                result['tests'] = int(count[1]) if count else 0
                assert result['tests'] > 0, result
                suites.append(result)
                print(folder, result['tests'], flush=True)
    demos = []
    for folder, script, args, expected in [
        ('line-1', 'threeway/merge.py', ['--demo', '--format', 'json'], 0),
        ('line-1', 'merge-review/review.py', ['--demo', 'clean', '--format', 'json'], 0),
        ('line-1', 'tree-review/tree_review.py', ['--demo', 'clean', '--format', 'json'], 0),
        ('line-1', 'review-recheck/recheck.py', ['--demo', 'clean'], 0),
        ('line-1', 'candidate-export/export.py', ['--demo'], 0),
        ('line-2', 'state-witness/witness.py', ['demo'], 0),
        ('line-2', 'header-anchor/anchor.py', ['demo'], 0),
        ('line-2', 'code-witness/code_witness.py', ['demo'], 0),
        ('line-2', 'proof-set/proof_set.py', ['demo'], 0),
        ('line-2', 'pool-state/pool_state.py', ['demo'], 0),
        ('line-2', 'header-chain/header_chain.py', ['demo'], 0),
        ('line-2', 'header-chain/header_chain.py', ['demo', '--pool'], 0),
        ('line-3', 'evidence-search/search.py', ['demo'], 0),
        ('line-3', 'corpus-freshness/freshness.py', ['demo'], 0),
        ('line-3', 'search-receipt/receipt.py', ['demo'], 0),
        ('line-3', 'evidence-bundle/bundle.py', ['demo'], 0),
        ('line-3', 'corpus-change-receipt/receipt.py', ['demo'], 0),
        ('line-3', 'query-impact/impact.py', ['demo'], 0),
        ('line-4', 'offline-resolver/resolve.py', ['demo'], 0),
        ('line-4', 'conflict-core/core.py', ['demo'], 0),
        ('line-4', 'exhaustive-audit/audit.py', ['demo'], 0),
        ('line-4', 'root-repair/repair.py', ['demo'], 0),
    ]:
        result = run([f'{folder}/tools/{script}', *args], expected, 90)
        demos.append(result)
        print(result['command'], result['exit'], flush=True)
    after = fingerprints()
    assert before == after, 'line files or records changed'
    report = {'suites': suites, 'demos': demos,
              'total_tests': sum(s['tests'] for s in suites),
              'line_files_unchanged': True, 'protected_files': before}
    Path('gathering/checks-26.json').write_text(json.dumps(report, indent=2) + '\n')
    print('TOTAL', report['total_tests'], 'tests;', len(demos), 'demos')


if __name__ == '__main__':
    main()
