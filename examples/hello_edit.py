"""Boot the desktop editor programmatically.

Requires `pip install pharos-editor` (or `pip install pharos-engine[editor]`).

Run:   python examples/hello_edit.py
"""
from __future__ import annotations


def main() -> None:
    try:
        from pharos_editor.ui.editor_v2.shell import run
    except ImportError as exc:
        raise SystemExit(
            "pharos-editor is not installed. Install with:\n"
            "  pip install pharos-editor\n"
            f"(original error: {exc})"
        ) from exc
    run()


if __name__ == "__main__":
    main()
