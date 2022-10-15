from collections import deque

from rich.align import Align
from rich.console import Console, ConsoleOptions, RenderResult
from rich.layout import Layout
from rich.panel import Panel
from rich.style import StyleType
from rich.table import Table
from rich.text import Text

from data_structure.log_message_info import LogMessageInfo
from destination.rich_console.styles import RichTextStylesEnum
from utils.localization import get_translated_text as _


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
                type_text = Text(entry.type, style=style)
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
            title=_('Important logs ({width}x{height})').format(width=width, height=height),
            border_style="blue",
        )
