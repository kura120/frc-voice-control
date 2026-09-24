"""Turns recognizer results into robot commands: confidence gate + arm/disarm logic."""

import time
from typing import TYPE_CHECKING

from .config import ALWAYS_ALLOWED, ARM_PHRASE, COMMANDS, DISARM_PHRASE

if TYPE_CHECKING:  # keeps this module importable (and testable) without ntcore installed
    from .link import RobotLink


class VoiceController:
    def __init__(self, link: "RobotLink", min_conf: float, arm_seconds: float) -> None:
        self._link = link
        self._min_conf = min_conf
        self._arm_seconds = arm_seconds
        self._armed_until = 0.0
        self._armed_published = False

    @property
    def armed(self) -> bool:
        return time.monotonic() < self._armed_until

    def tick(self) -> None:
        """Call regularly so the armed flag expires on the robot/dashboard."""
        armed = self.armed
        if armed != self._armed_published:
            self._link.set_armed(armed)
            self._armed_published = armed
            print("  [armed]" if armed else "  [disarmed]")

    def shutdown(self) -> None:
        self._armed_until = 0.0
        self._link.set_armed(False)

    def handle(self, result: dict) -> None:
        text = result.get("text", "").strip()
        if not text:
            return
        words = result.get("result", [])
        conf = sum(w.get("conf", 0.0) for w in words) / len(words) if words else 0.0
        print(f"heard: '{text}' (conf {conf:.2f})")

        if "[unk]" in text or conf < self._min_conf:
            print("  rejected (unknown word or low confidence)")
            return

        if text == ARM_PHRASE:
            self._armed_until = time.monotonic() + self._arm_seconds
            self.tick()
            return
        if text == DISARM_PHRASE:
            self._armed_until = 0.0
            self.tick()
            return

        command = COMMANDS.get(text)
        if command is None:
            return
        if command not in ALWAYS_ALLOWED and not self.armed:
            print(f"  ignored {command}: say '{ARM_PHRASE}' first")
            return
        if self._link.send(command):
            print(f"  -> sent {command}")
