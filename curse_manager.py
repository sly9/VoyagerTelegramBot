import curses
import time
from collections import deque

from data_structure.error_message_info import ErrorMessageInfo
from data_structure.host_info import HostInfo
from data_structure.job_status_info import JobStatusInfo, GuideStatEnum, DitherStatEnum
from data_structure.log_message_info import LogMessageInfo
from data_structure.special_battery_percentage import SpecialBatteryPercentageEnum
from version import bot_version_string


class CursesManager:
    def __init__(self):
        # Initial a new screen
        self.stdscr = curses.initscr()
        self.stdscr.keypad(True)
        curses.noecho()
        curses.cbreak()

        # setup color styles
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
        self.normal_style = curses.color_pair(1)

        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_RED)
        self.critical_style = curses.color_pair(2)

        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_YELLOW)
        self.warning_style = curses.color_pair(3)

        curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_GREEN)
        self.safe_style = curses.color_pair(4)

        # status information used to update info
        self.last_error = ErrorMessageInfo()
        self.received_message_counter = 0
        self.host_info = HostInfo()
        self.log_queue = deque(maxlen=10)
        self.battery_percentage = 100
        self.job_status_info = JobStatusInfo()

    def _update_whole_scr(self):
        self.stdscr.clear()
        line_pos = 0

        # Horizontal Line
        self.stdscr.addstr(line_pos, 0, '+' + '-' * 118 + '+', self.normal_style)
        line_pos += 1

        # Version and Host Information
        self.stdscr.addstr(line_pos, 0, f'|     VoyagerTelegramBot v{bot_version_string()}     |', self.normal_style)
        host_str = f'{self.host_info.url}:{self.host_info.port} ({self.host_info.host_name})'
        self.stdscr.addstr(f' {host_str:54} | Battery |', self.normal_style)

        # Battery Info
        if self.battery_percentage == SpecialBatteryPercentageEnum.ON_AC_POWER:
            self.stdscr.addstr(f'  ON AC POWER  ', self.safe_style)
        elif self.battery_percentage == SpecialBatteryPercentageEnum.NOT_MONITORED:
            self.stdscr.addstr(f' NOT MONITORED ', self.safe_style)
        elif self.battery_percentage == SpecialBatteryPercentageEnum.NOT_AVAILABLE:
            self.stdscr.addstr(f' NOT AVAILABLE ', self.safe_style)
        else:
            battery_str = f'{self.battery_percentage} %'
            if self.battery_percentage > 75:
                self.stdscr.addstr(f' {battery_str:^13} ', self.safe_style)
            elif self.battery_percentage <= 25:
                self.stdscr.addstr(f' {battery_str:^13} ', self.critical_style)
            else:
                self.stdscr.addstr(f' {battery_str:^13} ', self.warning_style)
        self.stdscr.addstr('|', self.normal_style)
        line_pos += 1

        # Horizontal Line
        self.stdscr.addstr(line_pos, 0, '+' + '-' * 118 + '+', self.normal_style)
        line_pos += 1

        # Error
        self.stdscr.addstr(line_pos, 0, f'| ', self.normal_style)

        if self.last_error.code == 0:
            error_str = 'Everything is AWESOME!'
            self.stdscr.addstr(f'{error_str:116}', self.normal_style)
        else:
            error_str = f'[{self.last_error.code}] {self.last_error.message}'
            self.stdscr.addstr(f'{error_str:116.116}', self.critical_style)

        self.stdscr.addstr(' |', self.normal_style)
        line_pos += 1
        # Horizontal Line
        self.stdscr.addstr(line_pos, 0, '+' + '-' * 118 + '+', self.normal_style)
        line_pos += 1

        # Job Detail
        self.stdscr.addstr(line_pos, 0, f'| DragScript | {self.job_status_info.drag_script_name:26} |', self.normal_style)
        self.stdscr.addstr(f' Sequence | {self.job_status_info.sequence_name:26} | ', self.normal_style)

        motion_str = ''
        if self.job_status_info.is_slewing:
            motion_str = 'SLEWING'
        elif self.job_status_info.is_tracking:
            motion_str = 'TRACKING'
        self.stdscr.addstr(f'{motion_str:8}', self.safe_style)

        self.stdscr.addstr(' | ', self.normal_style)
        if self.job_status_info.guide_status == GuideStatEnum.STOPPED:
            self.stdscr.addstr(f' STOPPED ', self.critical_style)
        elif self.job_status_info.guide_status == GuideStatEnum.RUNNING:
            self.stdscr.addstr(f' GUIDING ', self.safe_style)
        else:
            self.stdscr.addstr(f' WAITING ', self.warning_style)
        self.stdscr.addstr(' | ', self.normal_style)

        if self.job_status_info.dither_status == DitherStatEnum.STOPPED:
            self.stdscr.addstr(f' STOPPED ', self.critical_style)
        elif self.job_status_info.dither_status == DitherStatEnum.RUNNING:
            self.stdscr.addstr(f'DITHERING', self.safe_style)
        else:
            self.stdscr.addstr(f' WAITING ', self.warning_style)
        self.stdscr.addstr(' |', self.normal_style)
        line_pos += 1

        # Horizontal Line
        self.stdscr.addstr(line_pos, 0, '+' + '-' * 118 + '+', self.normal_style)
        line_pos += 1

        # Log
        for log_item in self.log_queue:
            self.stdscr.addstr(line_pos, 0, f'| ', self.normal_style)
            if log_item.type == 'CRITICAL' or log_item.type == 'EMERGENCY':
                self.stdscr.addstr(f'{log_item.type:9}', self.critical_style)
            elif log_item.type == 'WARNING':
                self.stdscr.addstr(f'{log_item.type:9}', self.warning_style)
            else:
                self.stdscr.addstr(f'{log_item.type:9}', self.safe_style)

            self.stdscr.addstr(f' | {log_item.message:104.104} |', self.normal_style)
            line_pos += 1

        # Horizontal Line
        self.stdscr.addstr(line_pos, 0, '+' + '-' * 118 + '+', self.normal_style)
        line_pos += 1

        # Message Counter
        counter_str = f'{self.received_message_counter} messages have been processed...'
        self.stdscr.addstr(line_pos, 0, f'| {counter_str:116.116} |', self.normal_style)
        line_pos += 1

        # Horizontal Line
        self.stdscr.addstr(line_pos, 0, '+' + '-' * 118 + '+', self.normal_style)

        self.stdscr.refresh()

    def update_message_counter(self, counter_number: int = 0):
        self.received_message_counter = counter_number
        self._update_whole_scr()

    def update_lass_error(self, error_info: ErrorMessageInfo = None):
        if error_info:
            self.last_error = error_info
            self._update_whole_scr()

    def update_host_info(self, host_info: HostInfo = None):
        self.host_info = host_info
        self._update_whole_scr()

    def update_battery_percentage(self, battery_percentage: int = 0, update: bool = True):
        self.battery_percentage = battery_percentage
        if update:
            self._update_whole_scr()

    def append_log(self, new_message: LogMessageInfo = None):
        if new_message:
            self.log_queue.append(new_message)
            self._update_whole_scr()

    def update_job_status_info(self, job_status_info: JobStatusInfo = None):
        if job_status_info:
            self.job_status_info = job_status_info
            self._update_whole_scr()

    def close(self):
        # Close the screen
        curses.nocbreak()
        self.stdscr.keypad(False)
        curses.echo()
        curses.endwin()


if __name__ == '__main__':
    curses_mgr = CursesManager()

    curses_mgr.update_message_counter(2)
    time.sleep(2)

    curses_mgr.update_message_counter(99)
    curses_mgr.update_lass_error(ErrorMessageInfo(code=999, message='Error 999'))
    time.sleep(2)

    curses_mgr.update_message_counter(99)
    curses_mgr.update_lass_error(ErrorMessageInfo(code=0, message='No Error'))
    time.sleep(2)

    curses_mgr.close()
