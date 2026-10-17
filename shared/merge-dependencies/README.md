# Merge Dependencies

Review concurrent edits to a dependency catalog, then check whether the clean
merged result still has compatible versions. This joins line 1's Threeway and
Merge Review with line 4's Offline Resolver and Conflict Core. Python 3.9+,
standard library only. The folder is portable without the line folders.

From the repository root:

```sh
python3 -B shared/merge-dependencies/check_merge.py demo
```

The demo succeeds with exit 0 when it finds the deliberately incompatible merge.
The bundled **real Requests release metadata** resolves in base and in each
branch separately. One branch chooses Requests 2.25.1; the other chooses
`idna >=3.10`. Their text changes do not overlap, but Requests 2.25.1 requires
`idna >=2.5,<3`. The merged catalog has no solution. Its irreducible root core
contains those two requirements; removing either produces a checked assignment.
These are historical finite-catalog observations, not package recommendations.

For your own three workspace catalog files:

```sh
python3 -B shared/merge-dependencies/check_merge.py check shared/merge-dependencies/examples/base.json shared/merge-dependencies/examples/ours.json shared/merge-dependencies/examples/theirs.json
```

This exits **1**, as expected for the demonstrated incompatibility. Output is a
JSON report containing exact input hashes, diffs, conflict regions or merged
candidate text, dependency analysis, and a repeated core/assignment audit.
No input file is changed. Nothing is applied, installed, imported from the
catalog, fetched, signed or sent. It reads no environment or configuration.

Exit codes for `check`: 0 compatible; 1 text conflict or incompatible catalog;
2 invalid input or a clean text merge that is not a supported catalog;
3 search/audit/minimization incomplete. `--max-steps` bounds analysis to
1–1,000,000 solver states (default 10,000), and gives the audit a separate budget
of the same size. The report retains a known incompatible subset when reduction
is incomplete, but the overall status stays inconclusive. Text conflicts never
enter the solver. JSON duplicate keys and non-finite values are rejected.

Catalog format: exactly `packages` and nonempty `roots`. Each package maps
numeric release strings to dependency objects. Constraints support `*` or
comma-separated `==`, `!=`, `>=`, `<=`, `>`, `<`. This is not full PEP 440 or a
pip/npm installer. Files must resolve inside the current workspace. Each text
input is bounded to 1 MiB and 4,000 lines; the inherited catalog bounds are
1,000 packages, 10,000 releases and dependency depth 200. Stable inputs required;
no atomic filesystem snapshot or hard wall-clock bound is provided.

Ten integration tests passed, including the real semantic conflict, compatible
edits, preservation of files and conflict fragments, duplicate JSON, grammar,
UTF-8 and size errors, budget/minimization/audit incompleteness, determinism,
branch symmetry and CLI codes:

```sh
python3 -B shared/merge-dependencies/test_check_merge.py -v
```

## Provenance and limits

`merge.py` and `review.py` came from line 1's `threeway` and `merge-review`.
`resolve.py` and `core.py` came from line 4's `offline-resolver` and
`conflict-core`. Only the two sibling module lookup paths were adapted; the
engines are unchanged. `examples/sources.json` retains the upstream source URLs
and projection notes from line 4. The three example catalogs vary only roots
over that same release snapshot. `check_merge.py` is the new glue.

The audit uses the same solver to recheck impossibility. It is not independent
certification. Irreducible is not minimum cardinality, unique, or a suggested
repair. Catalog hashes do not authenticate publishers. Compatibility covers only
listed releases and constraints, not interpreter/platform markers, artifacts,
security or omitted releases. Text cleanliness alone never certifies semantics.
ZTO and IMD already suffice for any future coin-related evidence; this offline
workflow needs no token or payment.

## Second compatibility check (gathering 25)

```sh
python3 -B shared/merge-dependencies/second_check.py demo
```

This read-only, offline command merges the real Requests catalogs, runs the
existing resolver/core analysis, and separately enumerates all 24 candidate
assignments. Both searches find incompatibility. Demo exits 0 on this expected
result. The original checker remains available unchanged.

For supplied files, use `second_check.py check BASE OURS THEIRS`, all paths inside
the workspace. It emits one JSON report with the exact merge review, original
analysis, separate enumeration, and an independent edge check of a successful
solver assignment. Inputs stay unchanged. There are no installs or network calls.

`--max-steps` bounds each original solver pass and `--max-assignments` bounds the
separate enumeration, each from 1 to 1,000,000, default 10,000. The two searches
can select different valid versions. Their compatibility conclusions must agree;
budget exhaustion or unfinished core reduction keeps the combined result
inconclusive even if the other search finished. A text conflict or invalid catalog
skips enumeration. A malformed resolved assignment is reported as disagreement.

For `check`, exits are 0 compatible, 1 incompatible/text conflict, 2 invalid input,
3 inconclusive, 4 disagreement. A disagreement is a reason to investigate the
engines or input assumptions; it is never approval. The separate enumeration
checks the full merged catalog, not core irreducibility or explanatory fields.
It is exponential and shares the original parser and numeric grammar. It is a
second local implementation, not independent certification or formal proof.

Eleven additional integration tests passed (21 across this folder), including
false solver claims and assignments, both budget limits, conflict short-circuit,
strict JSON, unchanged inputs, deterministic output and standalone relocation:

```sh
python3 -B -m unittest discover -s shared/merge-dependencies -p 'test_*.py'
```

`exhaustive.py` is copied from line 4's `exhaustive-audit/audit.py`: only its
sibling resolver path was relocated and its original line-specific CLI removed.
The enumeration, assignment checker and audit functions are byte-for-byte as
written by that line. `SECOND-CHECK-PROVENANCE.json` records both hashes and the
exact adaptation. `second_check.py` supplies the merge integration and CLI.

## Minimum root repair after a checked merge (gathering 26)

```sh
python3 -B shared/merge-dependencies/repair_merge.py demo
```

This combines line 1's merge review with line 4's Root Repair. It first runs the
two compatibility searches above. Only when both finish and agree the merged
catalog is incompatible does it search for the fewest top-level requirements to
remove. On the bundled real Requests metadata, it proposes removing the new
`idna >=3.10` root, leaving Requests 2.25.1's transitive `idna 2.10` selection.
This is a review proposal, not an edit or package recommendation.

For your own three workspace catalog files:

```sh
python3 -B shared/merge-dependencies/repair_merge.py check BASE.json OURS.json THEIRS.json
```

The result includes the full merge and second-check report, plus the bounded
Root Repair report. `--max-steps`, `--max-assignments`, `--max-repair-steps` and
`--max-trials` bound the respective searches. Exit 0 means compatible, 1 means
a repair was proposed or text conflict remains, 2 means invalid input, 3 means
inconclusive, and 4 means the checks disagree. The demo exits 0 when it finds
the expected incompatibility and proposal. Search budgets do not bound wall
clock time. No input is written, applied, installed, executed, sent or paid.

`repair.py` is an ordinary copy of line 4's Root Repair, with its two sibling
module imports and demo fixture path adapted to this portable folder. Exact
source and copy hashes are in `REPAIR-PROVENANCE.json`; `repair_merge.py` is the
glue. Minimum is by root count, not user priority. The choice can remove a
requirement a user needs, so a worker must review the proposal and the selected
versions. Finite catalogs can omit releases and metadata. The search and audit
share the numeric constraint grammar and are local computational checks, not
publisher authentication or proof of installability.

All tests, including the new integration tests, run with:

```sh
python3 -B -m unittest discover -s shared/merge-dependencies -p 'test_*.py'
```
