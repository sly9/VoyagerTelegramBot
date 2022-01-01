import base64
import json
import os
import sys
import uuid

import requests
import yaml
from rich.prompt import Confirm, Prompt, IntPrompt
from websocket import create_connection

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
        self.test_connection(domain=domain, port=port, username=username, password=password,
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

    def test_connection(self, domain, port, username, password, should_enable_telegram, telegram_token,
                        telegram_chat_id, enable_fancy_ui):
        if should_enable_telegram:
            main_console.print('Validating telegram related settings...')
            if not (telegram_token and telegram_chat_id):
                main_console.print(
                    'You want telegram messages, but your token or chat_id is empty, I can\'t work without both',
                    locals())
                return False
            payload = {'chat_id': telegram_chat_id, 'text': 'Hello world!', 'parse_mode': 'html'}
            send_text_message_response = requests.post(f'https://api.telegram.org/bot{telegram_token}/sendMessage',
                                                       data=payload)
            response_json = json.loads(send_text_message_response.text)
            if response_json['ok']:
                main_console.print('You should\'ve received a hello world message on your telegram now, check it out?')
            else:
                main_console.print(
                    'I can\'t sent a message on your behalf.. here\'s some more details...',
                    locals())
                sys.exit(1)
        main_console.print('Validating voyager connections..')
        self.test_voyager_connection(domain=domain, port=port, username=username, password=password)
        return True

    def test_voyager_connection(self, domain, port, username, password):
        try:
            ws = create_connection(f'ws://{domain}:{port}/')
            if username and password:
                print("Send authentication")
                auth_token = f'{username}:{password}'
                encoded_token = base64.urlsafe_b64encode(auth_token.encode('ascii'))

                command_uuid = str(uuid.uuid1())
                command = {
                    'method': 'AuthenticateUserBase',
                    'params': {'Base': encoded_token.decode('ascii'), 'UID': command_uuid},
                    'id': 1
                }

                ws.send(json.dumps(command) + '\r\n')
                print("Sent")
            print("Receiving...")
            version_received = False
            authentication_succeeded = False
            if not (username and password):
                authentication_succeeded = True
            while not (version_received and authentication_succeeded):
                result = ws.recv()
                print("Received '%s'" % result)
                result_json = json.loads(result)
                if 'Event' in result_json and result_json['Event'] == 'Version':
                    version_received = True
                if 'jsonrpc' in result_json and 'authbase' in result_json:
                    authentication_succeeded = True
            ws.close()
        except Exception as exception:
            main_console.print_exception(exception)
            return False
        print('Validation succeeded!')
        return True


if __name__ == '__main__':
    w = Wizard(config_yml_path='test.yml', config_yml_example_path='../config.yml.example')
    w.go()
    #w.test_voyager_connection('liuyi.us', 5950, 'admin', 'A.qW!7q7F$')
