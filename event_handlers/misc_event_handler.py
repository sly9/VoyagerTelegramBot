from typing import Dict

from curse_manager import CursesManager
from data_structure.host_info import HostInfo
from event_handlers.voyager_event_handler import VoyagerEventHandler
from telegram import TelegramBot


class MiscellaneousEventHandler(VoyagerEventHandler):
    def __init__(self, config, telegram_bot: TelegramBot, curses_manager: CursesManager):
        super().__init__(config=config,
                         telegram_bot=telegram_bot,
                         handler_name='MiscellaneousEventHandler',
                         curses_manager=curses_manager)
        self.message_counter = 0

    def interested_in_all_events(self):
        return True

    def handle_event(self, event_name: str, message: Dict):
        self.message_counter += 1
        if event_name == 'Version':
            self.handle_version(message)

        self.curses_manager.update_message_counter(counter_number=self.message_counter)

    def handle_version(self, message: Dict):
        host_info = HostInfo(host_name=message['Host'],
                             url=self.config.voyager_setting.domain,
                             port=str(self.config.voyager_setting.port),
                             voyager_ver=message['VOYVersion'])
        telegram_message = 'Connected to <b>{host_name}({url})</b> [{version}]'.format(
            host_name=host_info.host_name,
            url=host_info.url,
            version=host_info.voyager_ver)

        self.curses_manager.update_host_info(host_info=host_info)

        self.send_text_message(telegram_message)
