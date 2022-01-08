import datetime
import os
import threading
from collections import deque
from time import sleep
from typing import Dict

import psutil

from data_structure.special_battery_percentage import SpecialBatteryPercentageEnum, MemoryUsage
from event_emitter import ee
from event_handlers.voyager_event_handler import VoyagerEventHandler
from event_names import BotEvent


class BatteryStatusEventHandler(VoyagerEventHandler):
    """
    An event handler which is interested in local -- the bot's local, not voyager application's local, battery status.
    """

    def __init__(self, config):
        super().__init__(config=config)
        self.thread = None

        self.last_battery_warning_timestamp = datetime.datetime.now()
        self.battery_check_enabled = True
        self.last_battery_status = None

        self.memory_usage_history = deque(maxlen=8640)  # 1 data point for 10 sec duration => 1 day usage.
        self.start_gathering()


    def interested_event_names(self):
        return ['LogEvent', 'ShotRunning', 'ControlData']

    def handle_event(self, event_name: str, message: Dict):
        if not self.config.monitor_local_computer:
            ee.emit(BotEvent.UPDATE_BATTERY_PERCENTAGE.name,
                    battery_percentage=SpecialBatteryPercentageEnum.NOT_MONITORED, update=False)
            return

        self.check_battery_status()

        # Check log content and see if there's an OOM exception
        if event_name == 'LogEvent':
            text = message['Text']  # type: str
            if text.lower().find('insufficient memory') >= 0 or text.lower().find('OutOfMemoryException') >= 0:
                self.maybe_add_memory_datapoint(oom_observed=True)

    def start_gathering(self):
        if self.thread:
            return
        self.thread = threading.Thread(target=self.run_loop)
        self.thread.daemon = True
        self.thread.start()

    def run_loop(self):
        while True:
            self.maybe_add_memory_datapoint()
            try:
                if datetime.datetime.now() - self.last_battery_warning_timestamp > datetime.timedelta(minutes=1):
                    self.check_battery_status()
                    self.last_battery_warning_timestamp = datetime.datetime.now()
            except Exception as exception:
                pass
            sleep(10)

    def maybe_add_memory_datapoint(self, oom_observed: bool = False):
        # Iterate over the list
        voyager_vms_usage = 0
        voyager_rss_usage = 0
        bot_vms_usage = 0
        bot_rss_usage = 0
        bot_pid = os.getpid()
        for proc in psutil.process_iter():
            try:
                # Fetch process details as dict
                pinfo = proc.as_dict(attrs=['pid', 'name', 'username'])
                if pinfo['name'] == 'Voyager2.exe':
                    voyager_vms_usage = proc.memory_info().vms / (1024 * 1024)
                    voyager_rss_usage = proc.memory_info().rss / (1024 * 1024)
                if pinfo['pid'] == bot_pid:
                    bot_vms_usage = proc.memory_info().vms / (1024 * 1024)
                    bot_rss_usage = proc.memory_info().rss / (1024 * 1024)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        timestamp = datetime.datetime.now().timestamp()
        memory_usage = MemoryUsage(timestamp=timestamp, voyager_vms=voyager_vms_usage, voyager_rss=voyager_rss_usage,
                                   bot_vms=bot_vms_usage, bot_rss=bot_rss_usage, oom_observed=oom_observed)
        self.memory_usage_history.append(memory_usage)
        ee.emit(BotEvent.UPDATE_MEMORY_USAGE.name,
                memory_history=self.memory_usage_history, memory_usage=memory_usage)

    def check_battery_status(self):
        battery = psutil.sensors_battery()
        if battery and self.last_battery_status and battery.percent == self.last_battery_status.percent and battery.power_plugged == self.last_battery_status.power_plugged:
            # nothing really changed, return.
            return

        if not battery:
            # no battery, nothing to watch for. just return
            return

        if battery.power_plugged:
            # this means battery status has changed from unplugged to plugged.
            ee.emit(BotEvent.UPDATE_BATTERY_PERCENTAGE.name,
                    battery_percentage=SpecialBatteryPercentageEnum.ON_AC_POWER, update=True)
            battery_msg = 'Power is back on AC again'
        else:
            if battery.percent > 30:
                battery_msg = f'Battery ({battery.percent}%)'
            else:
                battery_msg = f'!!Critical battery ({battery.percent}%)!!'

        telegram_message = f'<b><pre>{battery_msg}</pre></b>'
        ee.emit(BotEvent.UPDATE_BATTERY_PERCENTAGE.name,
                battery_percentage=SpecialBatteryPercentageEnum.ON_AC_POWER, update=True)
        ee.emit(BotEvent.SEND_TEXT_MESSAGE.name, telegram_message)

        self.last_battery_status = battery
