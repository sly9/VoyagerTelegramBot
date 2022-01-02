from rich import box
from rich.align import Align
from rich.console import RenderResult, Console, ConsoleOptions
from rich.panel import Panel
from rich.progress_bar import ProgressBar
from rich.table import Table
from rich.text import Text

from data_structure.shot_running_info import ShotRunningStatus, ShotRunningInfo


class ProgressPanel:
    def __init__(self):
        self.sequence_name = ''
        self.image_progress = ProgressBar(total=100)
        self.sequence_progress = ProgressBar(total=100)
        self.image_progress.update(0)
        self.sequence_progress.update(0)
        self.shot_running_info = None

    def __rich_console__(
            self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        progress_table = Table.grid(padding=(0, 1))
        progress_table.add_column(justify='left', style='bold gold3')
        if self.shot_running_info:
            if self.shot_running_info.status == ShotRunningStatus.EXPOSE:
                progress_table.add_row(
                    f'Status: {self.shot_running_info.status.name}    {self.shot_running_info.elapsed_exposure}s / {self.shot_running_info.total_exposure}s')
            else:
                progress_table.add_row(f'Status: {self.shot_running_info.status.name}')
            imaging_text = Text(f'Imaging: {self.shot_running_info.filename}', overflow='ellipsis', no_wrap=True)
            progress_table.add_row(imaging_text)
            progress_table.add_row(self.image_progress)
            progress_table.add_row(f'Sequence: {self.sequence_name}')
            progress_table.add_row(self.sequence_progress)

        yield Panel(Align.center(progress_table, vertical='top'),
                    box=box.ROUNDED,
                    padding=(1, 2, 0, 2),
                    title="[bold blue]Progress",
                    border_style='bright_blue', )

    def update_shot_running_info(self, shot_running_info: ShotRunningInfo):
        self.shot_running_info = shot_running_info
        self.image_progress.update(shot_running_info.elapsed_percentage)
