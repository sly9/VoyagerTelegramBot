import datetime
import enum
from dataclasses import dataclass

cloud_cover_color_map = {100: '#FBFBFB',
                         90: '#EAEAEA',
                         80: '#C2C2C2',
                         70: '#AEEEEE',
                         60: '#9ADADA',
                         50: '#77B7F7',
                         40: '#63A3E3',
                         30: '#4F8FCF',
                         20: '#2767A7',
                         10: '#135393',
                         0: '#003F7F'}
seeing_color_map = {0: '#F9F9F9',
                    1: '#C7C7C7',
                    2: '#95D5D5',
                    3: '#63A3E3',
                    4: '#2C6CAC',
                    5: '#003F7F'}

transparency_color_map = {5: '#F9F9F9',
                          4: '#C7C7C7',
                          3: '#95D5D5',
                          2: '#63A3E3',
                          1: '#2C6CAC',
                          0: '#003F7F'}


class Transparency(enum.IntEnum):
    TRANSPARENT = 0
    ABOVE_AVERAGE = 1
    AVERAGE = 2
    BELOW_AVERAGE = 3
    POOR = 4
    TOO_CLOUDY_TO_FORECAST = 5


class Seeing(enum.IntEnum):
    EXCELLENT = 5
    GOOD = 4
    AVERAGE = 3
    POOR = 2
    BAD = 1
    TOO_CLOUDY_TO_FORECAST = 0


class WindSpeed(enum.IntEnum):
    ZERO_TO_FIVE = 0
    SIX_TO_ELEVEN = 1
    TWELVE_TO_SIXTEEN = 2
    SEVENTEEN_TO_TWENTY_EIGHT = 3
    TWENTY_NINE_TO_FORTY_FIVE = 4
    LARGER_THAN_FORTY_FIVE = 5


@dataclass
class ClearDarkSkyDataPoint:
    time: datetime.datetime = datetime.datetime.now()

    local_hour: int = -1
    utc_hour: int = -1

    cloud_cover_percentage: int = -1  # Negative number means Overcast
    transparency: Transparency = Transparency.TRANSPARENT
    seeing: Seeing = Seeing.TOO_CLOUDY_TO_FORECAST

    # darkness_limiting_magnitude: float = -100.0

    smoke_level_in_ug_m3: int = 0
    wind_speed: int = 0

    def __repr__(self):
        return f'[ClearDarkSkyDataPoint {self.local_hour}:00 CloudCover: ' \
               f'{self.cloud_cover_percentage}%, Transparency: {self.transparency}, Seeing: {self.seeing}]'
