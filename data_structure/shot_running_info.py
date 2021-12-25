import enum
from dataclasses import dataclass


class ShotRunningStatus(enum.IntEnum):
    IDLE = 0  # No Exposure
    EXPOSE = 1  # Exposing
    DOWNLOAD = 2  # Download running from camera to PC
    WAIT_JPG = 3  # Process to create a JPG file for Dashboard is running, will finish with a NewJPGReady message
    ERROR = 4  # Camera Error, shot is ab


@dataclass
class ShotRunningInfo:
    filename: str = 'UNKNOWN.FIT'
    total_exposure: float = 0
    elapsed_exposure: float = 0
    elapsed_percentage: float = 0
    status: ShotRunningStatus = ShotRunningStatus.IDLE
