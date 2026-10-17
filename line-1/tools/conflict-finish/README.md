# Conflict Finish

Stage a conflicted three-directory text merge after a reviewer explicitly chooses
the contents of **every** conflicted path. Python 3.10+ standard library only.
Keep the sibling Candidate Export, Review Recheck, Tree Review, Merge Review and
Threeway folders: this tool reuses their bounded readers and merge logic. It
never changes any of the three source trees.

One command from the workspace root shows it working on real files:

```sh
python3 -B line-1/tools/conflict-finish/test_finish.py
```

When tried, all 9 integration tests passed. They stage reviewed UTF-8 and CRLF
content; verify unchanged inputs and the output manifest; require exactly one
decision per conflict; reject stale or tampered packets, wrong hashes, unsafe
paths, symlinks, unresolved file/directory collisions and existing outputs; and
roll back a simulated write failure. A separate trial copied the inherited
Threeway source tree into three directories. Both workers edited the same
README line; one explicit decision kept both changes, and all 6 source files
were preserved. See `../../REAL-TRIAL-26.json`.

## Use on your own review

Run from the workspace root. Create and inspect a Tree Review packet outside all
three input trees, then retain the exact packet SHA-256 separately. The packet
can exit 1 because it has conflicts. Write a UTF-8 decisions JSON file like:

```json
{
  "schema": "conflict-finish/v1",
  "packet_sha256": "THE_RETAINED_LOWERCASE_SHA256",
  "decisions": {
    "path/to/conflicted.txt": {
      "candidate": "the complete reviewed replacement text\n",
      "reason": "Explain how the competing edits were reconciled."
    }
  }
}
```

Use JSON `null` for `candidate` when explicitly deleting a conflicted file.
Include every path whose Tree Review status ends in `conflict`, and no other
paths. For a file/directory collision, select a consistent final path layout;
the tool rejects a parent file kept alongside a child file. A reason is required
for each choice, but the program cannot judge whether the reason or replacement
text is correct. Review the full candidate text and both source versions first.

```sh
python3 -B line-1/tools/conflict-finish/finish.py PACKET.json BASE_DIR OURS_DIR THEIRS_DIR DECISIONS.json NEW_OUTPUT_DIR --expected-sha256 RETAINED_LOWERCASE_SHA256
```

Replace the uppercase placeholders with workspace paths and the retained digest.
The new output directory's parent must already exist. It must be separate from
all input trees and must not exist yet. The packet and decisions file must be
regular files inside the workspace without symlink traversal. Keep the retained
digest independent of the packet and decisions file: a digest supplied by the
same untrusted source adds no authentication.

Before creating output, Conflict Finish checks the exact packet hash and
recomputes the entire Tree Review report from current inputs. It refuses any
stale or altered report. It takes clean file candidates only from the recomputed
report and conflicted candidates only from explicit decisions. It writes exact
UTF-8 bytes into a new directory, rereads them, and returns a JSON receipt with
the packet/decisions hashes, per-file hashes, output manifest, omitted paths and
the reason, original status and three input fingerprints for each resolution.
Inspect the staged tree and receipt before adopting the result.

Exit 0: staged result. Exit 1: reproducible review refused because it is stale,
altered or clean. Exit 2: malformed input, unsafe path, invalid decision or
filesystem failure. No receipt is printed on failure.

## Limits

Explicit choices make losses visible; they do not prove semantic correctness,
author identity or approval. The reviewer may still choose text that discards a
contribution, so inspect every decision. This tool supports the inherited small
UTF-8 trees: at most 128 files, 256 directories, 16 levels, 1 MiB and 4,000
lines per file, 8 MiB combined input; packets at most 64 MiB and decisions at
most 16 MiB. Resolved output is at most 128 files and 8 MiB, with each file
within inherited per-file bounds. No binaries, renames, permissions or empty
directories are merged. Inputs and output parent must stay stable during use;
there is no atomic filesystem snapshot or crash-safe publication. An interrupted
process can leave partial output, which must be discarded. No network, coin,
wallet, signing, sending or payment is involved.
