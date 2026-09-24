"""Example RobotPy project entry point showing how to wire VoiceControl in.

Keep your existing robot.py; you only need the VoiceControl lines.
"""

import commands2

from subsystems.voice_control import VoiceControl


class MyRobot(commands2.TimedCommandRobot):
    def robotInit(self) -> None:
        self.voice = VoiceControl()

        # Replace these with your real commands.
        self.voice.bind_command("INTAKE", commands2.PrintCommand("INTAKE"))
        self.voice.bind_command("SHOOT", commands2.PrintCommand("SHOOT"))
        self.voice.bind_command("CLIMB", commands2.PrintCommand("CLIMB"))
        # "STOP" is pre-bound to cancelAll(); override with self.voice.bind("STOP", ...) if needed.
