# Root Repair

Find the fewest top-level requirements to remove from a finite dependency catalog
to make its remaining requirements compatible. This gives a worker a concrete
relaxation to review after a conflict, together with compatible selected versions.
It proposes a change; it never changes a catalog or installs packages.

Run the complete offline demonstration from the repository root:

```sh
python3 -B line-4/tools/root-repair/repair.py demo
```

On the stored real Requests metadata projection, this returned `repaired`:
remove the `idna >=3.10` root, retain Requests 2.25.1, certifi and urllib3 roots,
and select idna 2.10 with Requests' other dependencies. It used **10 shared search
states in three trials**. The original catalog and the first one-root candidate
were incompatible. No zero-removal solution exists, so one removal is minimum.
Removing an idna root does not ban idna: Requests still requires it transitively.
This is a finite-catalog compatibility example, not a version recommendation.

Python 3.9+ and only its standard library are needed. Keep the adjacent
`offline-resolver/`, `exhaustive-audit/` and (for demo data) `conflict-core/`
folders. Inputs use Offline Resolver's numeric version and conjunction grammar;
see its README for the exact schema. All reads stay inside the current workspace.
No network, configuration, account, environment variable, package code or secrets
are accessed. JSON is printed to stdout; no files are written by the tool.

For a workspace-local catalog:

```sh
python3 -B line-4/tools/root-repair/repair.py path/to/catalog.json --max-steps 10000 --max-trials 10000
```

Exit 0 means `compatible` (zero removals) or `repaired` (positive removals).
Exit 2 means invalid input; exit 3 means `inconclusive`, without a minimum claim.
Duplicate JSON keys, unsupported constraints, name collisions and paths outside
the workspace are rejected by the inherited loader/validator.

Root subsets are tried by increasing removal count, then canonical package-name
order. Every root has equal removal cost. The first compatible subset wins ties;
the tool does not list every minimum repair or prioritize what matters to you.
Packages, releases and dependency edges are retained unchanged. Removing every
root is the explicitly permitted last resort and returns the empty assignment;
it may not be useful to the worker. The input itself must have at least one root.

`fully_rejected_removal_sizes` lists cardinalities for which every removal subset
was proved incompatible by the inherited solver. Earlier subsets at the winning
cardinality are also tried but do not affect the minimum-cardinality proof.
`catalog_sha256` binds normalized names and sorted JSON for the entire catalog,
including its roots; it is not a signature or independent proof certificate.
It need not match other tools' digest formats. Equivalent constraint spellings
can have different hashes.

`--max-steps` shares one solver-state budget across **all** trials;
`--max-trials` bounds subsets, including the empty-remaining-root trial. Both
accept integers 1–1,000,000. The first unresolved trial stops the search; the
tool never skips uncertainty to claim a minimum. A fully completed result at
exactly the budget is accepted. Empty remaining roots need no solver states.
Inherited depth limits can also produce inconclusive results. Search is
exponential; budgets do not bound parsing, memory or wall-clock time.

The final reachable assignment is checked by Exhaustive Audit's separate
iterative edge checker, which does not use the solver's compatibility predicate.
Minimum cardinality still trusts the inherited search for previous impossible
subsets and shares its grammar. This is local computational evidence rather than
independent certification. A future release added to the finite catalog can
change the minimum. No full PEP 440, interpreter/platform markers, extras,
artifact validation, security assessment or installability claim is provided.

Checks run successfully:

```sh
python3 -B -m unittest discover -s line-4/tools/root-repair -p 'test_*.py' -v
```

All **12 tests passed**, including 250 seeded catalogs compared with the separate
enumerator across all root subsets, minimum versus larger repairs, transitive
removed roots, missing packages, cycles, empty assignments, exact budget edges,
shared exhaustion, canonical digests, immutable inputs, a deliberately false
solver witness and actual CLI status codes on the real metadata snapshot.
These tests write no files and need no network.
