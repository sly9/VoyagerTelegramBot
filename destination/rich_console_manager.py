#!/bin/env python3
import enum
import threading
from collections import deque
from datetime import datetime
from time import sleep

import rich.text
from rich import box
from rich.align import Align
from rich.console import ConsoleOptions, RenderResult, Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress_bar import ProgressBar
from rich.style import StyleType
from rich.table import Table
from rich.text import Text

from data_structure.log_message_info import LogMessageInfo
from data_structure.shot_running_info import ShotRunningInfo, ShotRunningStatus
from data_structure.system_status_info import SystemStatusInfo, MountInfo, GuideStatusEnum, DitherStatusEnum, \
    MountStatusEnum, CcdStatusEnum
from event_emitter import ee
from event_names import BotEvent
from version import bot_version_string


class RichTextStylesEnum(enum.Enum):
    CRITICAL = 'bold white on dark_red'
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
        self.progress_panel = None

        self.setup()
        # Register events
        ee.on(BotEvent.UPDATE_SYSTEM_STATUS.name, self.update_status_panels)
        ee.on(BotEvent.APPEND_LOG.name, self.update_log)
        ee.on(BotEvent.UPDATE_SHOT_STATUS.name, self.update_shot_status)

    def setup(self):
        self.make_layout()
        self.log_panel = LogPanel(layout=self.layout['logs'], config=self.config)
        self.progress_panel = ProgressPanel()

        self.layout['header'].update(self.header)
        self.update_status_panels(SystemStatusInfo())

        self.layout['logs'].update(self.log_panel)

        self.layout['imaging'].update(self.progress_panel)

    def run(self):
        if self.thread:
            return
        self.thread = threading.Thread(target=self.run_loop)
        self.thread.daemon = True
        self.thread.start()

    def run_loop(self):
        with Live(self.layout, refresh_per_second=4, screen=True):
            while True:
                sleep(0.25)

    def make_layout(self):
        """Define the layout."""
        layout = Layout(name='root')
        layout.split(
            Layout(name='header', size=3),
            Layout(name='status', size=8),
            Layout(name='main', ratio=1),
            Layout(name='footer', size=1)
        )

        layout['status'].split_row(
            Layout(name='mount_info', size=45),  # DEC, RA, ALT, AZ, etc.
            Layout(name='stat', ratio=3),  # guiding error, last focusing result, last image HFD, staridx,
            Layout(name='imaging', ratio=3),
            # Focuser status, ccd status(temp), current_img, sequence_%, rotator, filter
        )

        layout['main'].split_row(
            Layout(name='logs', ratio=1),  # general logs, last error etc
            Layout(name='device_status', size=20)  # Slewing, guiding, parked, dithering, etc.
        )
        self.layout = layout

    def update_status_panels(self, system_status_info: SystemStatusInfo = None):
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
        status_table = Table.grid(padding=(0, 1))
        status_table.add_column(justify='left')

        # Connection status for setup, camera, mount, etc.
        # status_table.add_row('Device Connection')
        # connection_text = Text()
        #
        # if device_connection_info.setup_connected:
        #     connection_text.append('S', style=RichTextStylesEnum.SAFE.value)
        # else:
        #     connection_text.append('S', style=RichTextStylesEnum.CRITICAL.value)
        #
        # if device_connection_info.camera_connected:
        #     connection_text.append('C', style=RichTextStylesEnum.SAFE.value)
        # else:
        #     connection_text.append('C', style=RichTextStylesEnum.CRITICAL.value)
        #
        # if device_connection_info.mount_connected:
        #     connection_text.append('M', style=RichTextStylesEnum.SAFE.value)
        # else:
        #     connection_text.append('M', style=RichTextStylesEnum.CRITICAL.value)
        #
        # if device_connection_info.focuser_connected:
        #     connection_text.append('F', style=RichTextStylesEnum.SAFE.value)
        # else:
        #     connection_text.append('F', style=RichTextStylesEnum.CRITICAL.value)
        #
        # if device_connection_info.guide_connected:
        #     connection_text.append('G', style=RichTextStylesEnum.SAFE.value)
        # else:
        #     connection_text.append('G', style=RichTextStylesEnum.CRITICAL.value)
        #
        # if device_connection_info.planetarium_connected:
        #     connection_text.append('P', style=RichTextStylesEnum.SAFE.value)
        # else:
        #     connection_text.append('P', style=RichTextStylesEnum.CRITICAL.value)
        #
        # if device_connection_info.rotator_connected:
        #     connection_text.append('R', style=RichTextStylesEnum.SAFE.value)
        # else:
        #     connection_text.append('R', style=RichTextStylesEnum.CRITICAL.value)
        #
        # status_table.add_row(connection_text)

        device_status_info = system_status_info.device_status_info
        # CCD
        status_table.add_row('Main Camera')
        if device_connection_info.camera_connected:
            ccd_status_str = CcdStatusEnum(device_status_info.ccd_status.status)
            ccd_temperature = device_status_info.ccd_status.temperature
            ccd_power_percentage = device_status_info.ccd_status.power_percentage
            if ccd_status_str == CcdStatusEnum.UNDEF:
                ccd_text = Text('CONNECTED', style=RichTextStylesEnum.SAFE.value)
            elif ccd_status_str == CcdStatusEnum.TIMEOUT_COOLING or ccd_status_str == CcdStatusEnum.ERROR:
                ccd_text = Text(ccd_status_str.name, style=RichTextStylesEnum.CRITICAL.value)
            elif ccd_status_str == CcdStatusEnum.COOLING or ccd_status_str == CcdStatusEnum.WARMUP_RUNNING:
                ccd_text = Text(f'{ccd_temperature}°C | {ccd_status_str.name}', style=RichTextStylesEnum.WARNING.value)
            elif ccd_status_str == CcdStatusEnum.COOLED or ccd_status_str == CcdStatusEnum.WARMUP_END:
                ccd_text = Text(f'{ccd_temperature}°C | {ccd_power_percentage} %', style=RichTextStylesEnum.SAFE.value)
            else:
                # CcdStatEnum.INIT, NO_COOLER, or OFF:
                ccd_text = Text(ccd_status_str.name, style=RichTextStylesEnum.SAFE.value)
        else:
            ccd_text = Text('DISCONNECTED', style=RichTextStylesEnum.CRITICAL.value)

        status_table.add_row(ccd_text)
        # Mount
        status_table.add_row('Mount')
        if device_connection_info.mount_connected:
            mount_status = device_status_info.mount_status
            if mount_status == MountStatusEnum.TRACKING:
                mount_text = Text(mount_status.name, style=RichTextStylesEnum.SAFE.value)
            elif mount_status == MountStatusEnum.PAKRED:
                mount_text = Text(mount_status.name, style=RichTextStylesEnum.CRITICAL.value)
            elif mount_status == MountStatusEnum.SLEWING:
                mount_text = Text(mount_status.name, style=RichTextStylesEnum.WARNING.value)
            else:
                # MountOperationEnum.UNDEF and invalid values
                mount_text = Text('CONNECTED', style=RichTextStylesEnum.SAFE.value)
        else:
            mount_text = Text('DISCONNECTED', style=RichTextStylesEnum.CRITICAL.value)

        status_table.add_row(mount_text)
        # Auto Focuser
        if device_connection_info.focuser_connected:
            status_table.add_row('Focuser')
            focuser_status = device_status_info.focuser_status
            status_table.add_row(Text(f'{focuser_status.temperature}°C | {focuser_status.position}',
                                      style=RichTextStylesEnum.SAFE.value))
        # Rotator
        if device_connection_info.rotator_connected:
            status_table.add_row('Rotator')
            rotator_status = device_status_info.rotator_status
            if rotator_status.is_rotating:
                status_table.add_row(Text('ROTATING', style=RichTextStylesEnum.WARNING.value))
            else:
                status_table.add_row(f'Sky PA: {rotator_status.sky_pa}°')
                status_table.add_row(f'Rotator PA: {rotator_status.rotator_pa}°')

        # Guiding
        status_table.add_row('Guiding')
        if device_status_info.guide_status == GuideStatusEnum.RUNNING:
            guide_text = Text('ON', style=RichTextStylesEnum.SAFE.value)
        else:
            guide_text = Text('OFF', style=RichTextStylesEnum.CRITICAL.value)
        status_table.add_row(guide_text)
        # Dithering
        status_table.add_row('Dithering')
        if device_status_info.dither_status == DitherStatusEnum.RUNNING:
            dither_text = Text('ON', style=RichTextStylesEnum.SAFE.value)
        else:
            dither_text = Text('OFF', style=RichTextStylesEnum.CRITICAL.value)

        status_table.add_row(dither_text)

        status_panel = Panel(
            Align.center(status_table, vertical='top'),
            box=box.ROUNDED,
            padding=(1, 2),
            title="[b blue]Device Status",
            border_style='bright_blue',
        )

        self.layout['device_status'].update(status_panel)

        self.progress_panel.sequence_name = system_status_info.sequence_name
        if system_status_info.sequence_total_time_in_sec > 0:
            self.progress_panel.sequence_progress.update(
                system_status_info.sequence_elapsed_time_in_sec * 100.0 / system_status_info.sequence_total_time_in_sec)
        self.layout['imaging'].update(self.progress_panel)

    def update_log(self, log: LogMessageInfo):
        self.log_panel.append_log(log)
        self.layout['logs'].update(self.log_panel)
        if log.type == 'TITLE' or log.type == 'SUBTITLE':
            try:
                self.header.show_action_toast(log.message)
                self.layout['header'].update(self.header)
            except Exception as exception:
                print(exception)

    def update_shot_status(self, shot_running_info: ShotRunningInfo):
        self.progress_panel.file_name = shot_running_info.filename
        self.progress_panel.status = shot_running_info.status
        self.progress_panel.image_progress.update(shot_running_info.elapsed_percentage)
        self.layout['imaging'].update(self.progress_panel)


