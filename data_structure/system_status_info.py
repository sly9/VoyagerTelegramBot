import enum
from dataclasses import dataclass


class GuideStatusEnum(enum.IntEnum):
    STOPPED = 0,
    WAITING_SETTLE = 1,
    RUNNING = 2,
    TIMEOUT_SETTLE = 3


class DitherStatusEnum(enum.IntEnum):
    STOPPED = 0,
    RUNNING = 1,
    WAITING_SETTLE = 2,
    TIMEOUT_SETTLE = 3


class VoyagerStatusEnum(enum.IntEnum):
    STOPPED = 0,
    IDLE = 1,
    RUN = 2,
    ERRORE = 3,
    UNDEFINED = 4,
    WARNING = 5


class CcdStatusEnum(enum.IntEnum):
    INIT = 0,
    UNDEF = 1,
    NO_COOLER = 2,
    OFF = 3,
    COOLING = 4,
    COOLED = 5,
    TIMEOUT_COOLING = 6,
    WARMUP_RUNNING = 7,
    WARMUP_END = 8,
    ERROR = 9


class MountStatusEnum(enum.Enum):
    PARKED = 'PARKED',
    SLEWING = 'SLEWING',
    TRACKING = 'TRACKING',
    UNDEFINED = 'UNDEFINED'


@dataclass
class CcdStatus:
    status: CcdStatusEnum = CcdStatusEnum.OFF,
    temperature: float = 0,
    power_percentage: float = 0


@dataclass
class FocuserStatus:
    temperature: float = 0,
    position: float = 0


@dataclass
class RotatorStatus:
    sky_pa: float = 0,
    rotator_pa: float = 0,
    is_rotating: bool = False


@dataclass
class MountInfo:
    ra: str = '00:00:00'
    dec: str = '0°0\'0"'
    ra_j2000: str = '00:00:00'
    dec_j2000: str = '0°00\'00"'
    az: str = '0°00\'00"'
    alt: str = '0°00\'00"'
    pier: str = 'N/A'


@dataclass
class DeviceConnectedInfo:
    setup_connected: bool = False
    camera_connected: bool = False
    mount_connected: bool = False
    focuser_connected: bool = False
    guide_connected: bool = False
    planetarium_connected: bool = False
    rotator_connected: bool = False


@dataclass
class DeviceStatusInfo:
    guide_status: GuideStatusEnum = GuideStatusEnum.STOPPED
    dither_status: DitherStatusEnum = DitherStatusEnum.STOPPED
    voyager_status: VoyagerStatusEnum = VoyagerStatusEnum.STOPPED
    ccd_status: CcdStatus = CcdStatus()
    mount_status: MountStatusEnum = MountStatusEnum.UNDEFINED
    focuser_status: FocuserStatus = FocuserStatus()
    rotator_status: RotatorStatus = RotatorStatus()


@dataclass
class SystemStatusInfo:
    drag_script_name: str = ''
    sequence_name: str = ''
    sequence_total_time_in_sec: int = 0
    sequence_elapsed_time_in_sec: int = 0
    mount_info: MountInfo = MountInfo()
    device_connection_info: DeviceConnectedInfo = DeviceConnectedInfo()
    device_status_info: DeviceStatusInfo = DeviceStatusInfo()
