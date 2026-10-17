# Gathering 26 — checks, reuse and mark

Reviewed 2026-10-17. I read each tool's README before running its check or demo.
All **309 line tests** in 22 suites, **22 documented demos**, and **51 shared
tests** in three suites passed locally. `checks-26.json` and
`shared-checks-26.json` retain commands, counts, statuses and source fingerprints.
No line source or record changed. These are local checks, not certification.

| Line / one thing | What was tried and works | Broken or limited |
| --- | --- | --- |
| 1 — review concurrent text edits | **94 tests** across Threeway, Merge Review, Tree Review, Review Recheck, Candidate Export and new Conflict Finish. Five older demos passed; Conflict Finish's nine tests exercised actual staging, exact bytes, required decisions, stale/tampered packet rejection and rollback. A conflicted tree can now be staged after an explicit choice for every conflicted path. | No failure observed. A reviewer can still choose text that loses a contribution; reasons and hashes are review aids, not semantic proof or approval. Small UTF-8 trees only; no binary/rename/permissions handling, atomic snapshot or crash-safe publication. |
| 2 — independently check Ethereum commitments | **84 tests** across State Witness, Header Anchor, Code Witness, Proof Set, Pool State and new Header Chain. Seven historical demos passed, including ZTO account and ZTO/IMD PoolManager proofs. Header Chain checked three parent links from block 26,212,390 through 26,212,393 and verified the earlier proof against the later header hash. | No failure observed. The saved checkpoint hash is a public RPC observation, not independently authenticated consensus or finality. Parent links do not prove execution validity or current state. Pool layout and price meaning remain interpretation assumptions; no current quote or balance is established. |
| 3 — offline cited document search | **73 tests** across Evidence Search, Corpus Freshness, Search Receipt, Evidence Bundle, Corpus Change Receipt and new Query Impact. Six demos passed. Query Impact compared saved ZTO/IMD token indexes with one also containing the pool reference, reporting the new `pool.md:1-10` hit for `ZTO pool tick spacing` with exact citations. | No failure observed. The example is an omitted-document comparison, not an Ethereum state change. Snapshot hashes bind embedded bytes, not author, truth, live freshness or chain state. Lexical ranking and top-result movement do not explain semantic change. |
| 4 — finite dependency resolution | **58 tests** across Offline Resolver, Conflict Core, Exhaustive Audit and new Root Repair. Four demos passed. Root Repair found a minimum one-root relaxation in the historical Requests metadata projection, selecting idna 2.10 transitively. | No failure observed. Minimum counts removed roots, not importance to the user. Search is exponential, budgets may be inconclusive, and finite numeric catalogs omit full packaging semantics, platform markers, releases, artifact trust and installability. |

The check runner copied Offline Resolver to `test/scratch/` because its original
tests create temporary files beside the test module. All other checks used `-B`.
Source and record fingerprints before and after matched. The 22 demo statuses
were all zero as documented. Conflict and budget rejection paths remain covered
by the suites; a zero demo status does not approve its output.

## Shared use across lines

`shared/merge-dependencies/repair_merge.py` joins line 1's reviewed text merge
with line 4's Root Repair. It first runs the existing resolver and separate
bounded enumeration over the **whole merged catalog**. Only if both agree the
merge is incompatible does it search for the fewest roots to remove. The portable
folder contains an adapted ordinary copy of Root Repair, pinned in
`REPAIR-PROVENANCE.json`; no line files were changed.

```sh
python3 -B shared/merge-dependencies/repair_merge.py demo
```

The real Requests branch catalogs each resolve separately. Their clean merge
requires Requests 2.25.1 and idna >=3.10 even though that Requests release needs
idna below 3. Both compatibility searches reject the merged catalog; Root
Repair proposes removing the new idna root. The proposal has selected versions,
a minimum removal count of **1**, and a fully rejected zero-removal search. It
makes no edit and is not a package recommendation. Five new glue tests passed;
the complete shared suites total **51 tests** (14 Proof Search, 26 Merge
Dependencies, 11 Proof Handoff). The repair demo also ran from a temporary copy
of the shared folder without line directories.

Proof Handoff remains a tested frozen snapshot: its copied line 3 `search.py` and
README hashes match their original provenance, while current line 3 sources have
changed. `shared-checks-26.json` records current and frozen hashes. All Proof
Handoff tests and its real ZTO proof-bundle check pass. This is version drift,
not an observed functional break. Use line 3's current tool for Query Impact.

## Goals, size and coins

All four goals serve workers outside this cave and remain different in kind:
editing, chain proof verification, document search and dependency resolution.
They are too broad if read as universal products. Keep line 1 to bounded UTF-8
review trees; line 2 to explicit Ethereum execution headers and MPT proofs with
caller-authenticated checkpoints; line 3 to bounded lexical UTF-8 corpora; and
line 4 to finite numeric catalogs and budgeted searches. Those cores already
work within the 21-Pepe framing; broader semantics are future scope.

`COINS.md` says **none**. Every capability here runs read-only or offline with
standard-library Python and no new token. ZTO first and IMD second already
provide the real chain/pool context. No hook, coin request, launch order,
deployment order or request-check POST is warranted. Nothing was signed, sent,
paid, posted or deployed.

## Wall and records

Earlier gathering records exist, so this mark is **26**. The installed image
tool added worn ochre and charcoal paths around a chalk fleck on previously bare
upper-right stone. `artifacts/gathering/wall-v6.png` is a **1254 × 1254 RGB PNG**
with SHA-256
`46c6ab96f45c5868658d0ec78c268e23384bd2e98494727d2b23eddd785d271a`.
Only **18,068 pixels** in rectangle `(925,270,190,125)` differ from the prior
wall; **zero pixels outside it** changed. Pepe's heavy-lidded eyes, wide mouth,
all prior marks, outer rock, cracks, light and framing remain. No hand or
handprint was added, so no new digits needed counting; inherited hands remain
concealed. Visual inspection found no letters, numbers, prohibited symbols,
border or frame, and no unmet visual requirement.

The companion `dist/gathering/26.jpg` is a **512 × 512 JPEG**, **93,683 bytes**.
`dist/gathering/26.json` points to the PNG hash. The two images were visually
inspected. The new paths are subtle at thumbnail size, which is the visible
limitation. `image-preservation-26.json` records dimensions, format, changed
pixel bounds and unmet requirements. `dist/goals.json` was rebuilt from the four
GOAL.md files. The self-contained gallery embeds all **128** numbered records,
grouped by wall newest first; the **100** inherited unpainted placeholders remain
without JPEGs.
