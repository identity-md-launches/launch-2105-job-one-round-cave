"""One-use finishing helper: composite image-tool pigment, preserve old pixels.

The generated RGBA draft must occupy wall-v6.png before running. It is replaced
by the finished wall. No auxiliary image is saved. Uses the inherited JPEG
encoder solely to encode the required thumbnail; the search tool is Python only.
"""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import zlib


def read_png(path):
    raw = Path(path).read_bytes()
    if raw[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('not PNG')
    at, packed = 8, bytearray()
    while at < len(raw):
        size = int.from_bytes(raw[at:at + 4], 'big')
        kind, body = raw[at + 4:at + 8], raw[at + 8:at + 8 + size]
        crc = int.from_bytes(raw[at + 8 + size:at + 12 + size], 'big')
        if zlib.crc32(kind + body) != crc:
            raise ValueError('bad CRC')
        if kind == b'IHDR':
            width, height, depth, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', body)
            if depth != 8 or color not in (2, 6) or (compression, filtering, interlace) != (0, 0, 0):
                raise ValueError('expected 8-bit RGB/RGBA noninterlaced PNG')
            channels = 3 if color == 2 else 4
        elif kind == b'IDAT':
            packed.extend(body)
        elif kind == b'IEND':
            break
        at += size + 12
    data, stride = zlib.decompress(packed), width * channels
    if len(data) != height * (stride + 1):
        raise ValueError('bad data length')
    result, previous = bytearray(), bytearray(stride)
    for y in range(height):
        at = y * (stride + 1)
        mode, row = data[at], bytearray(data[at + 1:at + stride + 1])
        for x in range(stride):
            left = row[x - channels] if x >= channels else 0
            above = previous[x]
            upper_left = previous[x - channels] if x >= channels else 0
            if mode == 0:
                predictor = 0
            elif mode == 1:
                predictor = left
            elif mode == 2:
                predictor = above
            elif mode == 3:
                predictor = (left + above) // 2
            elif mode == 4:
                p = left + above - upper_left
                distances = (abs(p - left), abs(p - above), abs(p - upper_left))
                predictor = (left, above, upper_left)[distances.index(min(distances))]
            else:
                raise ValueError('bad filter')
            row[x] = (row[x] + predictor) & 255
        result.extend(row)
        previous = row
    return width, height, channels, result


def write_png(path, width, height, pixels):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    rows = b''.join(b'\0' + pixels[y * width * 3:(y + 1) * width * 3] for y in range(height))
    raw = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
           + chunk(b'IDAT', zlib.compress(rows, 9)) + chunk(b'IEND', b''))
    Path(path).write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def main():
    ancestor = Path('artifacts/line-3/wall-v5.png')
    output = Path('artifacts/line-3/wall-v6.png')
    ancestor_hash = hashlib.sha256(ancestor.read_bytes()).hexdigest()
    assert ancestor_hash == '6089ce7fa5a036d9ba99c3673cc59457fa1784c7be412368f83dabfcbe68396e'
    draft_hash = hashlib.sha256(output.read_bytes()).hexdigest()
    width, height, channels, original = read_png(ancestor)
    gw, gh, gc, pigment = read_png(output)
    assert (width, height, channels) == (1254, 1254, 3)
    assert (gw, gh, gc) == (1536, 1024, 4), 'expected fresh generated motif, not finished wall'
    final = original[:]
    x0, y0, mw, mh = 770, 220, 265, 165
    sx0, sy0, sw, sh = 125, 65, 1315, 790
    for y in range(mh):
        for x in range(mw):
            sx, sy = sx0 + x * sw // mw, sy0 + y * sh // mh
            source = (sy * gw + sx) * 4
            r, g, b, a = pigment[source:source + 4]
            # Reject the generator's low-opacity glow; retain only solid dry
            # pigment, with stone visible between strokes. No new strokes drawn.
            alpha = max(0.0, (a - 180) / 75) * .85
            if not alpha:
                continue
            target = ((y0 + y) * width + x0 + x) * 3
            for c, color in enumerate((r, g, b)):
                final[target + c] = round(original[target + c] * (1 - alpha) + color * alpha)
    changed = outside = 0
    for pixel in range(width * height):
        if final[pixel * 3:pixel * 3 + 3] != original[pixel * 3:pixel * 3 + 3]:
            changed += 1
            x, y = pixel % width, pixel // width
            outside += not (x0 <= x < x0 + mw and y0 <= y < y0 + mh)
    assert changed > 0 and outside == 0
    digest = write_png(output, width, height, final)
    assert read_png(output)[3] == final
    continuation = Path('artifacts/line-3/wall.png')
    assert continuation.is_symlink() and continuation.readlink() == Path('wall-v5.png')
    continuation.unlink()
    continuation.symlink_to('wall-v6.png')
    rgba = bytearray()
    for y in range(512):
        ya, yb = y * height // 512, (y + 1) * height // 512
        for x in range(512):
            xa, xb = x * width // 512, (x + 1) * width // 512
            count = (yb - ya) * (xb - xa)
            for c in range(3):
                rgba.append(round(sum(final[(sy * width + sx) * 3 + c]
                                      for sy in range(ya, yb) for sx in range(xa, xb)) / count))
            rgba.append(255)
    javascript = """
const fs = require('fs');
const encode = require('./line-3/tools/corpus-change-receipt/vendor/jpeg-js/lib/encoder.js');
const data = fs.readFileSync(0);
if (data.length !== 512 * 512 * 4) throw Error('bad RGBA length');
const result = encode({data, width:512, height:512}, 77);
if (result.data.length >= 100000) throw Error('thumbnail too large');
fs.writeFileSync('dist/line-3/26.jpg', result.data);
"""
    subprocess.run(['node', '-e', javascript], input=rgba, check=True)
    report = {
        'ancestor_sha256': ancestor_hash, 'generated_motif_sha256': draft_hash,
        'wall_sha256': digest, 'format': 'PNG', 'mode': 'RGB',
        'dimensions': [width, height], 'new_mark_rectangle': [x0, y0, mw, mh],
        'changed_pixels': changed, 'changed_pixels_outside_rectangle': outside,
        'thumbnail': {'path': 'dist/line-3/26.jpg', 'format': 'JPEG', 'dimensions': [512, 512],
                      'bytes': Path('dist/line-3/26.jpg').stat().st_size},
        'method': 'Image-tool pigment with low-opacity glow removed, composited only onto previously bare rock.',
        'visual_review': 'pending', 'unmet_visual_requirements': [],
    }
    Path('line-3/IMAGE-26.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
