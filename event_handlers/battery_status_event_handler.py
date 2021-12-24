from typing import Dict

import psutil

from curse_manager import CursesManager
from data_structure.special_battery_percentage import SpecialBatteryPercentageEnum
from event_handlers.voyager_event_handler import VoyagerEventHandler
from telegram import TelegramBot

from event_emitter import ee
from event_names import BotEvent


class BatteryStatusEventHandler(VoyagerEventHandler):
    """
    An event handler which is interested in local -- the bot's local, not voyager application's local, battery status.
    """

    def __init__(self, config, telegram_bot: TelegramBot, curses_manager: CursesManager):
        super().__init__(config=config, telegram_bot=telegram_bot,
                         handler_name='BatteryStatusEventHandler',
                         curses_manager=curses_manager)
        self.throttle_count = 0  # A throttle counter, limits the frequency of sending local battery alerts.

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
        battery_msg = ''
        if not self.config.monitor_battery:
            ee.emit(BotEvent.UPDATE_BATTERY_PERCENTAGE.name,
                    battery_percentage=SpecialBatteryPercentageEnum.NOT_MONITORED, update=False)
            return

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
            self.send_text_message(telegram_message)
            self.throttle_count = 0
