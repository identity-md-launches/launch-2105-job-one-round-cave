# First joining

Step 01 establishes the line's three-way text merge goal and leaves the working `tools/threeway` tool. The cave figure joins red ochre and chalk trails without losing either colour: the same idea as keeping both contributors' edits visible.

## Wall output and review

- `artifacts/line-1/wall.png`: PNG, RGB, 1254 × 1254 pixels, matching the input cave's dimensions.
- `dist/line-1/01.jpg`: JPEG, RGB, 512 × 512 pixels; thumbnail of the finished wall.
- `dist/line-1/01.json`: first numbered record; its image address is the lowercase SHA-256 of the actual final PNG bytes.
- Method: built-in imagegen, editing the supplied bare cave reference; thumbnail made by format conversion and resizing.

I opened and visually reviewed the generated PNG. Pepe has a wide mouth, heavy-lidded eyes, and two visible hands. Each has four fingers and one thumb (five digits); there are no other hands or handprints. There is no visible writing, number, caption, logo, signature, watermark, border, political symbol or real person. Pigments are ochre, charcoal and chalk; the cave framing, warm light, major cracks, floor and corner crystals remain recognisable. Both images also passed decode and dimension checks.

Limitations: generative editing is not pixel-identical preservation of unpainted rock; fine texture varies. No prior painting existed to preserve. This is a local visual review, not external approval. The brief simultaneously requests a JPEG beside the dist record and forbids pictures outside artifacts; the JPEG follows the explicit beside-record layout, so that blanket location restriction is unmet. No other visual requirement was observed unmet.

## Generation prompt

Use case: precise-object-edit. Edit target: the supplied square bare cave wall. Create the FIRST cave painting by adding pigments onto the central rock only. Preserve the exact cave framing, warm rock colours, cracks, torch lighting, floor and crystals at bottom corners; do not reimagine or smooth the cave. Output square at the original 1254 by 1254 dimensions if possible. Main mark: one recognisable Pepe the frog, drawn primitively with charcoal black and red/yellow ochre and chalk, big heavy-lidded eyes, very wide mouth and thick lips, squatting small in the left-middle part of the wall. Ancient uneven worn stick-and-thumb pigment, exposed stone visible through it, Lascaux/Chauvet aesthetic. His two arms end in open hands: each hand must have exactly FIVE clearly separated digits, four fingers plus one thumb. Count five each. To his right, two wandering short trails of dots, one red ochre and one chalk white, join into a single trail carrying both pigments, a symbol of preserving two contributors' work. Keep composition modest and leave most rock free for later ancestors. No writing, letters, numbers, labels, signatures, logos, watermarks, borders, frames, photorealistic frog or 3D render. Do not add other hands or handprints. Save the final PNG at artifacts/line-1/wall.png if file saving is supported.

## Step 22: review before joining

`tools/merge-review` adds contributor diffs, exact-byte input fingerprints and contextual conflict packets while keeping the original merger unchanged. Run `python3 -B line-1/tools/merge-review/review.py --demo clean` from the workspace root. See `STEP-22.md` for this step's output dimensions, preservation check and limitations. The new wall has a small reviewing eye above the old trails; all older marks are preserved.

## Step 23: review a directory tree

`tools/tree-review` extends review to additions, deletions and concurrent edits
across three directories. It explicitly flags delete/modify and file/directory
conflicts, retains contributor diffs, and never modifies its inputs. Run
`python3 -B line-1/tools/tree-review/tree_review.py --demo clean` from the workspace
root. All 61 line-1 tests passed. The new wall's small ochre twig holds three chalk
pebbles; ancestral marks remain unchanged. See `STEP-23.md` for output dimensions,
verification and limitations, and the tool README for use on your own text files.

## Step 26: finish explicit conflicts

`tools/conflict-finish` stages a conflicted three-directory merge only after a
reviewer supplies complete replacement text or deletion and a reason for every
conflicted path. It rechecks the saved review and writes a new candidate tree
with an audit receipt. Run `python3 -B line-1/tools/conflict-finish/test_finish.py`
from the workspace root; the 9 new tests passed. See `STEP-26.md` and the tool
README for the real-file trial, use and limits. A small ochre bridge now spans
an open patch of the inherited wall.
