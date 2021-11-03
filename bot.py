#!/usr/bin/env python3

import _thread
import json
import time
import uuid
from collections import deque
from datetime import datetime

import websocket

from configs import Configs
from voyager_client import VoyagerClient


class VoyagerConnectionManager:
    def __init__(self):
        configs = Configs().configs
        self.voyager_url = configs['voyager_setting']['url']
        self.voyager_port = configs['voyager_setting']['port']

        self.ws = None
        self.keep_alive_thread = None
        self.voyager_client = VoyagerClient(configs=configs)
        self.command_queue = deque([])
        self.ongoing_command = None
        self.next_id = 1

        self.dump_log = 'log_json_fn' in configs
        if self.dump_log:
            now = datetime.now()
            date_str = now.strftime('%Y_%m_%d_')
            self.log_json_f = open(date_str + configs['log_json_fn'] + '.txt', 'w')

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
        # print('sending command .. %s' % json.dumps(command))
        self.ws.send(json.dumps(command) + '\r\n')

    def on_message(self, ws, message_string):
        if not message_string or not message_string.strip():
            # Empty message string, nothing to do
            return

        message = json.loads(message_string)
        if self.dump_log:
            self.log_json_f.write(message_string.strip() + '\n')

        if 'jsonrpc' in message:
            # some command finished, try to see if we have anything else.
            self.ongoing_command = None
            self.try_to_process_next_command()
            return

        event = message['Event']
        self.voyager_client.parse_message(event, message)

    def on_error(self, ws, error):
        if self.dump_log:
            self.log_json_f.flush()
            self.log_json_f.close()

        print("### {error} ###".format(error=error))

    def on_close(self, ws, close_status_code, close_msg):
        if self.dump_log:
            self.log_json_f.flush()
            self.log_json_f.close()

        print("### [{code}] {msg} ###".format(code=close_status_code, msg=close_msg))

    def on_open(self, ws):
        self.send_command('RemoteSetDashboardMode', {'IsOn': True})
        self.send_command('RemoteSetLogEvent', {'IsOn': True, 'Level': 0})
        if self.keep_alive_thread is None:
            self.keep_alive_thread = _thread.start_new_thread(self.keep_alive_routine, ())

    def run_forever(self):
        self.ws = websocket.WebSocketApp(
            'ws://{server_url}:{port}/'.format(server_url=self.voyager_url, port=self.voyager_port),
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close)

        self.ws.run_forever()

    def keep_alive_routine(self):
        while True:
            self.ws.send('{"Event":"Polling","Timestamp":%d,"Inst":1}\r\n' % time.time())
            time.sleep(5)


if __name__ == "__main__":
    # websocket.enableTrace(True)
    connection_manager = VoyagerConnectionManager()
    connection_manager.run_forever()
