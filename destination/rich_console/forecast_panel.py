import math
from datetime import datetime, timezone

import pytz
from rich.align import Align
from rich.console import RenderResult, Console, ConsoleOptions
from rich.layout import Layout
from rich.panel import Panel
from rich.style import StyleType
from rich.table import Table
from rich.text import Text

from data_structure.forecast_color_mapping import get_temperature_color, get_humidity_color, get_cloud_cover_color, \
    get_wind_speed_color
from utils.forecast.clear_dark_sky_forecast import ClearDarkSkyForecast
from utils.forecast.open_weather_forecast import OpenWeatherForecast
from utils.sun_and_moon import SunAndMoon


class ForecastPanel:
    def __init__(self, config: object, layout: Layout, style: StyleType = "") -> None:
        self.config = config
        self.layout = layout
        self.style = style
        self.table = None

        self.clear_dark_sky_forecast = ClearDarkSkyForecast(config=config)
        self.open_weather_forecast = None

        if hasattr(config.observing_condition_config, 'forecast_service') and 'OpenWeather' in config.observing_condition_config.forecast_service:
            self.open_weather_forecast = OpenWeatherForecast(config=config)

        self.clear_dark_sky_forecast.maybe_update_forecast()
        if self.open_weather_forecast:
            self.open_weather_forecast.maybe_update_forecast()

        self.sun_moon = SunAndMoon(latitude=config.observing_condition_config.latitude,
                                   longitude=config.observing_condition_config.longitude)

        self.current_service =  self.clear_dark_sky_forecast
        self.timestamp_since_changing_table = datetime.now()

    def clear_sky_table(self, height: int = 8, width: int = 20) -> Table:
        forecast_table = Table.grid(padding=(0, 0), expand=False)
        forecast_table.add_column(style='bold')

        length = min(len(self.clear_dark_sky_forecast.forecast), int(math.floor((width - 2 - 2 - 7) / 2)), 12)

        for i in range(length - 1):
            forecast_table.add_column(width=2, max_width=2)

        hour_list = ['Hour']
        seeing_list = ['Seeing']
        cloud_cover_list = ['Cloud']
        transparency_list = ['Transp ']
        wind_list = ['Wind S']
        temperature_list = ['Temp']

        # find the right index to blink:
        right_index_to_blink = 0
        time_zone = pytz.timezone(self.config.timezone)
        now = datetime.now(tz=time_zone)
        for i in range(min(length, 23)):
            forecast = self.clear_dark_sky_forecast.forecast[i]
            if now.hour == forecast.local_hour:
                right_index_to_blink = i

        for i in range(length):
            forecast = self.clear_dark_sky_forecast.forecast[i]
            style_string = 'grey62'
            place_holder_string = '  '
            if i % 2 == 0:
                style_string = 'bright_white'
            if i == right_index_to_blink:
                style_string += ' blink'
                place_holder_string = '●'
            hour_list.append(Text(f'{forecast.local_hour:02}', style=style_string))
            seeing_list.append(Text(place_holder_string, style=f'red on {forecast.seeing.value}'))
            cloud_cover_list.append(Text(place_holder_string, style=f'red on {forecast.cloud_cover_percentage.value}'))
            transparency_list.append(Text(place_holder_string, style=f'red on {forecast.transparency.value}'))
            wind_list.append(Text(place_holder_string, style=f'red on {forecast.wind_speed.value}'))
            temperature_list.append(Text(place_holder_string, style=f'red on {forecast.temperature.value}'))

        forecast_table.add_row(*hour_list)
        forecast_table.add_row(*seeing_list)
        forecast_table.add_row(*cloud_cover_list)
        forecast_table.add_row(*transparency_list)
        forecast_table.add_row(*wind_list)
        forecast_table.add_row(*temperature_list)
        return forecast_table

    def open_weather_table(self, height: int = 8, width: int = 20) -> Table:
        forecast_table = Table.grid(padding=(0, 0), expand=False)
        forecast_table.add_column(style='bold')

        length = min(len(self.open_weather_forecast.forecast), 12)

        if length > 0:
            # Column to explicitly show current condition
            forecast_table.add_column(justify='right')
        for i in range(1, length):
            forecast_table.add_column(width=2, max_width=2)  # Fit -99 ~ 100

        hour_list = ['Hour']
        temperature_list = ['Temperature ']
        dew_list = ['Dew Point']
        humidity_list = ['Humidity']
        cloud_cover_list = ['Cloud']
        wind_speed_list = ['Wind']
        # weather_list = ['Weather ']

        if length > 0:
            forecast = self.forecast_service.forecast[0]
            # Explicitly show current condition

            hour_list.append(Text('Now ', style='white on black'))

            color_string = get_temperature_color(forecast.temperature)
            temperature_list.append(Text(str(forecast.temperature) + '°C', style=f'black on {color_string}'))

            color_string = get_temperature_color(forecast.dew_point)
            dew_list.append(Text(str(forecast.dew_point) + '°C', style=f'black on {color_string}'))

            color_string = get_humidity_color(forecast.humidity)
            humidity_list.append(Text(str(forecast.humidity) + '%', style=f'black on {color_string}'))

            color_string = get_cloud_cover_color(forecast.cloud_cover_percentage)
            cloud_cover_list.append(Text(str(forecast.cloud_cover_percentage) + '%', style=f'black on {color_string}'))

            # weather_list.append(Text(str(forecast.weather_id), style=style_string))

            color_string = get_wind_speed_color(forecast.wind_speed)
            wind_speed_list.append(Text(str(forecast.wind_speed) + 'm/s', style=f'black on {color_string}'))

        time_zone = pytz.timezone(self.config.timezone)
        for i in range(length):
            forecast = self.open_weather_forecast.forecast[i]
            style_string = 'grey62'
            if i % 2 == 0:
                style_string = 'bright_white'
            dt_object = datetime.utcfromtimestamp(forecast.dt)
            dt_object = dt_object.replace(tzinfo=timezone.utc).astimezone(tz=time_zone)

            hour = (dt_object.hour + i) % 24
            hour_list.append(Text(f'{hour:02}', style=style_string))

            color_string = get_temperature_color(forecast.temperature)
            temperature_list.append(Text('  ', style=f'{color_string} on {color_string}'))

            color_string = get_temperature_color(forecast.dew_point)
            dew_list.append(Text('  ', style=f'{color_string} on {color_string}'))

            color_string = get_humidity_color(forecast.humidity)
            humidity_list.append(Text('  ', style=f'{color_string} on {color_string}'))

            color_string = get_cloud_cover_color(forecast.cloud_cover_percentage)
            cloud_cover_list.append(Text('  ', style=f'{color_string} on {color_string}'))

            # weather_list.append(Text(str(forecast.weather_id), style=style_string))

            color_string = get_wind_speed_color(forecast.wind_speed)
            wind_speed_list.append(Text('  ', style=f'{color_string} on {color_string}'))

        forecast_table.add_row(*hour_list)
        forecast_table.add_row(*temperature_list)
        forecast_table.add_row(*dew_list)
        forecast_table.add_row(*humidity_list)
        forecast_table.add_row(*cloud_cover_list)
        # forecast_table.add_row(*weather_list)
        forecast_table.add_row(*wind_speed_list)

        return forecast_table

    def forecast_table(self, height: int = 8, width: int = 20) -> Table:
        if self.open_weather_forecast:
            self.open_weather_forecast.maybe_update_forecast()
        self.clear_dark_sky_forecast.maybe_update_forecast()

        now = datetime.now()
        if (now - self.timestamp_since_changing_table).total_seconds() < 8:
            if self.current_service == self.clear_dark_sky_forecast:
                return self.clear_sky_table(width=width, height=height)
            else:
                return self.open_weather_table(width=width, height=height)

        self.timestamp_since_changing_table = now
        if self.current_service == self.clear_dark_sky_forecast:
            self.current_service = self.open_weather_forecast
            return self.open_weather_table(width=width, height=height)
        else:
            self.current_service = self.clear_dark_sky_forecast
            return self.clear_sky_table(width=width, height=height)

    def sun_moon_table(self):
        observation = self.sun_moon.observe()  # type : SunAndMoonDataPoint
        table = Table.grid(padding=(0, 2), expand=False)

        def readable_time(time):
            return f'{time.hour}:{time.minute}'

        table.add_row('Summary', Text('Clear', style='white on green'), Text('Calm', style='white on green'),
                      Text('Dry', style='white on green'), Text('Dark', style='white on green'))
        table.add_row('☀', f'Alt {observation.sun_altitude:.1f}°', 'Set ' + readable_time(observation.sunset_localtime),
                      'Rise ' + readable_time(observation.sunrise_localtime))
        table.add_row(observation.moon_phase_emoji, f'Illum {observation.moon_phase * 100:0.0f}%',
                      f'Set {readable_time(observation.moonset_localtime)}',
                      f'Rise {readable_time(observation.moonrise_localtime)}')
        table.add_row('Astro Twi', 'Start', f'{readable_time(observation.astro_twilight_start_localtime)}', 'End',
                      f'{readable_time(observation.astro_twilight_end_localtime)}')
        return table

    def __rich_console__(
            self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        width = options.max_width
        height = options.height or options.size.height
        layout = self.layout
        title = f'Forecast ({width}x{height})'
        if self.current_service == self.clear_dark_sky_forecast and self.current_service.title:
            title = f'Forecast for {self.current_service.title}'

        table = Table.grid(padding=(0, 2), expand=False)
        table.add_row(self.forecast_table(width=width, height=height), self.sun_moon_table())

        yield Panel(
            Align.left(table, vertical="top"),
            style=self.style,
            title=title,
            border_style="blue",
        )
