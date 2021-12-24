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


class VoyagerStatEnum(enum.IntEnum):
    STOPPED = 0,
    IDLE = 1,
    RUN = 2,
    ERRORE = 3,
    UNDEFINED = 4,
    WARNING = 5


class CcdStatEnum(enum.IntEnum):
    INIT = 0
    UNDEF = 1
    NO_COOLER = 2
    OFF = 3
    COOLING = 4
    COOLED = 5
    TIMEOUT_COOLING = 6
    WARMUP_RUNNING = 7
    WARMUP_END = 8
    ERROR = 9


@dataclass
class MountInfo:
    ra: str = '00:00:00'
    dec: str = '0°0\'0"'
    ra_j2000: str = '00:00:00'
    dec_j2000: str = '0°0\'0"'
    az: str = '0°0\'0"'
    alt: str = '0°0\'0"'
    pier: str = 'N/A'


@dataclass
class SystemStatusInfo:
    drag_script_name: str = ''
    sequence_name: str = ''
    guide_status: int = GuideStatEnum.STOPPED
    dither_status: int = DitherStatEnum.STOPPED
    voyager_status: int = VoyagerStatEnum.STOPPED
    ccd_status: int = CcdStatEnum.OFF
    is_tracking: bool = False
    is_slewing: bool = False
    mount_info: MountInfo = MountInfo()
