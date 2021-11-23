#!/bin/env python3
from datetime import datetime

import psutil

from configs import ConfigBuilder
from html_telegram_bot import HTMLTelegramBot
from sequence_stat import ExposureInfo, SequenceStat, StatPlotter
from telegram import TelegramBot


class VoyagerClient:
    def __init__(self, config_builder: ConfigBuilder):
        self.config = config_builder.build()
        if self.config.debugging:
            self.telegram_bot = HTMLTelegramBot()
        else:
            self.telegram_bot = TelegramBot(config_builder=config_builder)

        self.stat_plotter = StatPlotter(plotter_configs=self.config.sequence_stats_config)

        # interval vars
        self.running_seq = ''
        self.running_dragscript = ''
        self.img_fn = ''
        self.guiding_idx = -1
        self.guided = False

        self.ignored_counter = 0

        self.sequence_map = dict()
        # Note this violates the assumption that there could be more chat ids we should send message to...
        # but let's bear with it for now
        self.current_sequence_stat_chat_id = None
        self.current_sequence_stat_message_id = None

    def send_text_message(self, msg_text: str = ''):
        if self.telegram_bot:
            self.telegram_bot.send_text_message(msg_text)

    def send_image_message(self, base64_img: bytes = None, image_fn: str = '', msg_text: str = '', as_doc: bool = True):
        if self.telegram_bot:
            return self.telegram_bot.send_image_message(base64_img, image_fn, msg_text, as_doc)
        return None, None

    def parse_message(self, event, message):
        battery_msg = ''
        if self.config.monitor_battery:
            battery = psutil.sensors_battery()
            if battery.power_plugged:
                battery_msg = '🔋: 🔌'
            elif battery.percent >= 80:
                battery_msg = '🔋: 🆗'
            elif battery.percent >= 20:
                battery_msg = '🔋: ❗'
            else:
                battery_msg = '🔋: ‼️'

        message['battery'] = battery_msg

        if event == 'Version':
            self.ignored_counter = 0
            self.handle_version(message)
        elif event == 'NewJPGReady':
            self.ignored_counter = 0
            self.handle_jpg_ready(message)
        elif event == 'AutoFocusResult':
            self.ignored_counter = 0
            self.handle_focus_result(message)
        elif event == 'LogEvent':
            self.ignored_counter = 0
            self.handle_log(message)
        elif event == 'ShotRunning':
            self.ignored_counter = 0
            self.handle_shot_running(message)
        elif event == 'ControlData':
            self.ignored_counter = 0
            self.handle_control_data(message)
        elif event in self.config.ignored_events:
            # do nothing
            message.pop('Event', None)
            message.pop('Host', None)
            message.pop('Inst', None)
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
            print(f'[{datetime.fromtimestamp(timestamp)}][{event}]: {message}')

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
        if img_fn != self.img_fn or guiding_shot_idx != self.guiding_idx:
            # new image or new guiding image
            self.img_fn = img_fn
            self.guiding_idx = guiding_shot_idx
            self.guided = True
            # print('!!!{} G{}-D{}'.format(timestamp, main_shot_elapsed, guiding_shot_idx))

    def handle_control_data(self, message):
        timestamp = message['Timestamp']
        guide_stat = message['GUIDESTAT']
        dither_stat = message['DITHSTAT']
        is_tracking = message['MNTTRACK']
        is_slewing = message['MNTSLEW']
        guide_x = message['GUIDEX']
        guide_y = message['GUIDEY']
        running_seq = message['RUNSEQ']
        running_dragscript = message['RUNDS']

        if self.guided:
            self.guided = False
            self.add_guide_error_stat(guide_x, guide_y)
            # print('{} G{}-D{} | T{}-S{} | X{} Y{}'.format(timestamp, guide_stat, dither_stat,
            #                                               is_tracking, is_slewing, guide_x, guide_y))

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
        if is_empty:
            return

        done = message['Done']
        last_error = message['LastError']
        if not done:
            self.send_text_message(f'Auto focusing failed with reason: {last_error}')
            return

        filter_index = message['FilterIndex']
        filter_color = message['FilterColor']
        HFD = message['HFD']
        star_index = message['StarIndex']
        focus_temp = message['FocusTemp']
        position = message['Position']
        telegram_message = f'AutoFocusing for filter {filter_index} is done with position {position}, HFD: {HFD}'
        self.send_text_message(telegram_message)

    def current_sequence_stat(self) -> SequenceStat:
        self.sequence_map.setdefault(self.running_seq, SequenceStat(name=self.running_seq))
        return self.sequence_map[self.running_seq]

    def add_exposure_stats(self, exposure: ExposureInfo):
        self.current_sequence_stat().add_exposure(exposure)

    def add_guide_error_stat(self, error_x: float, error_y: float):
        self.current_sequence_stat().add_guide_error((error_x, error_y))

    def handle_jpg_ready(self, message):
        expo = message['Expo']
        filter_name = message['Filter']
        HFD = message['HFD']
        star_index = message['StarIndex']
        sequence_target = message['SequenceTarget']

        # new stat code
        exposure = ExposureInfo(filter_name=filter_name, exposure_time=expo, hfd=HFD, star_index=star_index)
        self.add_exposure_stats(exposure)

        base64_photo = message['Base64Data']

        telegram_message = f'Exposure of {sequence_target} for {expo}sec using {filter_name} filter.' \
                           + f'HFD: {HFD}, StarIndex: {star_index}'

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

    def handle_log(self, message):
        type_dict = {1: 'DEBUG', 2: 'INFO', 3: 'WARNING', 4: 'CRITICAL', 5: 'ACTION', 6: 'SUBTITLE', 7: 'EVENT',
                     8: 'REQUEST', 9: 'EMERGENCY'}
        type_name = type_dict[message['Type']]
        content = f'[{type_name}]{message["Text"]}'
        telegram_message = f'<b><pre>{content}</pre></b>'
        print(content)
        if message['Type'] != 3 and message['Type'] != 4 and message['Type'] != 5 and message['Type'] != 9:
            return
        self.send_text_message(telegram_message)

    def report_stats_for_current_sequence(self):
        if self.current_sequence_stat().name == '':
            # one-off shots doesn't need stats, we only care about sequences.
            return
        sequence_stat = self.current_sequence_stat()

        base64_img = self.stat_plotter.plotter(seq_stat=sequence_stat, target_name=self.running_seq)

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
