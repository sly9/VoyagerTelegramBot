#!/bin/env python3
import enum
import threading
from collections import deque
from datetime import datetime
from time import sleep
from version import bot_version_string
from rich import box
from rich.align import Align
from rich.console import ConsoleOptions, RenderResult, Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.style import StyleType
from rich.table import Table
from rich.text import Text

from data_structure.log_message_info import LogMessageInfo
from data_structure.system_status_info import SystemStatusInfo, MountInfo, GuideStatEnum, DitherStatEnum
from event_emitter import ee
from event_names import BotEvent


class RichTextStylesEnum(enum.Enum):
    CRITICAL = 'bold black on dark_red'
    WARNING = 'bold black on gold3'
    SAFE = 'bold black on dark_sea_green4'


class RichConsoleManager:
    """A console manager powered by rich"""

    def __init__(self, config):
        self.config = config
        self.thread = None
        self.header = RichConsoleHeader()
        self.layout = None
        self.log_panel = None

        # Register events
        ee.on(BotEvent.UPDATE_SYSTEM_STATUS.name, self.update_status_panel)
        ee.on(BotEvent.APPEND_LOG.name, self.update_log)

    def run(self):
        if self.thread:
            return
        self.thread = threading.Thread(target=self.run_loop)
        self.thread.daemon = True
        self.thread.start()

    def run_loop(self):
        self.make_layout()

        self.layout['header'].update(self.header)

        self.update_status_panel()

        # self.dummy_updater(self.layout['logs'])
        self.dummy_updater(self.layout['imaging'])

        self.log_panel = LogPanel(self.layout['logs'])

        with Live(self.layout, refresh_per_second=4, screen=True):
            while True:
                sleep(0.25)

    def make_layout(self) -> Layout:
        """Define the layout."""
        layout = Layout(name='root')
        layout.split(
            Layout(name='header', size=3),
            Layout(name='status', size=8),
            Layout(name='main', ratio=1)
        )

        layout['status'].split_row(
            Layout(name='mount_info', size=45),  # DEC, RA, ALT, AZ, etc.
            Layout(name='operations', ratio=3),  # Slewing, guiding, parked, dithering, etc.
            Layout(name='stat', ratio=3),  # guiding error, last focusing result, last image HFD, staridx,
        )

        layout['main'].split_row(
            Layout(name='logs', ratio=1),  # general logs, last error etc
            Layout(name='imaging', size=20)
            # Focuser status, ccd status(temp), current_img, sequence_%, rotator, filter
        )
        self.layout = layout

    def update_status_panel(self, system_status_info: SystemStatusInfo = None):
        if not system_status_info:
            # A dummy info object with default values
            system_status_info = SystemStatusInfo()

        device_connection_info = system_status_info.device_connection_info
        if device_connection_info.mount_connected:
            mount_info = system_status_info.mount_info
        else:
            # if mount is not connected, all info is not trustable.
            mount_info = MountInfo()

        # Update mount information sub-panel
        mount_table = Table.grid(padding=(0, 1))
        mount_table.add_column(justify='right', style='bold grey89')
        mount_table.add_column(justify='left', style='bold gold3')
        mount_table.add_column(justify='right', style='bold grey89')
        mount_table.add_column(justify='left', style='bold gold3')
        mount_table.add_row('RA', mount_info.ra, 'DEC', mount_info.dec)
        mount_table.add_row('RA J2K', mount_info.ra, 'DEC J2K', mount_info.dec_j2000)
        mount_table.add_row('AZ', mount_info.az, 'ALT', mount_info.alt)
        mount_table.add_row('Pier', mount_info.pier, '', '')

        mount_info_panel = Panel(
            Align.center(mount_table, vertical='top'),
            box=box.ROUNDED,
            padding=(1, 2),
            title="[b blue]Mount Info",
            border_style='bright_blue',
        )

        self.layout['mount_info'].update(mount_info_panel)

        # Update operation and device connection status
        operation_table = Table.grid(padding=(0, 1))
        operation_table.add_column(justify='right', style='bold grey89')
        operation_table.add_column(justify='left')

        # Connection status for setup, camera, mount, etc.
        connection_text = Text()

        if device_connection_info.setup_connected:
            connection_text.append('S', style=RichTextStylesEnum.SAFE.value)
        else:
            connection_text.append('S', style=RichTextStylesEnum.CRITICAL.value)

        if device_connection_info.camera_connected:
            connection_text.append('C', style=RichTextStylesEnum.SAFE.value)
        else:
            connection_text.append('C', style=RichTextStylesEnum.CRITICAL.value)

        if device_connection_info.mount_connected:
            connection_text.append('M', style=RichTextStylesEnum.SAFE.value)
        else:
            connection_text.append('M', style=RichTextStylesEnum.CRITICAL.value)

        if device_connection_info.focuser_connected:
            connection_text.append('F', style=RichTextStylesEnum.SAFE.value)
        else:
            connection_text.append('F', style=RichTextStylesEnum.CRITICAL.value)

        if device_connection_info.guide_connected:
            connection_text.append('G', style=RichTextStylesEnum.SAFE.value)
        else:
            connection_text.append('G', style=RichTextStylesEnum.CRITICAL.value)

        if device_connection_info.planetarium_connected:
            connection_text.append('P', style=RichTextStylesEnum.SAFE.value)
        else:
            connection_text.append('P', style=RichTextStylesEnum.CRITICAL.value)

        if device_connection_info.rotator_connected:
            connection_text.append('R', style=RichTextStylesEnum.SAFE.value)
        else:
            connection_text.append('R', style=RichTextStylesEnum.CRITICAL.value)

        operation_table.add_row('Device Connection:', connection_text)
        if device_connection_info.mount_connected:
            if mount_info.operation == '':
                mount_operation = 'CONNECTED'
            else:
                mount_operation = mount_info.operation
        else:
            mount_operation = 'DISCONNECTED'

        operation_table.add_row('Mount Operation:', mount_operation)
        if system_status_info.guide_status == GuideStatEnum.RUNNING:
            guide_text = Text('GUIDING', style=RichTextStylesEnum.SAFE.value)
        else:
            guide_text = Text('')

        if system_status_info.dither_status == DitherStatEnum.RUNNING:
            dither_text = Text('DITHERING', style=RichTextStylesEnum.SAFE.value)
        else:
            dither_text = Text('')

        operation_table.add_row(guide_text, dither_text)

        operation_panel = Panel(
            Align.center(operation_table, vertical='top'),
            box=box.ROUNDED,
            padding=(1, 2),
            title="[b blue]Operations & Devices",
            border_style='bright_blue',
        )

        self.layout['operations'].update(operation_panel)
        self.dummy_updater(self.layout['stat'])

    def update_log(self, log: LogMessageInfo):
        self.log_panel.append_log(log)
        self.layout['logs'].update(self.log_panel)

    def dummy_updater(self, layout: Layout = None):
        if not layout:
            return
        layout.update(self.dummy_maker())

    def dummy_maker(self) -> Panel:
        dummy_message = Text.from_markup(
            '''
            Dummy Message for Dummy Panel with love!
            '''
        )

        message = Table(padding=1)
        message.add_column()
        message.add_row(dummy_message)

        message_panel = Panel(
            Align.center(
                dummy_message,
                vertical="middle",
            ),
            box=box.ROUNDED,
            padding=(1, 2),
            title="[b red]Dummy Panel",
            border_style="bright_blue",
        )
        return message_panel


