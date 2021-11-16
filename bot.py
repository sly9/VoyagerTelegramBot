#!/usr/bin/env python3

import _thread
import json
import base64
import time
import uuid
from collections import deque
from datetime import datetime

import websocket

from configs import ConfigBuilder
from voyager_client import VoyagerClient
from log_writer import LogWriter


class VoyagerConnectionManager:
    """
    Low level class that maintains a live connection with voyager application server.
    It allows command sending, keep-alive, reconnect, etc.
    Logic to understand the content of each packet lives in 'VoyagerClient'.
    TODO: Consider reverse the order of creation. Maybe let voyager client create an instance of connection manager.
    """
    def __init__(self, config_builder=None):
        if config_builder is None:
            config_builder = ConfigBuilder()
        self.config = config_builder.build()
        self.voyager_settings = self.config.voyager_setting

        self.ws = None
        self.keep_alive_thread = None
        self.voyager_client = VoyagerClient(config_builder=config_builder)
        self.command_queue = deque([])
        self.ongoing_command = None
        self.next_id = 1

        self.log_writer = LogWriter(config_builder=config_builder)

        self.reconnect_delay_sec = 1
        self.should_exit_keep_alive_thread = False

    def send_command(self, command_name, params):
        params['UID'] = str(uuid.uuid1())
        command = {
            'method': command_name,
            'params': params,
            'id': self.next_id
        }
        self.next_id = self.next_id + 1
        self.command_queue.append(command)
        self.try_to_process_next_command()

    def try_to_process_next_command(self):
        if self.ongoing_command is not None:
            print('wait a while before sending out the second command.')
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
            return

        event = message['Event']
        self.voyager_client.parse_message(event, message)

    def on_error(self, ws, error):
        self.log_writer.maybe_flush()
        print("### {error} ###".format(error=error))

    def on_close(self, ws, close_status_code, close_msg):
        print("### [{code}] {msg} ###".format(code=close_status_code, msg=close_msg))
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
        if self.keep_alive_thread is None:
            self.should_exit_keep_alive_thread = False
            self.keep_alive_thread = _thread.start_new_thread(self.keep_alive_routine, ())

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
    connection_manager = VoyagerConnectionManager()
    connection_manager.run_forever()
