"""
Drag-and-drop support for progression grid cells.

Uses mouse tracking to create a "ghost cell" overlay during drag.
On drop, presents Insert / Replace / Swap options.
"""

from typing import Optional

import dearpygui.dearpygui as dpg

from klo_chords.state import (
    _prog_cells, PROG_CELLS_TOTAL, PROG_COLS,
    _prog_selected_idx,
    _rebuild_progression_grid, _select_prog_cell,
    stop_prog_sound_for_idx,
)
from klo_chords.chord_box import PROG_CELL_W, PROG_CELL_H

# ── Drag state ──────────────────────────────────────────────────────────────────
_drag_source_idx: Optional[int] = None
_drag_active: bool = False
_ghost_tag = "ghost_cell"

# The last known mouse position (for ghost rendering)
_last_mouse_x: float = 0
_last_mouse_y: float = 0


def drag_start(idx: int):
    """Begin dragging the cell at *idx*."""
    global _drag_source_idx, _drag_active
    if idx < 0 or idx >= PROG_CELLS_TOTAL:
        return
    cell = _prog_cells[idx]
    if cell.is_empty():
        return
    # Stop sound if cell was playing
    stop_prog_sound_for_idx(idx)
    _drag_source_idx = idx
    _drag_active = True


def drag_update(mouse_x: float, mouse_y: float):
    """Update ghost position during drag."""
    global _last_mouse_x, _last_mouse_y
    _last_mouse_x = mouse_x
    _last_mouse_y = mouse_y
    if not _drag_active or _drag_source_idx is None:
        return
    _render_ghost()


def drag_end(mouse_x: float, mouse_y: float) -> Optional[int]:
    """End drag, returning the target cell index under the cursor, or None."""
    global _drag_active, _drag_source_idx
    if not _drag_active or _drag_source_idx is None:
        _cleanup_ghost()
        _drag_active = False
        _drag_source_idx = None
        return None
    target = _cell_at_pos(mouse_x, mouse_y)
    _cleanup_ghost()
    src = _drag_source_idx
    _drag_active = False
    _drag_source_idx = None
    if target is not None and target != src:
        return target
    return None


def is_dragging() -> bool:
    return _drag_active


def get_drag_source() -> Optional[int]:
    return _drag_source_idx


def show_drop_menu(src_idx: int, tgt_idx: int):
    """Execute drop using the persistent paste-mode setting."""
    from klo_chords.state import get_paste_mode
    mode = get_paste_mode()
    _do_drop(src_idx, tgt_idx, mode)


def show_paste_menu(clipboard_data: list):
    """Execute paste using the persistent paste-mode setting."""
    from klo_chords.state import get_paste_mode
    mode = get_paste_mode()
    _do_paste(clipboard_data, mode)


# ── Internal helpers ────────────────────────────────────────────────────────────

