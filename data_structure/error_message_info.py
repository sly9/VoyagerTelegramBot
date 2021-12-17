from dataclasses import dataclass


@dataclass
class ErrorMessageInfo:
    code: int = 0
    message: str = ''