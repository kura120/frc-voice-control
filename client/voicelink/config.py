"""Vocabulary and constants. Edit COMMANDS to change what the robot understands."""

TABLE_NAME = "VoiceControl"

# spoken phrase -> command id sent to the robot.
# Keep phrases short and phonetically distinct: a small closed vocabulary is
# what makes Vosk fast and accurate.
COMMANDS = {
    "intake": "INTAKE",
    "shoot": "SHOOT",
    "stop": "STOP",
    "climb": "CLIMB",
    "auto one": "AUTO_1",
    "auto two": "AUTO_2",
}

ACTIVATE_PHRASE = "activate"
DEACTIVATE_PHRASE = "deactivate"

# Command ids accepted even when not armed. Stopping should never be gated.
ALWAYS_ALLOWED = frozenset({"STOP"})

SAMPLE_RATE = 16000
BLOCK_SIZE = 1600  # 100 ms of audio per block
DEFAULT_MIN_CONF = 0.6
DEFAULT_ARM_SECONDS = 30.0
DEFAULT_PTT_KEY = "x"
# 0 = status/last-heard only, 1 = + outcome history, 2 = + raw rx/debug rows
DEFAULT_VERBOSITY = 1
PTT_TAIL_SECONDS = 0.1  # keep listening briefly after release so words aren't clipped


def grammar() -> list[str]:
    """Phrases Vosk is allowed to output. '[unk]' catches everything else."""
    return [*COMMANDS, ACTIVATE_PHRASE, DEACTIVATE_PHRASE, "[unk]"]