def _cell_at_pos(mx: float, my: float) -> Optional[int]:
    """Determine which cell index (if any) is at screen position (mx, my)."""
    # This is approximate: we need to know the grid's position on screen.
    # We'll use a simpler approach: check the drawlist positions.
    # Since Dear PyGui doesn't give us direct screen coords for drawlists,
    # we'll compute based on known grid layout.
    # The grid starts at (GRID_PAD, ?) from the window left edge.
    # We store the viewport-relative position of the progression tab.
    win_w = dpg.get_viewport_width()
    # Grid starts at: GRID_PAD=20 from left, and below toolbar + tab bar
    grid_left = 20  # GRID_PAD
    grid_top = 130  # Approximate: toolbar (~30) + separator + tab bar + scale chooser row + spacing
    cell_w = PROG_CELL_W + 6  # cell width + gap
    cell_h = PROG_CELL_H + 6  # cell height + gap
    rel_x = mx - grid_left
    rel_y = my - grid_top
    if rel_x < 0 or rel_y < 0:
        return None
    col = int(rel_x // cell_w)
    row = int(rel_y // cell_h)
    if col >= PROG_COLS or row >= (PROG_CELLS_TOTAL // PROG_COLS):
        return None
    idx = row * PROG_COLS + col
    if 0 <= idx < PROG_CELLS_TOTAL:
        return idx
    return None


def _render_ghost():
    """Draw a semi-transparent ghost cell at the cursor position."""
    _cleanup_ghost()
    src = _drag_source_idx
    if src is None:
        return
    cell = _prog_cells[src]
    if cell.is_empty():
        return
    with dpg.drawlist(tag=_ghost_tag + "_dl", width=PROG_CELL_W,
                      height=PROG_CELL_H):
        # Semi-transparent fill
        dpg.draw_rectangle([0, 0], [PROG_CELL_W - 1, PROG_CELL_H - 1],
                           fill=[80, 170, 255, 160],
                           color=[80, 170, 255, 255], thickness=2)
        # Chord name
        from klo_chords.quality import quality_symbol
        q = quality_symbol(cell.quality).strip()
        name = cell.root + (" " + q if q else "")
        dpg.draw_text([5, 20], name, color=[255, 255, 255, 200],
                      size=16, parent=_ghost_tag + "_dl")


def _cleanup_ghost():
    if dpg.does_item_exist(_ghost_tag + "_dl"):
        dpg.delete_item(_ghost_tag + "_dl")


def _do_drop(src_idx: int, tgt_idx: int, mode: str):
    """Execute the drop operation."""
    from klo_chords.state import _do_insert, _do_replace, _do_swap, _prog_selected_idx
    from klo_chords.undo_manager import get_undo_manager
    um = get_undo_manager()
    if mode == "insert":
        _do_insert(src_idx, tgt_idx, with_undo=True)
    elif mode == "replace":
        _do_replace(src_idx, tgt_idx, with_undo=True)
    elif mode == "swap":
        _do_swap(src_idx, tgt_idx, with_undo=True)
    # Select target
    _select_prog_cell(tgt_idx)
    _rebuild_progression_grid()


def _do_paste(clipboard_data: list, mode: str):
    """Execute paste from clipboard."""
    from klo_chords.state import (
        _prog_selected_idx, _prog_cells, PROG_CELLS_TOTAL, PROG_COLS,
        _rebuild_progression_grid, _select_prog_cell, ProgCell,
        get_paste_shape,
    )
    from klo_chords.undo_manager import get_undo_manager
    import copy

    um = get_undo_manager()
    target = _prog_selected_idx if _prog_selected_idx is not None else 0

    shape = get_paste_shape()

    if mode == "replace":
        if shape == "shape":
            _do_paste_shape_replace(clipboard_data, target, um)
        else:
            # Save old state for undo
            old_data = [copy.deepcopy(_prog_cells[i]) for i in
                        range(target, min(target + len(clipboard_data), PROG_CELLS_TOTAL))]
            um.do(
                do_fn=lambda: _paste_replace(clipboard_data, target),
                undo_fn=lambda: _restore_replace(old_data, target),
                description="paste (replace)"
            )
    elif mode == "insert":
        old_tail = [copy.deepcopy(_prog_cells[i]) for i in
                    range(target, PROG_CELLS_TOTAL)]
        um.do(
            do_fn=lambda: _paste_insert(clipboard_data, target),
            undo_fn=lambda: _restore_insert(old_tail, target),
            description="paste (insert)"
        )
    elif mode == "swap":
        um.do(
            do_fn=lambda: _paste_swap(clipboard_data, target),
            undo_fn=lambda: _paste_swap_backward(clipboard_data, target),
            description="paste (swap)"
        )
    _select_prog_cell(target)
    _rebuild_progression_grid()


def _compute_clipboard_shape(data: list):
    """Compute the bounding dimensions of copied cells from their stored indices.
    
    Returns (n_rows, n_cols, min_row, min_col) or (1, len(data), 0, 0) if no indices.
    """
    indices = [d.get("_idx") for d in data if d.get("_idx") is not None]
    if not indices:
        return 1, len(data), 0, 0
    rows = [i // PROG_COLS for i in indices]
    cols = [i % PROG_COLS for i in indices]
    min_row, max_row = min(rows), max(rows)
    min_col, max_col = min(cols), max(cols)
    return (max_row - min_row + 1, max_col - min_col + 1, min_row, min_col)


def _do_paste_shape_replace(data: list, target: int, um):
    """Paste with shape preservation: maintain 2D layout of copied cells."""
    from klo_chords.state import _prog_cells, PROG_CELLS_TOTAL, PROG_COLS
    import copy

    n_rows, n_cols, min_row, min_col = _compute_clipboard_shape(data)
    tr, tc = target // PROG_COLS, target % PROG_COLS

    # Build index map: (copy_row_offset, copy_col_offset) -> cell_data
    shape_map = {}
    for d in data:
        src_idx = d.get("_idx")
        if src_idx is not None:
            sr = src_idx // PROG_COLS - min_row
            sc = src_idx % PROG_COLS - min_col
            shape_map[(sr, sc)] = d
        else:
            # No index — fall back to linear
            pass

    # For items without index, fill linear into the shape
    linear_idx = 0
    for d in data:
        if d.get("_idx") is None:
            # Find next empty slot in the shape
            for r in range(n_rows):
                for c in range(n_cols):
                    if (r, c) not in shape_map:
                        shape_map[(r, c)] = d
                        break
                if (r, c) in shape_map and shape_map[(r, c)] == d:
                    break

    # Save old state for undo
    old_data = {}
    for r in range(n_rows):
        for c in range(n_cols):
            idx = (tr + r) * PROG_COLS + (tc + c)
            if 0 <= idx < PROG_CELLS_TOTAL:
                old_data[(r, c)] = copy.deepcopy(_prog_cells[idx])

    def do_shape():
        for (r_offset, c_offset), cell_data in shape_map.items():
            idx = (tr + r_offset) * PROG_COLS + (tc + c_offset)
            if idx < 0 or idx >= PROG_CELLS_TOTAL:
                continue
            _prog_cells[idx].root = cell_data.get("root", _prog_cells[idx].root)
            _prog_cells[idx].quality = cell_data.get("quality", _prog_cells[idx].quality)
            _prog_cells[idx].inversion = cell_data.get("inversion", 0)
            _prog_cells[idx].octave = cell_data.get("octave", 3)
            _prog_cells[idx].voicing_idx = cell_data.get("voicing_idx", 0)

    def undo_shape():
        for (r_offset, c_offset), old in old_data.items():
            idx = (tr + r_offset) * PROG_COLS + (tc + c_offset)
            if idx < 0 or idx >= PROG_CELLS_TOTAL:
                continue
            _prog_cells[idx] = old

    um.do(do_shape, undo_shape, description="paste shape (replace)")


def _paste_replace(data: list, target: int):
    for i, cell_data in enumerate(data):
        idx = target + i
        if idx >= PROG_CELLS_TOTAL:
            break
        _prog_cells[idx].root = cell_data["root"]
        _prog_cells[idx].quality = cell_data["quality"]
        _prog_cells[idx].inversion = cell_data.get("inversion", 0)
        _prog_cells[idx].octave = cell_data.get("octave", 3)
        _prog_cells[idx].voicing_idx = cell_data.get("voicing_idx", 0)


def _restore_replace(old_data: list, target: int):
    for i, cell in enumerate(old_data):
        idx = target + i
        if idx >= PROG_CELLS_TOTAL:
            break
        _prog_cells[idx] = cell
    _rebuild_progression_grid()


def _paste_insert(data: list, target: int):
    # Shift cells down by len(data)
    n = len(data)
    for i in range(PROG_CELLS_TOTAL - 1, target + n - 1, -1):
        if i >= n and i - n >= 0:
            _prog_cells[i].root = _prog_cells[i - n].root
            _prog_cells[i].quality = _prog_cells[i - n].quality
            _prog_cells[i].inversion = _prog_cells[i - n].inversion
            _prog_cells[i].octave = _prog_cells[i - n].octave
            _prog_cells[i].voicing_idx = _prog_cells[i - n].voicing_idx
    for i, cell_data in enumerate(data):
        idx = target + i
        if idx >= PROG_CELLS_TOTAL:
            break
        _prog_cells[idx].root = cell_data["root"]
        _prog_cells[idx].quality = cell_data["quality"]
        _prog_cells[idx].inversion = cell_data.get("inversion", 0)
        _prog_cells[idx].octave = cell_data.get("octave", 3)
        _prog_cells[idx].voicing_idx = cell_data.get("voicing_idx", 0)


def _restore_insert(old_tail: list, target: int):
    for i, cell in enumerate(old_tail):
        idx = target + i
        if idx >= PROG_CELLS_TOTAL:
            break
        _prog_cells[idx] = cell
    _rebuild_progression_grid()


def _paste_swap(data: list, target: int):
    """Swap clipboard cells with existing cells at target position."""
    _swap_buf = []
    for i, cell_data in enumerate(data):
        idx = target + i
        if idx >= PROG_CELLS_TOTAL:
            break
        _swap_buf.append({
            "root": _prog_cells[idx].root,
            "quality": _prog_cells[idx].quality,
            "inversion": _prog_cells[idx].inversion,
            "octave": _prog_cells[idx].octave,
            "voicing_idx": _prog_cells[idx].voicing_idx,
        })
        _prog_cells[idx].root = cell_data["root"]
        _prog_cells[idx].quality = cell_data["quality"]
        _prog_cells[idx].inversion = cell_data.get("inversion", 0)
        _prog_cells[idx].octave = cell_data.get("octave", 3)
        _prog_cells[idx].voicing_idx = cell_data.get("voicing_idx", 0)
    # Store for undo
    import klo_chords.state as state
    state._paste_swap_buf = _swap_buf


def _paste_swap_backward(data: list, target: int):
    """Undo the swap by swapping back."""
    import klo_chords.state as state
    _swap_buf = getattr(state, "_paste_swap_buf", [])
    for i, cell_data in enumerate(_swap_buf):
        idx = target + i
        if idx >= PROG_CELLS_TOTAL:
            break
        _prog_cells[idx].root = cell_data["root"]
        _prog_cells[idx].quality = cell_data["quality"]
        _prog_cells[idx].inversion = cell_data["inversion"]
        _prog_cells[idx].octave = cell_data["octave"]
        _prog_cells[idx].voicing_idx = cell_data["voicing_idx"]
    _rebuild_progression_grid()
