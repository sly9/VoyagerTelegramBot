from dataclasses import dataclass


@dataclass
class LogMessageInfo:
    type: str = ''
    type_emoji: str = ''
    message: str = ''

