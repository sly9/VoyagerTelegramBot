from rich.console import Console, ConsoleOptions, RenderResult
from rich.table import Table

from data_structure.host_info import HostInfo


class FooterPanel:
    def __init__(self, host_info: HostInfo = HostInfo()):
        self.host_info = host_info

    def __rich_console__(
            self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        footer_table = Table.grid(expand=True)
        footer_table.add_column(justify='center', min_width=4)
        footer_table.add_column(justify='left', style='bold gold3', ratio=1)
        footer_table.add_column(justify='right', style='bold gold3', min_width=40)
        footer_table.add_column(justify='center', min_width=4)

        footer_table.add_row('',
                             f'{self.host_info.url}:{self.host_info.port} ({self.host_info.host_name})',
                             '2021-2022. Liuyi and Kun in California.',
                             '')

        yield footer_table
