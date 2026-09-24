# frc-voice-control

Voice commands for an FRC robot. Speech is recognized **on the driver station laptop**
(Vosk, restricted grammar) and sent to the robot over NetworkTables. The robot side is a
small drop-in subsystem in Python, Java or C++.

```
mic -> voicelink (laptop, NT client) -> NetworkTables (roboRIO is the server) -> VoiceControl subsystem -> your commands
```

There is no server script to write: the roboRIO already hosts NetworkTables. The Raspberry Pi
is not needed.

## Layout

```
client/                     laptop program (Python)
  voicelink/
    __main__.py             CLI + audio loop
    config.py               vocabulary and constants  <- edit COMMANDS here
    asr.py                  Vosk wrapper
    ptt.py                  push-to-talk key
    controller.py           confidence gate + arm/disarm
    link.py                 NetworkTables publisher
robot/
  py/                       robot.py, subsystems/voice_control.py
  java/                     Robot.java, RobotContainer.java, subsystems/VoiceControl.java
  cpp/                      Robot.{h,cpp}, RobotContainer.{h,cpp}, subsystems/VoiceControl.{h,cpp}
```

The Java and C++ folders are kept flat for readability. They are not complete Gradle
projects: generate one with the WPILib VS Code extension and copy the files in.

- Java: copy into `src/main/java/frc/robot/` (the `package frc.robot` lines already match).
  File names are case-sensitive (`Robot.java`, not `robot.java`).
- C++: put the `.cpp` files in `src/main/cpp/` and the `.h` files in `src/main/include/`,
  keeping the `subsystems/` subfolder in each.

## Laptop setup

```
cd client
pip install -r requirements.txt
```

Download a small English Vosk model from https://alphacephei.com/vosk/models
(e.g. `vosk-model-small-en-us-0.15`) and unzip it. Use a small model: the large ones do not
support the runtime grammar this project relies on.

```
python -m voicelink --model ./vosk-model-small-en-us-0.15 --team 1234
python -m voicelink --model ./model --server localhost     # robot simulation
python -m voicelink --list-devices                         # find your mic
```

Hold **F9** to talk (`--ptt-key` to change). Say **"robot arm"**, then a command such as
"shoot". Arming lasts 8 seconds (`--arm-seconds`). "Stop" always works. "Robot disarm" ends the
window early. Commands under 0.6 mean word confidence are dropped (`--min-conf`).

## Robot setup

Copy the subsystem for your language into your project, construct one `VoiceControl`, and bind
command names to actions:

| Language | File | Wiring example |
|---|---|---|
| Python | `robot/py/subsystems/voice_control.py` | `robot/py/robot.py` |
| Java | `robot/java/subsystems/VoiceControl.java` | `RobotContainer.java` |
| C++ | `robot/cpp/subsystems/VoiceControl.{h,cpp}` | `RobotContainer.{h,cpp}` |

The subsystem must be registered with the scheduler (constructing it does this) and the
scheduler must run each loop (`TimedCommandRobot` / `CommandScheduler.run()`).

## NetworkTables protocol

Table `VoiceControl`:

| Topic | Type | Meaning |
|---|---|---|
| `command` | string | `"<seq>:<COMMAND>"`, e.g. `"1758700123:SHOOT"` |
| `armed` | boolean | true while the laptop is accepting non-STOP commands |

The robot acts only when `<seq>` changes, ignores anything older than `MAX_AGE` (1 s, using the
NT server timestamp), and ignores whatever value was already present at startup.

## Adding a command

1. Add the phrase to `COMMANDS` in `client/voicelink/config.py`.
2. Bind the same id on the robot: `voice.bind_command("NAME", ...)`.

Keep phrases short and phonetically distinct.

## Safety

- Voice is for high-level, low-risk actions (modes, targets, auto selection). Do not drive
  motors directly from it.
- The robot ignores voice commands while disabled (except `STOP`) and while connected to FMS
  (`ALLOW_ON_FMS`). Flip that only after checking the rules.
- Keep the physical e-stop and controller as the override.
- Check the current-year FRC game manual on operator input and driver station software before
  using this in a match.

## Development

CI runs `ruff check` and `ruff format --check`. Locally: `pip install ruff && ruff check . && ruff format .`

## License

See `LICENSE`.
