"""Turn the 10 reference logos (raster, on white / grey / checkerboard) into trimmed RGBA cutouts.
Colours and proportions are untouched; only the background is removed."""
import sys, numpy as np
from PIL import Image
src, dst = sys.argv[1], sys.argv[2]

def save(rgb, a, name, pad=0.04):
    a = np.clip(a, 0, 1)
    ys, xs = np.where(a > 0.04)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    out = np.dstack([np.clip(rgb, 0, 255), a * 255]).astype(np.uint8)[y0:y1, x0:x1]
    im = Image.fromarray(out, 'RGBA')
    p = int(max(im.size) * pad)
    canvas = Image.new('RGBA', (im.width + 2 * p, im.height + 2 * p), (0, 0, 0, 0))
    canvas.paste(im, (p, p)); canvas.save(f'{dst}/{name}.png'); print(name, canvas.size)

def by_distance(arr, bg, lo=10, hi=70):
    d = np.sqrt(((arr - bg) ** 2).sum(-1))
    a = np.clip((d - lo) / (hi - lo), 0, 1)
    safe = np.maximum(a, 1e-3)[..., None]
    rgb = bg + (arr - bg) / safe           # un-premultiply against the old background
    return rgb, a

def by_chroma(arr, lo=18, hi=70):
    ch = arr.max(-1) - arr.min(-1)
    return arr, np.clip((ch - lo) / (hi - lo), 0, 1)

L = lambda i: np.asarray(Image.open(f'{src}/img-{i:03d}.png').convert('RGB')).astype(float)

# 1 Anthropic: cream spark on its orange tile -> keep spark, tile is redrawn in the same orange
a = L(0); save(*by_distance(a, np.array([218, 119, 88.]), 20, 90), 'anthropic')
save(*by_chroma(L(1)), 'google')
save(*by_distance(L(2), np.array([242, 242, 242.])), 'meta')
save(*by_distance(L(3), np.array([255, 255, 255.])), 'nvidia')
save(*by_chroma(L(4), 25, 80), 'microsoft')
save(*by_distance(L(5), np.array([255, 255, 255.])), 'openai')
save(*by_distance(L(6), np.array([255, 255, 255.])), 'ibm')
for i, name in ((7, 'aws'), (8, 'deeplearningai')):   # these crops carry dark frame lines: drop the frame
    arr = L(i)
    rgb, al = by_distance(arr, np.array([255, 255, 255.]))
    # these crops carry dark frame lines: erase any row/column that is mostly dark (+ a few px around it)
    dark = arr.sum(-1) < 330
    for idx in np.where(dark.mean(0) > 0.6)[0]: al[:, max(0, idx - 4):idx + 5] = 0
    for idx in np.where(dark.mean(1) > 0.6)[0]: al[max(0, idx - 4):idx + 5, :] = 0
    save(rgb, al, name)
hf = L(9); hfa = np.asarray(Image.open(f'{src}/img-010.png')).astype(float) / 255
save(hf, hfa, 'huggingface')
