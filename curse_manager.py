import curses
import time
from collections import deque
from typing import Dict

from data_structure.host_info import HostInfo
from data_structure.log_info import LogInfo
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
        self.last_error_dict = {'error_code': 0, 'description': ''}
        self.received_message_counter = 0
        self.host_info = HostInfo()
        self.log_queue = deque(maxlen=10)
        self.battery_percentage = 100

    def _update_whole_scr(self):
        self.stdscr.clear()
        line_pos = 0

        # Horizontal Line
        self.stdscr.addstr(line_pos, 0, '+' + '-' * 118 + '+', self.normal_style)
        line_pos += 1

        # Version and Host Information
        self.stdscr.addstr(line_pos, 0,
                           f'|     VoyagerTelegramBot v{bot_version_string()}     |',
                           self.normal_style)
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
            if self.battery_percentage > 75:
                self.stdscr.addstr(f' {self.battery_percentage:^13} ', self.safe_style)
            elif self.battery_percentage <= 25:
                self.stdscr.addstr(f' {self.battery_percentage:^13} ', self.critical_style)
            else:
                self.stdscr.addstr(f' {self.battery_percentage:^13} ', self.warning_style)
        self.stdscr.addstr('|', self.normal_style)
        line_pos += 1

        # Horizontal Line
        self.stdscr.addstr(line_pos, 0, '+' + '-' * 118 + '+', self.normal_style)
        line_pos += 1

        # Error
        self.stdscr.addstr(line_pos, 0, f'| ', self.normal_style)

        if self.last_error_dict['error_code'] == 0:
            error_str = 'Everything is AWESOME!'
            self.stdscr.addstr(f'{error_str:116}', self.normal_style)
        else:
            error_str = f'[{self.last_error_dict["error_code"]}] {self.last_error_dict["description"]}'
            self.stdscr.addstr(f'{error_str:116.116}', self.critical_style)

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
        self.stdscr.addstr(line_pos, 0,
                           f'| {counter_str:116.116} |',
                           self.normal_style)

        line_pos += 1
        # Horizontal Line
        self.stdscr.addstr(line_pos, 0, '+' + '-' * 118 + '+', self.normal_style)

        self.stdscr.refresh()

    def update_message_counter(self, counter_number: int = 0):
        self.received_message_counter = counter_number
        self._update_whole_scr()

    def update_lass_error(self, error_dict: Dict = None):
        if error_dict and 'error_code' in error_dict and 'description' in error_dict:
            self.last_error_dict = error_dict
            self._update_whole_scr()

    def update_host_info(self, host_info: HostInfo):
        self.host_info = host_info
        self._update_whole_scr()

    def update_battery_percentage(self, battery_percentage: int = 0, update: bool = True):
        self.battery_percentage = battery_percentage
        if update:
            self._update_whole_scr()

    def append_log(self, new_message: LogInfo = None):
        self.log_queue.append(new_message)
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
    curses_mgr.update_lass_error({'error_code': 111, 'description': 'xxx'})
    time.sleep(2)

    curses_mgr.update_message_counter(99)
    curses_mgr.update_lass_error({'error_code': 0, 'description': ''})
    time.sleep(2)

    curses_mgr.close()
