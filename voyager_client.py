#!/bin/env python3
from collections import defaultdict
from datetime import datetime
from typing import Dict, List

from configs import ConfigBuilder
from event_handlers.log_event_handler import LogEventHandler
from event_handlers.giant_event_handler import GiantEventHandler
from event_handlers.voyager_event_handler import VoyagerEventHandler
from html_telegram_bot import HTMLTelegramBot
from telegram import TelegramBot


class VoyagerClient:
    def __init__(self, config_builder: ConfigBuilder):
        self.config = config_builder.build()
        if self.config.debugging:
            telegram_bot = HTMLTelegramBot()
        else:
            telegram_bot = TelegramBot(config_builder=config_builder)

        self.telegram_bot = telegram_bot

        self.handler_dict = defaultdict(set)

        self.giant_handler = GiantEventHandler(config_builder=config_builder, telegram_bot=telegram_bot)

        log_event_handler = LogEventHandler(config_builder=config_builder, telegram_bot=telegram_bot)
        self.register_event_handler(log_event_handler)

    def parse_message(self, event_name: str, message: Dict):
        if event_name in self.handler_dict:
            for handler in self.handler_dict[event_name]:
                try:
                    handler.handle_event(event_name, message)
                except Exception as exception:
                    print(f'Exception occurred while handling {event_name}, raw message: {message}, exception details:',
                          exception)

        # always let giant handler do the work
        try:
            self.giant_handler.handle_event(event_name, message)
        except Exception as exception:
            print(f'Exception occurred while handling {event_name}, raw message: {message}, exception details:',
                  exception)

    def register_event_handler(self, event_handler: VoyagerEventHandler):
        if event_handler.interested_event_name():
            self.handler_dict[event_handler.interested_event_name()].add(event_handler)
        if event_handler.interested_event_names():
            for v in event_handler.interested_event_names():
                self.handler_dict[v].add(event_handler)
