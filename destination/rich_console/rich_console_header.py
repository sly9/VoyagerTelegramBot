from datetime import datetime

from rich.console import RenderResult, Console, ConsoleOptions
from rich.panel import Panel
from rich.table import Table

from destination.rich_console.styles import RichTextStylesEnum
from version import bot_version_string


class RichConsoleHeader:
    """Display header with clock."""

    def __init__(self):
        self.toast_string = ''

    def __rich_console__(
            self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield Panel(self.generate_grid(), style="white on blue")

    def generate_grid(self):
        grid = Table.grid(expand=True)
        grid.add_column(justify='center', min_width=25)
        grid.add_column(justify='center', ratio=1, style=RichTextStylesEnum.CRITICAL.value)
        grid.add_column(justify='right', min_width=25)

        grid.add_row(
            f'VogagerBot v{bot_version_string()}',
            self.toast_string,
            datetime.now().ctime().replace(":", "[blink]:[/]"),
        )

        return grid

    def show_action_toast(self, toast_string: str):
        self.toast_string = toast_string

    def hide_action_toast(self):
        self.toast_string = None