class LogPanel:
    def __init__(self, layout: Layout, style: StyleType = "") -> None:
        self.layout = layout
        self.style = style
        self.table = None
        self.recent_logs = deque(maxlen=500)

    def append_log(self, log: LogMessageInfo):
        log.message = log.message.replace('\r\n', '\n').replace('\n\n', '\n')
        self.recent_logs.append(log)

    def visible_log_entry_list(self, height: int):
        result = []
        used_height = 0
        for i in range(len(self.recent_logs)):
            log = self.recent_logs[-i - 1]
            used_height += log.message.strip().count('\n') + 1
            if used_height > height:
                result.reverse()
                return result
            result.append(log)
        result.reverse()
        return result

    def visible_log_table(self, height: int):
        log_entry_list = self.visible_log_entry_list(height=height)
        log_table = Table.grid(padding=(0, 1), expand=True)
        log_table.add_column(justify='left', style='bold grey89', max_width=8, width=8)
        log_table.add_column(justify='left', style='bold gold3')
        for entry in log_entry_list:
            log_table.add_row(entry.type, entry.message)
        return log_table

    def __rich_console__(
            self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        width = options.max_width
        height = options.height or options.size.height
        layout = self.layout

        yield Panel(
            Align.left(self.visible_log_table(height=height), vertical="top"),
            style=self.style,
            title=f'Important logs ({width}x{height})',
            border_style="blue",
        )


class RichConsoleHeader:
    """Display header with clock."""

    def __rich__(self) -> Panel:
        grid = Table.grid(expand=True)
        grid.add_column(justify='center', min_width=25)
        grid.add_column(justify='left', ratio=1)
        grid.add_column(justify='right')
        grid.add_row(
            f'VogagerBot v{bot_version_string()}',
            '127.0.0.1:5950 (Unknown Host)',
            datetime.now().ctime().replace(":", "[blink]:[/]"),
        )
        return Panel(grid, style="white on blue")
