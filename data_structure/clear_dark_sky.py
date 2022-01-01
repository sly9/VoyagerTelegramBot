import datetime
import enum
from dataclasses import dataclass


class CloudCover(enum.Enum):
    OVER_CAST = '#FBFBFB'
    NINETY_PERCENT = '#EAEAEA'
    EIGHTY_PERCENT = '#C2C2C2'
    SEVENTY_PERCENT = '#AEEEEE'
    SIXTY_PERCENT = '#9ADADA'
    FIFTY_PERCENT = '#77B7F7'
    FORTY_PERCENT = '#63A3E3'
    THIRTY_PERCENT = '#4F8FCF'
    TWENTY_PERCENT = '#2767A7'
    TEN_PERCENT = '#135393'
    CLEAR = '#003F7F'


class Transparency(enum.Enum):
    TRANSPARENT = '#003F7F'
    ABOVE_AVERAGE = '#2C6CAC'
    AVERAGE = '#63A3E3'
    BELOW_AVERAGE = '#95D5D5'
    POOR = '#C7C7C7'
    TOO_CLOUDY_TO_FORECAST = '#F9F9F9'


class Seeing(enum.Enum):
    EXCELLENT = '#003F7F'
    GOOD = '#2C6CAC'
    AVERAGE = '#63A3E3'
    POOR = '#95D5D5'
    BAD = '#C7C7C7'
    TOO_CLOUDY_TO_FORECAST = '#F9F9F9'


class WindSpeed(enum.Enum):
    ZERO_TO_FIVE = '#003F7F'
    SIX_TO_ELEVEN = '#2C6CAC'
    TWELVE_TO_SIXTEEN = '#63A3E3'
    SEVENTEEN_TO_TWENTY_EIGHT = '#95D5D5'
    TWENTY_NINE_TO_FORTY_FIVE = '#C7C7C7'
    LARGER_THAN_FORTY_FIVE = '#F9F9F9'


class Temperature(enum.Enum):
    LESS_THAN_NEG_40 = '#FC00FC'
    NEG_40_TO_NEG_31 = '#000085'
    NEG_30_TO_NEG_21 = '#0000B2'
    NEG_21_TO_NEG_12 = '#0000EC'
    NEG_12_TO_NEG_3 = '#0034FE'
    NEG_3_TO_5 = '#0089FE'
    POS_5_TO_14 = '#00D4FE'
    POS_14_TO_23 = '#1EFEDE'
    POS_23_TO_32 = '#FBFBFB'
    POS_32_TO_41 = '#5EFE9E'
    POS_41_TO_50 = '#A2FE5A'
    POS_50_TO_59 = '#FEDE00'
    POS_59_TO_68 = '#FE9E00'
    POS_68_TO_77 = '#FE5A00'
    POS_77_TO_86 = '#FE1E00'
    POS_86_TO_95 = '#E20000'
    POS_95_TO_104 = '#A90000'
    POS_104_TO_113 = '#7E0000'
    LARGER_THAN_113 = '#C6C6C6'


@dataclass
class ClearDarkSkyDataPoint:
    time: datetime.datetime = datetime.datetime.now()

    local_hour: int = -1
    utc_hour: int = -1

    cloud_cover_percentage: CloudCover = CloudCover.CLEAR  # Negative number means Overcast
    transparency: Transparency = Transparency.TRANSPARENT
    seeing: Seeing = Seeing.EXCELLENT

    # darkness_limiting_magnitude: float = -100.0

    smoke_level_in_ug_m3: int = 0
    wind_speed: WindSpeed = WindSpeed.ZERO_TO_FIVE
    temperature: Temperature = Temperature.LESS_THAN_NEG_40

    def __repr__(self):
        return f'[ClearDarkSkyDataPoint {self.local_hour}:00 CloudCover: ' \
               f'{self.cloud_cover_percentage}%, Transparency: {self.transparency}, Seeing: {self.seeing}]'
