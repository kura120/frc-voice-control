"""Voice command receiver (RobotPy / commands2).

Reads "<seq>:<COMMAND>" from NetworkTables table "VoiceControl" and runs whatever
you bound to COMMAND. Drop this file into your subsystems folder, construct one
VoiceControl in robotInit, and call bind()/bind_command().
"""

from collections.abc import Callable

import commands2
import ntcore
from wpilib import DriverStation, RobotController, SmartDashboard

TABLE_NAME = "VoiceControl"
MAX_AGE_S = 1.0  # ignore commands older than this (stale / delayed)
ALLOW_ON_FMS = False  # voice input is ignored on a real field unless you flip this
ALWAYS_ALLOWED = frozenset({"STOP"})  # accepted even when the robot is disabled

# Console verbosity, printed as "[CMD] ...":
#   0 = silent
#   1 = one line per command outcome (executed / stale / unbound / blocked)
#   2 = also log every received value and every binding
VERBOSITY = 1


class VoiceControl(commands2.Subsystem):
    def __init__(self, verbosity: int = VERBOSITY) -> None:
        super().__init__()
        self.verbosity = verbosity
        table = ntcore.NetworkTableInstance.getDefault().getTable(TABLE_NAME)
        self._command_sub = table.getStringTopic("command").subscribe("")
        self._armed_sub = table.getBooleanTopic("armed").subscribe(False)
        self._actions: dict[str, Callable[[], None]] = {}

        # Whatever is already on the topic at startup is old news: never run it.
        initial = self._parse(self._command_sub.get())
        self._last_seq = initial[0] if initial else None

        self.bind("STOP", commands2.CommandScheduler.getInstance().cancelAll)
        self._log(2, f"ready (verbosity {self.verbosity})")

    def set_verbosity(self, level: int) -> None:
        self.verbosity = level

    # ---- registration -------------------------------------------------
    def bind(self, name: str, action: Callable[[], None]) -> None:
        """Run `action` immediately when `name` is heard."""
        self._actions[name.upper()] = action
        self._log(2, f"bound {name.upper()}")

    def bind_command(self, name: str, command: commands2.Command) -> None:
        """Schedule `command` when `name` is heard."""
        self.bind(name, lambda: commands2.CommandScheduler.getInstance().schedule(command))

    # ---- internals ----------------------------------------------------
    def _log(self, level: int, message: str) -> None:
        if self.verbosity >= level:
            print(f"[CMD] {message}")

    def _report(self, name: str, status: str) -> None:
        SmartDashboard.putString("Voice/Last", f"{name}: {status}")
        self._log(1, f"{name} {status}")

    @staticmethod
    def _parse(raw: str) -> tuple[int, str] | None:
        seq, sep, name = raw.partition(":")
        if not sep or not name:
            return None
        try:
            return int(seq), name.strip().upper()
        except ValueError:
            return None

    @staticmethod
    def _allowed(name: str) -> bool:
        if name in ALWAYS_ALLOWED:
            return True
        if DriverStation.isFMSAttached() and not ALLOW_ON_FMS:
            return False
        return DriverStation.isEnabled()

    def periodic(self) -> None:
        SmartDashboard.putBoolean("Voice/Armed", self._armed_sub.get())

        atomic = self._command_sub.getAtomic()
        parsed = self._parse(atomic.value)
        if parsed is None or parsed[0] == self._last_seq:
            return
        seq, name = parsed
        self._last_seq = seq

        # NT server time and FPGA time share a clock on the roboRIO.
        age_s = (RobotController.getFPGATime() - atomic.serverTime) / 1e6
        self._log(2, f"rx seq={seq} name={name} age={age_s:.2f}s")

        if age_s > MAX_AGE_S:
            self._report(name, f"stale ({age_s:.1f}s)")
        elif name not in self._actions:
            self._report(name, "unbound")
        elif not self._allowed(name):
            self._report(name, "blocked (disabled/FMS)")
        else:
            self._actions[name]()
            self._report(name, "executed")