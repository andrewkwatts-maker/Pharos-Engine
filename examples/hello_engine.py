"""Headless smoke: import Pharos, spawn some entities, tick.

Run:   python examples/hello_engine.py
"""
from __future__ import annotations

import pharos_engine as ph


def main() -> None:
    print(f"pharos_engine v{ph.__version__}")
    print(f"native _core loaded: {ph.HAS_NATIVE}")

    engine = ph.Engine()

    # Engine starts scene-less; construct one and attach.
    scene = ph.Scene()
    engine.load_scene(scene)

    for i in range(3):
        scene.add(ph.Entity(name=f"cube_{i}", position=(float(i), 0.0)))

    print(f"scene has {len(scene.entities)} entities")
    for e in scene.entities:
        print(f"  - {e.name} @ {e.position}")

    # Tick each entity for a few frames headlessly. The full
    # Engine.run() loop needs a GPU + window; this stepping form
    # exercises the entity-side simulation in isolation.
    dt = 1.0 / 60.0
    for _ in range(10):
        for entity in scene.entities:
            entity.tick(dt)
    print("ticked 10 frames headlessly - OK")


if __name__ == "__main__":
    main()
