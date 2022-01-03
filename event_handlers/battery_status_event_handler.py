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
        self.throttle_count = 0  # A throttle counter, limits the frequency of sending local battery alerts.
        self.memory_usage_history = deque(maxlen=8640)  # 1 data point for 10 sec duration => 1 day usage.
        self.start_gathering()

    def interested_event_names(self):
        try:
            battery = psutil.sensors_battery()
            if battery is None:
                ee.emit(BotEvent.UPDATE_BATTERY_PERCENTAGE.name,
                        battery_percentage=SpecialBatteryPercentageEnum.NOT_AVAILABLE, update=False)
                return list()
            return ['LogEvent', 'ShotRunning', 'ControlData']
        except Exception as exception:
            ee.emit(BotEvent.UPDATE_BATTERY_PERCENTAGE.name,
                    battery_percentage=SpecialBatteryPercentageEnum.NOT_AVAILABLE, update=False)
            return list()

    def handle_event(self, event_name: str, message: Dict):
        if not self.config.monitor_local_computer:
            ee.emit(BotEvent.UPDATE_BATTERY_PERCENTAGE.name,
                    battery_percentage=SpecialBatteryPercentageEnum.NOT_MONITORED, update=False)
            return
        self.check_battery_status()

    def start_gathering(self):
        if self.thread:
            return
        self.thread = threading.Thread(target=self.run_loop)
        self.thread.daemon = True
        self.thread.start()

    def run_loop(self):
        while True:
            self.maybe_add_memory_datapoint()
            sleep(10)

    def maybe_add_memory_datapoint(self):
        # Iterate over the list
        voyager_usage = None
        bot_usage = None
        bot_pid = os.getpid()
        for proc in psutil.process_iter():
            try:
                # Fetch process details as dict
                pinfo = proc.as_dict(attrs=['pid', 'name', 'username'])
                if pinfo['name'] == 'Voyager2.exe':
                    voyager_usage = proc.memory_info().vms / (1024 * 1024)
                if pinfo['pid'] == bot_pid:
                    bot_usage = proc.memory_info().vms / (1024 * 1024)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        timestamp = datetime.datetime.now().timestamp()
        memory_usage = MemoryUsage(timestamp=timestamp, voyager_vms=voyager_usage, bot_vms=bot_usage)
        self.memory_usage_history.append(memory_usage)
        ee.emit(BotEvent.UPDATE_MEMORY_USAGE.name,
                memory_history=self.memory_usage_history, memory_usage=memory_usage)

    def check_battery_status(self):
        battery_msg = ''
        battery = psutil.sensors_battery()
        if battery.power_plugged:
            ee.emit(BotEvent.UPDATE_BATTERY_PERCENTAGE.name,
                    battery_percentage=SpecialBatteryPercentageEnum.ON_AC_POWER, update=False)
            battery_msg = 'AC power is connected.'
        elif battery.percent > 30:
            battery_msg = f'Battery ({battery.percent}%)'
        else:
            battery_msg = f'!!Critical battery ({battery.percent}%)!!'

        telegram_message = f'<b><pre>{battery_msg}</pre></b>'

        if self.throttle_count < 30:
            self.throttle_count += 1
        else:
            ee.emit(BotEvent.UPDATE_BATTERY_PERCENTAGE.name,
                    battery_percentage=SpecialBatteryPercentageEnum.ON_AC_POWER, update=True)
            ee.emit(BotEvent.SEND_TEXT_MESSAGE.name, telegram_message)
            self.throttle_count = 0
