from typing import Dict

from curse_manager import CursesManager
from data_structure.log_message_info import LogMessageInfo
from event_handlers.voyager_event_handler import VoyagerEventHandler
from telegram import TelegramBot
from event_emitter import ee
from event_names import BotEvent


# This is just one of the event handlers which are interested in log events. You can write more
class LogEventHandler(VoyagerEventHandler):
    def __init__(self, config, telegram_bot: TelegramBot, curses_manager: CursesManager):
        super().__init__(config=config, telegram_bot=telegram_bot, handler_name='LogEventHandler', curses_manager=curses_manager)

    def interested_event_name(self):
        return 'LogEvent'

    def handle_event(self, event_name: str, message: Dict):
        # dictionary of log level number to readable name.
        type_dict = {1: 'DEBUG', 2: 'INFO', 3: 'WARNING', 4: 'CRITICAL', 5: 'ACTION', 6: 'SUBTITLE', 7: 'EVENT',
                     8: 'REQUEST', 9: 'EMERGENCY'}
        type_emoji_dict = {1: '🐞', 2: 'ℹ️', 3: '⚠️', 4: '⛔️', 5: '🔧', 6: '📢', 7: '📰',
                           8: '🈸', 9: '☢️'}

        type_emoji = type_emoji_dict[message['Type']]
        type_name = type_dict[message['Type']]

        telegram_message = f'{type_emoji}  <b><pre>{message["Text"]}</pre></b>'
        allowed_log_type_names = self.config.text_message_config.allowed_log_types

        if type_name in allowed_log_type_names:
            self.curses_manager.append_log(LogMessageInfo(type=type_name, message=message['Text']))
            self.send_text_message(telegram_message)
            ee.emit(BotEvent.SEND_TEXT_MESSAGE.name, telegram_message)

