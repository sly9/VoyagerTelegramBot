from enum import Enum


# Next id: 15
class BotEvent(Enum):
    # These telegram specific events should be merged into more 'logic' oriented names
    SEND_TEXT_MESSAGE = 1
    SEND_IMAGE_MESSAGE = 2
    EDIT_IMAGE_MESSAGE = 3
    UPDATE_SEQUENCE_STAT_IMAGE = 4
    PIN_MESSAGE = 5
    UNPIN_MESSAGE = 6
    UNPIN_ALL_MESSAGE = 7
    # Console related events, for now.
    UPDATE_BATTERY_PERCENTAGE = 8
    UPDATE_MESSAGE_COUNTER = 9
    UPDATE_HOST_INFO = 10
    UPDATE_SYSTEM_STATUS = 11
    UPDATE_SHOT_STATUS = 14
    # APPEND_ERROR_LOG and APPEND_LOG should be merged.
    APPEND_ERROR_LOG = 12
    APPEND_LOG = 13
