#!/usr/bin/env python3
"""Stage a reproduced conflicted tree review after explicit per-path decisions."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import shutil
import sys

SOURCE = Path(__file__).resolve().parents[1] / 'candidate-export' / 'export.py'
SPEC = importlib.util.spec_from_file_location('finish_export', SOURCE)
export = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(export)
r = export.r

MAX_DECISIONS_BYTES = 16 * 1024 * 1024


def read_decisions(path, packet_sha256):
    candidate = Path(path)
    if '..' in candidate.parts:
        raise ValueError('decisions path must not contain parent traversal')
    parent = r.tree.workspace_directory(candidate.parent)
    source = parent / candidate.name
    if source.is_symlink() or not source.is_file():
        raise ValueError('decisions must be a regular non-symlink file')
    with source.open('rb') as handle:
        raw = handle.read(MAX_DECISIONS_BYTES + 1)
    if len(raw) > MAX_DECISIONS_BYTES:
        raise ValueError('decisions exceed 16 MiB')
    value = json.loads(raw.decode('utf-8'), object_pairs_hook=r.unique_object,
                       parse_constant=r.reject_constant)
    if (not isinstance(value, dict) or set(value) !=
            {'schema', 'packet_sha256', 'decisions'} or
            value['schema'] != 'conflict-finish/v1' or
            value['packet_sha256'] != packet_sha256 or
            not isinstance(value['decisions'], dict)):
        raise ValueError('decisions schema or packet SHA-256 mismatch')
    return value['decisions'], hashlib.sha256(raw).hexdigest()


def resolve(current, decisions):
    """Return only recomputed clean candidates and explicit conflict decisions."""
    conflicts = {entry['path'] for entry in current['files']
                 if entry['status'].endswith('conflict')}
    if set(decisions) != conflicts:
        missing = sorted(conflicts - set(decisions))
        extra = sorted(set(decisions) - conflicts)
        raise ValueError('decisions must cover exactly the conflicts; missing=' +
                         ascii(missing) + ', extra=' + ascii(extra))
    files, omitted, audit = {}, [], {}
    for entry in current['files']:
        name = entry['path']
        parts = PurePosixPath(name)
        if parts.is_absolute() or '..' in parts.parts or not parts.parts:
            raise ValueError('invalid recomputed candidate path')
        if name in conflicts:
            decision = decisions[name]
            if not isinstance(decision, dict) or set(decision) != {'candidate', 'reason'}:
                raise ValueError('each conflict needs candidate and reason: ' + ascii(name))
            reason = decision['reason']
            if (not isinstance(reason, str) or not reason.strip() or
                    len(reason) > 300 or '\x00' in reason):
                raise ValueError('reason must be 1-300 nonblank characters: ' + ascii(name))
            text = decision['candidate']
            if text is not None:
                r.tree.validate_text(text)
            audit[name] = {
                'original_status': entry['status'], 'reason': reason,
                'chosen': 'delete' if text is None else 'file',
                'chosen_sha256': None if text is None else hashlib.sha256(text.encode()).hexdigest(),
                'inputs': entry['inputs'],
            }
        else:
            text = entry['candidate']
            if text is None and entry['status'] != 'deleted':
                raise ValueError('non-deletion has no candidate: ' + ascii(name))
            if text is not None and hashlib.sha256(text.encode()).hexdigest() != entry['candidate_sha256']:
                raise ValueError('candidate fingerprint mismatch: ' + ascii(name))
        if text is None:
            omitted.append(name)
        else:
            files[name] = text.encode('utf-8')
    # A path conflict can be resolved by deleting either its parent file or its
    # descendants. Never let a later write turn a file into a directory.
    names = set(files)
    for name in names:
        if any('/'.join(PurePosixPath(name).parts[:n]) in names
               for n in range(1, len(PurePosixPath(name).parts))):
            raise ValueError('selected files contain a file/directory collision')
    if len(files) > r.tree.MAX_FILES or sum(map(len, files.values())) > r.tree.MAX_TOTAL_BYTES:
        raise ValueError('resolved tree exceeds inherited output bounds')
    return files, omitted, audit


def finish(packet_path, inputs, decisions_path, output, expected_sha256):
    if expected_sha256 is None:
        raise ValueError('an independently retained packet SHA-256 is required')
    saved, digest = r.load_packet(packet_path, expected_sha256)
    sources = [r.tree.workspace_directory(path) for path in inputs]
    target = export.destination(output, sources)
    current = r.tree.from_directories(sources)
    check = r.compare(saved, current)
    if not check['matches']:
        raise export.Refused('review does not reproduce: ' + check['status'])
    if current['clean']:
        raise export.Refused('use Candidate Export for a clean review')
    decisions, decisions_sha = read_decisions(decisions_path, digest)
    files, omitted, audit = resolve(current, decisions)
    target.mkdir()
    try:
        for name, data in sorted(files.items()):
            path = target / name
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as handle:
                handle.write(data)
        staged = r.tree.snapshot(target, [0])
        if staged['files'] != {name: data.decode('utf-8') for name, data in files.items()}:
            raise ValueError('staged tree verification failed')
        receipt = {
            'schema': 'conflict-finish-receipt/v1',
            'packet_sha256': digest, 'decisions_sha256': decisions_sha,
            'review_matches': True,
            'output': target.relative_to(Path.cwd().resolve()).as_posix(),
            'manifest': r.tree.manifest(staged),
            'files': {name: {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
                      for name, data in sorted(files.items())},
            'omitted': omitted, 'resolutions': audit,
            'limits': [
                'Explicit decisions document choices but do not establish semantic correctness.',
                'Input trees and output parent must stay stable during the operation.',
                'No atomic snapshot, crash-safe publication, binary files or permissions.',
                'An interrupted process may leave an incomplete output directory.']}
    except BaseException:
        shutil.rmtree(target)
        raise
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('packet')
    parser.add_argument('base')
    parser.add_argument('ours')
    parser.add_argument('theirs')
    parser.add_argument('decisions')
    parser.add_argument('new_output')
    parser.add_argument('--expected-sha256', required=True)
    args = parser.parse_args(argv)
    try:
        receipt = finish(args.packet, [args.base, args.ours, args.theirs],
                         args.decisions, args.new_output, args.expected_sha256)
    except export.Refused as error:
        print('conflict-finish: ' + ascii(str(error)), file=sys.stderr)
        return 1
    except (OSError, ValueError, UnicodeError, RecursionError) as error:
        print('conflict-finish: ' + ascii(str(error)), file=sys.stderr)
        return 2
    print(json.dumps(receipt, ensure_ascii=True, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
