"""Event types the controller reports. Kept separate from *how* they're shown
so the same controller works with the plain printer or the Rich dashboard."""

from enum import Enum, auto


class Outcome(Enum):
    SENT = auto()  # command sent to the robot
    CONTROL = auto()  # "robot arm" / "robot disarm" was heard
    REJECTED_CONF = auto()  # confidence below --min-conf
    REJECTED_UNKNOWN = auto()  # grammar matched "[unk]"
    IGNORED_NOT_ACTIVATED = auto()  # valid command, but not activated yet
    NO_MATCH = auto()  # recognized text isn't a known phrase at all
