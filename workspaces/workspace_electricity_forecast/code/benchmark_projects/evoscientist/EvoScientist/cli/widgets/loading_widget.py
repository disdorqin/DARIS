"""Loading spinner widget shown while waiting for the first token."""

from __future__ import annotations

from textual.widgets import Static

_SPINNER_FRAMES = "\u280b\u2819\u2839\u2838\u283c\u2834\u2826\u2827\u2807\u280f"


class LoadingWidget(Static):
    """Spinner + 'Thinking...' with elapsed time counter.

    Mount when a turn starts; call ``remove()`` when the first
    thinking/text/tool_call event arrives.
    """

    DEFAULT_CSS = """
    LoadingWidget {
        height: auto;
        color: #22d3ee;
        padding: 0 0;
    }
    """

    def __init__(self) -> None:
        super().__init__("")
        self._frame = 0
        self._elapsed = 0.0
        self._timer_handle = None

    def on_mount(self) -> None:
        self._timer_handle = self.set_interval(0.1, self._tick)
        self._refresh_display()

    def _tick(self) -> None:
        self._frame = (self._frame + 1) % len(_SPINNER_FRAMES)
        self._elapsed += 0.1
        self._refresh_display()

    def _refresh_display(self) -> None:
        char = _SPINNER_FRAMES[self._frame]
        secs = int(self._elapsed)
        self.update(f"{char} Thinking... ({secs}s)")

    async def cleanup(self) -> None:
        """Stop timer and remove from DOM."""
        if self._timer_handle is not None:
            self._timer_handle.stop()
            self._timer_handle = None
        await self.remove()
