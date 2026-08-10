"""Replace look-anchor 000 from a clean generated up-pose, rebuild strips."""
from pathlib import Path
from PIL import Image

ASSETS = Path(r"C:\Users\lixun\.cursor\projects\c-Users-lixun-Projects-buding-pet\assets")
RUN = Path(r"C:\Users\lixun\Projects\buding-pet\runs\buding")
SRC = ASSETS / "buding-look-000-v5.png"
ANCHORS = RUN / "decoded" / "look-anchors"
REF = ANCHORS / "090.png"  # geometry reference

CELL_W, CELL_H = 192, 208
CHROMA = (0, 0, 255)
THRESH = 96


def is_chroma(rgb: tuple[int, int, int]) -> bool:
    return sum(abs(int(a) - int(b)) for a, b in zip(rgb, CHROMA)) <= THRESH


def extract_rgba(path: Path) -> Image.Image:
    im = Image.open(path).convert("RGBA")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if is_chroma((r, g, b)):
                px[x, y] = (0, 0, 0, 0)
            else:
                px[x, y] = (r, g, b, 255)
    return im


def bbox(im: Image.Image) -> tuple[int, int, int, int]:
    alpha = im.split()[-1]
    return alpha.getbbox()


def fit_cell(im: Image.Image, target_bbox_h: int | None = None) -> Image.Image:
    box = bbox(im)
    if not box:
        raise SystemExit("empty subject")
    crop = im.crop(box)
    cw, ch = crop.size
    # Match roughly the body height used by other anchors (~target usable height)
    max_h = 190
    max_w = 160
    scale = min(max_w / cw, max_h / ch)
    nw, nh = max(1, int(cw * scale)), max(1, int(ch * scale))
    crop = crop.resize((nw, nh), Image.Resampling.LANCZOS)
    cell = Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
    # baseline near bottom like other anchors
    x = (CELL_W - nw) // 2
    y = CELL_H - nh - 5
    cell.paste(crop, (x, y), crop)
    return cell


rgba = extract_rgba(SRC)
cell = fit_cell(rgba)
out000 = ANCHORS / "000.png"
cell.save(out000)
print(f"wrote {out000} size={cell.size} bbox={bbox(cell)}")

# rebuild approved strip via same layout as compose script expects: 4 cells side by side
dirs = ["000", "090", "180", "270"]
cells = [Image.open(ANCHORS / f"{d}.png").convert("RGBA") for d in dirs]
approved = Image.new("RGBA", (CELL_W * 4, CELL_H), (0, 0, 0, 0))
for i, c in enumerate(cells):
    approved.paste(c, (i * CELL_W, 0), c)
approved_path = RUN / "decoded" / "look-anchors-approved.png"
approved.save(approved_path)
print(f"wrote {approved_path}")

# rebuild look-cardinals viewing strip on blue
scale = 3
view = Image.new("RGB", (CELL_W * 4 * scale, CELL_H * scale), CHROMA)
for i, c in enumerate(cells):
    big = c.resize((CELL_W * scale, CELL_H * scale), Image.Resampling.NEAREST)
    # composite onto blue
    layer = Image.new("RGBA", big.size, (*CHROMA, 255))
    layer = Image.alpha_composite(layer, big)
    view.paste(layer.convert("RGB"), (i * CELL_W * scale, 0))
card_path = RUN / "decoded" / "look-cardinals.png"
view.save(card_path)
print(f"wrote {card_path} {view.size}")
