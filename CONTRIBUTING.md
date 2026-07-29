# Contributing to Pharos-Engine

Short version:

1. Fork the repo.
2. Make your change.
3. Verify locally:

   ```
   cargo test --workspace
   python scripts/import_lint.py
   python scripts/build_wheel.py     # builds + installs the wheel
   ```

4. Open a pull request.

## Ground rules

- **Rust owns the hot path.** Physics, rendering, GPU compute all live in `crates/`. Python is a thin wrapper on top of the PyO3 bindings in `pharos_engine._core`.
- **Editor lives in its own repo.** UI / imgui / theming work belongs at [andrewkwatts-maker/Pharos-Editor](https://github.com/andrewkwatts-maker/Pharos-Editor). `pharos_engine` must never import `pharos_editor` at top level.
- **Never skip hooks** (`--no-verify`) or force-push. Never touch git config.
- **New commit, not amend.** Amending pushed commits rewrites history.

## Filing issues

Include: OS, Python version, `pharos_engine.__version__`, `HAS_NATIVE`, and a minimal repro. GPU issues: `wgpu-info` output helps.

## Licence

By contributing you agree your changes ship under the [MIT licence](LICENSE).
