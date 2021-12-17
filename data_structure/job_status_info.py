import enum
from dataclasses import dataclass


class GuideStatEnum(enum.IntEnum):
    STOPPED = 0,
    WAITING_SETTLE = 1,
    RUNNING = 2,
    TIMEOUT_SETTLE = 3


class DitherStatEnum(enum.IntEnum):
    STOPPED = 0,
    RUNNING = 1,
    WAITING_SETTLE = 2,
    TIMEOUT_SETTLE = 3


@dataclass
class JobStatusInfo:
    drag_script_name: str = ''
    sequence_name: str = ''
    guide_status: int = GuideStatEnum.STOPPED
    dither_status: int = DitherStatEnum.STOPPED
    is_tracking: bool = False
    is_slewing: bool = False
