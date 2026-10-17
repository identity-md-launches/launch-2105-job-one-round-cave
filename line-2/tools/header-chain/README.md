# Header Chain

Verify an older Ethereum account/storage witness using a **later block hash**
you already trust. The tool hashes every execution header, follows its committed
parent hash backward, and verifies the witness against the oldest header's
state root. This lets a worker reuse an earlier proof without separately
authenticating that earlier block hash.

Run from the repository root, offline, with Python 3.9+ standard library only:

```sh
python3 -B line-2/tools/header-chain/header_chain.py demo
```

Keep sibling `header-anchor/` and `state-witness/` alongside this folder. No
installation, network access or external account is needed. Runtime only reads
the supplied workspace files and prints JSON; it never writes files, consults
environment variables, accesses a wallet, signs, sends, pays or deploys.

## What happened when tried

On 2026-10-17, three newly fetched real Ethereum headers joined the inherited
ZTO header into a four-header chain from block **26,212,390** through
**26,212,393**, spanning **36 seconds**. Header Chain verified all three parent
links and then ZTO's actual account and slots 0 and 1 at the oldest block.
Slot 0 is proven absent. No meaning is assigned to those raw storage slots.

The optional real ZTO/IMD pool trial also passed:

```sh
python3 -B line-2/tools/header-chain/header_chain.py demo --pool
```

It proves the inherited PoolManager slot at block 26,212,390, with value
`0x30d400000001b32f000000000000010675ff9d949ea2d3c11613bc41`.
The tool reports raw state rather than a current price or swap quote.

The endpoint source is <https://ethereum-rpc.publicnode.com>. Capture used only
`eth_chainId` and `eth_getBlockByNumber`, with User-Agent
`Pepeolithic-StateWitness/1.0` through the inherited read-only RPC helper. Full
block response bodies were kept in memory; only supported header fields were
saved. Each header's Keccak/RLP hash and parent link were checked before saving
`examples/zto-header-chain.json`. The earliest header and both witnesses were
reused unchanged. Demo checkpoints are RPC observations, **not independently
authenticated consensus checkpoints**. This is historical data.

| Position | Block | Execution block hash |
| --- | --- | --- |
| Target | 26212390 | `0x38dc4deb12174972d332cc1f95008b25ea87434f420ce0a51938e1b28755e9dc` |
| Parent link 1 | 26212391 | `0x003dfd9ff18b7d051d3301685d5b9afcb4d6a341203088868087b27b6904db2e` |
| Parent link 2 | 26212392 | `0x2c81bcf83428135ad1c9e91340473d4d407982dbf8b8b9ccf0c8652ed2fad2fd` |
| Checkpoint | 26212393 | `0xead51f4e385140de3b2010a5b4c96106e8bf27fdb836246e57e18ad5df545a33` |

All **14 new tests and 70 ancestor tests passed**. The tests reject changed
checkpoint/header/proof bytes, missing/reordered/duplicate links, wrong account
or slots, unknown fields and invalid JSON. Synthetic adversarial chains with
consistently recomputed hashes still fail if block numbers skip or timestamps
do not increase. A one-header chain works as direct anchoring. Neither good
headers nor saved RPC metadata can turn a bad state proof into partial success.

```sh
python3 -B -m unittest discover -s line-2/tools/header-chain -p 'test_*.py' -v
```

## Your own observation

The chain JSON has exactly two fields: `format` set to `header-chain/1`, and
`headers`, an array of complete header-only RPC objects **oldest first**.
Supply the witness for the first header and a separately authenticated hash
for the last header. The following reproduces the historical ZTO trial:

```sh
python3 -B line-2/tools/header-chain/header_chain.py verify \
  line-2/tools/header-chain/examples/zto-header-chain.json \
  line-2/tools/state-witness/examples/zto-mainnet.json \
  --tip-hash 0xead51f4e385140de3b2010a5b4c96106e8bf27fdb836246e57e18ad5df545a33 \
  --address 0xd782bdea4ef02a0bd391eb9089470c8080f0a68e \
  --slot 0x0 --slot 0x1
```

For another account, supply its actual address and exact requested slot set.
There is no default checkpoint for `verify`, and no trust hash can be supplied
inside the chain file. Witness metadata such as block labels and chain ID does
not replace the proof or caller expectations. Reported state belongs to
`ancestry.target`; `ancestry.checkpoint` is the later trust anchor.

Limits: 1–64 headers (at most 63 links), 256 KiB chain file, and the inherited
1 MB witness/64-slot bounds. Files must resolve inside the current working
directory, including symlink targets. Duplicate JSON keys, NaN, incomplete fork
suffixes and unknown header fields are refused. Supported encodings are legacy,
London, Shanghai, Cancun and Prague; unsupported future fields fail closed.
Exit 0 prints a complete success JSON; exit 1 prints error JSON on stderr and
no success output; argparse usage errors exit 2.

## Trust boundary

A later header commits to its ancestors through parent hashes. Trust therefore
flows **backward** here. An old checkpoint cannot authenticate a new descendant:
anyone could construct a competing chain that names it as an ancestor. Giving
the oldest hash to `--tip-hash` with newer headers is rejected.

The caller still authenticates the checkpoint's chain, canonicality, validity
and finality. Header Chain checks hash commitments, consecutive block numbers
and strictly increasing timestamps. It does not validate consensus, signatures,
execution, gas rules, fork activation, or transaction/receipt bodies. Even a
long successful chain is no finality proof. A proof at an older block says
nothing about whether the state changed later. No token ABI, layout or pool
semantics are inferred from storage bytes.

Reference: Ethereum's [Prague execution header validation](https://github.com/ethereum/execution-specs/blob/master/src/ethereum/forks/prague/fork.py)
specifies parent-hash, block-number and timestamp relationships; this tool checks
only that subset plus the inherited strict header encoding. [EIP-1186](https://eips.ethereum.org/EIPS/eip-1186)
defines the account/storage proof format. Neither reference is a runtime
dependency. No new coin is needed.
