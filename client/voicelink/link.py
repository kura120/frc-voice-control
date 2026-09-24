"""NetworkTables publisher. The laptop is an NT4 client; the roboRIO is the server."""

import time

import ntcore

from .config import TABLE_NAME


class RobotLink:
    def __init__(self, team: int | None = None, server: str | None = None) -> None:
        if team is None and server is None:
            raise ValueError("provide a team number or a server address")
        self._inst = ntcore.NetworkTableInstance.getDefault()
        table = self._inst.getTable(TABLE_NAME)
        self._command_pub = table.getStringTopic("command").publish()
        self._armed_pub = table.getBooleanTopic("armed").publish()
        self._armed_pub.set(False)
        self._inst.startClient4("voicelink")
        if server:
            self._inst.setServer(server)
        else:
            self._inst.setServerTeam(team)
        # Start above any previous run so the robot never sees a repeated sequence number.
        self._seq = int(time.time())

    @property
    def connected(self) -> bool:
        return self._inst.isConnected()

    def send(self, command: str) -> bool:
        """Publish '<seq>:<COMMAND>'. Dropped (not queued) if the robot isn't connected."""
        if not self.connected:
            print(f"  ! not connected to robot, dropped {command}")
            return False
        self._seq += 1
        self._command_pub.set(f"{self._seq}:{command}")
        return True

    def set_armed(self, armed: bool) -> None:
        self._armed_pub.set(armed)
