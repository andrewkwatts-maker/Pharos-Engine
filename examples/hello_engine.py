"""Headless smoke: import Pharos, spawn an entity, tick the engine.

Run:   python examples/hello_engine.py
"""
from __future__ import annotations

import pharos_engine as ph


def main() -> None:
    print(f"pharos_engine v{ph.__version__}")
    print(f"native _core loaded: {ph.HAS_NATIVE}")

    engine = ph.Engine()
    scene = engine.scene

    for i in range(3):
        scene.add_entity(ph.Entity(name=f"cube_{i}", position=(float(i), 0.0)))

    print(f"scene has {len(scene.entities)} entities")
    for e in scene.entities:
        print(f"  - {e.name} @ {e.position}")

    for step in range(10):
        engine.tick(1.0 / 60.0)
    print("ticked 10 frames headlessly — OK")


if __name__ == "__main__":
    main()
