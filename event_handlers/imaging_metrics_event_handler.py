from typing import Dict

from data_structure.imaging_metrics import ImagingMetrics
from event_emitter import ee
from event_handlers.voyager_event_handler import VoyagerEventHandler
from event_names import BotEvent


class ImagingMetricsEventHandler(VoyagerEventHandler):
    def __init__(self, config):
        super().__init__(config=config)
        self.imaging_metrics = ImagingMetrics()

    def interested_event_names(self):
        return ['ControlData', 'AutoFocusResult', 'NewJPGReady']

    def handle_event(self, event_name: str, message: Dict):
        if event_name == 'ControlData':
            self.imaging_metrics.guiding_metrics.error_x = message['GUIDEX']
            self.imaging_metrics.guiding_metrics.error_y = message['GUIDEY']
        elif event_name == 'AutoFocusResult':
            self.imaging_metrics.focusing_metrics.position = message['Position']
            self.imaging_metrics.focusing_metrics.hfd = message['HFD']
            self.imaging_metrics.focusing_metrics.temperature = message['FocusTemp']
            # TODO: Get filter name from index
            self.imaging_metrics.focusing_metrics.filter_name = message['FilterIndex']
            self.imaging_metrics.focusing_metrics.filter_color = message['FilterColor']
        elif event_name == 'NewJPGReady':
            self.imaging_metrics.jpg_metrics.star_index = message['StarIndex']
            self.imaging_metrics.jpg_metrics.hfd = message['HFD']

        ee.emit(BotEvent.UPDATE_METRICS, imaging_metrics_info=self.imaging_metrics)
