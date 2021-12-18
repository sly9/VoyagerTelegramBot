from dataclasses import dataclass


@dataclass
class ErrorMessageInfo:
    code: int = 0
    message: str = ''
    error_module: str = ''
    error_operation: str = ''
