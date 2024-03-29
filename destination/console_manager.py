#!/bin/env python3

from curse_manager import CursesManager
from data_structure.host_info import HostInfo
from data_structure.log_message_info import LogMessageInfo
from data_structure.system_status_info import SystemStatusInfo
from event_emitter import ee
from event_names import BotEvent


class ConsoleManager:
    def __init__(self, config=None, curses_manager: CursesManager = None):
        self.config = config
        self.curses_manager = curses_manager
        ee.on(BotEvent.UPDATE_BATTERY_PERCENTAGE.name, self.update_battery_percentage)
        ee.on(BotEvent.UPDATE_MESSAGE_COUNTER.name, self.update_message_counter)
        ee.on(BotEvent.UPDATE_HOST_INFO.name, self.update_host_info)
        ee.on(BotEvent.UPDATE_SYSTEM_STATUS.name, self.update_system_status_info)
        ee.on(BotEvent.APPEND_LOG.name, self.append_log)

    # public methods
    def update_message_counter(self, counter_number: int = 0):
        if not self.curses_manager:
            return
        self.curses_manager.update_message_counter(counter_number=counter_number)

    def update_host_info(self, host_info: HostInfo):
        if not self.curses_manager:
            return
        self.curses_manager.update_host_info(host_info=host_info)

    def update_battery_percentage(self, battery_percentage: int = 0, update: bool = True):
        if not self.curses_manager:
            return
        self.curses_manager.update_battery_percentage(battery_percentage=battery_percentage, update=update)

    def append_log(self, log: LogMessageInfo = None):
        if not self.curses_manager:
            return
        self.curses_manager.append_log(new_message=log)

    def update_system_status_info(self, job_status: SystemStatusInfo = None):
        if not self.curses_manager:
            return
        self.curses_manager.update_system_status_info(system_status_info=job_status)

    # private methods
