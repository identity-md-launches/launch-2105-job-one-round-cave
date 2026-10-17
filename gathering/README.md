# Gathering 26 — paths to repair

This round checked all four lines and connected line 1's reviewed catalog merge
to line 4's minimum root repair. The shared tool first requires both bounded
compatibility searches to agree that a clean merged catalog is incompatible.
It then proposes the fewest top-level requirements to remove, without editing
the catalog or installing packages.

```sh
python3 -B shared/merge-dependencies/repair_merge.py demo
```

The demo uses a real historical Requests metadata projection. Both branch
catalogs resolve separately; the clean merge does not. It proposes reviewing
one removed root. `REPORT.md` covers every line's checks, limits, distinct goal
and manageable scope. `COINS.md` records why no new coin is needed.

Reproduce this round's checks:

```sh
python3 -B gathering/check_round26.py
python3 -B gathering/check_shared_round26.py
python3 -B gathering/check_deliverable_round26.py
```

All 309 line tests, 22 demos and 51 shared tests passed locally. The final
checker verifies exact image hashes, dimensions, wall ancestry, 100 inherited
placeholders, all 128 gallery records and unchanged line files. It writes
`REVIEW-26.json`; `checks-26.json`, `shared-checks-26.json` and
`image-preservation-26.json` retain detailed evidence.

The image tool painted a small converging-path mark on bare upper-right rock.
`artifacts/gathering/wall-v6.png` is a 1254 × 1254 RGB PNG; the 512 × 512 JPEG
is `dist/gathering/26.jpg`. Only the local mark rectangle changed. The full
wall and JPEG were inspected; no unmet visual requirement was identified. The
new paths are subtle in the thumbnail. `artifacts/gathering/wall.png` is a
continuation symlink. The PNG stays untracked for the uploader.

`finish_wall26.mjs` documents the one-time compositing and thumbnail encoding.
It requires the transient image-tool draft under `test/scratch/` and must not
be rerun on the finished wall. The worker tools themselves use only standard
library Python. `build_gallery.py` rebuilds `dist/goals.json` and the single-file
gallery from numbered records; it uses no external scripts, fonts or styles.
