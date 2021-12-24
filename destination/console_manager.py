#!/bin/env python3

from curse_manager import CursesManager
from data_structure.error_message_info import ErrorMessageInfo
from data_structure.host_info import HostInfo
from data_structure.job_status_info import JobStatusInfo
from data_structure.log_message_info import LogMessageInfo
from event_emitter import ee
from event_names import BotEvent


class ConsoleManager:
    def __init__(self, config=None, curses_manager: CursesManager = None):
        self.config = config
        self.curses_manager = curses_manager
        ee.on(BotEvent.UPDATE_BATTERY_PERCENTAGE.name, self.update_battery_percentage)
        ee.on(BotEvent.UPDATE_MESSAGE_COUNTER.name, self.update_message_counter)
        ee.on(BotEvent.UPDATE_HOST_INFO.name, self.update_host_info)
        ee.on(BotEvent.UPDATE_JOB_STATUS.name, self.update_job_status)
        ee.on(BotEvent.APPEND_ERROR_LOG.name, self.append_error)
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

    def append_error(self, error: ErrorMessageInfo = None):
        if not self.curses_manager:
            return
        self.curses_manager.update_lass_error(error_info=error)

    def append_log(self, log: LogMessageInfo = None):
        if not self.curses_manager:
            return
        self.curses_manager.append_log(new_message=log)

    def update_job_status(self, job_status: JobStatusInfo = None):
        if not self.curses_manager:
            return
        self.curses_manager.update_job_status_info(job_status_info=job_status)

    # private methods
