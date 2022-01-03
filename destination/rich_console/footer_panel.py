from rich.console import Console, ConsoleOptions, RenderResult
from rich.table import Table

from data_structure.host_info import HostInfo
from data_structure.special_battery_percentage import SpecialBatteryPercentageEnum, MemoryUsage


class FooterPanel:
    def __init__(self, config: object, host_info: HostInfo = HostInfo()):
        self.host_info = host_info
        self.battery_percentage = SpecialBatteryPercentageEnum.NOT_MONITORED.value
        self.memory_usage = None  # type: MemoryUsage
        self.config = config

    def __rich_console__(
            self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        footer_table = Table.grid(expand=True)
        footer_table.add_column(justify='center', min_width=2)
        footer_table.add_column(justify='left', style='bold gold3', ratio=1)
        footer_table.add_column(justify='right', style='bold gold3', min_width=40)
        footer_table.add_column(justify='center', min_width=2)

        battery_row = ''
        host_name = self.host_info.host_name
        if self.config.monitor_local_computer:
            if self.battery_percentage == SpecialBatteryPercentageEnum.ON_AC_POWER.value:
                battery_row = '🔌'
            elif self.battery_percentage >= 0:
                battery_row = f'🔋{self.battery_percentage}%'
            memory_row = ''
            if self.memory_usage:
                memory_row = f'Voyager {self.memory_usage.voyager_rss:0.0f}/{self.memory_usage.voyager_vms:0.0f}MB Bot {self.memory_usage.bot_rss:0.0f}/{self.memory_usage.bot_vms:0.0f}MB'
            host_name = memory_row

        footer_table.add_row('',
                             f'{self.host_info.url}:{self.host_info.port} ({host_name})',
                             '2021-2022. Liuyi and Kun in California.',
                             battery_row)

        yield footer_table
