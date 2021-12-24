#!/usr/bin/env python3

import _thread
import asyncio
import base64
import json
import time
import uuid
from collections import deque
from threading import Thread

import websocket

from configs import ConfigBuilder
from log_writer import LogWriter


class VoyagerConnectionManager(Thread):
    """
    Low level class that maintains a live connection with voyager application server.
    It allows command sending, keep-alive, reconnect, etc.
    Logic to understand the content of each packet lives in 'VoyagerClient'.
    TODO: Consider reverse the order of creation. Maybe let voyager client create an instance of connection manager.
    """

    def __init__(self, config=None, thread_id: str = 'WSThread'):
        Thread.__init__(self)
        self.thread_id = thread_id
        self.wst = None

        self.config = config
        self.voyager_settings = self.config.voyager_setting

        self.ws = None
        self.keep_alive_thread = None
        self.command_queue = deque([])
        self.ongoing_command = None
        self.current_command_future = None
        self.next_id = 1

        self.log_writer = LogWriter(config=config)

        self.reconnect_delay_sec = 1
        self.should_exit_keep_alive_thread = False

        self.receive_message_callback = None
        self.bootstrap = None
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    async def send_command(self, command_name, params, ):
        print('sending command..' + command_name)
        params['UID'] = str(uuid.uuid1())
        command = {
            'method': command_name,
            'params': params,
            'id': self.next_id
        }
        self.next_id = self.next_id + 1
        event_loop = asyncio.get_event_loop()
        future = event_loop.create_future()
        # future = asyncio.Future()

        self.command_queue.append((command, future))
        self.try_to_process_next_command()
        print('about to wait for a future, related to command ' + command_name, future)
        while not future.done():
            await asyncio.sleep(1)
        await future
        result = future.result()
        print('a previous future was complete, result is: ' + str(result), future)
        return result

    def try_to_process_next_command(self):
        if self.ongoing_command is not None:
            print('wait a while before sending out the second command.')
            # this command will be invoked later for sure
            return

        if len(self.command_queue) == 0:
            return

        command, future = self.command_queue.popleft()
        print('Trying to send out command' + str(command))
        self.ongoing_command = command
        self.current_command_future = future
        self.ws.send(json.dumps(command) + '\r\n')
        print('Sending command done')

    def on_message(self, ws, message_string):
        if not message_string or not message_string.strip():
            # Empty message string, nothing to do
            return

        message = json.loads(message_string)
        self.log_writer.write_line(message_string)

        if 'jsonrpc' in message:
            print('received a message that looks like a method result')
            # some command finished, try to see if we have anything else.
            self.ongoing_command = None
            print('setting future result to' + str(message), self.current_command_future)
            self.current_command_future.set_result(message)
            print('setting future result done', self.current_command_future)
            self.try_to_process_next_command()
            return

        event = message['Event']
        # self.voyager_client.parse_message(event, message)
        if self.receive_message_callback:
            self.receive_message_callback(event, message)

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
        # if self.bootstrap:
        #    task = self.loop.create_task(self.bootstrap())
        #    self.loop.run_until_complete(task)

        self.reconnect_delay_sec = 1

        if self.keep_alive_thread is None:
            self.should_exit_keep_alive_thread = False
            self.keep_alive_thread = _thread.start_new_thread(self.keep_alive_routine, ())

    def run_forever(self):
        print(str(self.thread_id) + " Starting thread")

        self.ws = websocket.WebSocketApp(
            'ws://{server_url}:{port}/'.format(server_url=self.voyager_settings.domain,
                                               port=self.voyager_settings.port),
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close)
        self.ws.keep_running = True
        self.wst = Thread(target=self.ws.run_forever)
        self.wst.daemon = True
        self.wst.start()

    def keep_alive_routine(self):
        while not self.should_exit_keep_alive_thread:
            self.ws.send('{"Event":"Polling","Timestamp":%d,"Inst":1}\r\n' % time.time())
            time.sleep(5)


async def main():
    websocket.enableTrace(True)
    c = ConfigBuilder()
    connection_manager = VoyagerConnectionManager(c)
    connection_manager.run_forever()

    time.sleep(1)

    auth_token = f'{connection_manager.voyager_settings.username}:{connection_manager.voyager_settings.password}'
    encoded_token = base64.urlsafe_b64encode(auth_token.encode('ascii'))
    result = await connection_manager.send_command('AuthenticateUserBase',
                                                   {'Base': encoded_token.decode('ascii')})
    print(result, 'step 1')

    result = await connection_manager.send_command('RemoteSetDashboardMode', {'IsOn': True})
    print(result, 'step 2')

    result = await connection_manager.send_command('RemoteSetLogEvent', {'IsOn': True, 'Level': 0})
    print(result, 'step 3')


if __name__ == "__main__":
    asyncio.run(main())
