import json
import time
from datetime import datetime

import pytz
from rich import pretty

from configs import class_from_dict
from data_structure.free_weather import FreeWeatherDataPoint
from utils.forecast.base_forecast import BaseForecast


class OpenWeatherForecast(BaseForecast):
    def __init__(self, config: object):
        super().__init__(config=config)

    def get_api_url(self) -> str:
        if not self.api_url:
            # Concatenate URL for API call based on configuration
            if not self.config.observing_condition_config:
                self.key = ''
                self.api_url = ''
                return self.api_url

            observing_config = self.config.observing_condition_config
            if not hasattr(observing_config, 'open_weather_api_key'):
                self.key = ''
                self.api_url = ''
                return self.api_url

            self.key = observing_config.open_weather_api_key
            lat = 0
            lon = 0
            if hasattr(observing_config, 'latitude'):
                lat = observing_config.latitude
            if hasattr(observing_config, 'longitude'):
                lon = observing_config.longitude
            self.api_url = 'https://api.openweathermap.org/data/2.5/onecall?' + \
                           f'lat={lat}&lon={lon}&appid={self.key}&units=metric' + \
                           '&exclude=minutely,daily,alerts'

        return self.api_url

    def parse_response(self, raw_response: str = None):
        if not raw_response:
            return
        json_response = json.loads(raw_response)
        if 'hourly' not in json_response:
            # response is not from 'onecall' API
            return

        hourly_forecast_records = json_response['hourly']
        for hourly_record in hourly_forecast_records:
            data_point = FreeWeatherDataPoint(
                temperature=hourly_record['temp'],
                weather_id=hourly_record['weather'][0]['id'],
                cloud_cover_percentage=hourly_record['clouds'],
                humidity=hourly_record['humidity'],
                dew_point=hourly_record['dew_point'],
                wind_speed=hourly_record['wind_speed']
            )
            self.forecast.append(data_point)


if __name__ == '__main__':
    config = {
        'observing_condition_config': {
            'open_weather_api_key': '',
            'latitude': 0,
            'longitude': 0},
        'timezone': 'America/Los_Angeles'}
    config = class_from_dict('Configs', config)()
    pretty.install()
    c = OpenWeatherForecast(config=config)
    c.maybe_update_forecast()  # 'SanJoseCAkey')
    print(c.forecast)

    timezone = pytz.timezone('America/Los_Angeles')
    now = datetime.now(tz=timezone)
    time.sleep(5)
    now1 = datetime.now(tz=timezone)
    diff = now1 - now
    print(diff)
