from dataclasses import dataclass

weather_id_text_mapping = {
    801: 'Few clouds',
    802: 'Scattered clouds',

}


@dataclass
class FreeWeatherDataPoint:
    dt: int = 0
    temperature: int = 0
    weather_id: int = 0
    cloud_cover_percentage: int = -1
    humidity: int = 0
    dew_point: int = 0
    wind_speed: int = 0
