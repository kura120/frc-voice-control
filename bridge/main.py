#!/usr/bin/env python3
import subprocess
import ntcore
import sys

def main():
    inst = ntcore.NetworkTableInstance.getDefault()
    inst.setServerTeam(3340)  # Configure with your absolute FRC Team Number
    inst.startClient4("Voice Coprocessor Bridge")
    
    table = inst.getTable("VoiceCommands")
    asr_pub = table.getStringTopic("asrResult").publish()
    heartbeat_pub = table.getIntegerTopic("heartbeat").publish()

    heartbeat_index = 0

    process = subprocess.Popen(
        ['../target/release/core-asr'], 
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1
    )

    print("Coprocessor bridge active. Forwarding data...")
    try:
        for line in iter(process.stdout.readline, ''):
            command = line.strip()
            if command:
                heartbeat_index += 1
                asr_pub.set(command)
                heartbeat_pub.set(heartbeat_index)
                print(f"[BRIDGE] Forwarded command: '{command}' | Heartbeat: {heartbeat_index}")
    except KeyboardInterrupt:
        process.terminate()

if __name__ == "__main__":
    main()
