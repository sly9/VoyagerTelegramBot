import enum


class ImageTypeEnum(enum.IntEnum):
    LIGHT = 0
    BIAS = 1
    DARK = 2
    FLAT = 3


class FitTypeEnum(enum.Enum):
    TEST = 'TEST'
    SHOT = 'SHOT'
    SYNC = 'SYNC'
