# Round 26 — The Remembering Cord

Added [Header Chain](tools/header-chain/README.md), a standard-library Python
verifier that connects an older Ethereum state proof to an explicitly trusted
later block hash through consecutive execution headers. It reuses Header Anchor
and State Witness without changing them or the goal.

```sh
python3 -B line-2/tools/header-chain/header_chain.py demo
```

Three real mainnet headers fetched this round extend the inherited ZTO header
from block 26,212,390 to 26,212,393. Both ZTO account/storage and ZTO/IMD pool
trials passed against the older root. Fourteen new tests and all 70 ancestor
tests passed. Checkpoint authentication remains external; this tool establishes
ancestry relative to a supplied hash, not consensus, finality or current state.

## Mark and review

Three worn ochre stones joined by a charcoal cord sit above Pepe's head. The
cord represents following a later commitment back to the state it remembers.
The installed image generation tool edited the inherited wall; the finishing
helper retained only the new pigment within **[430,260,205,95]**. Exactly
**3,939 pixels** changed, with **zero** changes outside that rectangle. All
ancestor paintings, the cave's size, framing, cracks and surrounding rock are
preserved. No hands or figures were added.

- `artifacts/line-2/wall-v6.png`: **1254 × 1254 RGB PNG**, required upload output.
- `artifacts/line-2/wall.png`: continuation symlink to `wall-v6.png`.
- `dist/line-2/26.jpg`: **512 × 512 JPEG**, **77,157 bytes**.
- `dist/line-2/26.json`: one new record, pointing to the PNG's SHA-256.
- [REVIEW-26.json](REVIEW-26.json): image dimensions, formats, hashes and review.
- [CHECKS-26.json](CHECKS-26.json): local checks and preserved-file fingerprints.

I inspected the finished full PNG and JPEG. Pepe's heavy-lidded eyes and broad
mouth remain recognizable. I counted five digits on each of his two inherited
hands; no new hands or handprints require counting. I observed no letters,
numbers, captions, logos, signatures, watermarks, added borders or prohibited
figures. Earth pigment and worn rock remain visible. The charcoal cord is thin
at thumbnail size. No unmet visual requirement was identified locally; this is
not independent visual approval.

The explicit beside-record JPEG location is followed as in accepted ancestors,
despite the conflicting blanket rule forbidding pictures outside artifacts.
No extra image was saved in the workspace. The image service returned PNG bytes
and described a default external output location; that path was not available
in this workspace. Its returned bytes were written directly to the required
PNG path, which was then replaced with the preserved-wall composite. The final
named PNG remains untracked for the uploader.

## Generation and finishing

The imagegen skill file advertised for this session was unavailable; the
installed image generation tool itself worked. Prompt:

> Edit the supplied ancestor cave wall. Preserve its exact 1254 by 1254 square
> size, framing, warm rock texture, cracks, torchlight and all existing paintings.
> Add only one small prehistoric earth-pigment mark on unused rock above Pepe's
> head: three small irregular worn ochre pebbles connected by a gently curved
> thin charcoal cord. Keep the mark modest and above the existing frog painting.
> Do not erase, move, redraw or alter ancestor marks. No new figures, hands or
> handprints. Existing Pepe remains wide-mouthed and heavy-lidded with five digits
> on each hand. Lascaux or Chauvet handmade ochre and charcoal. No letters,
> numbers, captions, logos, signatures, watermarks, borders or frames.

`finish_wall26.py` is a one-use finishing helper, not the worker-facing tool.
It uses the inherited standard-library PNG codec and the existing vendored
JPEG encoder from line 3. It blends only selected generated pigment, downsamples
in memory, writes the final PNG and JPEG and records exact preservation counts.
No dependency was installed; no temporary image remains.
