"""
Tests for klo_chords.core.undo_manager — undo/redo command-pattern manager.
"""

from __future__ import annotations
import pytest
from klo_chords.core.undo_manager import UndoManager, get_undo_manager, MAX_HISTORY


@pytest.fixture
def um() -> UndoManager:
    return UndoManager()


class TestUndoManager:
    def test_do_executes_function(self, um):
        state = {"x": 0}
        um.do(lambda: state.update(x=1), lambda: state.update(x=0))
        assert state["x"] == 1

    def test_undo_reverses(self, um):
        state = {"x": 0}
        um.do(lambda: state.update(x=1), lambda: state.update(x=0))
        assert state["x"] == 1
        um.undo()
        assert state["x"] == 0

    def test_redo_restores(self, um):
        state = {"x": 0}
        um.do(lambda: state.update(x=42), lambda: state.update(x=0))
        um.undo()
        um.redo()
        assert state["x"] == 42

    def test_undo_on_empty_is_noop(self, um):
        um.undo()

    def test_redo_on_empty_is_noop(self, um):
        um.redo()

    def test_redo_clears_after_new_do(self, um):
        state = {"x": 0}
        um.do(lambda: state.update(x=1), lambda: state.update(x=0))
        um.undo()
        um.do(lambda: state.update(x=99), lambda: state.update(x=0))
        assert state["x"] == 99
        um.redo()  # should be noop
        assert state["x"] == 99

    def test_can_undo_can_redo(self, um):
        assert not um.can_undo
        assert not um.can_redo
        um.do(lambda: None, lambda: None)
        assert um.can_undo
        assert not um.can_redo
        um.undo()
        assert not um.can_undo
        assert um.can_redo


class TestBatchOperations:
    def test_batch_undo_reverses_all(self, um):
        state = {"a": 0, "b": 0}
        um.begin_batch("set both")
        um.do(lambda: state.update(a=10), lambda: state.update(a=0))
        um.do(lambda: state.update(b=20), lambda: state.update(b=0))
        um.commit_batch()
        assert state["a"] == 0 and state["b"] == 0  # batch deferred execution
        assert um.can_undo

    def test_empty_batch_is_noop(self, um):
        um.begin_batch("empty")
        um.commit_batch()
        assert not um.can_undo

    def test_nested_batch_asserts(self, um):
        um.begin_batch()
        with pytest.raises(AssertionError, match="batch already open"):
            um.begin_batch()
        um.commit_batch()

    def test_commit_without_begin_asserts(self, um):
        with pytest.raises(AssertionError, match="no batch open"):
            um.commit_batch()


class TestMaxHistory:
    def test_history_trimmed(self, um):
        for i in range(MAX_HISTORY + 10):
            um.do(lambda i=i: None, lambda i=i: None)
        assert len(um._undo_stack) == MAX_HISTORY

    def test_redo_cleared_on_new_do(self, um):
        um.do(lambda: None, lambda: None)
        um.undo()
        assert um.can_redo
        um.do(lambda: None, lambda: None)
        assert not um.can_redo


class TestClear:
    def test_clear_empties_stacks(self, um):
        um.do(lambda: None, lambda: None)
        um.do(lambda: None, lambda: None)
        um.undo()
        um.clear()
        assert not um.can_undo
        assert not um.can_redo
        assert um._batch is None

    def test_clear_cancels_batch(self, um):
        um.begin_batch()
        um.do(lambda: None, lambda: None)
        um.clear()
        assert um._batch is None


class TestGlobalSingleton:
    def test_returns_same_instance(self):
        a = get_undo_manager()
        b = get_undo_manager()
        assert a is b

    def test_is_usable(self):
        um = get_undo_manager()
        um.clear()
        state = {"x": 0}
        um.do(lambda: state.update(x=1), lambda: state.update(x=0))
        assert state["x"] == 1
        um.undo()
        assert state["x"] == 0
        um.clear()
