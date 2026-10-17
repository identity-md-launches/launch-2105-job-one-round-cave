# Query Impact

See how a query's ranked, exactly cited answers change between two saved document
collections. A worker can tell whether a new source appeared in the results,
whether an excerpt changed, or whether the same evidence moved in rank. Runs
offline on Python 3.9+ with the standard library and the adjacent line-3 tools.
No installation, network, source execution, environment access or file writes.

From the repository root, one command shows it working:

```sh
python3 -B line-3/tools/query-impact/impact.py demo
```

When tried, the before snapshot had the two inherited ZTO/IMD token documents;
the after snapshot also included the inherited pool reference. The query
`ZTO pool tick spacing` with all terms required gained exactly `pool.md:1-10`,
including the real ZTO/IMD pool ID, fee 12500 and tick spacing 60. The output is
saved in [examples/zto-impact.json](examples/zto-impact.json).
This deliberately omitted-document comparison demonstrates completeness, not a
claim that Ethereum changed. Token metadata is a historical observation; pool
parameters are assignment-supplied, as the original source document states.

To compare your own Evidence Search indexes:

```sh
python3 -B line-3/tools/query-impact/impact.py compare before-index.json after-index.json "your search terms" --all --limit 5
```

Create each index using Evidence Search's `build ROOT --index NEW.json` command
while the corresponding document collection is available. Retain both JSON
indexes; Query Impact needs their embedded text, not the original directories.
All selected input paths must remain within the current working directory, with
no parent traversal or symlinks. Indexes contain full source text.

The report includes both complete search results, exact inclusive line citations,
excerpts and source hashes. `corpus` distinguishes document additions, removals
and byte edits. `changes` compares the selected top results:

- `entered` and `left` mean entering/leaving the top results, not necessarily
  adding/removing source files. Rank and overlap suppression can also cause this.
- `retained` matches exact `(path, line_start, line_end)` coordinates and compares
  ranks, normalized excerpts, whole-source hashes, scores and matched query terms.
  It makes no claim that edited text at those coordinates has the same meaning.
- `answers_changed` compares the ordered citations, excerpts and whole-source
  hashes. A CRLF-only edit or an edit outside a selected passage changes its
  source hash. A score-only change leaves this flag false.

Moving text or renaming a file is reported as leaving and entering; it is not
guessed to be a rename. Scores use the existing engine's eight-decimal output.
Adding unrelated sources can change BM25 scores without changing answer identity.
A report explains observed differences; it does not isolate each edit's causal
contribution or judge semantic change.

Every embedded source hash is validated, including non-hit sources. Snapshot
SHA-256 values bind canonical JSON with documents sorted by path; the report hash
binds the complete report excluding `report_sha256`. Formatting and document order
do not affect these hashes. A self-reported hash does not authenticate authorship:
retain hashes separately if you need to compare against an earlier trusted value.

All hits have `source_verified: false`: the bytes were checked inside the saved
snapshot, not against live files. No truth, remote freshness, chain verification,
or current ZTO price is established. Existing Evidence Search live queries still
verify selected files and return `source_verified: true` only after verification.
They share one ranking function with this tool; no second ranking implementation
was introduced. Corpus, passage, query and result bounds remain those documented
in [Evidence Search](../evidence-search/README.md).

JSON goes to stdout; invalid input gives JSON on stderr with no partial report.
Exit 0 means comparison succeeded, including changes and zero hits. Exit 2 means
invalid input or I/O failure. Neither exit code expresses approval of the evidence.

Sixteen new behavioral tests and all 57 existing line-3 tests passed:

```sh
python3 -B line-3/tools/query-impact/test_impact.py -v
```

Checks cover changed excerpts, CRLF-only edits, edits outside a hit, rank-only
movement, top-limit displacement, unrelated-source score changes, moved citations,
empty/no-hit/all-term queries, malformed and forged snapshots, unsafe paths,
document instructions remaining data, deterministic hashes and input preservation.
Thirty seeded corpora compare snapshot results with live searches in both query
modes. A separate regression trial also compared the refactored live engine to
the inherited implementation on 60 searches with identical results.

The JPEG encoder elsewhere in line 3 is used only for the wall export; it is not
loaded or required by Query Impact.
