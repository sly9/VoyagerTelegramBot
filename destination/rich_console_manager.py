#!/bin/env python3
import enum
import math
import threading
from collections import deque
from datetime import datetime
from time import sleep

import pytz
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

from console import main_console
from data_structure.clear_dark_sky import transparency_color_map, seeing_color_map, cloud_cover_color_map
from data_structure.host_info import HostInfo
from data_structure.imaging_metrics import ImagingMetrics
from data_structure.log_message_info import LogMessageInfo
from data_structure.shot_running_info import ShotRunningInfo, ShotRunningStatus
from data_structure.system_status_info import SystemStatusInfo, MountInfo, GuideStatusEnum, DitherStatusEnum, \
    MountStatusEnum, CcdStatusEnum
from destination.rich_console.device_status_panel import DeviceStatusPanel
from destination.rich_console.footer_panel import FooterPanel
from destination.rich_console.forecast_panel import ForecastPanel
from destination.rich_console.log_panel import LogPanel
from destination.rich_console.progress_panel import ProgressPanel
from destination.rich_console.rich_console_header import RichConsoleHeader
from event_emitter import ee
from event_names import BotEvent
from utils.clear_dark_sky_forecast import ClearDarkSkyForecast
from version import bot_version_string



class RichConsoleManager:
    """A console manager powered by rich"""

    def __init__(self, config=None):
        self.config = config
        self.thread = None
        self.header = RichConsoleHeader()
        self.layout = None
        self.log_panel = None
        self.progress_panel = None
        self.device_status_panel = None
        self.forecast_panel = None

        self.footer_panel = None

        self.setup()
        # Register events
        ee.on(BotEvent.UPDATE_SYSTEM_STATUS.name, self.update_status_panels)
        ee.on(BotEvent.APPEND_LOG.name, self.update_log_panel)
        ee.on(BotEvent.UPDATE_SHOT_STATUS.name, self.update_shot_status_panel)
        ee.on(BotEvent.UPDATE_HOST_INFO.name, self.update_footer_panel)
        ee.on(BotEvent.UPDATE_METRICS.name, self.update_metrics_panel)

    def setup(self):
        self.make_layout()
        self.log_panel = LogPanel(layout=self.layout['logs'], config=self.config)
        self.progress_panel = ProgressPanel()
        self.footer_panel = FooterPanel(host_info=HostInfo())
        self.device_status_panel = DeviceStatusPanel(layout=self.layout['logs'])
        self.forecast_panel = ForecastPanel(layout=self.layout['logs'], config=self.config)
        self.layout['forecast'].update(self.forecast_panel)
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
        with Live(self.layout, refresh_per_second=4, screen=True, redirect_stderr=False):
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
            Layout(name='forecast', ratio=3),  # guiding error, last focusing result, last image HFD, staridx,
            Layout(name='imaging', ratio=3),  # current_img, sequence_%
        )

        layout['main'].split_row(
            Layout(name='logs', ratio=1),  # general logs
            Layout(name='device_status', size=24)  # status of all connected devices, etc.
        )

        self.layout = layout

    def update_mount_info_panel(self, mount_info: MountInfo = MountInfo()):
        if not mount_info:
            return

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

        mount_info_panel = Panel(
            Align.center(mount_table, vertical='top'),
            box=box.ROUNDED,
            padding=(1, 1),
            title="[bold blue]Mount Info",
            border_style='bright_blue',
        )

        self.layout['mount_info'].update(mount_info_panel)

    def update_metrics_panel(self, imaging_metircs: ImagingMetrics = ImagingMetrics()):
        return

    def update_device_status_panel(self, system_status_info: SystemStatusInfo = SystemStatusInfo()):
        self.device_status_panel.system_status_info = system_status_info
        self.layout['device_status'].update(self.device_status_panel)

    def update_status_panels(self, system_status_info: SystemStatusInfo = SystemStatusInfo()):
        """Update 3 panels related to status of the system"""
        # Mount Info panel which includes the coordination of the mount pointing at
        if system_status_info.device_connection_info.mount_connected:
            mount_info = system_status_info.mount_info
        else:
            # if mount is not connected, all info is not trustable.
            mount_info = MountInfo()

        self.update_mount_info_panel(mount_info=mount_info)
        # Device Status panel which shows status of all connected devices
        self.update_device_status_panel(system_status_info=system_status_info)
        # Progress Panel which shows the progress of the imaging session
        self.progress_panel.sequence_name = system_status_info.sequence_name
        if system_status_info.sequence_total_time_in_sec > 0:
            self.progress_panel.sequence_progress.update(
                system_status_info.sequence_elapsed_time_in_sec * 100.0 / system_status_info.sequence_total_time_in_sec)
        self.layout['imaging'].update(self.progress_panel)

    def update_log_panel(self, log: LogMessageInfo = LogMessageInfo()):
        if not log:
            return

        self.log_panel.append_log(log)
        self.layout['logs'].update(self.log_panel)
        if log.type == 'TITLE' or log.type == 'SUBTITLE':
            try:
                self.header.show_action_toast(log.message)
                self.layout['header'].update(self.header)
            except Exception as exception:
                main_console.print(exception)

    def update_shot_status_panel(self, shot_running_info: ShotRunningInfo = ShotRunningInfo()):
        if not shot_running_info:
            return
        self.progress_panel.update_shot_running_info(shot_running_info=shot_running_info)
        self.layout['imaging'].update(self.progress_panel)

    def update_footer_panel(self, host_info: HostInfo = HostInfo()):
        self.footer_panel.host_info = host_info
        self.layout['footer'].update(self.footer_panel)

