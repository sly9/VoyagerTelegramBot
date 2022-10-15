from rich.console import Console, ConsoleOptions, RenderResult
from rich.table import Table

from data_structure.host_info import HostInfo, VoyagerConnectionStatus
from data_structure.special_battery_percentage import SpecialBatteryPercentageEnum, MemoryUsage
from utils.localization import get_translated_text as _


class FooterPanel:
    def __init__(self, config: object, host_info: HostInfo = HostInfo()):
        self.host_info = host_info
        self.battery_percentage = SpecialBatteryPercentageEnum.NOT_MONITORED.value
        self.memory_usage = None  # type: MemoryUsage
        self.config = config

    def host_info_row(self):
        host_name = self.host_info.host_name
        if self.config.monitor_local_computer:
            memory_row = ''
            if self.memory_usage:
                memory_row = f'Voyager {self.memory_usage.voyager_rss:0.0f}/{self.memory_usage.voyager_vms:0.0f}MB Bot {self.memory_usage.bot_rss:0.0f}/{self.memory_usage.bot_vms:0.0f}MB'
            host_name = memory_row

        connection_status = '📶' if self.host_info.connection_status == VoyagerConnectionStatus.CONNECTED else '🚫'
        return f'{self.host_info.url}:{self.host_info.port} {connection_status} ({host_name})'

    def battery_row(self):
        battery_row = ''
        if self.config.monitor_local_computer:
            if self.battery_percentage == SpecialBatteryPercentageEnum.ON_AC_POWER.value:
                battery_row = '🔌'
            elif self.battery_percentage >= 0:
                battery_row = f'🔋{self.battery_percentage}%'

        return battery_row

    def __rich_console__(
            self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        footer_table = Table.grid(expand=True)
        footer_table.add_column(justify='center', min_width=2)
        footer_table.add_column(justify='left', style='bold gold3', ratio=1)
        footer_table.add_column(justify='right', style='bold gold3', min_width=40)
        footer_table.add_column(justify='center', min_width=2)

        footer_table.add_row('', self.host_info_row(), _('2021-2022. Liuyi and Kun in California.'), self.battery_row())

        yield footer_table
