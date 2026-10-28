"""Prep a photo for ASCII conversion.

Removes the background, crops to the subject, boosts local contrast (CLAHE)
and saves a grayscale image plus an alpha mask. Run once per photo:

    python scripts/prep_photo.py assets/source-photo.jpg
"""

import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove

ROOT = Path(__file__).resolve().parent.parent
OUT_GRAY = ROOT / "assets" / "source-prepped.png"
OUT_MASK = ROOT / "assets" / "source-mask.png"
PAD = 0.04  # padding around the subject bbox, as a fraction of its size


def main(src: str) -> None:
    rgba = np.array(remove(Image.open(src).convert("RGB")))
    alpha = rgba[:, :, 3]

    ys, xs = np.where(alpha > 32)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    py, px = int((y1 - y0) * PAD), int((x1 - x0) * PAD)
    y0, x0 = max(0, y0 - py), max(0, x0 - px)
    y1, x1 = min(alpha.shape[0], y1 + py), min(alpha.shape[1], x1 + px)
    rgba = rgba[y0:y1, x0:x1]
    alpha = rgba[:, :, 3]

    # CLAHE on lightness gives a flat-lit face real highlights and shadows
    lab = cv2.cvtColor(rgba[:, :, :3], cv2.COLOR_RGB2LAB)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    lab[:, :, 0] = clahe.apply(lab[:, :, 0])
    gray = cv2.cvtColor(cv2.cvtColor(lab, cv2.COLOR_LAB2RGB), cv2.COLOR_RGB2GRAY)

    # composite on white so the background lands on the blank end of the ramp
    a = alpha.astype(np.float32) / 255.0
    gray = (gray.astype(np.float32) * a + 255.0 * (1 - a)).astype(np.uint8)

    Image.fromarray(gray).save(OUT_GRAY)
    Image.fromarray(alpha).save(OUT_MASK)
    print(f"wrote {OUT_GRAY.relative_to(ROOT)} and {OUT_MASK.relative_to(ROOT)} ({gray.shape[1]}x{gray.shape[0]})")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "assets" / "source-photo.jpg"))
