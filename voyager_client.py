#!/bin/env python3
from collections import defaultdict
from typing import Dict

from console import main_console
from curse_manager import CursesManager
from destination.console_manager import ConsoleManager
from destination.html_reporter import HTMLReporter
from destination.rich_console_manager import RichConsoleManager
from destination.telegram import Telegram
from event_handlers.bot_computer_status_event_handler import BotComputerStatusEventHandler
from event_handlers.giant_event_handler import GiantEventHandler
from event_handlers.log_event_handler import LogEventHandler
from event_handlers.misc_event_handler import MiscellaneousEventHandler
from event_handlers.shot_running_event_handler import ShotRunningEventHandler
from event_handlers.system_status_event_handler import SystemStatusEventHandler
from event_handlers.voyager_event_handler import VoyagerEventHandler
from event_handlers.weather_safety_event_handler import WeatherSafetyHandler
from utils.localization import get_translated_text as _


class VoyagerClient:
    def __init__(self, config=None):
        self.config = config

        if self.config.html_report_enabled:
            self.html_reporter = HTMLReporter(config=config)
        if self.config.telegram_enabled:
            self.telegram = Telegram(config=config)

        if self.config.console_config.console_type == 'BASIC':
            curses_manager = CursesManager()
            self.console_manager = ConsoleManager(config=config, curses_manager=curses_manager)
        elif self.config.console_config.console_type == 'FULL':
            self.console_manager = RichConsoleManager(config=config)
            self.console_manager.run()
        else:
            main_console.print(_('Not planning to take over the console'))

        # Event handlers for business logic:
        self.handler_dict = defaultdict(set)
        self.greedy_handler_set = set()

        self.register_event_handler(MiscellaneousEventHandler(config=config))
        self.register_event_handler(GiantEventHandler(config=config))
        self.register_event_handler(LogEventHandler(config=config))
        self.register_event_handler(WeatherSafetyHandler(config=config))
        self.register_event_handler(BotComputerStatusEventHandler(config=config))
        self.register_event_handler(SystemStatusEventHandler(config=config))
        self.register_event_handler(ShotRunningEventHandler(config=config))

    def parse_message(self, event_name: str, message: Dict):
        if event_name in self.handler_dict:
            for handler in self.handler_dict[event_name]:
                try:
                    handler.handle_event(event_name, message)
                except Exception as exception:
                    if 'Base64Data' in message:
                        message.pop('Base64Data')
                    main_console.print_exception(show_locals=True)

        for handler in self.greedy_handler_set:
            try:
                handler.handle_event(event_name, message)
            except Exception as exception:
                if 'Base64Data' in message:
                    message.pop('Base64Data')
                main_console.print_exception(show_locals=True)

    def register_event_handler(self, event_handler: VoyagerEventHandler):
        if event_handler.interested_event_name():
            self.handler_dict[event_handler.interested_event_name()].add(event_handler)
        if event_handler.interested_event_names():
            for v in event_handler.interested_event_names():
                self.handler_dict[v].add(event_handler)
        if event_handler.interested_in_all_events():
            self.greedy_handler_set.add(event_handler)
