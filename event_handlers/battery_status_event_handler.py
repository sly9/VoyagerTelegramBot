from typing import Dict

import psutil

from event_handlers.voyager_event_handler import VoyagerEventHandler
from telegram import TelegramBot


class BatteryStatusEventHandler(VoyagerEventHandler):
    """
    An event handler which is interested in local -- the bot's local, not voyager application's local, battery status.
    """

    def __init__(self, config, telegram_bot: TelegramBot):
        super().__init__(config=config, telegram_bot=telegram_bot,
                         handler_name='BatteryStatusEventHandler')
        self.throttle_count = 0  # A throttle counter, limits the frequency of sending local battery alerts.

    @staticmethod
    def interested_event_names():
        try:
            battery = psutil.sensors_battery()
            if battery is None:
                return []
            return ['LogEvent', 'ShotRunning', 'ControlData']
        except Exception:
            return []

    def handle_event(self, event_name: str, message: Dict):
        battery_msg = ''
        if not self.config.monitor_battery:
            return
        battery = psutil.sensors_battery()
        if battery.power_plugged:
            battery_msg = 'AC power is connected.'
        elif battery.percent > 30:
            battery_msg = f'Battery ({battery.percent}%)'
        else:
            battery_msg = f'!!Critical battery ({battery.percent}%)!!'

        telegram_message = f'<b><pre>{battery_msg}</pre></b>'
        self.send_text_message(telegram_message)

    def send_text_message(self, message: str):
        if self.throttle_count < 30:
            self.throttle_count += 1
        else:
            self.telegram_bot.send_text_message(message)
            self.throttle_count = 0
