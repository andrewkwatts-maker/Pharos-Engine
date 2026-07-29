"""Theme bridge — one YAML source of truth for v1 (DPG) + v2 (imgui-bundle).

The notebook themes at :mod:`pharos_editor.themes` (teengirl_notebook,
colorblind_safe, legacy_glass, dark_studio, pastel_soft, high_contrast,
nova_dark) declare colour palettes + geometry knobs. v1 reads them via
its own DPG bridge; this module gives v2 the equivalent path so a
user's picked theme applies to BOTH editors identically.

Contract:
- v2 calls :func:`apply_theme_to_imgui(theme_name)` once per frame
  (or whenever the active theme changes).
- The bridge pushes `imgui.style_color` slots + tweaks `imgui.style`
  fields (rounding, padding, spacing) to match the theme YAML.
- Extended theme knobs (washi-tape overlays, page-lining density,
  edge-stroke widths) are read by future v2 draw callbacks and
  overlaid as `imgui.get_window_draw_list()` primitives — v1 already
  does this via DPG drawlists, same idea.

Non-goals for this file: rendering the washi-tape decorations. That
lives in a separate module (`decor_overlay.py`) that Sprint 2+ wires
into each panel's `gui_function`.
"""
from __future__ import annotations

from typing import Any

from imgui_bundle import imgui


def _rgba_norm(rgba: list[int] | tuple[int, ...]) -> tuple[float, float, float, float]:
    """Convert theme YAML `[r, g, b, a]` 0-255 to `imgui.ImVec4`-compatible floats."""
    if not rgba:
        return (1.0, 1.0, 1.0, 1.0)
    if len(rgba) == 3:
        r, g, b = rgba
        a = 255
    else:
        r, g, b, a = rgba[0], rgba[1], rgba[2], rgba[3]
    return (r / 255.0, g / 255.0, b / 255.0, a / 255.0)


def _lookup(palette: dict[str, Any], name: str, fallback: tuple[int, ...]) -> tuple[float, float, float, float]:
    if name in palette:
        return _rgba_norm(palette[name])
    return _rgba_norm(list(fallback))


