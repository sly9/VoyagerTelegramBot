import base64
import os
from collections import deque
from typing import Dict

from data_structure.filter_info import ExposureInfo
from data_structure.focus_result import FocusResult
from data_structure.image_types import ImageTypeEnum, FitTypeEnum
from data_structure.log_message_info import LogMessageInfo
from data_structure.special_battery_percentage import MemoryUsage
from data_structure.system_status_info import GuideStatusEnum, DitherStatusEnum
from event_emitter import ee
from event_handlers.voyager_event_handler import VoyagerEventHandler
from event_names import BotEvent
from sequence_stat import StatPlotter, SequenceStat


# noinspection SpellCheckingInspection
class GiantEventHandler(VoyagerEventHandler):
    def __init__(self, config):
        super().__init__(config=config)

        self.stat_plotter = StatPlotter(config=self.config)

        self.running_seq = ''
        self.running_dragscript = ''

        self.shot_running = False  # whether the camera is exposing, inferred from 'ShotRunning' event

        # A dictionary of 'sequence name' => 'sequence stats'
        self.sequence_map = dict()

        self.current_sequence_stat_chat_id = None
        self.current_sequence_stat_message_id = None

        self.filter_name_list = [i for i in range(10)]  # initial with 10 unnamed filters
        self.image_type_set = set()
        self.memory_history = deque()

        self.i18n = self.config.i18n.messages
        ee.on(BotEvent.UPDATE_MEMORY_USAGE.name, self.update_memory_usage)

    def interested_event_names(self):
        return ['NewJPGReady',
                'NewFITReady',
                'AutoFocusResult',
                'ShotRunning',
                'ControlData',
                'RemoteActionResult']

    def handle_event(self, event_name: str, message: Dict):
        if event_name == 'NewJPGReady':
            self.handle_jpg_ready(message)
        elif event_name == 'NewFITReady':
            self.handle_fit_ready(message)
        elif event_name == 'AutoFocusResult':
            self.handle_focus_result(message)
        elif event_name == 'ShotRunning':
            self.handle_shot_running(message)
        elif event_name == 'ControlData':
            self.handle_control_data(message)
        elif event_name == 'RemoteActionResult':
            self.handle_remote_action_result(message)
        else:
            return

    # Handles each types of events
    def handle_remote_action_result(self, message: Dict):
        method_name = message['MethodName']
        if method_name == 'RemoteGetFilterConfiguration':
            # console.print(message)
            params = message['ParamRet']
            filter_count = params['FilterNum']
            for i in range(0, filter_count):
                self.filter_name_list[i] = params[f'Filter{i + 1}_Name']

    def handle_shot_running(self, message: Dict):
        timestamp = message['Timestamp']
        main_shot_elapsed = message['Elapsed']
        guiding_shot_idx = message['ElapsedPerc']
        img_fn = message['File']
        status = message['Status']
        self.shot_running = status == 1  # 1 means running, all other things are 'not running'

    def handle_control_data(self, message: Dict):
        timestamp = message['Timestamp']
        guide_status = message['GUIDESTAT']
        dither_status = message['DITHSTAT']
        is_tracking = message['MNTTRACK']
        is_slewing = message['MNTSLEW']
        guide_x = message['GUIDEX']
        guide_y = message['GUIDEY']
        running_seq = message['RUNSEQ']
        running_dragscript = message['RUNDS']

        if self.shot_running and guide_status == GuideStatusEnum.RUNNING and dither_status == DitherStatusEnum.STOPPED:
            self.add_guide_error_stat(guide_x, guide_y)

        if running_dragscript != self.running_dragscript:
            self.sequence_map = {}
            if running_dragscript == '':
                ee.emit(BotEvent.SEND_TEXT_MESSAGE.name,
                        self.i18n['drag_script_finish'].format(ds_name=self.running_dragscript))
            elif self.running_dragscript == '':
                ee.emit(BotEvent.SEND_TEXT_MESSAGE.name,
                        self.i18n['drag_script_start'].format(ds_name=running_dragscript))
            else:
                ee.emit(BotEvent.SEND_TEXT_MESSAGE.name,
                        self.i18n['drag_script_switch'].format(old_ds_name=running_dragscript,
                                                               new_ds_name=self.running_dragscript))
            self.running_dragscript = running_dragscript

        if running_seq != self.running_seq:
            # self.report_stats_for_current_sequence()
            if running_seq == '':
                ee.emit(BotEvent.SEND_TEXT_MESSAGE.name,
                        self.i18n['sequence_finish'].format(seq_name=self.running_seq))
            elif self.running_seq == '':
                ee.emit(BotEvent.SEND_TEXT_MESSAGE.name,
                        self.i18n['sequence_start'].format(seq_name=running_seq))
                self.current_sequence_stat_chat_id = None
                self.current_sequence_stat_message_id = None
                self.report_stats_for_current_sequence()
            else:
                ee.emit(BotEvent.SEND_TEXT_MESSAGE.name,
                        self.i18n['sequence_switch'].format(old_seq_name=running_seq, new_seq_name=self.running_seq))
                self.current_sequence_stat_chat_id = None
                self.current_sequence_stat_message_id = None
                self.report_stats_for_current_sequence()
            self.running_seq = running_seq

    def handle_focus_result(self, message: Dict):
        is_empty = message['IsEmpty']
        if is_empty == "true":
            return

        done = message['Done']
        last_error = message['LastError']
        if not done:
            error_message = self.i18n['focus_error_message'].format(err_msg=last_error)
            ee.emit(BotEvent.APPEND_ERROR_LOG.name,
                    error=LogMessageInfo(type='ERROR', message=error_message))
            ee.emit(BotEvent.SEND_TEXT_MESSAGE.name, error_message)
            return

        filter_index = message['FilterIndex']
        filter_color = message['FilterColor']
        hfd = message['HFD']
        focus_temp = message['FocusTemp']
        position = message['Position']
        timestamp = message['Timestamp']

        focus_result = FocusResult(filter_name=str(filter_index), filter_color=filter_color, hfd=hfd,
                                   timestamp=timestamp, temperature=focus_temp)
        self.add_focus_result(focus_result)

        filter_name = self.filter_name_list[filter_index]

        telegram_message = self.i18n['focus_success_message'].format(filter_name=filter_name, position=position,
                                                                     hfd=hfd)
        ee.emit(BotEvent.SEND_TEXT_MESSAGE.name, telegram_message)

    def handle_jpg_ready(self, message: Dict):
        expo = message['Expo']
        file_name = message['File']
        filter_name = message['Filter']
        hfd = message['HFD']
        star_index = message['StarIndex']
        sequence_target = message['SequenceTarget']
        timestamp = message['TimeInfo']

        telegram_message = self.i18n['shot_success_message'].format(sequence_target=sequence_target, expo=expo,
                                                                    filter_name=filter_name, hfd=hfd,
                                                                    star_index=star_index)

        file_identifier = self.get_image_identifier(raw_path=file_name)
        should_send_image = False

        if file_identifier in self.image_type_set:
            should_send_image = True
            self.image_type_set.remove(file_identifier)

        if should_send_image:
            # new stat code
            exposure = ExposureInfo(filter_name=filter_name, exposure_time=expo, hfd=hfd, star_index=star_index,
                                    timestamp=timestamp)
            self.add_exposure_stats(exposure=exposure, sequence_name=sequence_target)
            # with PINNING and UNPINNING implemented, we can safely report stats for all images
            self.report_stats_for_current_sequence()

            base64_photo = message['Base64Data']
            image_data = base64.b64decode(base64_photo)

            fit_filename = message['File']
            new_filename = fit_filename[fit_filename.rindex('\\') + 1: fit_filename.index('.')] + '.jpg'
            ee.emit(BotEvent.SEND_IMAGE_MESSAGE.name, image_data=image_data, filename=new_filename,
                    caption=telegram_message)
        else:
            ee.emit(BotEvent.SEND_TEXT_MESSAGE.name, telegram_message)

    def handle_fit_ready(self, message: Dict):
        file_name = message['File']
        image_type = message['Type']
        fit_type = message['VoyType']

        image_identifier = self.get_image_identifier(file_name)
        if image_type == ImageTypeEnum.LIGHT.value and fit_type != FitTypeEnum.SYNC.value:
            self.image_type_set.add(image_identifier)

    # Helper methods

    def current_sequence_stat(self) -> SequenceStat:
        self.sequence_map.setdefault(self.running_seq, SequenceStat(name=self.running_seq))
        return self.sequence_map[self.running_seq]

    def add_exposure_stats(self, exposure: ExposureInfo, sequence_name: str):
        self.current_sequence_stat().add_exposure(exposure)

    def add_guide_error_stat(self, error_x: float, error_y: float):
        self.current_sequence_stat().add_guide_error((error_x, error_y))

    def add_focus_result(self, focus_result: FocusResult):
        self.current_sequence_stat().add_focus_result(focus_result)

    def update_memory_usage(self, memory_history: deque, memory_usage: MemoryUsage):
        self.memory_history = memory_history

    @staticmethod
    def get_image_identifier(raw_path: str = '') -> str:
        if not raw_path:
            return ''

        raw_file_name = os.path.basename(raw_path)
        if '.' in raw_file_name:
            return raw_file_name[:raw_file_name.rindex('.')]

        return raw_file_name

    # Reporting methods

    def report_stats_for_current_sequence(self):
        if self.current_sequence_stat().name == '':
            # one-off shots doesn't need stats, we only care about sequences.
            return
        sequence_stat = self.current_sequence_stat()

        sequence_stat_image = self.stat_plotter.plot(sequence_stat=sequence_stat, memory_history=self.memory_history)
        ee.emit(BotEvent.UPDATE_SEQUENCE_STAT_IMAGE.name, sequence_stat_image=sequence_stat_image,
                sequence_name=self.running_seq, sequence_stat_message='This is a test message')


def main():
    fns = ['C:\\Users\\bigpi\\Documents\\GitHub\\VoyagerTelegramBot.fit',
           'VoyagerTelegramBot.fit',
           'VoyagerTelegramBot',
           'C:\\Users\\bigpi\\Documents\\GitHub\\VoyagerTelegramBot']

    for fn in fns:
        print(fn, GiantEventHandler.get_image_identifier(fn))


if __name__ == '__main__':
    main()
