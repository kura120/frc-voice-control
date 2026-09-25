"""Turns recognizer results into robot commands: confidence gate + arm/disarm logic."""

import time
from typing import TYPE_CHECKING

from .config import ALWAYS_ALLOWED, ACTIVATE_PHRASE, COMMANDS, DEACTIVATE_PHRASE
from .events import Outcome
from .reporting import PlainReporter, Reporter

if TYPE_CHECKING:  # keeps this module importable (and testable) without ntcore installed
    from .link import RobotLink


class VoiceController:
    def __init__(
        self,
        link: "RobotLink",
        min_conf: float,
        arm_seconds: float,
        reporter: Reporter | None = None,
    ) -> None:
        self._link = link
        self._min_conf = min_conf
        self._arm_seconds = arm_seconds
        self._reporter = reporter or PlainReporter()
        self._armed_until = 0.0
        self._armed_published = False

    @property
    def armed(self) -> bool:
        return time.monotonic() < self._armed_until

    @property
    def armed_remaining(self) -> float:
        return max(0.0, self._armed_until - time.monotonic())

    def tick(self) -> None:
        """Call regularly so the armed flag expires on the robot/dashboard."""
        armed = self.armed
        if armed != self._armed_published:
            self._link.set_armed(armed)
            self._armed_published = armed
            self._reporter.armed(armed=armed, remaining=self.armed_remaining)

    def shutdown(self) -> None:
        self._armed_until = 0.0
        self._link.set_armed(False)
        self._reporter.armed(armed=False, remaining=0.0)

    def handle(self, result: dict) -> None:
        text = result.get("text", "").strip()
        if not text:
            return
        words = result.get("result", [])
        conf = sum(w.get("conf", 0.0) for w in words) / len(words) if words else 0.0

        if "[unk]" in text or conf < self._min_conf:
            outcome = Outcome.REJECTED_UNKNOWN if "[unk]" in text else Outcome.REJECTED_CONF
            self._reporter.heard(text=text, confidence=conf, outcome=outcome)
            return

        if text == ACTIVATE_PHRASE:
            self._armed_until = time.monotonic() + self._arm_seconds
            self._reporter.heard(
                text=text, confidence=conf, outcome=Outcome.CONTROL, detail="activated"
            )
            self.tick()
            return
        if text == DEACTIVATE_PHRASE:
            self._armed_until = 0.0
            self._reporter.heard(
                text=text, confidence=conf, outcome=Outcome.CONTROL, detail="deactivated"
            )
            self.tick()
            return

        command = COMMANDS.get(text)
        if command is None:
            self._reporter.heard(text=text, confidence=conf, outcome=Outcome.NO_MATCH)
            return
        if command not in ALWAYS_ALLOWED and not self.armed:
            self._reporter.heard(
                text=text,
                confidence=conf,
                outcome=Outcome.IGNORED_NOT_ACTIVATED,
                detail=f"say '{ACTIVATE_PHRASE}' first",
            )
            return
        if self._link.send(command):
            self._reporter.heard(text=text, confidence=conf, outcome=Outcome.SENT, detail=command)