import datetime
import re
import time
from collections import deque

import pytz
import requests
from bs4 import BeautifulSoup
from rich import pretty

from data_structure.clear_dark_sky import ClearDarkSkyDataPoint, Transparency, Seeing, WindSpeed


class ClearDarkSkyForecast:
    def __init__(self, config: object):
        self.forecast = list()  # type: List[ClearDarkSkyDataPoint]
        self.config = config
        self.timezone = pytz.timezone(self.config.timezone)
        self.last_updated_time = None  # type: datetime.datetime
        self.key = 'RnhHdlAZkey'
        self.determine_key()

    def determine_key(self):
        if not self.config.observing_condition_config:
            self.key = 'RnhHdlAZkey'
            return
        config = self.config.observing_condition_config
        if hasattr(config, 'clear_dark_sky_key'):
            self.key = config.clear_dark_sky_key
        elif hasattr(config, 'latitude') and hasattr(config, 'longitude'):
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            }
            find_result = requests.get(
                f'http://www.cleardarksky.com/cgi-bin/find_chart.py?type=llmap&Mn=telescope%2520accessory&olat={config.latitude}&olong={config.longitude}&olatd=&olatm=&olongd=&olongm=&unit=1',
                headers=headers)
            if find_result.status_code != 200:
                print(f'failed to search for {config.latitude}x{config.latitude}')
            soup = BeautifulSoup(find_result.text, 'html.parser')
            links = soup.select('tr td>a')
            link = links[0].get('href').replace('../c/', '')
            self.key = re.sub(r'\.html.*$', '', link)
        else:
            self.key = 'RnhHdlAZkey'

    def parse_html_response(self, html_string: str):
        soup = BeautifulSoup(html_string, 'html.parser')
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

        current_hour_seen = False
        now = datetime.datetime.now(tz=self.timezone)
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
            # if not current_hour_seen and datapoint.local_hour == now.hour:
            #     current_hour_seen = True
            # if current_hour_seen:
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
        if cloud_cover == 'clear':
            datapoint.cloud_cover_percentage = 0
        elif cloud_cover == 'overcast':
            datapoint.cloud_cover_percentage = 100
        else:
            datapoint.cloud_cover_percentage = int(cloud_cover[:2])

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
        elif seeing == 'excellent  5/5':
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
        elif wind == '>45 mph':
            datapoint.wind_speed = WindSpeed.LARGER_THAN_FORTY_FIVE

        return datapoint

    def update_forecast(self):
        # http://www.cleardarksky.com/c/RnhHdlAZkey.html

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
        }

        response = requests.get(f'http://www.cleardarksky.com/c/{self.key}.html', headers=headers)
        if response.status_code != 200:
            print(f'Failed to fetch clear dark sky page: http://www.cleardarksky.com/c/{self.key}.html')
        self.parse_html_response(html_string=response.text)
        self.last_updated_time = datetime.datetime.now()

    def maybe_update_forecast(self):
        if self.last_updated_time and (
                datetime.datetime.now() - self.last_updated_time).total_seconds() < 3600:
            # recently updated, do nothing
            return
        self.update_forecast()


if __name__ == '__main__':
    pretty.install()
    c = ClearDarkSkyForecast()
    c.maybe_update_forecast()  # 'SanJoseCAkey')
    print(c.forecast)

    timezone = pytz.timezone('America/New_York')
    now = datetime.datetime.now(tz=timezone)
    time.sleep(5)
    now1 = datetime.datetime.now(tz=timezone)
    diff = now1 - now
    print(diff)
