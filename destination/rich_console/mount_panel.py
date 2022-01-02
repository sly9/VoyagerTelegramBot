from rich import box
from rich.align import Align
from rich.console import Console, ConsoleOptions, RenderResult
from rich.panel import Panel
from rich.table import Table

from data_structure.system_status_info import MountInfo


class MountPanel:
    def __init__(self, config: object) -> None:
        self.config = config
        self.mount_info = None  # type: MountInfo

    def mount_table(self, height: int):
        mount_info = self.mount_info
        # Update mount information sub-panel
        mount_table = Table.grid(padding=(0, 2))
        mount_table.add_column(justify='right', style='bold grey89')
        mount_table.add_column(justify='left', style='bold gold3')
        mount_table.add_column(justify='right', style='bold grey89')
        mount_table.add_column(justify='left', style='bold gold3')
        mount_table.add_row('RA', mount_info.ra, 'RA J2K', mount_info.ra_j2000)
        mount_table.add_row('DEC', mount_info.dec, 'DEC J2K', mount_info.dec_j2000)
        mount_table.add_row('AZ', mount_info.az, 'ALT', mount_info.alt)
        mount_table.add_row('Pier', mount_info.pier, 'FLIP', mount_info.time_to_flip)

        return mount_table

    def __rich_console__(
            self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        width = options.max_width
        height = options.height or options.size.height

        yield Panel(
            Align.center(self.mount_table(height=height), vertical="top"),
            box=box.ROUNDED,
            padding=(1, 1),
            title="[bold blue]Mount Info",
            border_style='bright_blue',
        )
