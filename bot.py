#!/usr/bin/env python3

import uuid
import websocket
import _thread
import time
import json
from datetime import datetime
from collections import deque
from voyager_client import VoyagerClient

class VoyagerConnectionManager:
    SERVER_ADDRESS='ws://liuyi.us:5950/'
    
    def __init__(self):
        self.ws = None
        self.keep_alive_thread = None
        self.voyager_client = VoyagerClient()
        self.command_queue = deque([])
        self.ongoing_command = None
        self.next_id = 1
        
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
        print('sending command .. %s' % json.dumps(command))
        self.ws.send(json.dumps(command)+'\r\n')

    def on_message(self,ws, message_string):
        message = json.loads(message_string)
        
        if 'jsonrpc' in message:
            print(message)
            # some command finished, try to see if we have anything else.
            self.ongoing_command = None
            self.try_to_process_next_command()
            return
        event = message['Event']
        self.voyager_client.parse_message(event, message)

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws, close_status_code, close_msg):
        print("### closed ###")

    def on_open(self,ws):
        self.send_command('RemoteSetDashboardMode', {'IsOn': True})
        self.send_command('RemoteSetLogEvent', {'IsOn': True, 'Level': 0})
        if self.keep_alive_thread is None:
            self.keep_alive_thread = _thread.start_new_thread(self.keep_alive_routine, ())
        

    def run_forever(self):
        self.ws = websocket.WebSocketApp(VoyagerConnectionManager.SERVER_ADDRESS,
                            on_open=self.on_open,
                            on_message=self.on_message,
                            on_error=self.on_error,
                            on_close=self.on_close)
        self.ws.run_forever()


    def keep_alive_routine(self):
        count = 0
        while True:            
            self.ws.send('{"Event":"Polling","Timestamp":%d,"Inst":1}\r\n' % time.time())
            time.sleep(5)
        


if __name__ == "__main__":
    #websocket.enableTrace(True)
    connection_manager = VoyagerConnectionManager()
    connection_manager.run_forever()