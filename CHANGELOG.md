# Changelog

## v0.1.0a1 — 2026-07-29

Initial alpha release. First `pip install pharos-engine` on PyPI.

### Engine

- Rust workspace with three crates: `pharos_core` (kernels), `pharos_render` (wgpu backend + VCR scaffold), `pharos_py` (PyO3 cdylib exposed as `pharos_engine._core`).
- Headless Python surface: `pharos_engine.Engine()`, `Scene`, `Entity`.
- Physics kernels (Rust): XPBD softbody, PBF fluid, geometry, IK, material_eval.
- 2D CPU raster path via `pharos_engine.layer.Layer` (numpy uint8 RGBA).
- Nova3D VCR bug-fix intake — 6 shipped-code fixes ported (MRT state, HiZ compute seed, RefractComposite guards, transparency rim).
- GPU compute pipeline scaffolds (PBF + softbody WGSL — dispatch chooser in Python).

### Editor (separate wheel: `pip install pharos-editor`)

- Nova3D-parity docked editor via `imgui-bundle` (`DockingParams` + `DockingSplit`).
- Five docked panels: Hierarchy, Properties, Viewport (Rust wgpu blit), Content Browser, Console.
- Multi-select + right-click context menus + Ctrl+Z/Y/C/V/D/Del/F hotkeys.
- Fly camera (RMB orbit / MMB pan / scroll dolly / WASD fly).
- Runtime theme swap across 6 shipped themes.
- Perf HUD (top-right FPS + Ready badge).
- Content Browser with breadcrumb nav + PIL thumbnails + rename/delete/reveal.

### Known gaps

- 3D vertex draw calls (scaffold only clears today; entities render as 2D-projected dots).
- 2D GPU pipeline (numpy raster works CPU-side; wgpu blit path pending).
- glTF import end-to-end.
- Project creation flow (Welcome dialog + template scaffolder — planned for v0.1.0a2).
