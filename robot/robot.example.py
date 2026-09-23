import wpilib
from subsystems.voice_control import VoiceControlSubsystem

class MyRobot(wpilib.TimedRobot):
    def robotInit(self) -> None:
        self.voice_control = VoiceControlSubsystem()
        
        # Mapping callbacks to the component framework seamlessly
        self.voice_control.register_command("intake cube", self.mock_intake)
        self.voice_control.register_command("stop", self.mock_stop)

    def robotPeriodic(self) -> None:
        self.voice_control.periodic()

    def mock_intake(self) -> None:
        print("[ROBOT ACTION] Extending intake mechanisms.")

    def mock_stop(self) -> None:
        print("[ROBOT ACTION] HALT.")

if __name__ == "__main__":
    wpilib.startRobot(MyRobot)
