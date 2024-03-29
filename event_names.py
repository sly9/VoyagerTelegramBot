from enum import Enum


# Next id: 18
class BotEvent(Enum):
    # These telegram specific events should be merged into more 'logic' oriented names
    SEND_TEXT_MESSAGE = 1
    SEND_IMAGE_MESSAGE = 2
    EDIT_IMAGE_MESSAGE = 3  # not needed
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
    UPDATE_METRICS = 15
    UPDATE_MEMORY_USAGE = 16

    # APPEND_ERROR_LOG is not used anymore, don't use it.
    APPEND_ERROR_LOG = 12
    APPEND_LOG = 13

    # DRAG_SCRIPT
    RECEIVE_DRAG_SCRIPT_LIST = 17
