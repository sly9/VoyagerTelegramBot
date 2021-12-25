from abc import abstractmethod
from typing import Dict


class VoyagerEventHandler:
    """
    A base class for all event handlers to inherit from.

    To handle an incoming event from voyager application server, Most important method is the 'handle_event' method.
    """

    def __init__(self, config):
        self.config = config

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
