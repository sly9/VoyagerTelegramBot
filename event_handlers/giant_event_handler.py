from datetime import datetime
from typing import Dict

import psutil

from configs import ConfigBuilder
from event_handlers.voyager_event_handler import VoyagerEventHandler
from sequence_stat import StatPlotter, FocusResult, SequenceStat, ExposureInfo
from telegram import TelegramBot


class GiantEventHandler(VoyagerEventHandler):
    def __init__(self, config_builder: ConfigBuilder, telegram_bot: TelegramBot):
        super().__init__(config_builder=config_builder, telegram_bot=telegram_bot, handler_name='GiantEventHandler')

        self.stat_plotter = StatPlotter(plotter_configs=self.config.sequence_stats_config)

        # interval vars
        self.running_seq = ''
        self.running_dragscript = ''

        self.shot_running = False  # whether the camera is exposing, inferred from 'ShotRunning' event

        self.ignored_counter = 0

        # A dictionary of 'sequence name' => 'sequence stats'
        self.sequence_map = dict()
        # Note this violates the assumption that there could be more chat ids we should send message to...
        # but let's bear with it for now
        self.current_sequence_stat_chat_id = None
        self.current_sequence_stat_message_id = None

    def send_text_message(self, msg_text: str = ''):
        if self.telegram_bot:
            self.telegram_bot.send_text_message(msg_text)

    def send_image_message(self, base64_img: bytes = None, image_fn: str = '', msg_text: str = '',
                           as_doc: bool = True):
        if self.telegram_bot:
            return self.telegram_bot.send_image_message(base64_img, image_fn, msg_text, as_doc)
        return None, None

    def handle_event(self, event_name: str, message: Dict):
        if event_name == 'Version':
            self.ignored_counter = 0
            self.handle_version(message)
        elif event_name == 'NewJPGReady':
            self.ignored_counter = 0
            self.handle_jpg_ready(message)
        elif event_name == 'AutoFocusResult':
            self.ignored_counter = 0
            self.handle_focus_result(message)
        elif event_name == 'LogEvent':
            self.ignored_counter = 0
        elif event_name == 'ShotRunning':
            self.ignored_counter = 0
            self.handle_shot_running(message)
        elif event_name == 'ControlData':
            self.ignored_counter = 0
            self.handle_control_data(message)
        elif event_name in self.config.ignored_events:
            # do nothing
            self.ignored_counter += 1
            if self.ignored_counter >= 30:
                print('.', end='\n', flush=True)
                self.ignored_counter = 0
            else:
                print('.', end='', flush=True)
        else:
            self.ignored_counter = 0
            timestamp = message['Timestamp']
            message.pop('Timestamp', None)
            print(f'[{datetime.fromtimestamp(timestamp)}][{event_name}]: {message}')

    def handle_version(self, message):
        telegram_message = 'Connected to <b>{host_name}({url})</b> [{version}]'.format(
            host_name=message['Host'],
            url=self.config.voyager_setting.domain,
            version=message['VOYVersion'])

        self.send_text_message(telegram_message)

    def handle_shot_running(self, message):
        timestamp = message['Timestamp']
        main_shot_elapsed = message['Elapsed']
        guiding_shot_idx = message['ElapsedPerc']
        img_fn = message['File']
        status = message['Status']
        self.shot_running = status == 1  # 1 means running, all other things are 'not running'

    def handle_control_data(self, message):
        timestamp = message['Timestamp']
        guide_status = message['GUIDESTAT']
        dither_status = message['DITHSTAT']
        is_tracking = message['MNTTRACK']
        is_slewing = message['MNTSLEW']
        guide_x = message['GUIDEX']
        guide_y = message['GUIDEY']
        running_seq = message['RUNSEQ']
        running_dragscript = message['RUNDS']

        # definition for GUIDESTAT, {0: STOPPED, 1: WAITING_SETTLE, 2: RUNNING, 3: TIMEOUT_SETTLE}
        # definition for DITHSTAT, {0: STOPPED, 1: RUNNING, 2: WAITING_SETTLE, 3: TIMEOUT_SETTLE}
        if self.shot_running and guide_status == 2 and dither_status == 0:
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

    def handle_focus_result(self, message):
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

        telegram_message = f'AutoFocusing for filter at index:{filter_index} succeeded with position {position}, HFD: {hfd:.2f}'
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

    def handle_jpg_ready(self, message):
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

        if self.config.monitor_battery:
            telegram_message = message['battery'] + ' ' + telegram_message

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
                                                          msg_text='Statistics for {target}'.format(
                                                              target=self.running_seq),
                                                          as_doc=False)
            self.current_sequence_stat_chat_id = chat_id
            self.current_sequence_stat_message_id = message_id
            self.telegram_bot.unpin_all_messages(chat_id=chat_id)
            self.telegram_bot.pin_message(chat_id=chat_id, message_id=message_id)
        else:
            self.telegram_bot.edit_image_message(chat_id=self.current_sequence_stat_chat_id,
                                                 message_id=self.current_sequence_stat_message_id,
                                                 base64_encoded_image=base64_img,
                                                 filename=self.running_seq + '_stat.jpg')
