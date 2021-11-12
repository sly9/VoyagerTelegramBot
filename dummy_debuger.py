import time

from bot import VoyagerConnectionManager
from configs import ConfigBuilder


class DummyDebugger:
    def __init__(self, interval: int = 5):
        self.interval = interval
        self.messages = None
        config_builder = ConfigBuilder()
        config = config_builder.build()
        config.debugging = True
        config.should_dump_log = False
        self.connection_manager = VoyagerConnectionManager(config_builder=config_builder)

    def load_messages(self, msg_fn: str = None):
        with open(msg_fn, 'r') as msg_f:
            self.messages = msg_f.readlines()

    def dummy_send(self):
        for msg in self.messages:
            self.connection_manager.on_message(ws=None, message_string=msg.strip())

    def good_night(self):
        self.connection_manager.voyager_client.telegram_bot.write_footer()



if __name__ == "__main__":
    dd = DummyDebugger(interval=0)
    dd.load_messages('log.txt')
    dd.dummy_send()
    dd.good_night()
