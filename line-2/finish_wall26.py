"""Keep only the image tool's new pigment; preserve ancestor pixels elsewhere.

One-use finishing helper. No painting is generated procedurally. The tool's
draft must already occupy wall-v6.png. Codecs are inherited repository files.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

spec = importlib.util.spec_from_file_location('inherited_png_codec', 'gathering/finish_wall.py')
png = importlib.util.module_from_spec(spec)
spec.loader.exec_module(png)


def main():
    old = Path('artifacts/line-2/wall-v5.png')
    output = Path('artifacts/line-2/wall-v6.png')
    ancestor_sha = hashlib.sha256(old.read_bytes()).hexdigest()
    assert ancestor_sha == '34a0d92d765d9fa30b6facd0dcca8c1df50ef3c541a7af69a89e61afbf48bbf0'
    draft_sha = hashlib.sha256(output.read_bytes()).hexdigest()
    width, height, original = png.read_png(old)
    dw, dh, draft = png.read_png(output)
    assert (width, height) == (dw, dh) == (1254, 1254)
    final = original[:]
    # Select generated ochre pebbles and the charcoal cord. These masks select
    # source pigment only; every output color comes from the generated draft
    # blended with the original rock. No strokes are drawn here.
    rectangle = (430, 260, 205, 95)
    x0, y0, rw, rh = rectangle
    for y in range(y0, y0 + rh):
        for x in range(x0, x0 + rw):
            index = (y * width + x) * 3
            r, g, b = draft[index:index + 3]
            ellipses = [((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
                        for cx, cy, rx, ry in ((453, 286, 22, 22),
                                              (527, 328, 20, 21),
                                              (608, 307, 22, 22))]
            distance = min(ellipses)
            alpha = 0.0
            if distance < 1 and r > 1.55 * g and r > 2.4 * b:
                alpha = .9 * min(1, (1 - distance) * 5)
            if 467 <= x <= 595 and 296 <= y <= 329 and r < 115 and g < 85:
                alpha = max(alpha, min(.9, (115 - r) / 45))
            if alpha:
                for channel in range(3):
                    final[index + channel] = round(original[index + channel] * (1 - alpha)
                                                   + draft[index + channel] * alpha)
    changed = outside = 0
    for i in range(width * height):
        if final[i * 3:i * 3 + 3] != original[i * 3:i * 3 + 3]:
            changed += 1
            x, y = i % width, i // width
            outside += not (x0 <= x < x0 + rw and y0 <= y < y0 + rh)
    assert changed > 0 and outside == 0
    digest = png.write_png(output, width, height, final)
    assert png.read_png(output)[2] == final
    continuation = Path('artifacts/line-2/wall.png')
    assert continuation.is_symlink() and continuation.readlink() == Path('wall-v5.png')
    continuation.unlink()
    continuation.symlink_to('wall-v6.png')

    # Area-average in memory, then use the already-vendored JPEG encoder.
    # There is no intermediate picture or raw-pixel file.
    rgba = bytearray()
    for y in range(512):
        ya, yb = y * height // 512, (y + 1) * height // 512
        for x in range(512):
            xa, xb = x * width // 512, (x + 1) * width // 512
            n = (yb - ya) * (xb - xa)
            for channel in range(3):
                rgba.append(round(sum(final[(sy * width + sx) * 3 + channel]
                                      for sy in range(ya, yb) for sx in range(xa, xb)) / n))
            rgba.append(255)
    javascript = """
const fs = require('fs');
const encode = require('./line-3/tools/corpus-change-receipt/vendor/jpeg-js/lib/encoder.js');
const data = fs.readFileSync(0);
if (data.length !== 512 * 512 * 4) throw Error('bad RGBA input');
const result = encode({data, width:512, height:512}, 78);
if (result.data.length >= 100000) throw Error('JPEG exceeds limit');
fs.writeFileSync('dist/line-2/26.jpg', result.data);
"""
    subprocess.run(['node', '-e', javascript], input=rgba, check=True)
    report = {
        'round': 26, 'ancestorSha256': ancestor_sha, 'generatedDraftSha256': draft_sha,
        'wallSha256': digest, 'dimensions': [width, height], 'format': 'PNG', 'channels': 'RGB',
        'newMarkRectangle': list(rectangle), 'changedPixels': changed,
        'changedPixelsOutsideRectangle': outside,
        'method': 'Imagegen edited the ancestor; only its new pigment was blended onto unused rock.',
        'images': [], 'unmetVisualRequirements': [],
    }
    for path, kind, size in ((output, 'PNG', [1254, 1254]),
                             (continuation, 'PNG', [1254, 1254]),
                             (Path('dist/line-2/26.jpg'), 'JPEG', [512, 512])):
        data = path.read_bytes()
        report['images'].append({'path': str(path), 'format': kind, 'dimensions': size,
                                 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
    Path('line-2/REVIEW-26.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
