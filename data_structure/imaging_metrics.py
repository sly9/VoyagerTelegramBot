from dataclasses import dataclass


@dataclass
class GuidingMetrics:
    error_x: float = 0
    error_y: float = 0
    unit: str = 'pixel'


@dataclass
class FocusingMetrics:
    position: float = 0
    hfd: float = 0
    temperature: float = 0
    filter_name: str = 'Ha'
    filter_color: str = '#FFFFFF'


@dataclass
class JpgMetrics:
    star_index: float = 0
    hfd: float = 0


@dataclass
class ImagingMetrics:
    guiding_metrics: GuidingMetrics = GuidingMetrics()
    focusing_metrics: FocusingMetrics = FocusingMetrics()
    jpg_metrics: JpgMetrics = JpgMetrics()
