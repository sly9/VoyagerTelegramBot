from enum import Enum


class BotEvent(Enum):
    SEND_TEXT_MESSAGE = 1
    SEND_IMAGE_MESSAGE = 2
    EDIT_IMAGE_MESSAGE = 3
    PIN_MESSAGE = 4
    UNPIN_MESSAGE = 5
    UNPIN_ALL_MESSAGE = 6
    # Console related events, for now.
    UPDATE_BATTERY_PERCENTAGE = 7
    UPDATE_MESSAGE_COUNTER = 8
    UPDATE_HOST_INFO = 9
    UPDATE_JOB_STATUS = 10
    # APPEND_ERROR_LOG and APPEND_LOG should be merged.
    APPEND_ERROR_LOG = 11
    APPEND_LOG = 12
