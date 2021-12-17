from dataclasses import dataclass


@dataclass
class FocusResult:
    filter_name: str = ''
    filter_color: str = '#ddd'
    hfd: float = 0
    timestamp: float = 0
    temperature: float = 0
    recommended_index = 0