class LogPanel:
    def __init__(self, config: object, layout: Layout, style: StyleType = "") -> None:
        self.config = config
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
        log_table.add_column(justify='left', style='bold', max_width=8)
        log_table.add_column(justify='left', style='bold grey89')
        use_emoji = self.config.console_config.use_emoji
        for entry in log_entry_list:
            if use_emoji:
                log_table.add_row(entry.type_emoji, entry.message)
            else:
                style = ''
                if entry.type == 'WARNING':
                    style = RichTextStylesEnum.WARNING.value
                elif entry.type == 'CRITICAL':
                    style = RichTextStylesEnum.CRITICAL.value
                type_text = rich.text.Text(entry.type, style=style)
                log_table.add_row(type_text, entry.message)
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

    def __init__(self):
        self.toast_string = None

    def __rich_console__(
            self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield Panel(self.generate_grid(), style="white on blue")

    def generate_grid(self):
        grid = Table.grid(expand=True)
        grid.add_column(justify='center', min_width=25)

        if self.toast_string:
            grid.add_column(justify='center', ratio=1, style=RichTextStylesEnum.CRITICAL.value)
        else:
            grid.add_column(justify='left', ratio=1)
        grid.add_column(justify='right')
        if self.toast_string:
            grid.add_row(
                f'VogagerBot v{bot_version_string()}',
                self.toast_string,
                datetime.now().ctime().replace(":", "[blink]:[/]"),
            )
        else:
            grid.add_row(
                f'VogagerBot v{bot_version_string()}',
                '127.0.0.1:5950 (Unknown Host)',
                datetime.now().ctime().replace(":", "[blink]:[/]"),
            )
        return grid

    def show_action_toast(self, toast_string: str):
        self.toast_string = toast_string

    def hide_action_toast(self):
        self.toast_string = None


class ProgressPanel:
    def __init__(self):
        self.file_name = ''
        self.status = ShotRunningStatus.IDLE
        self.sequence_name = ''
        self.image_progress = ProgressBar(total=100)
        self.sequence_progress = ProgressBar(total=100)
        self.image_progress.update(0)
        self.sequence_progress.update(0)

    def __rich_console__(
            self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        progress_table = Table.grid(padding=(0, 1))
        progress_table.add_column(justify='left', style='bold gold3')
        progress_table.add_row(f'Status: {self.status.name}')
        progress_table.add_row(f'Imaging: {self.file_name}')
        progress_table.add_row(self.image_progress)
        progress_table.add_row(f'Sequence: {self.sequence_name}')
        progress_table.add_row(self.sequence_progress)

        yield Panel(progress_table)
