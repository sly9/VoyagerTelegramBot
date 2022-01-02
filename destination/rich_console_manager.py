#!/bin/env python3
import threading
from time import sleep

from rich import box
from rich.align import Align
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from console import main_console
from data_structure.host_info import HostInfo
from data_structure.imaging_metrics import ImagingMetrics
from data_structure.log_message_info import LogMessageInfo
from data_structure.shot_running_info import ShotRunningInfo
from data_structure.system_status_info import SystemStatusInfo, MountInfo
from destination.rich_console.device_status_panel import DeviceStatusPanel
from destination.rich_console.footer_panel import FooterPanel
from destination.rich_console.forecast_panel import ForecastPanel
from destination.rich_console.log_panel import LogPanel
from destination.rich_console.mount_panel import MountPanel
from destination.rich_console.progress_panel import ProgressPanel
from destination.rich_console.rich_console_header import RichConsoleHeader
from event_emitter import ee
from event_names import BotEvent


class RichConsoleManager:
    """A console manager powered by rich"""

    def __init__(self, config=None):
        self.config = config
        self.thread = None
        self.header = RichConsoleHeader(config=config)
        self.layout = None
        self.mount_panel = None
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

        self.mount_panel = MountPanel(config=self.config)
        self.progress_panel = ProgressPanel()
        self.footer_panel = FooterPanel(host_info=HostInfo())
        self.device_status_panel = DeviceStatusPanel(layout=self.layout['logs'])
        self.forecast_panel = ForecastPanel(layout=self.layout['logs'], config=self.config)
        self.layout['forecast'].update(self.forecast_panel)
        self.layout['header'].update(self.header)
        self.update_status_panels()
        self.update_mount_info_panel()

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
            Layout(name='imaging', ratio=2),  # current_img, sequence_%
        )

        layout['main'].split_row(
            Layout(name='logs', ratio=1),  # general logs
            Layout(name='device_status', size=24)  # status of all connected devices, etc.
        )

        self.layout = layout

    def update_mount_info_panel(self, mount_info: MountInfo = MountInfo()):
        # Update mount information sub-panel
        self.mount_panel.mount_info = mount_info
        self.layout['mount_info'].update(self.mount_panel)

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
