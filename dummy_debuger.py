import time

import console
from bot import VoyagerConnectionManager
from configs import ConfigBuilder


class DummyDebugger:
    def __init__(self):
        self.messages = None
        config_builder = ConfigBuilder()
        config = config_builder.build()
        config.debugging = True
        config.telegram_enabled = False
        config.console_type = 'FULL'
        config.html_report_enabled = False
        config.should_dump_log = False
        self.connection_manager = VoyagerConnectionManager(config=config)

    def load_messages(self, msg_fn: str = None):
        with open(msg_fn, 'r') as msg_f:
            self.messages = msg_f.readlines()

    def dummy_send(self):
        for msg in self.messages:
            self.connection_manager.on_message(ws=None, message_string=msg.strip())

    def good_night(self):
        if self.connection_manager.voyager_client.html_reporter:
            self.connection_manager.voyager_client.html_reporter.write_footer()


if __name__ == "__main__":
    dd = DummyDebugger()
    dd.load_messages('2021_12_18__voyager_bot_log.txt')
    dd.dummy_send()
    dd.good_night()
    console.console.save_html('./replay/stdout.html')
