# PharosEngine

**A Rust + wgpu game engine with a Python authoring surface.** Runs headless from `pip install pharos-engine`; add the optional imgui-bundle editor with `pip install pharos-editor`.

```
pip install pharos-engine
```

```python
import pharos_engine as ph

engine = ph.Engine()
scene = engine.scene
scene.add_entity(ph.Entity(name="player", position=(0.0, 0.0)))

# Ticks the sim + advances renderer state. Engine works headless —
# no window, no GPU init required.
engine.tick(1.0 / 60.0)
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

## Status: alpha (v0.1.0a1)

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
