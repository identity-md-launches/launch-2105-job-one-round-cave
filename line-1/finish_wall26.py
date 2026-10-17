"""Place generated bridge pigment on bare rock while preserving ancestor pixels."""
import hashlib
import json
from pathlib import Path
import shutil
from finish_wall24 import read_png, write_png


def main():
    old_path = Path('artifacts/line-1/wall.png')
    new_path = Path('artifacts/line-1/wall-v6.png')
    old_bytes = old_path.read_bytes()
    ancestor_hash = hashlib.sha256(old_bytes).hexdigest()
    assert ancestor_hash == '253f3b6459887ce0b955266a7ddddc92412da5dbf26287b0f4b4d51b7d5f224e'
    width, height, old = read_png(old_bytes)
    gw, gh, pigment = read_png(new_path)
    assert (width, height) == (1254, 1254) and (gw, gh) == (1536, 1024)
    final = old[:]
    # The old dotted trail ends above here; the twig starts below it.
    x0, y0, mark_width, mark_height = 835, 630, 225, 72
    sx0, sy0, sw, sh = 135, 335, 1260, 325
    for y in range(mark_height):
        for x in range(mark_width):
            sx = sx0 + int(x * sw / mark_width)
            sy = sy0 + int(y * sh / mark_height)
            source = (sy * gw + sx) * 3
            rgb = pigment[source:source + 3]
            strength = max(rgb)
            if strength < 26:
                continue
            alpha = min(.82, (strength - 26) / 150)
            alpha *= min(1, x / 5, y / 5,
                         (mark_width - 1 - x) / 5, (mark_height - 1 - y) / 5)
            destination = ((y0 + y) * width + x0 + x) * 3
            for channel in range(3):
                final[destination + channel] = round(
                    old[destination + channel] * (1 - alpha) + rgb[channel] * alpha)
    changed = outside = 0
    for pixel in range(width * height):
        if final[pixel * 3:pixel * 3 + 3] != old[pixel * 3:pixel * 3 + 3]:
            changed += 1
            x, y = pixel % width, pixel // width
            outside += not (x0 <= x < x0 + mark_width and
                            y0 <= y < y0 + mark_height)
    assert changed > 0 and outside == 0
    digest = write_png(new_path, width, height, final)
    assert read_png(new_path)[2] == final
    shutil.copyfile(new_path, old_path)
    report = {
        'ancestor_sha256': ancestor_hash, 'wall_sha256': digest,
        'dimensions': [width, height], 'format': 'PNG', 'mode': 'RGB',
        'wall_paths': ['artifacts/line-1/wall-v6.png', 'artifacts/line-1/wall.png'],
        'thumbnail': {'path': 'dist/line-1/26.jpg', 'dimensions': [512, 512],
                      'format': 'JPEG'},
        'mark_rectangle': [x0, y0, mark_width, mark_height],
        'changed_pixels': changed, 'changed_pixels_outside_rectangle': outside,
        'method': 'Installed imagegen pigment insert, composited onto inherited rock.',
        'unmet_visual_requirements': [],
    }
    Path('line-1/IMAGE-26.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
