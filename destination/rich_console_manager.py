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


class RichConsoleManager:
    """A console manager powered by rich"""

    def __init__(self, config):
        self.config = config
        self.thread = None
        self.header = RichConsoleHeader()
        self.layout = None
        # ee.on(BotEvent.UPDATE_HOST_INFO, self.update_host_info)

    def run(self):
        if self.thread:
            return
        self.thread = threading.Thread(target=self.run_loop)
        self.thread.daemon = True
        self.thread.start()

    def run_loop(self):
        self.layout = self.make_layout()

        self.layout['header'].update(self.header)
        self.mount_info_panel_updater()
        self.dummy_updater(self.layout['operations'])
        self.dummy_updater(self.layout['stat'])
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

    def mount_info_panel_updater(self):
        mount_table = Table.grid(padding=1)
        mount_table.add_column()
        mount_table.add_column()
        mount_table.add_column()
        mount_table.add_column()
        mount_table.add_row('RA', '0', 'DEC', '0')
        mount_table.add_row('RA J2000', '0', 'DEC J2000', '0')
        mount_table.add_row('AZ', '0', 'ALT', '0')
        mount_table.add_row('Pier', 'WEST', '', '')

        mount_info_panel = Panel(
            Align.center(mount_table, vertical='top'),
            box=box.ROUNDED,
            padding=(0, 2),
            title="[b blue]Mount Info",
            border_style='bright_blue',
        )

        self.layout['mount_info'].update(mount_info_panel)

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

        message = Table.grid(padding=1)
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
