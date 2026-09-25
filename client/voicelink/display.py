"""Rich-based live dashboard. Selected by default; --plain uses PlainReporter
instead (see __main__.py). Import is deferred to __main__ so `rich` is only
required when the dashboard is actually used.
"""

from __future__ import annotations

import time
from collections import deque

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .events import Outcome

# (style, label) for each outcome, shared by the last-heard panel and history rows.
_OUTCOME_STYLE: dict[Outcome, tuple[str, str]] = {
    Outcome.SENT: ("bold green", "sent"),
    Outcome.CONTROL: ("cyan", "ok"),
    Outcome.REJECTED_CONF: ("yellow", "low confidence"),
    Outcome.REJECTED_UNKNOWN: ("yellow", "unrecognized"),
    Outcome.IGNORED_NOT_ACTIVATED: ("yellow", "not activated"),
    Outcome.NO_MATCH: ("dim", "no match"),
}

_FIXED_ROWS = 10  # rough height of the status bar + last-heard panel + table header/borders


def _conf_bar(conf: float, width: int = 10) -> Text:
    filled = round(max(0.0, min(1.0, conf)) * width)
    color = "green" if conf >= 0.8 else "yellow" if conf >= 0.6 else "red"
    return Text("█" * filled + "░" * (width - filled), style=color)


class RichReporter:
    """Persistent dashboard: status bar, last-heard panel, and a history table
    sized to fit the terminal. Use as a context manager so the Live display is
    always stopped cleanly, including on Ctrl+C.
    """

    def __init__(self, verbosity: int = 1) -> None:
        self.verbosity = verbosity
        self._console = Console()
        self._live = Live(console=self._console, refresh_per_second=8, screen=False)
        self._connected = False
        self._listening = False
        self._activated = False
        self._activation_remaining = 0.0
        self._last: tuple[str, float, Outcome, str] | None = None
        self._history: deque[tuple] = deque(maxlen=500)

    def __enter__(self) -> RichReporter:
        self._live.start()
        self._render()
        return self

    def __exit__(self, *exc) -> None:
        self._live.stop()

    # ---- Reporter protocol ---------------------------------------
    def status(self, *, connected: bool, listening: bool) -> None:
        self._connected = connected
        self._listening = listening
        self._render()

    def armed(self, *, armed: bool, remaining: float) -> None:
        self._activated = armed
        self._activation_remaining = remaining
        self._render()

    def heard(self, *, text: str, confidence: float, outcome: Outcome, detail: str = "") -> None:
        self._last = (text, confidence, outcome, detail)
        if self.verbosity >= 1:
            self._history.appendleft((time.strftime("%H:%M:%S"), text, confidence, outcome, detail))
        self._render()

    def log(self, message: str) -> None:
        if self.verbosity >= 2:
            self._history.appendleft((time.strftime("%H:%M:%S"), message, None, None, ""))
        self._render()

    # ---- rendering --------------------------------------------------
    def _status_line(self) -> Text:
        dot_style = "green" if self._connected else "red"
        dot = Text("● " if self._connected else "○ ", style=dot_style)
        line = Text.assemble(dot, "robot   ")
        if self._activated:
            line.append(f"● activated ({self._activation_remaining:0.1f}s)", style="bold green")
        else:
            line.append("○ not activated", style="dim")
        line.append("   ")
        listen_style = "cyan" if self._listening else "dim"
        line.append("● listening" if self._listening else "○ idle", style=listen_style)
        return line

    def _last_heard_panel(self) -> Panel:
        if self._last is None:
            body: Text | Group = Text("waiting for speech...", style="dim")
        else:
            text, conf, outcome, detail = self._last
            style, label = _OUTCOME_STYLE.get(outcome, ("white", ""))
            body = Text()
            body.append(f'"{text}"\n', style="bold")
            body.append_text(_conf_bar(conf))
            body.append(f"  {conf:.2f}\n")
            suffix = f" — {detail}" if detail and outcome != Outcome.SENT else ""
            body.append(label + suffix, style=style)
        return Panel(body, title="last heard", border_style="blue")

    def _history_table(self) -> Table:
        table = Table(expand=True, show_edge=False, pad_edge=False)
        table.add_column("time", width=8, style="dim")
        table.add_column("phrase", ratio=2)
        table.add_column("conf", width=5, justify="right")
        table.add_column("outcome", ratio=1)

        height = self._console.size.height or 24
        rows_available = max(1, height - _FIXED_ROWS)
        for ts, text, conf, outcome, detail in list(self._history)[:rows_available]:
            if outcome is None:  # verbosity-2 log line, not a heard phrase
                table.add_row(ts, Text(text, style="dim"), "", "")
                continue
            style, label = _OUTCOME_STYLE.get(outcome, ("white", ""))
            shown = f"{text} → {detail}" if outcome is Outcome.SENT else text
            table.add_row(ts, shown, f"{conf:.2f}", Text(label, style=style))
        return table

    def _render(self) -> None:
        self._live.update(
            Group(
                Panel(self._status_line(), border_style="grey50"),
                self._last_heard_panel(),
                Panel(self._history_table(), title="history", border_style="grey50"),
            )
        )
