# PharosEngine

[![PyPI](https://img.shields.io/pypi/v/pharos-engine.svg)](https://pypi.org/project/pharos-engine/)
[![Python](https://img.shields.io/pypi/pyversions/pharos-engine.svg)](https://pypi.org/project/pharos-engine/)
[![Licence: MIT](https://img.shields.io/badge/licence-MIT-blue.svg)](LICENSE)
[![CI](https://github.com/andrewkwatts-maker/Pharos/actions/workflows/ci.yml/badge.svg)](https://github.com/andrewkwatts-maker/Pharos/actions/workflows/ci.yml)

**A Rust + wgpu game engine with a Python authoring surface.** Runs headless from `pip install pharos-engine`; add the optional imgui-bundle editor with `pip install pharos-editor`.

```
pip install pharos-engine
```

```python
import pharos_engine as ph

engine = ph.Engine()
scene = ph.Scene()
engine.load_scene(scene)
scene.add(ph.Entity(name="player", position=(0.0, 0.0)))

# The engine works headless — no window, no GPU init required.
# For a live tick loop, iterate the entities:
for _ in range(60):
    dt = 1.0 / 60.0
    for entity in scene.entities:
        entity.tick(dt)
```

## Optional desktop editor

```
pip install pharos-editor       # or:  pip install pharos-engine[editor]
pharos-edit                     # boots a Nova3D-parity docked editor
```

## Architecture

| Layer | Language | Contents |
|-------|----------|----------|
| Core simulation | **Rust** | `pharos_core` — physics, fluid (PBF), softbody (XPBD), geometry, IK |
| Renderer | **Rust + wgpu** (→ Vulkan / D3D12 / Metal) | `pharos_render` — VCR pipeline, CSM shadows, skinning, GPU compute |
| Python bindings | **Rust cdylib (PyO3)** | `pharos_py` — the `_core` extension module |
| Engine API | **Python** | `pharos_engine` — thin authoring surface |
| Desktop editor | **Python + imgui-bundle** | `pharos_editor` — separate optional wheel |

Python is a *wrapper*, not a runtime. Every hot path is Rust.

## Status: alpha (v0.0.1a1)

- ✅ Rust simulation kernels (physics / fluid / softbody)
- ✅ wgpu render backend (VCR pipeline scaffold, CSM, skinning)
- ✅ Python engine surface (`Engine`, `Scene`, `Entity`)
- ✅ 2D CPU raster path
- ✅ imgui-bundle Nova3D-parity editor (dockable panels, camera, hotkeys, undo/redo)
- 🚧 2D GPU pipeline (numpy → wgpu texture blit) — in progress
- 🚧 3D scene draw calls (renderer scaffold only clears today)
- 🚧 glTF import wiring end-to-end

See [`CHANGELOG.md`](CHANGELOG.md) for the alpha changelog.

## Licence

MIT.
