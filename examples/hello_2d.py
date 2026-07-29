"""Minimal 2D CPU raster demo — writes a checkerboard PNG.

Uses the numpy-backed Layer API; no GPU init required. Confirms the
2D CPU path is working before adding a GPU pipeline in v0.1.0a2.

Run:   python examples/hello_2d.py
"""
from __future__ import annotations

import numpy as np
from PIL import Image


def make_checkerboard(width: int = 256, height: int = 256, tile: int = 32) -> np.ndarray:
    """Return an (H, W, 4) uint8 RGBA checkerboard as a numpy layer."""
    layer = np.zeros((height, width, 4), dtype=np.uint8)
    for y in range(height):
        for x in range(width):
            if ((x // tile) + (y // tile)) % 2 == 0:
                layer[y, x] = (220, 90, 130, 255)     # pink
            else:
                layer[y, x] = (60, 65, 80, 255)       # slate
    return layer


def main() -> None:
    layer = make_checkerboard()
    Image.fromarray(layer, mode="RGBA").save("hello_2d.png")
    print("Wrote hello_2d.png (256x256 checkerboard).")


if __name__ == "__main__":
    main()
