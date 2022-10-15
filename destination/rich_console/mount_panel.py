import datetime
from datetime import datetime, timedelta

from rich import box
from rich.align import Align
from rich.console import Console, ConsoleOptions, RenderResult
from rich.panel import Panel
from rich.table import Table

from data_structure.system_status_info import MountInfo
from utils.localization import get_translated_text as _


class MountPanel:
    def __init__(self, config: object) -> None:
        self.config = config
        self.mount_info_ = MountInfo()  # type: MountInfo
        self.flip_updated_time = datetime.now()
        self.flip_duration = timedelta()  # the duration

    @property
    def mount_info(self):
        return self.mount_info_

    @mount_info.setter
    def mount_info(self, value: MountInfo):
        if self.mount_info_.time_to_flip != value.time_to_flip and len(value.time_to_flip):
            self.flip_updated_time = datetime.now()
            flip_string = value.time_to_flip.replace('+', '').strip()
            sign = 1
            if flip_string[0] == '-':
                sign = -1
            t = datetime.strptime(flip_string.replace('-', ''), "%H:%M:%S")
            # ...and use datetime's hour, min and sec properties to build a timedelta
            self.flip_duration = timedelta(hours=sign * t.hour, minutes=sign * t.minute, seconds=sign * t.second)
            self.flip_updated_time = datetime.now()

        self.mount_info_ = value

    def time_top_flip(self):
        elapsed_time = datetime.now() - self.flip_updated_time
        updated_duration = self.flip_duration + elapsed_time  # type: timedelta
        prefix = 'T+'
        if updated_duration.total_seconds() < 0:
            prefix = 'T-'
            updated_duration = -updated_duration
        hour = updated_duration.seconds // 3600
        minute = (updated_duration.seconds // 60) % 60
        sec = updated_duration.seconds % 60
        return f'{prefix}{hour:02}[blink]:[/]{minute:02}[blink]:[/]{sec:02}'

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
        mount_table.add_row('Pier', mount_info.pier, 'FLIP', self.time_top_flip())

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
            title='[bold blue]' + _('Mount Status'),
            border_style='bright_blue',
        )
