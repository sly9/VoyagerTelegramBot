#!/bin/env python3
import threading
from datetime import datetime
from time import sleep

from rich import box
from rich.align import Align
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from data_structure.system_status_info import SystemStatusInfo
from event_emitter import ee
from event_names import BotEvent


class RichConsoleManager:
    """A console manager powered by rich"""

    def __init__(self, config):
        self.config = config
        self.thread = None
        self.header = RichConsoleHeader()
        self.layout = None
        ee.on(BotEvent.UPDATE_SYSTEM_STATUS.name, self.update_status_panel)

    def run(self):
        if self.thread:
            return
        self.thread = threading.Thread(target=self.run_loop)
        self.thread.daemon = True
        self.thread.start()

    def run_loop(self):
        self.layout = self.make_layout()

        self.layout['header'].update(self.header)

        self.update_status_panel()

        self.dummy_updater(self.layout['logs'])
        self.dummy_updater(self.layout['imaging'])

        with Live(self.layout, refresh_per_second=10, screen=True):
            while True:
                sleep(0.1)

    def make_layout(self) -> Layout:
        """Define the layout."""
        layout = Layout(name='root')
        layout.split(
            Layout(name='header', size=3),
            Layout(name='status', size=8),
            Layout(name='main', ratio=1)
        )

        layout['status'].split_row(
            Layout(name='mount_info', ratio=3),  # DEC, RA, ALT, AZ, etc.
            Layout(name='operations', ratio=3),  # Slewing, guiding, parked, dithering, etc.
            Layout(name='stat', ratio=3),  # guiding error, last focusing result, last image HFD, staridx,
        )

        layout['main'].split_row(
            Layout(name='logs', ratio=1),  # general logs, last error etc
            Layout(name='imaging')  # Focuser status, ccd status(temp), current_img, sequence_%, rotator, filter
        )

        return layout

    def update_status_panel(self, system_status_info: SystemStatusInfo=None):
        if not system_status_info:
            # A dummy info object with default values
            system_status_info = SystemStatusInfo()

        # Update mount information sub-panel
        mount_info = system_status_info.mount_info
        mount_table = Table.grid(padding=(0, 3))
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
        self.dummy_updater(self.layout['operations'])
        self.dummy_updater(self.layout['stat'])

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


class RichConsoleHeader:
    """Display header with clock."""

    def __rich__(self) -> Panel:
        grid = Table.grid(expand=True)
        grid.add_column(justify='center', min_width=25)
        grid.add_column(justify='left', ratio=1)
        grid.add_column(justify='right')
        grid.add_row(
            'VogagerBot v0.5',
            '127.0.0.1:5950 (Unknown Host)',
            datetime.now().ctime().replace(":", "[blink]:[/]"),
        )
        return Panel(grid, style="white on blue")
