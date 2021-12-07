from typing import Dict

from configs import ConfigBuilder
from event_handlers.voyager_event_handler import VoyagerEventHandler
from telegram import TelegramBot


# This is just one of the event handlers which are interested in log events. You can write more
class LogEventHandler(VoyagerEventHandler):
    def __init__(self, config_builder: ConfigBuilder, telegram_bot: TelegramBot):
        super().__init__(config_builder=config_builder, telegram_bot=telegram_bot, handler_name='LogEventHandler')

    @staticmethod
    def interested_event_name():
        return 'LogEvent'

    def handle_event(self, event_name: str, message: Dict):
        type_dict = {1: 'DEBUG', 2: 'INFO', 3: 'WARNING', 4: 'CRITICAL', 5: 'ACTION', 6: 'SUBTITLE', 7: 'EVENT',
                     8: 'REQUEST', 9: 'EMERGENCY'}
        type_name = type_dict[message['Type']]
        content = f'[{type_name}]{message["Text"]}'
        telegram_message = f'<b><pre>{content}</pre></b>'
        allowed_log_type_names = self.config.text_message_config.allowed_log_types
        if type_name in allowed_log_type_names:
            self.telegram_bot.send_text_message(telegram_message)
