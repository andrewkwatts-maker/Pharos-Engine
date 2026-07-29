# Changelog

## v0.0.1a1 — 2026-07-29

Initial alpha release. First `pip install pharos-engine` on PyPI.

Version scheme: `0.0.1a1` — deliberately very early to signal that
even API surfaces may shift before `0.1.0`. Semantic-versioning
stability guarantees kick in at `0.1.0`.

### Engine

- Rust workspace with three crates: `pharos_core` (kernels), `pharos_render` (wgpu backend + VCR scaffold), `pharos_py` (PyO3 cdylib exposed as `pharos_engine._core`).
- Headless Python surface: `pharos_engine.Engine()`, `Scene`, `Entity`.
- Physics kernels (Rust): XPBD softbody, PBF fluid, geometry, IK, material_eval.
- 2D CPU raster path via `pharos_engine.layer.Layer` (numpy uint8 RGBA).
- Nova3D VCR bug-fix intake — 6 shipped-code fixes ported: MRT canonical target set (f0d524b), HiZ mip-0 compute seed (39cc44a), RefractComposite black-sample fallback (3d21abd), caustic-emitter Gaussian 2x/4x (0c0c890), refract() TIR NaN guard (96a23e0), transparent silhouette rim fix (4fe12cb). Regression suite in `crates/pharos_render/tests/regression_intake.rs` locks all six against silent refactor regressions.
- GPU compute pipeline scaffolds (PBF + softbody WGSL — dispatch chooser in Python).

### Editor (separate wheel: `pip install pharos-editor`)

- Nova3D-parity docked editor via `imgui-bundle` (`DockingParams` + `DockingSplit`).
- Five docked panels: Hierarchy, Properties, Viewport (Rust wgpu blit), Content Browser, Console.
- Multi-select + right-click context menus + Ctrl+Z/Y/C/V/D/Del/F hotkeys.
- Fly camera (RMB orbit / MMB pan / scroll dolly / WASD fly).
- Runtime theme swap across 6 shipped themes.
- Perf HUD (top-right FPS + Ready badge).
- Content Browser with breadcrumb nav + PIL thumbnails + rename/delete/reveal.

### Packaging

- Default `engine.yml` shipped inside the wheel at `pharos_engine/_defaults/engine.yml` — `pip install pharos-engine` followed by `Engine()` works with zero project setup.
- `wgpu.gui` imported lazily — `import pharos_engine` succeeds on headless boxes with no display toolkit (glfw / qt) installed.
- `.cargo/config.toml` no longer pins a machine-specific Windows Python path; a fresh Linux/macOS clone can `cargo check --workspace` immediately.

### Known gaps

- 3D vertex draw calls (scaffold only clears today; entities render as 2D-projected dots).
- 2D GPU pipeline (numpy raster works CPU-side; wgpu blit path pending).
- glTF import end-to-end.
- Editor Welcome / project-picker dialog (`pharos new` CLI scaffolder ships and works — planned for v0.0.1a2 to gate the GUI on picking a project).
