from abc import abstractmethod
from datetime import datetime

import pytz
import requests

FORECAST_HEADER = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
}


class BaseHttpForecast:
    def __init__(self, config: object):
        self.service_name = ''
        self.forecast = list()
        self.config = config
        self.timezone = pytz.timezone(self.config.timezone)
        self.last_updated_time = None  # type: datetime.datetime
        self.key = None
        self.api_url = None

    @abstractmethod
    def get_api_url(self) -> str:
        return ''

    @abstractmethod
    def parse_response(self, raw_response: str = None):
        return

    def update_forecast(self):
        if self.get_api_url() == '':
            print('Fail to generate API URL')
            return

        response = requests.get(self.get_api_url(), headers=FORECAST_HEADER)
        if response.status_code != 200:
            print(f'Failed to fetch data from: {self.get_api_url()}')
        self.parse_response(raw_response=response.text)
        self.last_updated_time = datetime.now()

    def maybe_update_forecast(self):
        if self.last_updated_time and (
                datetime.now() - self.last_updated_time).total_seconds() < 3600:
            # recently updated, do nothing
            return
        self.update_forecast()


class BaseAlgorithmForecast:
    def __init__(self, config: object):
        self.service_name = ''
        self.forecast = None
        self.config = config
        self.timezone = pytz.timezone(self.config.timezone)
        self.last_updated_time = None  # type: datetime.datetime

    def update_forecast(self):
        self.last_updated_time = datetime.now()

    def maybe_update_forecast(self):
        if self.last_updated_time and (
                datetime.now() - self.last_updated_time).total_seconds() < 3600:
            # recently updated, do nothing
            return
        self.update_forecast()
