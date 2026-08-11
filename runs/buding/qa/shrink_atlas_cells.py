"""Uniformly shrink all non-empty atlas cells, keep bottom baseline."""
from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image

CW, CH = 192, 208
COLS, ROWS = 8, 11
SCALE = 0.55
BOTTOM_PAD = 18
SIDE_MIN = 24

RUN = Path(r"C:\Users\lixun\Projects\buding-pet\runs\buding")
PET_DIR = Path(r"C:\Users\lixun\.codex\pets\buding")
PKG = Path(r"C:\Users\lixun\Projects\buding-pet\package\buding")


def shrink(sheet: Image.Image) -> Image.Image:
    out = Image.new("RGBA", sheet.size, (0, 0, 0, 0))
    for r in range(ROWS):
        for c in range(COLS):
            x0, y0 = c * CW, r * CH
            cell = sheet.crop((x0, y0, x0 + CW, y0 + CH))
            bbox = cell.split()[-1].getbbox()
            if not bbox:
                continue
            crop = cell.crop(bbox)
            cw, ch = crop.size
            nw = max(1, int(round(cw * SCALE)))
            nh = max(1, int(round(ch * SCALE)))
            max_w = CW - 2 * SIDE_MIN
            max_h = CH - BOTTOM_PAD - SIDE_MIN
            fit = min(1.0, max_w / nw, max_h / nh)
            if fit < 1.0:
                nw = max(1, int(round(nw * fit)))
                nh = max(1, int(round(nh * fit)))
            resized = crop.resize((nw, nh), Image.Resampling.LANCZOS)
            new_cell = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
            px = (CW - nw) // 2
            py = max(SIDE_MIN, CH - nh - BOTTOM_PAD)
            new_cell.paste(resized, (px, py), resized)
            out.paste(new_cell, (x0, y0), new_cell)
    return out


def main() -> None:
    src = RUN / "final" / "spritesheet-extended.before-shrink.webp"
    backup = RUN / "final" / "spritesheet-extended.before-shrink.webp"
    out_png = RUN / "final" / "spritesheet-extended.png"
    out_webp = RUN / "final" / "spritesheet-extended.webp"
    sheet = Image.open(src).convert("RGBA")
    assert sheet.size == (CW * COLS, CH * ROWS)
    if not backup.exists():
        shutil.copy2(src, backup)
    out = shrink(sheet)
    out.save(out_png)
    out.save(out_webp, "WEBP", lossless=True)
    shutil.copy2(out_webp, PET_DIR / "spritesheet.webp")
    shutil.copy2(out_webp, PKG / "spritesheet.webp")
    print("ok", out_webp)


if __name__ == "__main__":
    main()
