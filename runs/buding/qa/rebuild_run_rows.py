"""Build clean running-right/left cells from v3 strip and rebuild atlas package."""
from __future__ import annotations

from pathlib import Path
from PIL import Image

ASSETS = Path(r"C:\Users\lixun\.cursor\projects\c-Users-lixun-Projects-buding-pet\assets")
RUN = Path(r"C:\Users\lixun\Projects\buding-pet\runs\buding")
PET = Path(r"C:\Users\lixun\.codex\pets\buding-fixed")
SKILL = Path(r"C:\Users\lixun\.codex\skills\hatch-pet\scripts")

CELL_W, CELL_H = 192, 208
CHROMA = (0, 0, 255)
THRESH = 110
MAX_W, MAX_H = 145, 170


def is_fg(rgb: tuple[int, int, int]) -> bool:
    return sum(abs(int(c) - int(k)) for c, k in zip(rgb, CHROMA)) > THRESH


def chroma_rgba(im: Image.Image) -> Image.Image:
    im = im.convert("RGBA")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            px[x, y] = (0, 0, 0, 0) if not is_fg((r, g, b)) else (r, g, b, 255)
    return im


def extract_boxes(im: Image.Image, min_area: int = 1500):
    rgb = im.convert("RGB")
    px = rgb.load()
    w, h = rgb.size
    seen = [[False] * w for _ in range(h)]
    boxes = []
    for y in range(h):
        for x in range(w):
            if seen[y][x] or not is_fg(px[x, y]):
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
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx] and is_fg(px[nx, ny]):
                        seen[ny][nx] = True
                        stack.append((nx, ny))
            if area >= min_area:
                boxes.append((minx, miny, maxx + 1, maxy + 1))
    boxes.sort(key=lambda b: b[0])
    return boxes


def clean_small(cell: Image.Image, max_noise: int = 80) -> Image.Image:
    px = cell.load()
    w, h = cell.size
    seen = [[False] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if seen[y][x] or cell.getpixel((x, y))[3] < 8:
                continue
            stack = [(x, y)]
            seen[y][x] = True
            pts = [(x, y)]
            while stack:
                cx, cy = stack.pop()
                for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx] and cell.getpixel((nx, ny))[3] >= 8:
                        seen[ny][nx] = True
                        stack.append((nx, ny))
                        pts.append((nx, ny))
            if len(pts) <= max_noise:
                for nx, ny in pts:
                    px[nx, ny] = (0, 0, 0, 0)
    return cell


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
    return clean_small(cell)


def extract_n(path: Path, n: int):
    raw = Image.open(path)
    rgba = chroma_rgba(raw)
    boxes = extract_boxes(raw, min_area=1500)
    print(f"{path.name}: {len(boxes)} components")
    if len(boxes) > n:
        boxes = sorted(
            sorted(boxes, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]), reverse=True)[:n],
            key=lambda b: b[0],
        )
    if len(boxes) < n:
        w, h = rgba.size
        slot = w / n
        boxes = [(int(i * slot), 0, int((i + 1) * slot), h) for i in range(n)]
    cells = []
    for x0, y0, x1, y1 in boxes[:n]:
        pad = 6
        x0 = max(0, x0 - pad)
        y0 = max(0, y0 - pad)
        x1 = min(rgba.size[0], x1 + pad)
        y1 = min(rgba.size[1], y1 + pad)
        cells.append(fit_cell(rgba.crop((x0, y0, x1, y1))))
    while len(cells) < n:
        cells.append(Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0)))
    return cells[:n]


def write_strip(cells, path: Path):
    strip = Image.new("RGB", (CELL_W * len(cells), CELL_H), CHROMA)
    for i, c in enumerate(cells):
        bg = Image.new("RGBA", c.size, (*CHROMA, 255))
        strip.paste(Image.alpha_composite(bg, c).convert("RGB"), (i * CELL_W, 0))
    path.parent.mkdir(parents=True, exist_ok=True)
    strip.save(path)
    print("wrote", path)


def write_frames(cells, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    for i, c in enumerate(cells):
        c.save(out / f"{i:02d}.png")


right = extract_n(ASSETS / "buding-running-right-v3.png", 8)
left = [c.transpose(Image.Transpose.FLIP_LEFT_RIGHT) for c in right]
write_strip(right, RUN / "decoded" / "running-right.png")
write_strip(left, RUN / "decoded" / "running-left.png")
write_frames(right, RUN / "frames" / "running-right")
write_frames(left, RUN / "frames" / "running-left")
print("R", [c.split()[-1].getbbox() for c in right])
print("L", [c.split()[-1].getbbox() for c in left])
