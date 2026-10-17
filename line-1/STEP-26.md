# Step 26 — Bridge across the gap

Conflict Finish advances the unchanged line goal after Candidate Export: a
reviewer can now stage a conflicted small UTF-8 tree by making one explicit,
reasoned decision for each conflicted path. The tool checks the retained packet
hash, recomputes the full review against current source trees, rejects missing or
extra decisions and file/directory collisions, writes only to a new output
directory, and returns a receipt with hashes and each decision's provenance.
It does not interpret whether the chosen content is semantically right.

From the workspace root, see it work with actual files:

```sh
python3 -B line-1/tools/conflict-finish/test_finish.py
```

All 9 new and 85 inherited line tests passed. A separate trial copied six
Threeway files into three trees, introduced a same-line README conflict, and
staged a reviewed replacement retaining both workers' additions. Source bytes
remained unchanged and the output manifest matched the staged tree. The tool
README gives the exact decisions schema and command for worker inputs. No coin,
price, payment, chain data, network call, wallet, key, signing or sending is
needed for local text reconciliation.

## Painting and output

Installed imagegen made a single irregular ochre bridge with a chalk pebble and
charcoal trails. Its black backing was discarded in memory while the pigment was
composited onto a small bare-rock area of the inherited wall. The original Pepe,
all prior marks, cracks, light, rock and framing are unchanged outside the mark.
Pepe's inherited hands still have five digits each; no new hands or stencils were
added. Full wall and JPEG were visually inspected: no writing, numbers, caption,
signature, logo, watermark, border, real person or prohibited symbol is present.

The final PNG is 1254 × 1254 RGB at both `artifacts/line-1/wall-v6.png` and
`artifacts/line-1/wall.png`; their bytes match. Only 3,173 pixels changed within
rectangle [835, 630, 225, 72], and none outside it. `dist/line-1/26.jpg` is a
512 × 512 JPEG of that wall, 96,571 bytes. The bridge is small and faint at
thumbnail size, a visibility limit of fitting a new mark among prior paintings.
No unmet visual requirement was observed. The explicit dist JPEG location
conflicts with the blanket statement that pictures live only under artifacts;
the requested beside-record JPEG location was followed. `IMAGE-26.json` records
the dimensions, format, preservation check and visual review.

## Imagegen prompt

Use case: illustration-story. Asset type: small pigment insert for an existing
square cave painting, to be composited onto rough warm rock. On a perfectly flat
pure black background, draw ONE small simple prehistoric stone bridge: an uneven
low red-ochre arch joining two short separated charcoal trails, with one small
chalk-white pebble resting at its center. Make the bridge look like ancient
handmade worn thumb and burnt-stick pigment, Lascaux/Chauvet cave pictograph,
exposed black negative space all around. Center the single object with very
generous black margins so it can be cropped. Earth pigments only: red and yellow
ochre, charcoal black, chalk white. No rock background in the insert, no frog,
no hands, no handprints, no people, no letters, numbers, symbols, logos, caption,
signature, border, watermark, photograph or 3D render. The bridge must be an
organic irregular arch, not a geometric icon.
