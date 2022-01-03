import enum
from dataclasses import dataclass


class SpecialBatteryPercentageEnum(enum.IntEnum):
    ON_AC_POWER = -1
    NOT_MONITORED = -2
    NOT_AVAILABLE = -3


@dataclass
class MemoryUsage:
    timestamp: float = 0  # timestamp in seconds since epoch
    voyager_vms: float = -1  # Memory used by voyager in mega bytes.
    bot_vms: float = -1  # Memory used by bot in mega bytes
