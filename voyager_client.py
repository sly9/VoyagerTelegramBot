#!/bin/env python3
import traceback
from collections import defaultdict
from typing import Dict

from curse_manager import CursesManager
from destination.console_manager import ConsoleManager
from event_handlers.battery_status_event_handler import BatteryStatusEventHandler
from event_handlers.giant_event_handler import GiantEventHandler
from event_handlers.log_event_handler import LogEventHandler
from event_handlers.misc_event_handler import MiscellaneousEventHandler
from event_handlers.voyager_event_handler import VoyagerEventHandler
from html_telegram_bot import HTMLTelegramBot
from telegram import TelegramBot
from destination.html_reporter import HTMLReporter
from console import console


class VoyagerClient:
    def __init__(self, config=None):
        self.config = config
        self.telegram_bot = None
        self.curses_manager = None

        if self.config.debugging:
            self.telegram_bot = HTMLTelegramBot()
            self.html_reporter = HTMLReporter()
        else:
            self.curses_manager = CursesManager()
            self.console_manager = ConsoleManager(curses_manager = self.curses_manager)
            self.telegram_bot = TelegramBot(config=config)

        # Event handlers for business logic:
        self.handler_dict = defaultdict(set)
        self.greedy_handler_set = set()

        miscellaneous_event_handler = MiscellaneousEventHandler(config=config, telegram_bot=self.telegram_bot,
                                                                curses_manager=self.curses_manager)
        self.register_event_handler(miscellaneous_event_handler)

        giant_handler = GiantEventHandler(config=config, telegram_bot=self.telegram_bot,
                                          curses_manager=self.curses_manager)
        self.register_event_handler(giant_handler)

        log_event_handler = LogEventHandler(config=config, telegram_bot=self.telegram_bot,
                                            curses_manager=self.curses_manager)
        self.register_event_handler(log_event_handler)

        client_status_event_handler = BatteryStatusEventHandler(config=config, telegram_bot=self.telegram_bot,
                                                                curses_manager=self.curses_manager)
        self.register_event_handler(client_status_event_handler)

    def parse_message(self, event_name: str, message: Dict):
        if event_name in self.handler_dict:
            for handler in self.handler_dict[event_name]:
                try:
                    handler.handle_event(event_name, message)
                except Exception as exception:
                    if 'Base64Data' in message:
                        message.pop('Base64Data')

                    print(f'\n[{handler.get_name()}] Exception occurred while handling {event_name}, '
                          f'raw message: {message}, exception details:{exception}')
                    console.print_exception(show_locals=True)

        for handler in self.greedy_handler_set:
            try:
                handler.handle_event(event_name, message)
            except Exception as exception:
                if 'Base64Data' in message:
                    message.pop('Base64Data')

                print(f'\n[{handler.get_name()}] Exception occurred while handling {event_name}, '
                      f'raw message: {message}, exception details:{exception}')
                #traceback.print_exc()
                console.print_exception(show_locals=True)


    def register_event_handler(self, event_handler: VoyagerEventHandler):
        if event_handler.interested_event_name():
            self.handler_dict[event_handler.interested_event_name()].add(event_handler)
        if event_handler.interested_event_names():
            for v in event_handler.interested_event_names():
                self.handler_dict[v].add(event_handler)
        if event_handler.interested_in_all_events():
            self.greedy_handler_set.add(event_handler)
