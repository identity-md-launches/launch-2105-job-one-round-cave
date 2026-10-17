"""Real historical chain/proof integration and adversarial ancestry checks."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('chain_tested', HERE / 'header_chain.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


class HeaderChainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chain = c.load_chain(HERE / 'examples/zto-header-chain.json')
        cls.bundle = c.w.load_bundle(HERE.parent / 'state-witness/examples/zto-mainnet.json')

    def verify(self, chain=None, bundle=None, tip=None):
        return c.verify(self.chain if chain is None else chain,
                        self.bundle if bundle is None else bundle,
                        c.DEMO_TIP if tip is None else tip, c.w.ZTO, ['0x0', '0x1'])

    def test_real_zto_chain_and_input_preservation(self):
        before = copy.deepcopy((self.chain, self.bundle))
        result = self.verify()
        self.assertTrue(result['verified'])
        self.assertEqual(result['ancestry']['target']['blockHash'], c.a.DEMO_HASH)
        self.assertEqual(result['ancestry']['checkpoint']['blockHash'], c.DEMO_TIP)
        self.assertEqual(result['ancestry']['parentLinks'], 3)
        self.assertEqual(result['ancestry']['elapsedSeconds'], 36)
        self.assertEqual(result['state']['stateRoot'], c.w.DEMO_ROOT)
        self.assertEqual(result['state']['address'], c.w.ZTO)
        self.assertTrue(result['state']['accountExists'])
        self.assertFalse(result['state']['storage'][0]['exists'])
        self.assertEqual((self.chain, self.bundle), before)
        self.assertEqual(result, self.verify())

    def test_real_pool_uses_oldest_root(self):
        bundle = c.w.load_bundle(HERE.parent / 'state-witness/examples/zto-pool-mainnet.json')
        result = c.verify(self.chain, bundle, c.DEMO_TIP, c.w.POOL_MANAGER, [c.a.POOL_SLOT])
        self.assertEqual(result['state']['storage'][0]['value'],
                         '0x30d400000001b32f000000000000010675ff9d949ea2d3c11613bc41')

    def test_wrong_tip_and_trust_direction_fail(self):
        for tip in (c.a.DEMO_HASH, '0x' + '11' * 32, '', False):
            with self.subTest(tip=tip), self.assertRaises(c.w.Invalid):
                self.verify(tip=tip)

    def test_missing_reordered_and_duplicate_headers_fail(self):
        h = self.chain['headers']
        for headers in (h[1:], h[:-1], [h[0], *h[2:]], list(reversed(h)),
                        [h[0], h[1], h[1], h[2], h[3]]):
            with self.subTest(length=len(headers)), self.assertRaises(c.w.Invalid):
                self.verify(chain={'format': 'header-chain/1', 'headers': headers})

    def test_each_headers_committed_fields_are_bound(self):
        for i in range(4):
            for field in ('parentHash', 'stateRoot', 'transactionsRoot', 'hash'):
                chain = copy.deepcopy(self.chain)
                chain['headers'][i][field] = '0x' + '11' * 32
                with self.subTest(index=i, field=field), self.assertRaises(c.w.Invalid):
                    self.verify(chain=chain)

    def test_optional_rpc_hashes_are_not_the_commitment(self):
        chain = copy.deepcopy(self.chain)
        for header in chain['headers']:
            del header['hash']
        self.assertEqual(self.verify(chain=chain), self.verify())

    def test_single_header_degenerates_to_direct_anchor(self):
        chain = {'format': 'header-chain/1', 'headers': [self.chain['headers'][0]]}
        result = self.verify(chain=chain, tip=c.a.DEMO_HASH)
        self.assertEqual(result['ancestry']['parentLinks'], 0)
        self.assertEqual(result['ancestry']['elapsedSeconds'], 0)

    def test_consistently_rehashed_bad_number_or_time_is_rejected(self):
        # Deliberately synthetic malformed two-header chains, not demo data.
        for field, value, message in (
                ('number', self.chain['headers'][0]['number'], 'consecutive'),
                ('timestamp', self.chain['headers'][0]['timestamp'], 'strictly later'),
                ('timestamp', '0x0', 'strictly later')):
            chain = copy.deepcopy(self.chain)
            chain['headers'] = chain['headers'][:2]
            child = chain['headers'][1]
            child[field] = value
            del child['hash']
            raw, _ = c.a.encode_header(child)
            tip = c.w.hex0(c.w.keccak256(raw))
            with self.subTest(field=field, value=value), self.assertRaisesRegex(c.w.Invalid, message):
                self.verify(chain=chain, tip=tip)

    def test_bad_witness_cannot_pass_with_good_chain(self):
        for field in ('value', 'proof'):
            bundle = copy.deepcopy(self.bundle)
            # Slot 1 is present in the real witness, so missing nodes must fail.
            bundle['proof']['storageProof'][1][field] = '0x1' if field == 'value' else []
            with self.subTest(field=field), self.assertRaises(c.w.Invalid):
                self.verify(bundle=bundle)

    def test_caller_address_and_slots_are_bound(self):
        for address, slots in ((c.w.POOL_MANAGER, ['0x0', '0x1']),
                               (c.w.ZTO, []), (c.w.ZTO, ['0x0', '0x2']),
                               (c.w.ZTO, ['0x0', '0x0'])):
            with self.subTest(address=address, slots=slots), self.assertRaises(c.w.Invalid):
                c.verify(self.chain, self.bundle, c.DEMO_TIP, address, slots)

    def test_unproven_metadata_is_ignored_and_embedded_trust_refused(self):
        bundle = copy.deepcopy(self.bundle)
        bundle.update(block={'hash': 'forged'}, address='forged', chainId=999, slots=['forged'])
        self.assertEqual(self.verify(bundle=bundle), self.verify())
        chain = dict(self.chain, trustedTipHash=c.DEMO_TIP)
        with self.assertRaises(c.w.Invalid):
            self.verify(chain=chain)

    def test_chain_shapes_limits_and_unknown_header_fields(self):
        for chain in (None, [], {}, {'format': 'unknown', 'headers': self.chain['headers']},
                      {'format': 'header-chain/1', 'headers': []},
                      {'format': 'header-chain/1', 'headers': [self.chain['headers'][0]] * 65},
                      {'format': 'header-chain/1', 'headers': [None]}):
            with self.subTest(chain=str(chain)[:60]), self.assertRaises(c.w.Invalid):
                c.verify_chain(chain, c.DEMO_TIP)
        chain = copy.deepcopy(self.chain)
        chain['headers'][0]['unknownFutureField'] = '0x1'
        with self.assertRaises(c.w.Invalid):
            self.verify(chain=chain)

    def test_loader_strict_json_size_and_workspace_boundary(self):
        for raw in (b'{"format":1,"format":2}', b'{"headers":NaN}', b' ' * (c.MAX_FILE + 1)):
            with mock.patch.object(c.w, 'workspace_path') as path:
                path.return_value.open.return_value.__enter__.return_value.read.return_value = raw
                with self.assertRaises(c.w.Invalid):
                    c.load_chain('unused')
        with self.assertRaises(c.w.Invalid):
            c.load_chain(Path.cwd().parent / 'outside.json')

    def test_cli_both_real_demos_and_atomic_failure(self):
        for args in (['demo'], ['demo', '--pool']):
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                self.assertEqual(c.main(args), 0)
            self.assertTrue(json.loads(out.getvalue())['verified'])
            self.assertEqual(err.getvalue(), '')
        args = ['verify', str(HERE / 'examples/zto-header-chain.json'),
                str(HERE.parent / 'state-witness/examples/zto-mainnet.json'),
                '--tip-hash', c.DEMO_TIP, '--address', c.w.ZTO]  # Missing slots.
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.assertEqual(c.main(args), 1)
        self.assertEqual(out.getvalue(), '')
        self.assertFalse(json.loads(err.getvalue())['verified'])


if __name__ == '__main__':
    unittest.main()
