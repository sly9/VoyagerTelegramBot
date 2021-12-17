from typing import Dict

from curse_manager import CursesManager
from data_structure.job_status_info import GuideStatEnum, DitherStatEnum, JobStatusInfo
from event_handlers.voyager_event_handler import VoyagerEventHandler
from sequence_stat import StatPlotter, FocusResult, SequenceStat, ExposureInfo
from telegram import TelegramBot


class GiantEventHandler(VoyagerEventHandler):
    def __init__(self, config, telegram_bot: TelegramBot, curses_manager: CursesManager):
        super().__init__(config=config, telegram_bot=telegram_bot,
                         handler_name='GiantEventHandler',
                         curses_manager=curses_manager)

        self.stat_plotter = StatPlotter(plotter_configs=self.config.sequence_stats_config)

        self.running_seq = ''
        self.running_dragscript = ''

        self.shot_running = False  # whether the camera is exposing, inferred from 'ShotRunning' event

        # A dictionary of 'sequence name' => 'sequence stats'
        self.sequence_map = dict()

        self.current_sequence_stat_chat_id = None
        self.current_sequence_stat_message_id = None

        self.filter_name_list = [i for i in range(10)]  # initial with 10 unnamed filters

    def interested_event_names(self):
        return ['NewJPGReady',
                'AutoFocusResult',
                'ShotRunning',
                'ControlData',
                'RemoteActionResult']

    def handle_event(self, event_name: str, message: Dict):
        if event_name == 'NewJPGReady':
            self.handle_jpg_ready(message)
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

    def handle_version(self, message: Dict):
        telegram_message = 'Connected to <b>{host_name}({url})</b> [{version}]'.format(
            host_name=message['Host'],
            url=self.config.voyager_setting.domain,
            version=message['VOYVersion'])

        self.send_text_message(telegram_message)

    def handle_remote_action_result(self, message: Dict):
        method_name = message['MethodName']
        if method_name == 'RemoteGetFilterConfiguration':
            # print(message)
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

        self.curses_manager.update_job_status_info(
            JobStatusInfo(drag_script_name=running_dragscript, sequence_name=running_seq,
                          guide_status=guide_status, dither_status=dither_status,
                          is_tracking=is_tracking, is_slewing=is_slewing))

        if self.shot_running and guide_status == GuideStatEnum.RUNNING and dither_status == DitherStatEnum.STOPPED:
            self.add_guide_error_stat(guide_x, guide_y)

        if running_dragscript != self.running_dragscript:
            self.sequence_map = {}
            if running_dragscript == '':
                self.send_text_message(f'Just finished DragScript {self.running_dragscript}')
            elif self.running_dragscript == '':
                self.send_text_message(f'Starting DragScript {running_dragscript}')
            else:
                self.send_text_message(
                    f'Switching DragScript from {running_dragscript} to {self.running_dragscript}')
            self.running_dragscript = running_dragscript

        if running_seq != self.running_seq:
            # self.report_stats_for_current_sequence()
            if running_seq == '':
                self.send_text_message(f'Just finished Sequence {self.running_seq}')
            elif self.running_seq == '':
                self.send_text_message(f'Starting Sequence {running_seq}')
                self.current_sequence_stat_chat_id = None
                self.current_sequence_stat_message_id = None
                self.report_stats_for_current_sequence()
            else:
                self.send_text_message(
                    f'Switching Sequence from {running_seq} to {self.running_seq}')
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
            self.send_text_message(f'Auto focusing failed with reason: {last_error}')
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

        telegram_message = f'AutoFocusing for filter {filter_name} succeeded with position {position}, HFD: {hfd:.2f}'
        self.send_text_message(telegram_message)

    def current_sequence_stat(self) -> SequenceStat:
        self.sequence_map.setdefault(self.running_seq, SequenceStat(name=self.running_seq))
        return self.sequence_map[self.running_seq]

    def add_exposure_stats(self, exposure: ExposureInfo, sequence_name: str):
        self.current_sequence_stat().add_exposure(exposure)

    def add_guide_error_stat(self, error_x: float, error_y: float):
        self.current_sequence_stat().add_guide_error((error_x, error_y))

    def add_focus_result(self, focus_result: FocusResult):
        self.current_sequence_stat().add_focus_result(focus_result)

    def handle_jpg_ready(self, message: Dict):
        expo = message['Expo']
        filter_name = message['Filter']
        hfd = message['HFD']
        star_index = message['StarIndex']
        sequence_target = message['SequenceTarget']
        timestamp = message['TimeInfo']

        # new stat code
        exposure = ExposureInfo(filter_name=filter_name, exposure_time=expo, hfd=hfd, star_index=star_index,
                                timestamp=timestamp)
        self.add_exposure_stats(exposure=exposure, sequence_name=sequence_target)

        base64_photo = message['Base64Data']

        telegram_message = f'Exposure of {sequence_target} for {expo}sec using {filter_name} filter.' \
                           + f'HFD: {hfd}, StarIndex: {star_index}'

        if expo >= self.config.exposure_limit:
            fit_filename = message['File']
            new_filename = fit_filename[fit_filename.rindex('\\') + 1: fit_filename.index('.')] + '.jpg'
            self.send_image_message(base64_photo, new_filename, telegram_message)
        else:
            self.send_text_message(telegram_message)
        # with PINNING and UNPINNING implemented, we can safely report stats for all images
        self.report_stats_for_current_sequence()

    def report_stats_for_current_sequence(self):
        if self.current_sequence_stat().name == '':
            # one-off shots doesn't need stats, we only care about sequences.
            return
        sequence_stat = self.current_sequence_stat()

        base64_img = self.stat_plotter.plot(sequence_stat=sequence_stat)

        if not self.current_sequence_stat_chat_id and not self.current_sequence_stat_message_id:
            chat_id, message_id = self.send_image_message(base64_img=base64_img, image_fn='good_night_stats.jpg',
                                                          msg_text=f'Statistics for {self.running_seq}',
                                                          as_doc=False)
            if chat_id and message_id:
                self.current_sequence_stat_chat_id = chat_id
                self.current_sequence_stat_message_id = message_id
                status, info_dict = self.telegram_bot.unpin_all_messages(chat_id=chat_id)
                if status == 'ERROR':
                    print(
                        f'\n[ERROR - {self.get_name()} - Unpin All Message]'
                        f'[{info_dict["error_code"]}]'
                        f'[{info_dict["description"]}]')

                status, info_dict = self.telegram_bot.pin_message(chat_id=chat_id, message_id=message_id)
                if status == 'ERROR':
                    print(
                        f'\n[ERROR - {self.get_name()} - Pin Message]'
                        f'[{info_dict["error_code"]}]'
                        f'[{info_dict["description"]}]')
        else:
            status, info_dict = self.telegram_bot.edit_image_message(chat_id=self.current_sequence_stat_chat_id,
                                                                     message_id=self.current_sequence_stat_message_id,
                                                                     base64_encoded_image=base64_img,
                                                                     filename=self.running_seq + '_stat.jpg')
            if status == 'ERROR':
                print(
                    f'\n[ERROR - {self.get_name()} - Edit Image Message]'
                    f'[{info_dict["error_code"]}]'
                    f'[{info_dict["description"]}]')
