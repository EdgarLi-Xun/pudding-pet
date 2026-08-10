"""Extract full pose components from run strips, shrink to safe cells, remirror left."""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw

ASSETS = Path(r"C:\Users\lixun\.cursor\projects\c-Users-lixun-Projects-buding-pet\assets")
RUN = Path(r"C:\Users\lixun\Projects\buding-pet\runs\buding")
CELL_W, CELL_H = 192, 208
CHROMA = (0, 0, 255)
THRESH = 110
MAX_W, MAX_H = 145, 170


def is_fg(rgb: tuple[int, int, int]) -> bool:
    return sum(abs(int(c) - int(k)) for c, k in zip(rgb, CHROMA)) > THRESH


def to_mask(im: Image.Image) -> list[list[bool]]:
    im = im.convert("RGB")
    w, h = im.size
    px = im.load()
    return [[is_fg(px[x, y]) for x in range(w)] for y in range(h)]


def components(mask: list[list[bool]], min_area: int = 800) -> list[tuple[int, int, int, int]]:
    h, w = len(mask), len(mask[0])
    seen = [[False] * w for _ in range(h)]
    boxes: list[tuple[int, int, int, int]] = []
    for y in range(h):
        for x in range(w):
            if not mask[y][x] or seen[y][x]:
                continue
            stack = [(x, y)]
            seen[y][x] = True
            minx = maxx = x
            miny = maxy = y
            area = 0
            while stack:
                cx, cy = stack.pop()
                area += 1
                minx = min(minx, cx)
                maxx = max(maxx, cx)
                miny = min(miny, cy)
                maxy = max(maxy, cy)
                for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                    if 0 <= nx < w and 0 <= ny < h and mask[ny][nx] and not seen[ny][nx]:
                        seen[ny][nx] = True
                        stack.append((nx, ny))
            if area >= min_area:
                boxes.append((minx, miny, maxx + 1, maxy + 1))
    boxes.sort(key=lambda b: b[0])
    return boxes


def chroma_rgba(im: Image.Image) -> Image.Image:
    im = im.convert("RGBA")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if not is_fg((r, g, b)):
                px[x, y] = (0, 0, 0, 0)
            else:
                px[x, y] = (r, g, b, 255)
    return im


def fit_cell(crop: Image.Image) -> Image.Image:
    box = crop.split()[-1].getbbox()
    if not box:
        return Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
    crop = crop.crop(box)
    cw, ch = crop.size
    scale = min(MAX_W / max(cw, 1), MAX_H / max(ch, 1), 1.0)
    nw, nh = max(1, int(cw * scale)), max(1, int(ch * scale))
    crop = crop.resize((nw, nh), Image.Resampling.LANCZOS)
    cell = Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
    cell.paste(crop, ((CELL_W - nw) // 2, CELL_H - nh - 10), crop)
    return cell


def extract_n(path: Path, n: int) -> list[Image.Image]:
    raw = Image.open(path)
    rgba = chroma_rgba(raw)
    boxes = components(to_mask(raw), min_area=1200)
    print(f"{path.name}: found {len(boxes)} components, need {n}")
    if len(boxes) < n:
        # fallback equal slots
        w, h = rgba.size
        slot = w / n
        boxes = [(int(i * slot), 0, int((i + 1) * slot), h) for i in range(n)]
    # if too many, merge nearest until n (take largest n left-to-right clusters)
    if len(boxes) > n:
        # keep n largest by area, then sort by x
        scored = sorted(boxes, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]), reverse=True)[:n]
        boxes = sorted(scored, key=lambda b: b[0])
    cells = []
    for box in boxes[:n]:
        # pad box slightly but stay in image
        x0, y0, x1, y1 = box
        pad = 4
        x0 = max(0, x0 - pad)
        y0 = max(0, y0 - pad)
        x1 = min(rgba.size[0], x1 + pad)
        y1 = min(rgba.size[1], y1 + pad)
        cells.append(fit_cell(rgba.crop((x0, y0, x1, y1))))
    while len(cells) < n:
        cells.append(Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0)))
    return cells[:n]


def write_strip(cells: list[Image.Image], path: Path) -> None:
    strip = Image.new("RGB", (CELL_W * len(cells), CELL_H), CHROMA)
    for i, cell in enumerate(cells):
        bg = Image.new("RGBA", cell.size, (*CHROMA, 255))
        composed = Image.alpha_composite(bg, cell)
        strip.paste(composed.convert("RGB"), (i * CELL_W, 0))
    path.parent.mkdir(parents=True, exist_ok=True)
    strip.save(path)
    print("wrote", path)


def write_frames(cells: list[Image.Image], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, cell in enumerate(cells):
        cell.save(out_dir / f"{i:02d}.png")


right_cells = extract_n(ASSETS / "buding-running-right-v2.png", 8)
left_cells = [c.transpose(Image.Transpose.FLIP_LEFT_RIGHT) for c in right_cells]
work_cells = extract_n(ASSETS / "buding-running-laptop-v2.png", 6)

write_strip(right_cells, RUN / "decoded" / "running-right.png")
write_strip(left_cells, RUN / "decoded" / "running-left.png")
write_strip(work_cells, RUN / "decoded" / "running.png")

for name, cells in (
    ("running-right", right_cells),
    ("running-left", left_cells),
    ("running", work_cells),
):
    write_frames(cells, RUN / "frames" / name)
    write_frames(cells, RUN / "qa" / "rows" / name / "frames" / name)

print("done")
for label, cells in (("R", right_cells), ("L", left_cells), ("W", work_cells)):
    print(label, [c.split()[-1].getbbox() for c in cells])
