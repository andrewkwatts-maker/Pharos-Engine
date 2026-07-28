# PharosEditor

Desktop editor for [PharosEngine](https://pypi.org/project/pharos-engine/).

```
pip install pharos-editor      # pulls pharos-engine transitively
pharos-edit                    # boots the Nova3D-parity docked editor
```

## What ships

- Nova3D-parity docked layout via `imgui-bundle` (`DockingParams` + `DockingSplit`).
- Five panels: Hierarchy / Properties / Viewport (Rust wgpu blit) / Content Browser / Console.
- Fly camera (RMB orbit / MMB pan / scroll dolly / RMB+WASD/QE fly).
- Multi-select (Ctrl / Shift click), right-click context menus.
- Undo / redo command stack (Ctrl+Z / Ctrl+Shift+Z), Ctrl+C / Ctrl+V clipboard, Ctrl+D duplicate, Del, F frame-selection.
- Runtime theme swap across six shipped themes.
- Perf HUD (top-right FPS + Ready badge).
- Content Browser with breadcrumb navigation + thumbnail grid + rename modal.
- Console panel wired to `pharos_engine.telemetry`.

## Architecture note

**Python is a UI wrapper only.** The wgpu render backend runs entirely in Rust (`pharos_render` crate); Python receives RGBA pixels through PyO3 and hands them to imgui's texture-blit path. Zero Python-side wgpu imports.

## Status

Alpha. See the [main repo CHANGELOG](https://github.com/andrewkwatts-maker/Pharos/blob/master/CHANGELOG.md).

## Licence

MIT.
