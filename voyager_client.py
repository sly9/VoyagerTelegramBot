#!/bin/env python3
from collections import defaultdict
from typing import Dict

from event_handlers.battery_status_event_handler import BatteryStatusEventHandler
from event_handlers.giant_event_handler import GiantEventHandler
from event_handlers.log_event_handler import LogEventHandler
from event_handlers.misc_event_handler import MiscellaneousEventHandler
from event_handlers.voyager_event_handler import VoyagerEventHandler
from html_telegram_bot import HTMLTelegramBot
from telegram import TelegramBot
import traceback


class VoyagerClient:
    def __init__(self, config=None):
        self.config = config
        self.telegram_bot = None

        if self.config.debugging:
            self.telegram_bot = HTMLTelegramBot()
        else:
            self.telegram_bot = TelegramBot(config=config)

        self.handler_dict = defaultdict(set)
        self.greedy_handler_set = set()

        miscellaneous_event_handler = MiscellaneousEventHandler(config=config, telegram_bot=self.telegram_bot)
        self.register_event_handler(miscellaneous_event_handler)

        giant_handler = GiantEventHandler(config=config, telegram_bot=self.telegram_bot)
        self.register_event_handler(giant_handler)

        log_event_handler = LogEventHandler(config=config, telegram_bot=self.telegram_bot)
        self.register_event_handler(log_event_handler)

        client_status_event_handler = BatteryStatusEventHandler(config=config, telegram_bot=self.telegram_bot)
        self.register_event_handler(client_status_event_handler)

    def parse_message(self, event_name: str, message: Dict):
        if event_name in self.handler_dict:
            for handler in self.handler_dict[event_name]:
                try:
                    handler.handle_event(event_name, message)
                except Exception as exception:
                    print(f'\n[{handler.get_name()}] Exception occurred while handling {event_name}, '
                          f'raw message: {message}, exception details:{exception}')
                    traceback.print_exc()

        for handler in self.greedy_handler_set:
            try:
                handler.handle_event(event_name, message)
            except Exception as exception:
                print(f'\n[{handler.get_name()}] Exception occurred while handling {event_name}, '
                      f'raw message: {message}, exception details:{exception}')
                traceback.print_exc()

    def register_event_handler(self, event_handler: VoyagerEventHandler):
        if event_handler.interested_event_name():
            self.handler_dict[event_handler.interested_event_name()].add(event_handler)
        if event_handler.interested_event_names():
            for v in event_handler.interested_event_names():
                self.handler_dict[v].add(event_handler)
        if event_handler.interested_in_all_events():
            self.greedy_handler_set.add(event_handler)
