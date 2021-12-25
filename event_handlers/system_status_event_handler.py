from typing import Dict

from data_structure.system_status_info import SystemStatusInfo, MountInfo, DeviceConnectedInfo
from event_emitter import ee
from event_handlers.voyager_event_handler import VoyagerEventHandler
from event_names import BotEvent


class SystemStatusEventHandler(VoyagerEventHandler):
    def __init__(self, config):
        super().__init__(config=config, handler_name='SystemStatusEventHandler')
        self.message_counter = 0

    def interested_event_name(self):
        return 'ControlData'

    def handle_event(self, event_name: str, message: Dict):
        if event_name == 'ControlData':
            self.handle_control_data_event(message)

    def handle_control_data_event(self, message: Dict):
        timestamp = message['Timestamp']
        guide_status = message['GUIDESTAT']
        dither_status = message['DITHSTAT']
        is_tracking = message['MNTTRACK']
        is_slewing = message['MNTSLEW']
        is_parked = message['MNTPARK']
        guide_x = message['GUIDEX']
        guide_y = message['GUIDEY']
        running_seq = message['RUNSEQ']
        running_dragscript = message['RUNDS']

        if is_parked:
            mount_operation = 'PARKED'
        elif is_slewing:
            mount_operation = 'SLEWING'
        elif is_tracking:
            mount_operation = 'TRACKING'
        else:
            mount_operation = ''
        mount_info = MountInfo(
            ra=message['MNTRA'], dec=message['MNTDEC'],
            ra_j2000=message['MNTRAJ2000'], dec_j2000=message['MNTDECJ2000'],
            az=message['MNTAZ'], alt=message['MNTALT'],
            pier=message['MNTPIER'][4:], operation=mount_operation
        )

        device_connection_info = DeviceConnectedInfo(
            setup_connected=message['SETUPCONN'],
            camera_connected=message['CCDCONN'],
            mount_connected=message['MNTCONN'],
            focuser_connected=message['AFCONN'],
            guide_connected=message['GUIDECONN'],
            planetarium_connected=message['PLACONN'],
            rotator_connected=message['ROTCONN']
        )

        ee.emit(BotEvent.UPDATE_SYSTEM_STATUS.name,
                system_status_info=SystemStatusInfo(
                    drag_script_name=running_dragscript, sequence_name=running_seq,
                    guide_status=guide_status, dither_status=dither_status,
                    is_tracking=is_tracking, is_slewing=is_slewing,
                    mount_info=mount_info, device_connection_info=device_connection_info))
