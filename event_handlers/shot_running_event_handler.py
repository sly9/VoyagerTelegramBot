from typing import Dict

from data_structure.shot_running_info import ShotRunningInfo, ShotRunningStatus
from event_emitter import ee
from event_handlers.voyager_event_handler import VoyagerEventHandler
from event_names import BotEvent


# This is just one of the event handlers which are interested in log events. You can write more
class ShotRunningEventHandler(VoyagerEventHandler):
    def __init__(self, config):
        super().__init__(config=config)

    def interested_event_name(self):
        return 'ShotRunning'

    def handle_event(self, event_name: str, message: Dict):
        # {"Event":"ShotRunning","Timestamp":1637695689.48418,"Host":"DESKTOP-USODEM7",
        # "Inst":1,"File":"SyncVoyager_20211123_192757.fit","Expo":5,"Elapsed":5,"ElapsedPerc":100,"Status":1}
        shot_running_info = ShotRunningInfo(filename=message['File'],
                                            total_exposure=message['Expo'],
                                            elapsed_exposure=message['Elapsed'],
                                            elapsed_percentage=message['ElapsedPerc'],
                                            status=ShotRunningStatus(message['Status']))
        ee.emit(BotEvent.UPDATE_SHOT_STATUS.name, shot_running_info)
