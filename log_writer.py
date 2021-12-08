#!/bin/env python3
from configs import ConfigBuilder
from datetime import timedelta
from datetime import datetime
import pytz
import os


class LogWriter:
    def __init__(self, config):
        self.config = config
        self._log_file = None
        self.should_dump_log = self.config.should_dump_log

    def __current_log_file_created_time(self):
        if not self._log_file:
            return None
        timestamp = os.stat(self._log_file.name).st_ctime
        timezone = pytz.timezone(self.config.timezone)
        return datetime.fromtimestamp(timestamp, tz=timezone)

    def write_line(self, message):
        if not self.should_dump_log:
            return
        self.current_log_file().write(message.strip() + '\n')

    def maybe_flush(self):
        if self._log_file and not self._log_file.closed:
            self._log_file.flush()

    def close(self):
        self.maybe_flush()
        if self._log_file and not self._log_file.closed:
            self._log_file.close()
            self._log_file = None

    def current_log_file(self):
        """Always returns a writable log file."""
        if self.__should_create_new_log_file():
            self.__create_new_log_file()
        return self._log_file

    def __should_create_new_log_file(self):
        if not self._log_file or self._log_file.closed:
            return True
        timezone = pytz.timezone(self.config.timezone)
        log_file_created_time = self.__current_log_file_created_time()
        old = log_file_created_time - timedelta(hours=12)
        now = datetime.now(timezone)
        if old.day == now.day and old.month == now.month and old.year == now.year:
            # still pretty new, reuse it.
            return False
        # current log file is old, create new one.
        return True

    def __create_new_log_file(self):
        now = datetime.now()
        date_str = now.strftime('%Y_%m_%d_')
        self.close()
        self._log_file = open(date_str + '_voyager_bot_log.txt', 'a')
        return self._log_file
