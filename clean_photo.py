"""
Cleans up a source photo so it converts well to ASCII art.

Steps:
  1. Remove the background (rembg) so only the subject remains.
  2. Even out lighting with CLAHE (adaptive histogram equalization).
  3. Composite onto a plain white canvas so the background falls at the
     light end of the character ramp instead of the dark end.

Usage:
    python tools/clean_photo.py my-photo.jpg
    # writes assets/photo-ready.png
"""

import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove

OUTPUT_PATH = Path("assets/photo-ready.png")


def remove_background(input_path: Path) -> Image.Image:
    with open(input_path, "rb") as f:
        input_bytes = f.read()
    output_bytes = remove(input_bytes)
    img = Image.open(__import__("io").BytesIO(output_bytes)).convert("RGBA")
    return img


def equalize_lighting(img: Image.Image) -> Image.Image:
    rgb = np.array(img.convert("RGB"))
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l_channel = clahe.apply(l_channel)

    lab = cv2.merge((l_channel, a_channel, b_channel))
    equalized_rgb = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

    equalized = Image.fromarray(equalized_rgb).convert("RGBA")
    equalized.putalpha(img.getchannel("A"))
    return equalized


def composite_on_white(img: Image.Image) -> Image.Image:
    canvas = Image.new("RGB", img.size, (255, 255, 255))
    canvas.paste(img, mask=img.getchannel("A"))
    return canvas


def main():
    if len(sys.argv) != 2:
        print("Usage: python tools/clean_photo.py <path-to-photo>")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"File not found: {input_path}")
        sys.exit(1)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    print("Removing background...")
    no_bg = remove_background(input_path)

    print("Equalizing lighting...")
    equalized = equalize_lighting(no_bg)

    print("Compositing on white canvas...")
    final = composite_on_white(equalized)

    final.save(OUTPUT_PATH)
    print(f"Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
