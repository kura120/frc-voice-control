"""Global push-to-talk key handling."""

import sys
import threading
import time

from pynput import keyboard


def parse_key(name: str):
    name = name.lower()
    if name in keyboard.Key.__members__:
        return keyboard.Key[name]
    if len(name) == 1:
        return keyboard.KeyCode.from_char(name)
    sys.exit(f"Unknown key '{name}'. Use one character or a pynput Key name (f9, ctrl_r, ...).")


class PushToTalk:
    """`active` is True while the key is held, plus a short tail after release."""

    def __init__(self, key, tail_s: float) -> None:
        self._key = key
        self._tail_s = tail_s
        self._down = threading.Event()
        self._deadline = 0.0
        self._listener = keyboard.Listener(on_press=self._press, on_release=self._release)

    def start(self) -> None:
        self._listener.start()

    def _press(self, key) -> None:
        if key == self._key:
            self._down.set()

    def _release(self, key) -> None:
        if key == self._key:
            self._deadline = time.monotonic() + self._tail_s
            self._down.clear()

    @property
    def active(self) -> bool:
        return self._down.is_set() or time.monotonic() < self._deadline
