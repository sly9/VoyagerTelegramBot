from abc import abstractmethod
from typing import Dict, Tuple

from curse_manager import CursesManager
from telegram import TelegramBot


class VoyagerEventHandler:
    """
    A base class for all event handlers to inherit from.

    To handle an incoming event from voyager application server, Most important method is the 'handle_event' method.
    """

    def __init__(self, config,
                 telegram_bot: TelegramBot,
                 handler_name: str = 'DefaultHandler',
                 curses_manager: CursesManager = None):
        self.name = handler_name
        self.config = config
        self.telegram_bot = telegram_bot
        self.curses_manager = curses_manager

    def interested_event_names(self):
        """
        :return: List of event names this event_handler wants to process.
        """
        return []

    def interested_event_name(self):
        """
        :return: An event name this event_handler wants to process.
        """
        return None

    def interested_in_all_events(self):
        """
        :return: A boolean indicating whether this event handler wants to process all possible events.
        """
        return False

    def get_name(self):
        """
        :return: The name of this event_handler
        """
        return self.name

    def send_text_message(self, message: str):
        """
        Send plain text message to Telegram, and print out error message
        :param message: The text that need to be sent to Telegram
        """
        if self.telegram_bot:
            status, info_dict = self.telegram_bot.send_text_message(message)

            if status == 'ERROR':
                print(
                    f'\n[ERROR - {self.get_name()} - Text Message]'
                    f'[{info_dict["error_code"]}]'
                    f'[{info_dict["description"]}]')
        else:
            print(f'\n[ERROR - {self.get_name()} - Telegram Bot]')

    def send_image_message(self, base64_img: bytes = None, image_fn: str = '', msg_text: str = '',
                           as_doc: bool = True) -> Tuple[str or None, str or None]:
        """
        Send image message to Telegram, and print out error message
        :param base64_img: image data that encoded as base64
        :param image_fn: the file name of the image
        :param msg_text: image capture in string format
        :param as_doc: if the image should be sent as document (for larger image file)
        :return: Tuple of chat_id and message_id to check status
        """
        if self.telegram_bot:
            status, info_dict = self.telegram_bot.send_image_message(base64_img, image_fn, msg_text, as_doc)

            if status == 'ERROR':
                print(
                    f'\n[ERROR - {self.get_name()} - Text Message]'
                    f'[{info_dict["error_code"]}]'
                    f'[{info_dict["description"]}]')
            elif status == 'OK':
                return str(info_dict['chat_id']), str(info_dict['message_id'])
        else:
            print(f'\n[ERROR - {self.get_name()} - Telegram Bot]')

        return None, None

    @abstractmethod
    def handle_event(self, event_name: str, message: Dict):
        """
        Processes the incoming event + message. Note: a single message might be
        processed by multiple event handlers. Don't modify the message dict.
        :param event_name: The event name in string format.
        :param message: A dictionary containing all messages
        :return: Nothing
        """
        print('handling event', event_name, message)
