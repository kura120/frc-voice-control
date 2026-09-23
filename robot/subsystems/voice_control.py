import ntcore
from typing import Callable, Dict

class VoiceControlSubsystem:
    def __init__(self, table_name: str = "VoiceCommands") -> None:
        self.nt_instance: ntcore.NetworkTableInstance = ntcore.NetworkTableInstance.getDefault()
        self.table: ntcore.NetworkTable = self.nt_instance.getTable(table_name)
        
        self.asr_subscriber: ntcore.StringSubscriber = self.table.getStringTopic("asrResult").subscribe("")
        self.heartbeat_subscriber: ntcore.IntegerSubscriber = self.table.getIntegerTopic("heartbeat").subscribe(0)
        
        self.last_heartbeat: int = 0
        self.command_registry: Dict[str, Callable[[], None]] = {}

    def register_command(self, command_phrase: str, callback: Callable[[], None]) -> None:
        self.command_registry[command_phrase.strip().lower()] = callback

    def periodic(self) -> None:
        current_heartbeat: int = self.heartbeat_subscriber.get()
        if current_heartbeat != self.last_heartbeat:
            self.last_heartbeat = current_heartbeat
            raw_command = self.asr_subscriber.get().strip().lower()
            
            if raw_command in self.command_registry:
                self.command_registry[raw_command]()
            elif raw_command:
                print(f"[Voice Subsystem] Warning: Unhandled Command: '{raw_command}'")
