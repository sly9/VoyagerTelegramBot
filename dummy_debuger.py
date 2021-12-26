import sys
import time

import console
from bot import VoyagerConnectionManager
from configs import ConfigBuilder


class DummyDebugger:
    def __init__(self):
        self.file_name = None
        config_builder = ConfigBuilder(config_filename='config.yml')
        if validate_result := config_builder.validate():
            print(f'validation failed: {validate_result}')
            if validate_result == 'NO_CONFIG_FILE':
                config_builder.copy_template()

            elif validate_result == 'LOAD_CONFIG_FAILED':
                print('Something is clearly wrong with the config!!')
            elif validate_result == 'TEMPLATE_VERSION_DIFFERENCE':
                config_builder.merge()
            sys.exit()
        config = config_builder.build()
        config.telegram_enabled = False
        config.console_type = 'FULL'
        config.html_report_enabled = False
        config.should_dump_log = False

        self.connection_manager = VoyagerConnectionManager(config=config)

    def load_messages(self, filename: str = None):
        self.file_name = filename

    def dummy_send(self):
        counter = 0
        with open(self.file_name, 'r') as infile:
            for line in infile:
                self.connection_manager.on_message(ws=None, message_string=line.strip())
                counter = counter + 1
                if counter == 100:
                    time.sleep(0.01)
                    counter = 0

    def good_night(self):
        if hasattr(self.connection_manager.voyager_client, 'html_reporter'):
            self.connection_manager.voyager_client.html_reporter.write_footer()


if __name__ == "__main__":
    dd = DummyDebugger()
    dd.load_messages('2021_12_18__voyager_bot_log.txt')
    dd.dummy_send()
    dd.good_night()
    console.console.save_html('./replay/stdout.html')
