from typing import Dict
from enum import Enum, IntEnum
import os


class SkyCondition(Enum):
    # See https://diffractionlimited.com/wp-content/uploads/2016/04/Cloud-SensorII-Users-Manual.pdf on pp.45(V0029)
    CLOUD = 'c'
    WIND = 'w'
    RAIN = 'r'
    DAYLIGHT = 'd'
    ROOF = 'C'
    ALERT = 'A'


class CloudCondition(Enum):
    # See https://diffractionlimited.com/wp-content/uploads/2016/04/Cloud-SensorII-Users-Manual.pdf on pp.48(V0029)
    UNKNOWN = 0
    CLEAR = 1
    CLOUDY = 2
    V_CLOUDY = 3


class WindCondition(Enum):
    # See https://diffractionlimited.com/wp-content/uploads/2016/04/Cloud-SensorII-Users-Manual.pdf on pp.49(V0029)
    UNKNOWN = 0
    CALM = 1
    WINDY = 2
    V_WINDY = 3


class RainCondition(Enum):
    # See https://diffractionlimited.com/wp-content/uploads/2016/04/Cloud-SensorII-Users-Manual.pdf on pp.49(V0029)
    UNKNOWN = 0
    DRY = 1
    WET = 2
    RAIN = 3


class DayCondition(Enum):
    # See https://diffractionlimited.com/wp-content/uploads/2016/04/Cloud-SensorII-Users-Manual.pdf on pp.49(V0029)
    UNKNOWN = 0
    DARK = 1
    LIGHT = 2
    V_LIGHT = 3


class RoofCondition(Enum):
    # See https://diffractionlimited.com/wp-content/uploads/2016/04/Cloud-SensorII-Users-Manual.pdf on pp.45(V0029)
    NOT_REQUESTED = 0
    REQUESTED = 1


class AlertCondition(Enum):
    # See https://diffractionlimited.com/wp-content/uploads/2016/04/Cloud-SensorII-Users-Manual.pdf on pp.45(V0029)
    SAFE = 0
    UNSAFE = 1


def get_weather_conditions(file_path: str = '') -> Dict[SkyCondition, int]:
    sky_conditions = dict()

    sky_conditions[SkyCondition.CLOUD] = CloudCondition.UNKNOWN.value
    sky_conditions[SkyCondition.WIND] = WindCondition.UNKNOWN.value
    sky_conditions[SkyCondition.RAIN] = RainCondition.UNKNOWN.value
    sky_conditions[SkyCondition.DAYLIGHT] = DayCondition.UNKNOWN.value
    sky_conditions[SkyCondition.ROOF] = RoofCondition.NOT_REQUESTED.value
    sky_conditions[SkyCondition.ALERT] = AlertCondition.SAFE.value

    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        return sky_conditions

    try:
        with open(file_path, 'r') as sky_file:
            conditions = sky_file.readline().rsplit(sep=' ', maxsplit=7)

            if len(conditions) < 7:
                return sky_conditions

            sky_conditions[SkyCondition.CLOUD] = int(conditions[-6])
            sky_conditions[SkyCondition.WIND] = int(conditions[-5])
            sky_conditions[SkyCondition.RAIN] = int(conditions[-4])
            sky_conditions[SkyCondition.DAYLIGHT] = int(conditions[-3])
            sky_conditions[SkyCondition.ROOF] = int(conditions[-2])
            sky_conditions[SkyCondition.ALERT] = int(conditions[-1])
    except PermissionError:
        pass
    return sky_conditions


def get_roof_condition(file_path: str = '') -> str:
    roof_condition = 'UNKNOWN'
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        return roof_condition
    try:
        with open(file_path, 'r') as sky_file:
            conditions = sky_file.readline().rsplit(sep=':', maxsplit=2)

            if len(conditions) < 2:
                return roof_condition

            roof_condition = conditions[-1].strip()
    except PermissionError:
        pass
    return roof_condition
