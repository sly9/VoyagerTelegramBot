from dataclasses import dataclass


@dataclass
class LogMessageInfo:
    type: str = ''
    message: str = ''
