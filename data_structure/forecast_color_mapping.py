def get_temperature_color(temperature: float = 0.0) -> str:
    if temperature < -40.00:
        return '#FC00FC'
    elif -40.00 <= temperature < -35.00:
        return '#000085'
    elif -35.00 <= temperature < -30.00:
        return '#0000B2'
    elif -30.00 <= temperature < -25.00:
        return '#0000EC'
    elif -25.00 <= temperature < -20.00:
        return '#0034FE'
    elif -20.00 <= temperature < -15.00:
        return '#0089FE'
    elif -15.00 <= temperature < -10.00:
        return '#00D4FE'
    elif -10.00 <= temperature < -5.00:
        return '#1EFEDE'
    elif -5.00 <= temperature < 0.00:
        return '#FBFBFB'
    elif 0.00 <= temperature < 5.00:
        return '#5EFE9E'
    elif 5.00 <= temperature < 10.00:
        return '#A2FE5A'
    elif 10.00 <= temperature < 15.00:
        return '#FEDE00'
    elif 15.00 <= temperature < 20.00:
        return '#FE9E00'
    elif 20.00 <= temperature < 25.00:
        return '#FE5A00'
    elif 25.00 <= temperature < 30.00:
        return '#FE1E00'
    elif 30.00 <= temperature < 35.00:
        return '#E20000'
    elif 35.00 <= temperature < 40.00:
        return '#A90000'
    elif 40.00 <= temperature < 45.00:
        return '#7E0000'
    else:
        return '#C6C6C6'


def get_humidity_color(humidity: float = 0.0) -> str:
    if humidity >= 95:
        return '#E10000'
    elif 90 <= humidity < 95:
        return '#B70000'
    elif 85 <= humidity < 90:
        return '#EA0000'
    elif 80 <= humidity < 85:
        return '#FE3401'
    elif 75 <= humidity < 80:
        return '#FC8602'
    elif 70 <= humidity < 75:
        return '#FEC600'
    elif 65 <= humidity < 70:
        return '#EAFB16'
    elif 60 <= humidity < 65:
        return '#94FE6A'
    elif 55 <= humidity < 60:
        return '#55FAAD'
    elif 50 <= humidity < 55:
        return '#09FEED'
    elif 45 <= humidity < 50:
        return '#80C0C0'
    elif 40 <= humidity < 45:
        return '#71B1F1'
    elif 35 <= humidity < 40:
        return '#4E8ECE'
    elif 30 <= humidity < 35:
        return '#3070B0'
    elif 25 <= humidity < 30:
        return '#0D4D8D'
    else:
        return '#08035D'


def get_cloud_cover_color(cloud_cover: int = 0) -> str:
    if cloud_cover < 10:
        return '#003F7F'
    elif 10 <= cloud_cover < 20:
        return '#135393'
    elif 20 <= cloud_cover < 30:
        return '#2767A7'
    elif 30 <= cloud_cover < 40:
        return '#4F8FCF'
    elif 40 <= cloud_cover < 50:
        return '#63A3E3'
    elif 50 <= cloud_cover < 60:
        return '#77B7F7'
    elif 60 <= cloud_cover < 0:
        return '#9ADADA'
    elif 70 <= cloud_cover < 70:
        return '#AEEEEE'
    elif 80 <= cloud_cover < 80:
        return '#C2C2C2'
    elif 90 <= cloud_cover < 90:
        return '#EAEAEA'
    else:
        return '#FBFBFB'


def get_wind_speed_color(wind_speed: float = 0.0) -> str:
    if 0 <= wind_speed < 5:
        return '#003F7F'
    elif 5 <= wind_speed < 11:
        return '#2C6CAC'
    elif 11 <= wind_speed < 16:
        return '#63A3E3'
    elif 16 <= wind_speed < 28:
        return '#95D5D5'
    elif 28 <= wind_speed < 45:
        return '#C7C7C7'
    else:
        return '#F9F9F9'


def get_sky_condition_bg_color(value: int = 0) -> str:
    if value == 0:
        # UNKNOWN
        return '#4285F4'
    elif value == 1:
        # CloudCondition.CLEAR, WindCondition.CALM, RainCondition.DRY, DayCondition.DARK
        return '#0F9D58'
    elif value == 2:
        # CloudCondition.CLOUDY, WindCondition.WINDY, RainCondition.WET, DayCondition.LIGHT
        return '#F4B400'
    elif value == 3:
        # CloudCondition.VERY_CLOUDY, WindCondition.VERY_WINDY, RainCondition.RAIN, DayCondition.VERY_LIGHT
        return '#DB4437'

    return '#000000'


def get_alert_bg_color(value: int = 0) -> str:
    if value == 0:
        # SAFE
        return '#0F9D58'
    elif value == 1:
        # UNSAFE
        return '#DB4437'

    return '#000000'


def get_roof_condition_bg_color(value: str = '') -> str:
    if value == 'OPEN':
        return '#0F9D58'
    elif value == 'CLOSED':
        return '#DB4437'

    return '#000000'
