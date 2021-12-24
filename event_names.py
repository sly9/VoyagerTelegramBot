from enum import Enum


class BotEvent(Enum):
    SEND_TEXT_MESSAGE = 1
    SEND_IMAGE_MESSAGE = 2
    EDIT_IMAGE_MESSAGE = 3
    PIN_MESSAGE = 4
    UNPIN_MESSAGE = 5
    UNPIN_ALL_MESSAGE = 6
