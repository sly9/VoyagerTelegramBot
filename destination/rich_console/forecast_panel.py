import math
from datetime import datetime, timezone

import ephem
import pytz
from astropy.coordinates import Angle
from rich.align import Align
from rich.console import RenderResult, Console, ConsoleOptions
from rich.layout import Layout
from rich.panel import Panel
from rich.style import StyleType
from rich.table import Table
from rich.text import Text

from data_structure.forecast_color_mapping import get_temperature_color, get_humidity_color, get_cloud_cover_color, \
    get_wind_speed_color, get_sky_condition_bg_color, get_roof_condition_bg_color, get_alert_bg_color
from data_structure.system_status_info import MountInfo
from destination.rich_console.styles import RichTextStylesEnum
from utils.forecast.clear_dark_sky_forecast import ClearDarkSkyForecast
from utils.forecast.open_weather_forecast import OpenWeatherForecast
from utils.forecast.sun_and_moon import SunAndMoon
from utils.localization import get_translated_text as _
from utils.sky_data_utils import get_weather_conditions, get_roof_condition, SkyCondition, CloudCondition, \
    WindCondition, RainCondition, DayCondition, AlertCondition


class ForecastPanel:
    def __init__(self, config: object, layout: Layout, style: StyleType = "") -> None:
        self.config = config
        self.layout = layout
        self.style = style
        self.table = None

        self.enabled_services = list()
        self.enabled_tables = list()
        self.mount_info = MountInfo()  # type: MountInfo

        if hasattr(config.observing_condition_config, 'forecast_service'):
            if 'ClearDarkSky' in config.observing_condition_config.forecast_service:
                clear_dark_sky_forecast = ClearDarkSkyForecast(config=config)
                clear_dark_sky_forecast.maybe_update_forecast()
                self.enabled_services.append(clear_dark_sky_forecast)
                self.enabled_tables.append(self.clear_sky_table)

            if 'OpenWeather' in config.observing_condition_config.forecast_service:
                open_weather_forecast = OpenWeatherForecast(config=config)
                open_weather_forecast.maybe_update_forecast()
                self.enabled_services.append(open_weather_forecast)
                self.enabled_tables.append(self.open_weather_table)

            if 'SunAndMoon' in config.observing_condition_config.forecast_service:
                sun_moon = SunAndMoon(config=config)
                sun_moon.maybe_update_forecast()
                self.enabled_services.append(sun_moon)
                self.enabled_tables.append(self.sun_moon_table)

                if hasattr(config.observing_condition_config, 'sky_condition_file'):
                    self.sky_condition_file = config.observing_condition_config.sky_condition_file
                else:
                    self.sky_condition_file = ''
                if hasattr(config.observing_condition_config, 'roof_condition_file'):
                    self.roof_condition_file = config.observing_condition_config.roof_condition_file
                else:
                    self.roof_condition_file = ''

        self.current_service_idx = 0
        self.current_service = self.enabled_services[self.current_service_idx]
        self.timestamp_since_changing_table = datetime.now()

    def clear_sky_table(self, height: int = 8, width: int = 20) -> Table:
        forecast_table = Table.grid(padding=(0, 0), expand=False)
        forecast_table.add_column(style='bold')

        if not self.current_service:
            forecast_table.add_row(Text(_('Unable to execute ClearDarkSky forecast service'),
                                        style=RichTextStylesEnum.CRITICAL.value))
        else:
            length = min(len(self.current_service.forecast), int(math.floor((width - 2 - 2 - 7) / 2)))

            for i in range(length - 1):
                forecast_table.add_column(width=2, max_width=2)

            hour_list = [_('Hour')]
            seeing_list = [_('Seeing')]
            cloud_cover_list = [_('Cloud')]
            transparency_list = [_('Transp ')]
            wind_list = [_('Wind S')]
            temperature_list = [_('Temp')]

            # find the right index to blink:
            right_index_to_blink = 0
            time_zone = pytz.timezone(self.config.timezone)
            now = datetime.now(tz=time_zone)
            for i in range(min(length, 23)):
                forecast = self.current_service.forecast[i]
                if now.hour == forecast.local_hour:
                    right_index_to_blink = i

            for i in range(length):
                forecast = self.current_service.forecast[i]
                style_string = 'grey62'
                place_holder_string = '  '
                if i % 2 == 0:
                    style_string = 'bright_white'
                if i == right_index_to_blink:
                    style_string += ' blink'
                    place_holder_string = '●'
                hour_list.append(Text(f'{forecast.local_hour:02}', style=style_string))
                seeing_list.append(Text(place_holder_string, style=f'red on {forecast.seeing.value}'))
                cloud_cover_list.append(
                    Text(place_holder_string, style=f'red on {forecast.cloud_cover_percentage.value}'))
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

        if not self.current_service:
            forecast_table.add_row(Text(_('Unable to execute OpenWeather forecast service'),
                                        style=RichTextStylesEnum.CRITICAL.value))
        else:
            length = min(len(self.current_service.forecast), 12)

            if length > 0:
                # Column to explicitly show current condition
                forecast_table.add_column(justify='right')
            for i in range(1, length):
                forecast_table.add_column(width=2, max_width=2)  # Fit -99 ~ 100

            hour_list = [_('Hour')]
            temperature_list = [_('Temp.')]
            dew_list = [_('Dew Point ')]
            humidity_list = [_('Humidity')]
            cloud_cover_list = [_('Cloud')]
            wind_speed_list = [_('Wind')]
            # weather_list = ['Weather ']

            if length > 0:
                forecast = self.current_service.forecast[0]
                # Explicitly show current condition

                hour_list.append(Text(_('Now '), style='white on black'))

                color_string = get_temperature_color(forecast.temperature)
                temperature_list.append(Text(f'{forecast.temperature}°C', style=f'black on {color_string}'))

                color_string = get_temperature_color(forecast.dew_point)
                dew_list.append(Text(f'{forecast.dew_point}°C', style=f'black on {color_string}'))

                color_string = get_humidity_color(forecast.humidity)
                humidity_list.append(Text(f'{forecast.humidity}%', style=f'black on {color_string}'))

                color_string = get_cloud_cover_color(forecast.cloud_cover_percentage)
                cloud_cover_list.append(Text(f'{forecast.cloud_cover_percentage}%', style=f'black on {color_string}'))

                # weather_list.append(Text(str(forecast.weather_id), style=style_string))

                color_string = get_wind_speed_color(forecast.wind_speed)
                wind_speed_list.append(Text(f'{forecast.wind_speed}m/s', style=f'black on {color_string}'))

            time_zone = pytz.timezone(self.config.timezone)
            for i in range(length):
                forecast = self.current_service.forecast[i]
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

    def sun_moon_table(self, height: int = 8, width: int = 20) -> Table:
        table = Table.grid(padding=(0, 2), expand=False)

        if not self.current_service:
            table.add_row(Text(_('Unable to execute ClearDarkSky forecast service'),
                               style=RichTextStylesEnum.CRITICAL.value))
        else:
            observation = self.current_service.forecast

            def readable_time(time):
                return f'{time.hour:02d}:{time.minute:02d}'

            sky_conditions = get_weather_conditions(file_path=self.sky_condition_file)
            roof_condition = get_roof_condition(file_path=self.roof_condition_file)

            # Sky Condition
            table.add_row(_('Condition'),
                          Text(CloudCondition(sky_conditions[SkyCondition.CLOUD]).name,
                               style=f'black on {get_sky_condition_bg_color(sky_conditions[SkyCondition.CLOUD])}'),
                          Text(WindCondition(sky_conditions[SkyCondition.WIND]).name,
                               style=f'black on {get_sky_condition_bg_color(sky_conditions[SkyCondition.WIND])}'),
                          Text(RainCondition(sky_conditions[SkyCondition.RAIN]).name,
                               style=f'black on {get_sky_condition_bg_color(sky_conditions[SkyCondition.RAIN])}'),
                          Text(DayCondition(sky_conditions[SkyCondition.DAYLIGHT]).name,
                               style=f'black on {get_sky_condition_bg_color(sky_conditions[SkyCondition.DAYLIGHT])}'))
            # Roof Condition
            table.add_row('🚨', Text(AlertCondition(sky_conditions[SkyCondition.ALERT]).name,
                                    style=f'black on {get_alert_bg_color(sky_conditions[SkyCondition.ALERT])}'),
                          _('Roof'),
                          Text(roof_condition, style=f'black on {get_roof_condition_bg_color(roof_condition)}'))
            table.add_row('')
            # Sun
            table.add_row(f'🔆 {observation.sun_altitude:.1f}°',
                          _('S: {}').format(readable_time(observation.sunset_localtime)),
                          _('R: {}').format(readable_time(observation.sunrise_localtime)))
            # Moon
            mount_alt_angle = Angle(self.mount_info.alt).dms
            mount_alt_degree = mount_alt_angle.d + mount_alt_angle.m / 60 + mount_alt_angle.s / 3600
            mount_az_angle = Angle(self.mount_info.az).dms
            mount_az_degree = mount_az_angle.d + mount_az_angle.m / 60 + mount_az_angle.s / 3600
            separation = ephem.separation(
                (observation.moon_azimuth / 180 * math.pi, observation.moon_altitude / 180 * math.pi),
                (mount_az_degree / 180 * math.pi, mount_alt_degree / 180 * math.pi))
            table.add_row(f'{observation.moon_phase_emoji} {observation.moon_phase * 100:0.0f}%',
                          _('R: {}').format(readable_time(observation.moonrise_localtime)),
                          _('S: {}').format(readable_time(observation.moonset_localtime)),
                          _(f'Alt: {observation.moon_altitude:.1f}°'),
                          f'🌙 {separation.real / math.pi * 180:.1f}° 🔭')
            # Twilight
            table.add_row(_('Twilight'), f'{readable_time(observation.astro_twilight_start_localtime)}',
                          f'{readable_time(observation.astro_twilight_end_localtime)}')

        return table

    def forecast_table(self, height: int = 8, width: int = 20) -> Table:
        now = datetime.now()
        if (now - self.timestamp_since_changing_table).total_seconds() > 8:
            self.current_service_idx += 1
            self.current_service_idx %= len(self.enabled_services)

            self.timestamp_since_changing_table = now

            self.current_service = self.enabled_services[self.current_service_idx]
            self.current_service.maybe_update_forecast()

        current_table = self.enabled_tables[self.current_service_idx](height=height, width=width)
        return current_table

    def __rich_console__(
            self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        width = options.max_width
        height = options.height or options.size.height
        layout = self.layout
        title = f'{self.current_service.service_name}'
        if self.current_service and hasattr(self.current_service, 'title'):
            title = f'{self.current_service.service_name} for {self.current_service.title}'

        table = self.forecast_table(width=width, height=height)
        yield Panel(
            Align.left(table, vertical="top"),
            style=self.style,
            title=title,
            border_style="blue",
        )
