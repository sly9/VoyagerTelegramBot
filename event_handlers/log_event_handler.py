from typing import Dict

from data_structure.log_message_info import LogMessageInfo
from event_emitter import ee
from event_handlers.voyager_event_handler import VoyagerEventHandler
from event_names import BotEvent


# This is just one of the event handlers which are interested in log events. You can write more
class LogEventHandler(VoyagerEventHandler):
    def __init__(self, config):
        super().__init__(config=config)

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
            ee.emit(BotEvent.APPEND_LOG.name,
                    log=LogMessageInfo(type=type_name, message=message['Text']))
            ee.emit(BotEvent.SEND_TEXT_MESSAGE.name, telegram_message)
