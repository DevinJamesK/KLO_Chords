"""
Undo/Redo manager using the Command pattern.

Each operation stores a pair of (do_fn, undo_fn) callables.
Supports unlimited undo/redo up to MAX_HISTORY steps.
"""

from typing import Callable, Dict, List, Optional

MAX_HISTORY = 100


class UndoManager:
    """Manages undo/redo history for grid mutations."""

    def __init__(self):
        self._undo_stack: List[Dict] = []
        self._redo_stack: List[Dict] = []
        self._batch: Optional[List[Dict]] = None

    def begin_batch(self, description: str = "batch"):
        """Start collecting commands into a single batch."""
        assert self._batch is None, "batch already open"
        self._batch = []

    def commit_batch(self):
        """Commit the current batch as a single undoable command."""
        assert self._batch is not None, "no batch open"
        if self._batch:
            # Consolidate into one command that does/undoes all sub-commands
            do_fns = [c["do"] for c in self._batch]
            undo_fns = [c["undo"] for c in self._batch]
            desc = self._batch[0].get("description", "batch")

            def do_all():
                for fn in do_fns:
                    fn()

            def undo_all():
                for fn in reversed(undo_fns):
                    fn()

            self._push({"do": do_all, "undo": undo_all, "description": desc})
        self._batch = None

    def _push(self, cmd: Dict):
        self._undo_stack.append(cmd)
        if len(self._undo_stack) > MAX_HISTORY:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def do(self, do_fn: Callable, undo_fn: Callable, description: str = ""):
        """Execute *do_fn* and store the pair for undo/redo."""
        if self._batch is not None:
            self._batch.append({"do": do_fn, "undo": undo_fn, "description": description})
            return
        do_fn()
        self._push({"do": do_fn, "undo": undo_fn, "description": description})

    def undo(self):
        """Undo the most recent command."""
        if not self._undo_stack:
            return
        cmd = self._undo_stack.pop()
        cmd["undo"]()
        self._redo_stack.append(cmd)

    def redo(self):
        """Redo the most recently undone command."""
        if not self._redo_stack:
            return
        cmd = self._redo_stack.pop()
        cmd["do"]()
        self._undo_stack.append(cmd)

    def clear(self):
        """Clear all history (e.g. on program init or full reset)."""
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._batch = None

    @property
    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    @property
    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0


# Global singleton
_undo_manager = UndoManager()


def get_undo_manager() -> UndoManager:
    return _undo_manager
