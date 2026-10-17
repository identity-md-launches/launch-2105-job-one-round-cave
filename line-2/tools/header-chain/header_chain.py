#!/usr/bin/env python3
"""Verify older Ethereum state through parent links from a trusted later hash.

Offline, bounded, Python standard library only. Headers are oldest first.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    'anchor_for_header_chain', HERE.parent / 'header-anchor' / 'anchor.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
w = a.w
MAX_HEADERS = 64
MAX_FILE = 262144
DEMO_TIP = '0xead51f4e385140de3b2010a5b4c96106e8bf27fdb836246e57e18ad5df545a33'


def check_shape(chain):
    w.require(isinstance(chain, dict) and set(chain) == {'format', 'headers'},
              'chain must contain exactly format and headers')
    w.require(chain['format'] == 'header-chain/1', 'unsupported chain format')
    headers = chain['headers']
    w.require(isinstance(headers, list) and 1 <= len(headers) <= MAX_HEADERS,
              'chain must contain 1..64 headers, oldest first')
    return headers


def load_chain(path):
    with w.workspace_path(path).open('rb') as stream:
        raw = stream.read(MAX_FILE + 1)
    w.require(len(raw) <= MAX_FILE, 'chain exceeds 256 KiB limit')
    chain = w.parse_json(raw)
    check_shape(chain)
    return chain


def verify_chain(chain, trusted_tip_hash):
    """Follow commitments backwards; never adopt a trust hash from the file.

    This is ancestry relative to a hash, not consensus validation or a way to
    authenticate a newer block from an older checkpoint.
    """
    headers = check_shape(chain)
    expected = w.hex0(w.hex_data(trusted_tip_hash, 32, 'trusted tip hash'))
    reverse_anchors = []
    child = None
    for index in range(len(headers) - 1, -1, -1):
        header = headers[index]
        try:
            anchor = a.verify_header(header, expected)
            if child is not None:
                w.require(int(anchor['blockNumber'], 16) + 1 == int(child['blockNumber'], 16),
                          'block numbers must be consecutive')
                w.require(int(anchor['timestamp'], 16) < int(child['timestamp'], 16),
                          'child timestamp must be strictly later')
            reverse_anchors.append(anchor)
            expected = header['parentHash']
            child = anchor
        except w.Invalid as error:
            raise w.Invalid(f'header {index}: {error}') from error
    anchors = list(reversed(reverse_anchors))
    return {
        'target': anchors[0], 'checkpoint': anchors[-1],
        'headerCount': len(anchors), 'parentLinks': len(anchors) - 1,
        'blockHashesOldestFirst': [anchor['blockHash'] for anchor in anchors],
        'elapsedSeconds': int(anchors[-1]['timestamp'], 16) - int(anchors[0]['timestamp'], 16),
    }


def verify(chain, bundle, trusted_tip_hash, address, slots):
    ancestry = verify_chain(chain, trusted_tip_hash)
    w.require(isinstance(bundle, dict) and bundle.get('format') == 'state-witness/1',
              'unsupported witness format')
    # A valid ancestry alone is never a success report for unverified state.
    state = w.verify(bundle.get('proof'), ancestry['target']['stateRoot'], address, slots)
    state.pop('trust')
    return {
        'verified': True, 'ancestry': ancestry, 'state': state,
        'trust': ('State is proven at the oldest supplied header, linked by parent hashes '
                  'to the explicitly supplied later checkpoint. Authenticate the checkpoint, '
                  'its chain, canonicality, consensus/execution validity and finality independently. '
                  'This checks header hashes, consecutive numbers and increasing timestamps, '
                  'not consensus rules. It does not authenticate newer headers from an older '
                  'checkpoint, prove current state, or establish token storage semantics.'),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    demo = sub.add_parser('demo', help='verify real historical ZTO through three parent links')
    demo.add_argument('--pool', action='store_true', help='use the real ZTO/IMD pool witness')
    check = sub.add_parser('verify', help='verify oldest-header state against a trusted later hash')
    check.add_argument('chain')
    check.add_argument('witness')
    check.add_argument('--tip-hash', required=True)
    check.add_argument('--address', required=True)
    check.add_argument('--slot', action='append', default=[])
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            name = 'zto-pool-mainnet.json' if args.pool else 'zto-mainnet.json'
            bundle = w.load_bundle(HERE.parent / 'state-witness' / 'examples' / name)
            result = verify(load_chain(HERE / 'examples' / 'zto-header-chain.json'),
                            bundle, DEMO_TIP, w.POOL_MANAGER if args.pool else w.ZTO,
                            [a.POOL_SLOT] if args.pool else ['0x0', '0x1'])
            result['demo'] = ('Real historical mainnet observations. The bundled checkpoint '
                              'was obtained from RPC, not independently authenticated.')
        else:
            result = verify(load_chain(args.chain), w.load_bundle(args.witness),
                            args.tip_hash, args.address, args.slot)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except w.Invalid as error:
        print(json.dumps({'verified': False, 'error': str(error)}), file=sys.stderr)
        return 1
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        print(json.dumps({'verified': False, 'error': 'Unreadable or malformed chain or witness.'}),
              file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
