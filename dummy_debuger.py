import time

from bot import VoyagerConnectionManager


class DummyDebugger:
    def __init__(self, interval: int = 5):
        self.interval = interval
        self.messages = None

        self.connection_manager = VoyagerConnectionManager()

    def load_messages(self, msg_fn: str = None):
        with open(msg_fn, 'r') as msg_f:
            self.messages = msg_f.readlines()

    def dummy_send(self):
        for msg in self.messages:
            self.connection_manager.on_message(ws=None, message_string=msg.strip())
            time.sleep(self.interval)


if __name__ == "__main__":
    dd = DummyDebugger(interval=1)
    dd.load_messages('log_json_dump.txt')
    dd.dummy_send()
