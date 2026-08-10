"""Fix unnatural red/magenta ear artifact on look-anchor 000."""
from pathlib import Path
from PIL import Image

src = Path(r"C:\Users\lixun\Projects\buding-pet\runs\buding\decoded\look-anchors\000.png")
backup = src.with_name("000-before-ear-fix.png")
original = Image.open(src).convert("RGBA")
original.save(backup)
img = original.copy()
px = img.load()
w, h = img.size

# Sample natural tan from viewer-left upper ear region
samples = []
for y in range(int(h * 0.08), int(h * 0.42)):
    for x in range(int(w * 0.20), int(w * 0.48)):
        r, g, b, a = px[x, y]
        if a < 200:
            continue
        if r > 120 and g > 90 and b < g + 20 and r < g + 80:
            samples.append((r, g, b))

if not samples:
    raise SystemExit("no tan samples found")

sr = sum(c[0] for c in samples) / len(samples)
sg = sum(c[1] for c in samples) / len(samples)
sb = sum(c[2] for c in samples) / len(samples)

mask_count = 0
for y in range(int(h * 0.02), int(h * 0.48)):
    for x in range(int(w * 0.48), int(w * 0.92)):
        r, g, b, a = px[x, y]
        if a < 8:
            continue
        red_dom = (r > g + 28) and (r > b + 28) and (r > 140)
        magentaish = (r > 160) and (b > g + 15) and (r > g + 20)
        if not (red_dom or magentaish):
            continue
        lum = 0.299 * r + 0.587 * g + 0.114 * b
        target_lum = 0.299 * sr + 0.587 * sg + 0.114 * sb
        scale = max(0.7, min(1.25, lum / max(target_lum, 1e-3)))
        nr, ng, nb = sr * scale, sg * scale, sb * scale
        excess = r - max(g, b)
        blend = max(0.35, min(0.95, (excess - 10) / 60.0))
        px[x, y] = (
            int((1 - blend) * r + blend * nr),
            int((1 - blend) * g + blend * ng),
            int((1 - blend) * b + blend * nb),
            a,
        )
        mask_count += 1

img.save(src)
print(f"mask_pixels={mask_count} samples={len(samples)} tan=({sr:.1f},{sg:.1f},{sb:.1f})")
print(f"wrote {src}")
print(f"backup {backup}")
