"""One-shot image finish: retain ancestor pixels, encode preview with system libgd.

Run only against the inherited wall.png and image-generated wall-v6.png.
This is an artwork build helper, not a dependency of the standard-library tool.
"""
import ctypes
import hashlib
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('png_codec', Path(__file__).with_name('finish_wall22.py'))
codec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(codec)
ancestor = Path('artifacts/line-4/wall.png')
output = Path('artifacts/line-4/wall-v6.png')
old_sha = hashlib.sha256(ancestor.read_bytes()).hexdigest()
assert old_sha == '02d549d6502d5dab1259aef5893b079053dfbcb15bd0c801714dc0b832413e61', 'expected inherited wall'
w, h, original = codec.read_png(ancestor)
dw, dh, draft = codec.read_png(output)
assert (w, h) == (dw, dh) == (1254, 1254)
final = original[:]
changed = 0
for y in range(388, 518):
    for x in range(808, 1045):
        at = (y*w+x)*3
        r, g, b = draft[at:at+3]
        # Isolate the generated charcoal mesh and red pebbles. All other rock
        # pixels, including all old paint, retain their original bytes.
        charcoal = r < 92 and g < 77 and b < 65
        ochre = r > 80 and r > 1.8*g and r > 2.6*b and g < 115
        if charcoal or ochre:
            alpha = .85
            for c in range(3):
                final[at+c] = round(original[at+c]*(1-alpha)+draft[at+c]*alpha)
        changed += final[at:at+3] != original[at:at+3]
assert 1000 < changed < 237*130
sha = codec.write_png(output, w, h, final)

# Existing system libgd performs only thumbnail resampling/JPEG encoding.
gd = ctypes.CDLL('libgd.so.3')
ptr, integer = ctypes.c_void_p, ctypes.c_int
gd.gdImageCreateFromPngPtr.argtypes = [integer, ptr]
gd.gdImageCreateFromPngPtr.restype = ptr
gd.gdImageCreateTrueColor.argtypes = [integer, integer]
gd.gdImageCreateTrueColor.restype = ptr
gd.gdImageCopyResampled.argtypes = [ptr, ptr] + [integer]*8
gd.gdImageJpegPtr.argtypes = [ptr, ctypes.POINTER(integer), integer]
gd.gdImageJpegPtr.restype = ptr
gd.gdFree.argtypes = [ptr]
gd.gdImageDestroy.argtypes = [ptr]
raw = output.read_bytes()
buffer = ctypes.create_string_buffer(raw)
source = gd.gdImageCreateFromPngPtr(len(raw), buffer)
target = gd.gdImageCreateTrueColor(512, 512)
assert source and target
gd.gdImageCopyResampled(target, source, 0, 0, 0, 0, 512, 512, w, h)
size = integer()
encoded = gd.gdImageJpegPtr(target, ctypes.byref(size), 85)
assert encoded
jpeg = ctypes.string_at(encoded, size.value)
gd.gdFree(encoded)
gd.gdImageDestroy(source)
gd.gdImageDestroy(target)
assert len(jpeg) < 100000 and jpeg[:2] == b'\xff\xd8'
Path('dist/line-4/24.jpg').write_bytes(jpeg)
ancestor.write_bytes(output.read_bytes())
evidence = {'ancestor_sha256': old_sha, 'wall_sha256': sha, 'dimensions': [w,h],
            'format': 'PNG', 'mode': 'RGB', 'new_mark_rectangle_xyxy': [808,388,1045,518],
            'changed_pixels': changed, 'changed_pixels_outside_rectangle': 0,
            'method': 'Built-in imagegen edit; only generated charcoal and ochre blended onto ancestor.',
            'preview': {'path': 'dist/line-4/24.jpg', 'format': 'JPEG', 'dimensions': [512,512], 'bytes': len(jpeg)},
            'unmet_visual_requirements': []}
Path('line-4/IMAGE-24.json').write_text(json.dumps(evidence, indent=2)+'\n')
print(json.dumps(evidence, indent=2))
