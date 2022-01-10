from typing import Dict

from data_structure.host_info import HostInfo, VoyagerConnectionStatus
from event_emitter import ee
from event_handlers.voyager_event_handler import VoyagerEventHandler
from event_names import BotEvent


class MiscellaneousEventHandler(VoyagerEventHandler):
    def __init__(self, config):
        super().__init__(config=config)
        self.message_counter = 0
        self.i18n = self.config.i18n.messages

    def interested_in_all_events(self):
        return True

    def handle_event(self, event_name: str, message: Dict):
        self.message_counter += 1
        if event_name == 'Version':
            self.handle_version(message)
        ee.emit(BotEvent.UPDATE_MESSAGE_COUNTER.name, counter_number=self.message_counter)

    def handle_version(self, message: Dict):
        host_info = HostInfo(host_name=message['Host'],
                             url=self.config.voyager_setting.domain,
                             port=str(self.config.voyager_setting.port),
                             voyager_ver=message['VOYVersion'],
                             connection_status=VoyagerConnectionStatus.CONNECTED)
        telegram_message = self.i18n['host_connected'].format(host_name=host_info.host_name,
                                                              url=host_info.url,
                                                              version=host_info.voyager_ver)
        ee.emit(BotEvent.UPDATE_HOST_INFO.name, host_info=host_info)
        ee.emit(BotEvent.SEND_TEXT_MESSAGE.name, telegram_message)
