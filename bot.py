#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import base64
import json
import os
import sys
import threading
import time
import uuid
from collections import deque
from pathlib import Path
import websocket
from rich import pretty
from rich.console import Console
from websocket import WebSocketAddressException

from configs import ConfigBuilder
from console import main_console
from data_structure.host_info import VoyagerConnectionStatus, HostInfo
from event_emitter import ee
from event_names import BotEvent
from log_writer import LogWriter
from voyager_client import VoyagerClient
from utils.localization import get_translated_text as _, select_locale

os.environ['PYTHONIOENCODING'] = 'utf-8'
pretty.install()


class VoyagerConnectionManager:
    """
    Low level class that maintains a live connection with voyager application server.
    It allows command sending, keep-alive, reconnect, etc.
    Logic to understand the content of each packet lives in 'VoyagerClient'.
    TODO: Consider reverse the order of creation. Maybe let voyager client create an instance of connection manager.
    """

    def __init__(self, config=None):
        self.config = config
        self.voyager_settings = self.config.voyager_setting

        select_locale(config.language)

        self.ws = None
        self.keep_alive_thread = None
        self.voyager_client = VoyagerClient(config=config)
        self.command_queue = deque([])
        self.ongoing_command = None
        self.next_id = 1

        self.log_writer = LogWriter(config=config)

        self.reconnect_delay_sec = 1
        self.should_exit_keep_alive_thread = False

        self.command_uid_to_method_name_dict = {}

    def send_command(self, command_name, params):
        command_uuid = str(uuid.uuid1())
        params['UID'] = command_uuid
        command = {
            'method': command_name,
            'params': params,
            'id': self.next_id
        }
        self.command_uid_to_method_name_dict[command_uuid] = command_name
        self.next_id = self.next_id + 1
        self.command_queue.append(command)
        self.try_to_process_next_command()

    def try_to_process_next_command(self):
        if self.ongoing_command is not None:
            # this command will be invoked later for sure
            return

        if len(self.command_queue) == 0:
            return

        command = self.command_queue.popleft()
        self.ongoing_command = command
        self.ws.send(json.dumps(command) + '\r\n')

    def on_message(self, ws, message_string):
        if not message_string or not message_string.strip():
            # Empty message string, nothing to do
            return

        message = json.loads(message_string)
        self.log_writer.write_line(message_string)

        if 'jsonrpc' in message:
            # some command finished, try to see if we have anything else.
            self.ongoing_command = None
            self.try_to_process_next_command()
            self.voyager_client.parse_message('jsonrpc', message)
        else:
            event_name = message['Event']
            if event_name == 'RemoteActionResult':
                uid = message['UID']
                command_name = self.command_uid_to_method_name_dict.get(uid, 'NOT_FOUND')
                message['MethodName'] = command_name
            self.voyager_client.parse_message(event_name, message)

    def on_error(self, ws, error):
        self.log_writer.maybe_flush()
        if isinstance(error, KeyboardInterrupt):
            self.config.allow_auto_reconnect = False
            main_console.print(_('Received KeyboardInterrupt, quit gracefully'))
        else:
            if type(error) == WebSocketAddressException or type(error) == ConnectionRefusedError:
                main_console.print(_('Connected refused'))
            else:
                main_console.print_exception(show_locals=True)

    def on_close(self, ws, close_status_code, close_msg):
        main_console.print(f'Closing connection, Code={close_status_code}, description= {close_msg}')
        host_info = HostInfo(host_name='',
                             url=self.config.voyager_setting.domain,
                             port=str(self.config.voyager_setting.port),
                             voyager_ver='',
                             connection_status=VoyagerConnectionStatus.DISCONNECTED)
        ee.emit(BotEvent.UPDATE_HOST_INFO.name, host_info=host_info)

        # try to reconnect with an exponentially increasing delay
        if self.config.allow_auto_reconnect:
            time.sleep(self.reconnect_delay_sec)
            if self.reconnect_delay_sec < 512:
                # doubles the reconnect delay so that we don't DOS server.
                self.reconnect_delay_sec = self.reconnect_delay_sec * 2
            # reset keep alive thread
            self.should_exit_keep_alive_thread = True
            self.keep_alive_thread = None
            self.run_forever()

    def on_open(self, ws):
        # Reset the reconnection delay to 1 sec
        self.reconnect_delay_sec = 1
        if hasattr(self.voyager_settings, 'username'):
            auth_token = f'{self.voyager_settings.username}:{self.voyager_settings.password}'
            encoded_token = base64.urlsafe_b64encode(auth_token.encode('ascii'))
            self.send_command('AuthenticateUserBase', {'Base': encoded_token.decode('ascii')})

        self.send_command('RemoteSetDashboardMode', {'IsOn': True})
        self.send_command('RemoteSetLogEvent', {'IsOn': True, 'Level': 0})
        self.send_command('RemoteGetFilterConfiguration', {})
        if self.keep_alive_thread is None:
            self.should_exit_keep_alive_thread = False
            thread = threading.Thread(target=self.keep_alive_routine)
            thread.daemon = True
            self.keep_alive_thread = thread
            thread.start()

    def run_forever(self):
        self.ws = websocket.WebSocketApp(
            'ws://{server_url}:{port}/'.format(server_url=self.voyager_settings.domain,
                                               port=self.voyager_settings.port),
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close)

        self.ws.run_forever()

    def keep_alive_routine(self):
        while not self.should_exit_keep_alive_thread:
            self.ws.send('{"Event":"Polling","Timestamp":%d,"Inst":1}\r\n' % time.time())
            time.sleep(5)


if __name__ == "__main__":
    config_builder = ConfigBuilder(config_filename='config.yml')

    if validate_result := config_builder.validate():
        main_console.print(_('validation failed: {}').format(validate_result))
        if validate_result == 'NO_CONFIG_FILE':
            config_builder.copy_template()

        elif validate_result == 'LOAD_CONFIG_FAILED':
            main_console.print(_('Something is clearly wrong with the config!!'))
        elif validate_result == 'TEMPLATE_VERSION_DIFFERENCE':
            config_builder.merge()
        sys.exit()

    config = config_builder.build()

    if config.console_config.console_type == 'FULL':
        Path(config.log_folder).mkdir(parents=True, exist_ok=True)
        sys.stderr = open(config.log_folder + '/error_log.txt', 'a')
        main_console = Console(stderr=True, color_system=None)
    else:
        main_console = Console()
    try:
        connection_manager = VoyagerConnectionManager(config=config)
        a = _('Something is clearly wrong with the config!')
        connection_manager.run_forever()
    except Exception as e:
        main_console.print_exception()
        print(e)
