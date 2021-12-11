from typing import Dict

from event_handlers.voyager_event_handler import VoyagerEventHandler
from telegram import TelegramBot


class MiscellaneousEventHandler(VoyagerEventHandler):
    def __init__(self, config, telegram_bot: TelegramBot):
        super().__init__(config=config, telegram_bot=telegram_bot, handler_name='MiscellaneousEventHandler')

        self.message_counter = 0

    def handle_event(self, event_name: str, message: Dict):
        self.message_counter += 1
        if event_name == 'Version':
            self.handle_version(message)

        print(f'\r{self.message_counter} message(s) have been received and handled.', end='', flush=True)

    def handle_version(self, message: Dict):
        telegram_message = 'Connected to <b>{host_name}({url})</b> [{version}]'.format(
            host_name=message['Host'],
            url=self.config.voyager_setting.domain,
            version=message['VOYVersion'])

        if self.telegram_bot:
            self.telegram_bot.send_text_message(telegram_message)
