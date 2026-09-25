"""Reporter interface: how the controller announces what happened, without
knowing whether that becomes a plain print or a Rich dashboard update.

PlainReporter is the default and is what --plain selects; it is also what the
tests use implicitly, so its behavior should stay boring and stable.
"""

from typing import Protocol

from .events import Outcome


class Reporter(Protocol):
    def status(self, *, connected: bool, listening: bool) -> None: ...
    def armed(self, *, armed: bool, remaining: float) -> None: ...
    def heard(
        self, *, text: str, confidence: float, outcome: Outcome, detail: str = ""
    ) -> None: ...
    def log(self, message: str) -> None: ...  # verbosity-2 detail (raw rx, bindings, ...)


_LABEL = {
    Outcome.SENT: "sent",
    Outcome.CONTROL: "ok",
    Outcome.REJECTED_CONF: "rejected (low confidence)",
    Outcome.REJECTED_UNKNOWN: "rejected (unrecognized word)",
    Outcome.IGNORED_NOT_ACTIVATED: "ignored (not activated)",
    Outcome.NO_MATCH: "no match",
}


class PlainReporter:
    """Old-style prints: one line per event, nothing repainted in place."""

    def __init__(self, verbosity: int = 1) -> None:
        self.verbosity = verbosity

    def status(self, *, connected: bool, listening: bool) -> None:
        pass  # plain mode doesn't repaint a status line every tick

    def armed(self, *, armed: bool, remaining: float) -> None:
        if self.verbosity >= 1:
            print("  [armed]" if armed else "  [disarmed]")

    def heard(self, *, text: str, confidence: float, outcome: Outcome, detail: str = "") -> None:
        if self.verbosity < 1:
            return
        print(f"heard: '{text}' (conf {confidence:.2f})")
        label = _LABEL.get(outcome, "")
        if outcome in (Outcome.SENT,):
            print(f"  -> sent {detail}")
        elif label:
            print(f"  {label}" + (f": {detail}" if detail else ""))

    def log(self, message: str) -> None:
        if self.verbosity >= 2:
            print(f"  {message}")

    def __enter__(self) -> "PlainReporter":
        return self

    def __exit__(self, *exc) -> None:
        pass
