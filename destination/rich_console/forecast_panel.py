import math
from datetime import datetime

import pytz
from rich.align import Align
from rich.console import RenderResult, Console, ConsoleOptions
from rich.layout import Layout
from rich.panel import Panel
from rich.style import StyleType
from rich.table import Table
from rich.text import Text

from data_structure.clear_dark_sky import seeing_color_map, cloud_cover_color_map, transparency_color_map
from utils.clear_dark_sky_forecast import ClearDarkSkyForecast
from utils.forecast.open_weather_forecast import OpenWeatherForecast


class ForecastPanel:
    def __init__(self, config: object, layout: Layout, style: StyleType = "") -> None:
        self.config = config
        self.layout = layout
        self.style = style
        self.table = None

        if hasattr(config.observing_condition_config, 'forecast_service'):
            self.service_name = config.observing_condition_config.forecast_service[0]
        else:
            self.service_name = 'ClearSky'

        if self.service_name == 'ClearSky':
            self.forecast_service = ClearDarkSkyForecast(config=config)
        else:
            self.forecast_service = OpenWeatherForecast(config=config)

        self.forecast_service.maybe_update_forecast()

    def clear_sky_table(self, height: int = 8, width: int = 20) -> Table:
        forecast_table = Table.grid(padding=(0, 0), expand=False)
        forecast_table.add_column(style='bold')

        length = min(len(self.forecast_service.forecast), int(math.floor((width - 2 - 2 - 7) / 2)), 12)

        for i in range(length - 1):
            forecast_table.add_column(width=2, max_width=2)

        hour_list = ['Hour']
        seeing_list = ['Seeing']
        cloud_cover_list = ['Cloud']
        transparency_list = ['Transp ']

        # find the right index to blink:
        right_index_to_blink = 0
        timezone = pytz.timezone(self.config.timezone)
        now = datetime.now(tz=timezone)
        for i in range(min(length, 23)):
            forecast = self.forecast_service.forecast[i]
            if now.hour == forecast.local_hour:
                right_index_to_blink = i

        for i in range(length):
            forecast = self.forecast_service.forecast[i]
            style_string = 'grey62'
            if i % 2 == 0:
                style_string = 'bright_white'
            if i == right_index_to_blink:
                style_string += ' blink'
            hour_list.append(Text(f'{forecast.local_hour:02}', style=style_string))

            color_string = seeing_color_map.get(forecast.seeing.value, 'white')
            seeing_list.append(Text('  ', style=f'{color_string} on {color_string}'))

            color_string = cloud_cover_color_map.get(forecast.cloud_cover_percentage, 'white')
            cloud_cover_list.append(Text('  ', style=f'{color_string} on {color_string}'))

            color_string = transparency_color_map.get(forecast.transparency.value, 'white')
            transparency_list.append(Text('  ', style=f'{color_string} on {color_string}'))

        forecast_table.add_row(*hour_list)
        forecast_table.add_row(*seeing_list)
        forecast_table.add_row(*cloud_cover_list)
        forecast_table.add_row(*transparency_list)
        return forecast_table

    def free_weather_table(self, height: int = 8, width: int = 20) -> Table:
        forecast_table = Table.grid(padding=(0, 0), expand=False)
        forecast_table.add_column(style='bold')

        length = min(len(self.forecast_service.forecast), 8)

        for i in range(length):
            forecast_table.add_column(width=3, max_width=3)  # Fit -99 ~ 100
        hour_list = ['Hour']
        temperature_list = ['T°C']
        dew_list = ['Dew°C']
        humidity_list = ['Hum.%']
        cloud_cover_list = ['Cloud%']
        wind_speed_list = ['Wind km/h']
        weather_list = ['Weather ']

        timezone = pytz.timezone(self.config.timezone)
        now = datetime.now(tz=timezone)
        current_hour = int(now.hour)

        for i in range(length):
            forecast = self.forecast_service.forecast[i]
            style_string = 'grey62'
            if i % 2 == 0:
                style_string = 'bright_white'
            hour = current_hour + i
            hour_list.append(Text(f'{hour:02}', style=style_string))

            temperature_list.append(Text(str(forecast.temperature), style=style_string))
            dew_list.append(Text(str(forecast.dew_point), style=style_string))
            humidity_list.append(Text(str(forecast.humidity), style=style_string))
            cloud_cover_list.append(Text(str(forecast.cloud_cover_percentage), style=style_string))
            weather_list.append(Text(str(forecast.weather_id), style=style_string))
            wind_speed_list.append(Text(str(forecast.wind_speed), style=style_string))

        forecast_table.add_row(*hour_list)
        forecast_table.add_row(*temperature_list)
        forecast_table.add_row(*dew_list)
        forecast_table.add_row(*humidity_list)
        forecast_table.add_row(*cloud_cover_list)
        forecast_table.add_row(*weather_list)
        forecast_table.add_row(*wind_speed_list)

        return forecast_table

    def forecast_table(self, height: int = 8, width: int = 20) -> Table:
        self.forecast_service.maybe_update_forecast()
        if self.service_name == 'ClearSky':
            return self.clear_sky_table(height=height, width=width)
        else:
            return self.free_weather_table(height=height, width=width)

    def __rich_console__(
            self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        width = options.max_width
        height = options.height or options.size.height
        layout = self.layout

        yield Panel(
            Align.left(self.forecast_table(width=width, height=height), vertical="top"),
            style=self.style,
            title=f'{self.service_name} Forecast ({width}x{height})',
            border_style="blue",
        )
