from dataclasses import dataclass


@dataclass
class WeatherSafety:
    old_status: str = ''# RESUME, SUSPEND, EXIT
    status: str='' # RESUME, SUSPEND, EXIT
    source: str = '' # S, SW, W, or empty
    cloud: str = '' # CLEAR, CLOUDY, VERY_CLOUDY
    wind: str = '' # CALM, WINDY, VERY_WINDY
    rain: str = ''# RAIN, DRY
    light: str = '' # DARK, LIGHT, VERY_LIGHT
    roof: str = '' # CLOSED, OPEN
    read: str = '' # OK, OLD, TIMEOUT, n.d. (???)
    weather_station_connected: bool = True
    safe_monitor_connected: bool = True
    safe_monitor_status: str = ''