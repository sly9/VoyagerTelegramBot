import os
import sys

import yaml
from rich.prompt import Confirm, Prompt, IntPrompt

from console import main_console



def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class Wizard:
    def __init__(self, config_yml_path: str = 'config.yml', config_yml_example_path: str = 'config.yml.example'):
        config_yml_path = os.path.abspath(config_yml_path)
        config_yml_example_path = resource_path(config_yml_example_path)

        self.config_yml_path = config_yml_path
        self.config_yml_example_path = config_yml_example_path

    def go(self):
        main_console.print('Welcome to Voyager bot! To get started, let me ask you a few questions: ')

        domain, port, username, password = self.configure_voyager_connection()
        main_console.print(locals())
        should_enable_telegram = Confirm.ask('Do you want to enable telegram notifications?', default=True)
        if should_enable_telegram:
            telegram_token, telegram_chat_id = self.configure_telegram()

        enable_fancy_ui = Confirm.ask('This bot also prints fancy commmand line UI, do you want to try it out?',
                                      default=True)
        self.write_to_file(domain=domain, port=port, username=username, password=password,
                           should_enable_telegram=should_enable_telegram, telegram_token=telegram_token,
                           telegram_chat_id=telegram_chat_id, enable_fancy_ui=enable_fancy_ui)

    def write_to_file(self, domain, port, username, password, should_enable_telegram, telegram_token, telegram_chat_id,
                      enable_fancy_ui):
        with open(self.config_yml_example_path, 'r') as template_file, open(self.config_yml_path, 'w') as yaml_file:
            try:
                config = yaml.safe_load(template_file)

                config['voyager_setting']['domain'] = domain
                config['voyager_setting']['port'] = port
                if username and password:
                    config['voyager_setting']['username'] = username
                    config['voyager_setting']['password'] = password

                if should_enable_telegram:
                    config['telegram_enabled'] = should_enable_telegram
                    config['telegram_setting']['bot_token'] = telegram_token
                    config['telegram_setting']['chat_id'] = telegram_chat_id

                if enable_fancy_ui:
                    config['console_config']['console_type'] = 'FULL'
                else:
                    config['console_config']['console_type'] = 'PLAIN'
                yaml.safe_dump(config, yaml_file)
            except Exception as exc:
                main_console.print_exception(exc)
                return 'LOAD_CONFIG_FAILED'

    def configure_voyager_connection(self):
        main_console.print('Let\'s start with voyager connection. \n'
                           'If you\'ve been  using web dashboard to voyager, these questions should be familiar to you')
        domain = Prompt.ask('What is the domain name or IP address of your voyager application server?\n'
                            'If you are running voyager bot and voyager on the same machine, it\'s usually ',
                            default='127.0.0.1')
        port = IntPrompt.ask('What is the port of voyager application server?\n', default=5950)
        need_authentication = Confirm.ask('Do you need to type in username and password when log on?', default=False)
        if not need_authentication:
            return domain, port, None, None

        username = Prompt.ask('What is the username?')
        password = Prompt.ask('What is the password?')
        return domain, port, username, password

    def configure_telegram(self):
        main_console.print(
            'To setup telegram notifications, first you need a bot..'
            ' please follow instructions here: https://core.telegram.org/bots#3-how-do-i-create-a-bot')
        token = Prompt.ask('Now we need an auth token to continue.\n'
                           'It\'s usually a 10digit number and ~30characters concatenated with a colon. \n'
                           'Please keep your token secure.\n'
                           'Now please type your token here')
        chat_id = IntPrompt.ask('Next question is chat id. It\'s usually a long integer number.\n'
                                'What is the chat id you want your messages to be sent to?')
        main_console.print(token, chat_id, locals())
        return token, chat_id


if __name__ == '__main__':
    w = Wizard(config_yml_path='test.yml', config_yml_example_path='../config.yml.example')
    w.go()