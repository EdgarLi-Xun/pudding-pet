"""Shrink run-cycle frames to fit safely inside 192x208 cells, then remirror left."""
from __future__ import annotations

from pathlib import Path
from PIL import Image

RUN = Path(r"C:\Users\lixun\Projects\buding-pet\runs\buding")
CELL_W, CELL_H = 192, 208
CHROMA = (0, 0, 255)
THRESH = 110
MAX_W, MAX_H = 150, 175


def chroma_to_alpha(im: Image.Image) -> Image.Image:
    im = im.convert("RGBA")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if sum(abs(int(c) - int(k)) for c, k in zip((r, g, b), CHROMA)) <= THRESH:
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
    scale = min(MAX_W / cw, MAX_H / ch, 1.0)
    nw, nh = max(1, int(cw * scale)), max(1, int(ch * scale))
    crop = crop.resize((nw, nh), Image.Resampling.LANCZOS)
    cell = Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
    x = (CELL_W - nw) // 2
    y = CELL_H - nh - 8
    cell.paste(crop, (x, y), crop)
    return cell


def strip_to_cells(path: Path, n: int) -> list[Image.Image]:
    raw = Image.open(path).convert("RGBA")
    rgba = chroma_to_alpha(raw)
    w, h = rgba.size
    slot = w / n
    cells = []
    for i in range(n):
        x0 = int(round(i * slot))
        x1 = int(round((i + 1) * slot))
        cells.append(fit_cell(rgba.crop((x0, 0, x1, h))))
    return cells


def write_strip(cells: list[Image.Image], path: Path) -> None:
    strip = Image.new("RGB", (CELL_W * len(cells), CELL_H), CHROMA)
    for i, cell in enumerate(cells):
        bg = Image.new("RGBA", cell.size, (*CHROMA, 255))
        composed = Image.alpha_composite(bg, cell)
        strip.paste(composed.convert("RGB"), (i * CELL_W, 0))
    path.parent.mkdir(parents=True, exist_ok=True)
    strip.save(path)


def write_frames(cells: list[Image.Image], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, cell in enumerate(cells):
        cell.save(out_dir / f"{i:02d}.png")


right_src = RUN / "decoded" / "running-right.png"
left_src = RUN / "decoded" / "running-left.png"

right_cells = strip_to_cells(right_src, 8)
# Remirror each fitted cell for leftward travel, preserving order
left_cells = [c.transpose(Image.Transpose.FLIP_LEFT_RIGHT) for c in right_cells]

write_strip(right_cells, right_src)
write_strip(left_cells, left_src)
write_frames(right_cells, RUN / "frames" / "running-right")
write_frames(left_cells, RUN / "frames" / "running-left")
write_frames(right_cells, RUN / "qa" / "rows" / "running-right" / "frames" / "running-right")
write_frames(left_cells, RUN / "qa" / "rows" / "running-left" / "frames" / "running-left")

# Also shrink working/running laptop row into safe cells
work_src = RUN / "decoded" / "running.png"
work_cells = strip_to_cells(work_src, 6)
write_strip(work_cells, work_src)
write_frames(work_cells, RUN / "frames" / "running")
write_frames(work_cells, RUN / "qa" / "rows" / "running" / "frames" / "running")

print("fitted running-right/left (8) and running/work (6)")
for label, cells in (("right", right_cells), ("left", left_cells), ("work", work_cells)):
    boxes = [c.split()[-1].getbbox() for c in cells]
    print(label, boxes)