def apply_theme_to_imgui(theme_name: str | None = None) -> None:
    """Push the active theme's palette into imgui's style + colour table.

    Idempotent: safe to call every frame. Callers should invoke once at
    startup and again whenever the user swaps themes via the future
    Sprint 8 theme picker.

    Parameters
    ----------
    theme_name:
        Name of a theme file under `python/pharos_editor/themes/*.yaml`.
        When ``None``, uses :class:`ThemeCatalog.default`.
    """
    try:
        from pharos_editor.themes import ThemeCatalog
    except Exception:
        return  # theme catalog unavailable — leave imgui defaults

    try:
        catalog = ThemeCatalog()
        theme = catalog.get(theme_name) if theme_name else catalog.default()
    except Exception:
        return

    palette = theme.palette
    geometry = theme.geometry

    # ── Colours ──────────────────────────────────────────────────────
    style = imgui.get_style()

    bg      = _lookup(palette, "bg",             (30, 30, 34, 255))
    bg_alt  = _lookup(palette, "bg_alt",         (40, 40, 45, 255))
    panel_bg = _lookup(palette, "panel_bg",      (45, 45, 50, 250))
    panel_bd = _lookup(palette, "panel_border",  (80, 80, 88, 255))
    text     = _lookup(palette, "text",          (235, 235, 240, 255))
    text_sec = _lookup(palette, "text_secondary", (180, 180, 190, 255))
    text_dis = _lookup(palette, "text_disabled", (110, 110, 120, 255))
    accent   = _lookup(palette, "accent_pink",   (204, 121, 167, 255))
    accent_a = _lookup(palette, "accent_teal",   (86, 180, 233, 255))
    ok       = _lookup(palette, "ok",            (0, 158, 115, 255))
    warn     = _lookup(palette, "warn",          (230, 159, 0, 255))
    error    = _lookup(palette, "error",         (213, 94, 0, 255))
    sel_bg   = _lookup(palette, "selection_bg",  (86, 180, 233, 180))
    sel_edge = _lookup(palette, "selection_edge", (230, 159, 0, 255))

    # imgui-bundle 1.92 replaced `style.colors[i] = ImVec4(...)` with
    # `style.set_color_(i, ImVec4(...))`. Same underlying array, wrapped
    # accessor so the C++ Style struct stays layout-frozen for pybind.
    def _set(idx, r, g, b, a):
        style.set_color_(idx, imgui.ImVec4(r, g, b, a))

    _set(imgui.Col_.text.value,                *text)
    _set(imgui.Col_.text_disabled.value,       *text_dis)
    _set(imgui.Col_.window_bg.value,           *panel_bg)
    _set(imgui.Col_.child_bg.value,            *bg)
    _set(imgui.Col_.popup_bg.value,            *bg_alt)
    _set(imgui.Col_.border.value,              *panel_bd)
    _set(imgui.Col_.frame_bg.value,            *bg_alt)
    _set(imgui.Col_.frame_bg_hovered.value,    accent_a[0], accent_a[1], accent_a[2], 0.35)
    _set(imgui.Col_.frame_bg_active.value,     accent_a[0], accent_a[1], accent_a[2], 0.55)
    _set(imgui.Col_.title_bg.value,            *bg_alt)
    _set(imgui.Col_.title_bg_active.value,     *panel_bg)
    _set(imgui.Col_.title_bg_collapsed.value,  *bg)
    _set(imgui.Col_.menu_bar_bg.value,         *bg_alt)
    _set(imgui.Col_.scrollbar_bg.value,        *bg)
    _set(imgui.Col_.scrollbar_grab.value,      *panel_bd)
    _set(imgui.Col_.check_mark.value,          *accent)
    _set(imgui.Col_.slider_grab.value,         *accent)
    _set(imgui.Col_.slider_grab_active.value,  *accent_a)
    _set(imgui.Col_.button.value,              accent[0], accent[1], accent[2], 0.55)
    _set(imgui.Col_.button_hovered.value,      accent[0], accent[1], accent[2], 0.80)
    _set(imgui.Col_.button_active.value,       *accent)
    _set(imgui.Col_.header.value,              accent[0], accent[1], accent[2], 0.30)
    _set(imgui.Col_.header_hovered.value,      accent[0], accent[1], accent[2], 0.55)
    _set(imgui.Col_.header_active.value,       *accent)
    _set(imgui.Col_.separator.value,           *panel_bd)
    _set(imgui.Col_.tab.value,                 *bg_alt)
    _set(imgui.Col_.tab_hovered.value,         accent[0], accent[1], accent[2], 0.60)
    _set(imgui.Col_.tab_selected.value,        *panel_bg)
    _set(imgui.Col_.tab_dimmed.value,          *bg)
    _set(imgui.Col_.docking_preview.value,     accent_a[0], accent_a[1], accent_a[2], 0.55)
    _set(imgui.Col_.text_selected_bg.value,    *sel_bg)
    _set(imgui.Col_.plot_lines.value,          *accent_a)
    _set(imgui.Col_.nav_cursor.value,          *sel_edge)

    # ── Geometry ─────────────────────────────────────────────────────
    style.window_rounding = float(geometry.get("window_rounding", 6))
    style.frame_rounding = float(geometry.get("frame_rounding", 4))
    style.child_rounding = float(geometry.get("child_rounding", 4))
    style.window_border_size = float(geometry.get("border_size", 1))
    style.frame_border_size = 0.0
    style.window_padding = imgui.ImVec2(
        float(geometry.get("padding_x", 10)),
        float(geometry.get("padding_y", 8)),
    )
    style.item_spacing = imgui.ImVec2(
        float(geometry.get("spacing_x", 6)),
        float(geometry.get("spacing_y", 4)),
    )


def theme_accent(theme_name: str | None = None) -> imgui.ImVec4:
    """Convenience: return the active theme's accent colour as an ImVec4.

    Used by v2 panels that want a themed highlight without repeating the
    palette lookup — e.g. `imgui.text_colored(theme_accent(), "...")`.
    """
    try:
        from pharos_editor.themes import ThemeCatalog

        catalog = ThemeCatalog()
        theme = catalog.get(theme_name) if theme_name else catalog.default()
        return imgui.ImVec4(*_lookup(theme.palette, "accent_pink", (204, 121, 167, 255)))
    except Exception:
        return imgui.ImVec4(0.80, 0.47, 0.65, 1.0)
