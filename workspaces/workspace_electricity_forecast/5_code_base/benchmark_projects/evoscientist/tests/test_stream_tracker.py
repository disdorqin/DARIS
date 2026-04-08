"""Tests for EvoScientist/stream/tracker.py."""

from EvoScientist.stream.tracker import ToolCallTracker


class TestToolCallTracker:
    def test_update_and_get(self):
        tracker = ToolCallTracker()
        tracker.update("tc1", name="execute", args={"command": "ls"})
        info = tracker.get("tc1")
        assert info is not None
        assert info.name == "execute"
        assert info.args == {"command": "ls"}

    def test_update_merges(self):
        tracker = ToolCallTracker()
        tracker.update("tc1", name="execute")
        tracker.update("tc1", args={"command": "ls"})
        info = tracker.get("tc1")
        assert info.name == "execute"
        assert info.args == {"command": "ls"}

    def test_get_missing(self):
        tracker = ToolCallTracker()
        assert tracker.get("nonexistent") is None

    def test_is_ready_true(self):
        tracker = ToolCallTracker()
        tracker.update("tc1", name="execute")
        assert tracker.is_ready("tc1") is True

    def test_is_ready_no_name(self):
        tracker = ToolCallTracker()
        tracker.update("tc1")
        assert tracker.is_ready("tc1") is False

    def test_is_ready_already_emitted(self):
        tracker = ToolCallTracker()
        tracker.update("tc1", name="execute")
        tracker.mark_emitted("tc1")
        assert tracker.is_ready("tc1") is False

    def test_is_ready_missing_id(self):
        tracker = ToolCallTracker()
        assert tracker.is_ready("tc_missing") is False

    def test_append_json_delta_and_finalize(self):
        tracker = ToolCallTracker()
        tracker.update("tc1", name="execute")
        tracker.append_json_delta('{"comma')
        tracker.append_json_delta('nd": "ls"}')
        tracker.finalize_all()
        info = tracker.get("tc1")
        assert info.args == {"command": "ls"}
        assert info.args_complete is True

    def test_finalize_invalid_json(self):
        tracker = ToolCallTracker()
        tracker.update("tc1", name="execute")
        tracker.append_json_delta("{invalid json")
        tracker.finalize_all()
        info = tracker.get("tc1")
        # Args should remain empty since JSON is invalid
        assert info.args == {}
        assert info.args_complete is True

    def test_emit_all_pending(self):
        tracker = ToolCallTracker()
        tracker.update("tc1", name="execute")
        tracker.update("tc2", name="read_file")
        pending = tracker.emit_all_pending()
        assert len(pending) == 2
        # All should now be marked emitted
        assert tracker.get("tc1").emitted is True
        assert tracker.get("tc2").emitted is True
        # Second call should return empty
        assert tracker.emit_all_pending() == []

    def test_get_pending(self):
        tracker = ToolCallTracker()
        tracker.update("tc1", name="execute")
        tracker.update("tc2", name="read_file")
        tracker.mark_emitted("tc1")
        pending = tracker.get_pending()
        assert len(pending) == 1
        assert pending[0].id == "tc2"

    def test_get_all(self):
        tracker = ToolCallTracker()
        tracker.update("tc1", name="execute")
        tracker.update("tc2", name="read_file")
        assert len(tracker.get_all()) == 2

    def test_clear(self):
        tracker = ToolCallTracker()
        tracker.update("tc1", name="execute")
        tracker.clear()
        assert tracker.get("tc1") is None
        assert tracker.get_all() == []
