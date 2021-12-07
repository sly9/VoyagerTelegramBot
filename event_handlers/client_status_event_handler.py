from typing import Dict

import psutil

from configs import ConfigBuilder
from event_handlers.voyager_event_handler import VoyagerEventHandler
from telegram import TelegramBot


class ClientStatusEventHandler(VoyagerEventHandler):
    def __init__(self, config_builder: ConfigBuilder, telegram_bot: TelegramBot):
        super().__init__(config_builder=config_builder, telegram_bot=telegram_bot,
                         handler_name='ClientStatusEventHandler')
        self.battery_disabled = False

    @staticmethod
    def interested_event_names():
        return ['LogEvent', 'ShotRunning', 'ControlData']

    def handle_event(self, event_name: str, message: Dict):
        battery_msg = ''
        if self.config.monitor_battery and not self.battery_disabled:
            battery = psutil.sensors_battery()
            if battery is None:
                #  If no battery is installed or metrics can’t be determined
                battery_msg = 'Cannot detect battery info'
                self.battery_disabled = True
            elif battery.power_plugged:
                battery_msg = 'AC power is connected.'
            elif battery.percent > 30:
                battery_msg = f'Battery ({battery.percent}%)'
            else:
                battery_msg = f'!!Critical battery ({battery.percent}%)!!'

        telegram_message = f'<b><pre>{battery_msg}</pre></b>'
        self.telegram_bot.send_text_message(telegram_message)
