import datetime
import re
import time
from collections import deque

import pytz
import requests
from bs4 import BeautifulSoup
from rich import pretty

from configs import class_from_dict
from data_structure.clear_dark_sky import ClearDarkSkyDataPoint, Transparency, Seeing, WindSpeed, CloudCover, \
    Temperature
from utils.forecast.base_forecast import BaseHttpForecast, FORECAST_HEADER


class ClearDarkSkyForecast(BaseHttpForecast):
    def __init__(self, config: object):
        super().__init__(config=config)
        self.title = ''
        self.service_name = 'ClearDarkSky'

    def get_api_url(self) -> str:
        self.determine_key()
        self.api_url = f'http://www.cleardarksky.com/c/{self.key}.html'

        return self.api_url

    def determine_key(self):
        if not self.config.observing_condition_config:
            self.key = 'RnhHdlAZkey'
            return
        config = self.config.observing_condition_config
        if hasattr(config, 'clear_dark_sky_key'):
            self.key = config.clear_dark_sky_key
        elif hasattr(config, 'latitude') and hasattr(config, 'longitude'):
            find_result = requests.get(
                f'http://www.cleardarksky.com/cgi-bin/find_chart.py?' + \
                f'type=llmap&Mn=telescope%2520accessory&olat={config.latitude}&olong={config.longitude}' + \
                f'&olatd=&olatm=&olongd=&olongm=&unit=1',
                headers=FORECAST_HEADER)
            if find_result.status_code != 200:
                print(f'failed to search for {config.latitude}x{config.latitude}')
            soup = BeautifulSoup(find_result.text, 'html.parser')
            links = soup.select('tr td>a')
            link = links[0].get('href').replace('../c/', '')
            self.key = re.sub(r'\.html.*$', '', link)
        else:
            self.key = 'RnhHdlAZkey'

    def parse_response(self, raw_response: str = None):
        soup = BeautifulSoup(raw_response, 'html.parser')

        header = soup.select('h1')
        if len(header):
            h1 = header[0]
            if h1.contents:
                self.title = h1.contents[0]

        areas = soup.select('map area')
        area_dict = dict()
        for area in areas:
            x, y, x1, y1 = [int(x) for x in area.get('coords').split(',')]
            if x == 0 or x1 - x < 10:
                # weird area tag, skip it
                continue
            if y not in area_dict:
                area_dict[y] = deque()
            area_dict[y].append((x, y, x1, y1, area.get('title')))
        cloud_cover_queue = area_dict.get(77)
        transparency_queue = area_dict.get(93)
        seeing_queue = area_dict.get(109)
        smoke_queue = area_dict.get(173)
        wind_queue = area_dict.get(189)
        humidity_queue = area_dict.get(205)
        temperature_queue = area_dict.get(221)

        while cloud_cover_queue and transparency_queue and seeing_queue and smoke_queue and wind_queue and humidity_queue and temperature_queue:
            cloud_cover_string = cloud_cover_queue.popleft()[4]
            transparency_string = transparency_queue.popleft()[4]
            seeing_string = seeing_queue.popleft()[4]
            smoke_string = smoke_queue.popleft()[4]
            wind_string = wind_queue.popleft()[4]
            humidity_string = humidity_queue.popleft()[4]
            temperature_string = temperature_queue.popleft()[4]
            datapoint = self.parse_record(cloud_cover_string=cloud_cover_string,
                                          transparency_string=transparency_string, seeing_string=seeing_string,
                                          smoke_string=smoke_string, wind_string=wind_string,
                                          humidity_string=humidity_string, temperature_string=temperature_string)
            self.forecast.append(datapoint)

    def parse_record(self, cloud_cover_string: str, transparency_string: str,
                     seeing_string: str, smoke_string: str, wind_string: str,
                     humidity_string: str, temperature_string: str):
        datapoint = ClearDarkSkyDataPoint()

        local_hour = int(cloud_cover_string[:cloud_cover_string.index(':')])
        datapoint.local_hour = local_hour

        # timezoned_hour_str = cloud_cover_string[cloud_cover_string.index('(') + 1:cloud_cover_string.index(')')]

        # parse cloud cover
        cloud_cover = cloud_cover_string[
                      cloud_cover_string.rindex(':') + 1: cloud_cover_string.index('(')].strip().lower()
        if cloud_cover == 'overcast':
            datapoint.cloud_cover_percentage = CloudCover.OVER_CAST
        elif cloud_cover == '90% covered':
            datapoint.cloud_cover_percentage = CloudCover.NINETY_PERCENT
        elif cloud_cover == '80% covered':
            datapoint.cloud_cover_percentage = CloudCover.EIGHTY_PERCENT
        elif cloud_cover == '70% covered':
            datapoint.cloud_cover_percentage = CloudCover.SEVENTY_PERCENT
        elif cloud_cover == '60% covered':
            datapoint.cloud_cover_percentage = CloudCover.SIXTY_PERCENT
        elif cloud_cover == '50% covered':
            datapoint.cloud_cover_percentage = CloudCover.FIFTY_PERCENT
        elif cloud_cover == '40% covered':
            datapoint.cloud_cover_percentage = CloudCover.FORTY_PERCENT
        elif cloud_cover == '30% covered':
            datapoint.cloud_cover_percentage = CloudCover.THIRTY_PERCENT
        elif cloud_cover == '20% covered':
            datapoint.cloud_cover_percentage = CloudCover.TWENTY_PERCENT
        elif cloud_cover == '10% covered':
            datapoint.cloud_cover_percentage = CloudCover.TEN_PERCENT
        elif cloud_cover == 'clear':
            datapoint.cloud_cover_percentage = CloudCover.CLEAR
        else:
            print(f'Failed to parse cloud cover string {cloud_cover_string}')

        # parse transparency '9:00: Below Average (12Z+4hr)'
        transparency = transparency_string[
                       transparency_string.rindex(':') + 1:transparency_string.index('(')].strip().lower()
        if transparency == 'too cloudy to forecast':
            datapoint.transparency = Transparency.TOO_CLOUDY_TO_FORECAST
        elif transparency == 'poor':
            datapoint.transparency = Transparency.POOR
        elif transparency == 'below average':
            datapoint.transparency = Transparency.BELOW_AVERAGE
        elif transparency == 'average':
            datapoint.transparency = Transparency.AVERAGE
        elif transparency == 'above average':
            datapoint.transparency = Transparency.ABOVE_AVERAGE
        elif transparency == 'transparent':
            datapoint.transparency = Transparency.TRANSPARENT
        else:
            print(f'Failed to parse transparency string {transparency_string}')

        # parse seeing '9:00: Average 3/5 (12Z+3hr)'
        seeing = seeing_string[seeing_string.rindex(':') + 1:seeing_string.index('(')].strip().lower()
        if seeing == 'too cloudy to forecast':
            datapoint.seeing = Seeing.TOO_CLOUDY_TO_FORECAST
        elif seeing == 'bad 1/5':
            datapoint.seeing = Seeing.BAD
        elif seeing == 'poor 2/5':
            datapoint.seeing = Seeing.POOR
        elif seeing == 'average 3/5':
            datapoint.seeing = Seeing.AVERAGE
        elif seeing == 'good 4/5':
            datapoint.seeing = Seeing.GOOD
        elif seeing == 'excellent 5/5':
            datapoint.seeing = Seeing.EXCELLENT
        else:
            print(f'Failed to parse seeing string {seeing_string}')

        # smoke
        smoke = smoke_string[smoke_string.rindex(':') + 1:smoke_string.index('(')].strip()
        if smoke == 'No Smoke':
            datapoint.smoke_level_in_ug_m3 = 0
        else:
            datapoint.smoke_level_in_ug_m3 = int(smoke.replace('ug/m^3', ''))

        # wind
        wind = wind_string[wind_string.rindex(':') + 1:wind_string.index('(')].strip()
        if wind == '0 to 5 mph':
            datapoint.wind_speed = WindSpeed.ZERO_TO_FIVE
        elif wind == '6 to 11 mph':
            datapoint.wind_speed = WindSpeed.SIX_TO_ELEVEN
        elif wind == '12 to 16 mph':
            datapoint.wind_speed = WindSpeed.TWELVE_TO_SIXTEEN
        elif wind == '17 to 28 mph':
            datapoint.wind_speed = WindSpeed.SEVENTEEN_TO_TWENTY_EIGHT
        elif wind == '29 to 45 mph':
            datapoint.wind_speed = WindSpeed.TWENTY_NINE_TO_FORTY_FIVE
        elif wind == '>45 mph':
            datapoint.wind_speed = WindSpeed.LARGER_THAN_FORTY_FIVE
        else:
            print(f'Failed to parse wind string {wind_string}')

        # temperature
        temperature = temperature_string[temperature_string.rindex(':') + 1:temperature_string.index('(')].strip()
        if temperature == '<-40F':
            datapoint.temperature = Temperature.LESS_THAN_NEG_40
        elif temperature == '-40F to -31F':
            datapoint.temperature = Temperature.NEG_40_TO_NEG_31
        elif temperature == '-30F to -21F':
            datapoint.temperature = Temperature.NEG_30_TO_NEG_21
        elif temperature == '-21F to -12F':
            datapoint.temperature = Temperature.NEG_21_TO_NEG_12
        elif temperature == '-12F to -3F':
            datapoint.temperature = Temperature.NEG_12_TO_NEG_3
        elif temperature == '-3F to 5F':
            datapoint.temperature = Temperature.NEG_3_TO_5
        elif temperature == '5F to 14F':
            datapoint.temperature = Temperature.POS_5_TO_14
        elif temperature == '14F to 23F':
            datapoint.temperature = Temperature.POS_14_TO_23
        elif temperature == '23F to 32F':
            datapoint.temperature = Temperature.POS_23_TO_32
        elif temperature == '32F to 41F':
            datapoint.temperature = Temperature.POS_32_TO_41
        elif temperature == '41F to 50F':
            datapoint.temperature = Temperature.POS_41_TO_50
        elif temperature == '50F to 59F':
            datapoint.temperature = Temperature.POS_50_TO_59
        elif temperature == '59F to 68F':
            datapoint.temperature = Temperature.POS_59_TO_68
        elif temperature == '68F to 77F':
            datapoint.temperature = Temperature.POS_68_TO_77
        elif temperature == '77F to 86F':
            datapoint.temperature = Temperature.POS_77_TO_86
        elif temperature == '86F to 95F':
            datapoint.temperature = Temperature.POS_86_TO_95
        elif temperature == '95F to 104F':
            datapoint.temperature = Temperature.POS_95_TO_104
        elif temperature == '104F to 113F':
            datapoint.temperature = Temperature.POS_104_TO_113
        elif temperature == '>113F':
            datapoint.temperature = Temperature.LARGER_THAN_113
        else:
            print(f'Failed to parse temperature string {temperature_string}')
        return datapoint


if __name__ == '__main__':
    config = {
        'observing_condition_config': {
            'clear_dark_sky_key': 'RssCrkObCAkey',
            'latitude': 0,
            'longitude': 0},
        'timezone': 'America/Los_Angeles'}
    config = class_from_dict('Configs', config)()
    pretty.install()
    c = ClearDarkSkyForecast(config=config)
    c.maybe_update_forecast()  # 'SanJoseCAkey')
    print(c.forecast)

    timezone = pytz.timezone('America/New_York')
    now = datetime.datetime.now(tz=timezone)
    time.sleep(5)
    now1 = datetime.datetime.now(tz=timezone)
    diff = now1 - now
    print(diff)
