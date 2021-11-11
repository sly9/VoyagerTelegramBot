#!/bin/env python3
import base64
import io
from datetime import datetime
from statistics import mean, stdev
import matplotlib.pyplot as plt
from sequence_stat import ExposureInfo, SequenceStat
from telegram import TelegramBot

filter_meta = {
    'Ha': {'marker': '+', 'color': '#E53935'},
    'SII': {'marker': 'v', 'color': '#B71C1C'},
    'OIII': {'marker': 'o', 'color': '#3F51B5'},
    'L': {'marker': '+', 'color': '#9E9E9E'},
    'R': {'marker': '+', 'color': '#F44336'},
    'G': {'marker': '+', 'color': '#4CAF50'},
    'B': {'marker': '+', 'color': '#2196F3'},
}


class VoyagerClient:
    def __init__(self, configs):
        self.telegram_bot = TelegramBot(configs=configs['telegram_setting'])
        self.configs = configs

        # interval vars
        self.running_seq = ''
        self.img_fn = ''
        self.guiding_idx = -1
        self.guided = False

        self.ignored_counter = 0

        self.sequence_map = dict()

    def send_text_message(self, msg_text: str = ''):
        if self.telegram_bot:
            self.telegram_bot.send_text_message(msg_text)

    def send_image_message(self, base64_img: bytes = None, image_fn: str = '', msg_text: str = '', as_doc: bool = True):
        if self.telegram_bot:
            self.telegram_bot.send_image_message(base64_img, image_fn, msg_text, as_doc)

    def parse_message(self, event, message):
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
        elif event in self.configs['ignored_events']:
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
            print('[%s][%s]: %s' % (datetime.fromtimestamp(timestamp), event, message))

    def handle_version(self, message):
        telegram_message = 'Connected to <b>{host_name}({url})</b> [{version}]'.format(
            host_name=message['Host'],
            url=self.configs['voyager_setting']['domain'],
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

        if running_dragscript == '':
            # clear data if there's no drag script running.
            self.sequence_map = {}

        if running_seq != self.running_seq:
            self.report_stats_for_current_sequence()
            self.running_seq = running_seq

    def handle_focus_result(self, message):
        is_empty = message['IsEmpty']
        if is_empty:
            return

        done = message['Done']
        last_error = message['LastError']
        if not done:
            self.send_text_message('Auto focusing failed with reason: %s' % last_error)
            return

        filter_index = message['FilterIndex']
        filter_color = message['FilterColor']
        HFD = message['HFD']
        star_index = message['StarIndex']
        focus_temp = message['FocusTemp']
        position = message['Position']
        telegram_message = 'AutoFocusing for filter %d is done with position %d, HFD: %f' % (
            filter_index, position, HFD)
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
        telegram_message = 'Exposure of %s for %dsec using %s filter. HFD: %.2f, StarIndex: %.2f' % (
            sequence_target, expo, filter_name, HFD, star_index)

        if expo >= self.configs['exposure_limit'] and self.configs['send_image_msgs']:
            fit_filename = message['File']
            new_filename = fit_filename[fit_filename.rindex('\\') + 1: fit_filename.index('.')] + '.jpg'
            self.send_image_message(base64_photo, new_filename, telegram_message)
        else:
            self.send_text_message(telegram_message)

    def handle_log(self, message):
        type_dict = {1: 'DEBUG', 2: 'INFO', 3: 'WARNING', 4: 'CRITICAL', 5: 'ACTION', 6: 'SUBTITLE', 7: 'EVENT',
                     8: 'REQUEST', 9: 'EMERGENCY'}
        type_name = type_dict[message['Type']]
        content = '[%s]%s' % (type_name, message['Text'])
        telegram_message = '<b><pre>%s</pre></b>' % content
        print(content)
        if message['Type'] != 3 and message['Type'] != 4 and message['Type'] != 5 and message['Type'] != 9:
            return
        self.send_text_message(telegram_message)

    def report_stats_for_current_sequence(self):
        if self.current_sequence_stat().name == '':
            # one-off shots doesn't need stats, we only care about sequences.
            return
        sequence_stat = self.current_sequence_stat()

        plt.rcParams.update({'text.color': '#F5F5F5', 'font.size': 40, 'font.weight': 'bold',
                             'axes.edgecolor': '#F5F5F5', 'xtick.color': '#F5F5F5', 'ytick.color': '#F5F5F5',
                             'figure.facecolor': '#212121'})

        figure_count = len(self.configs['sequence_stats_config'])
        fig, axes = plt.subplots(figure_count, figsize=(30, 10 * figure_count), squeeze=False)
        figure_index = 0
        if 'HFDPlot' in self.configs['sequence_stats_config']:
            img_ids = range(sequence_stat.exposure_count())
            hfd_values = list()
            dot_colors = list()
            star_indices = list()
            for exposure_info in sequence_stat.exposure_info_list:
                hfd_values.append(exposure_info.hfd)
                star_indices.append(exposure_info.star_index)
                dot_colors.append(filter_meta[exposure_info.filter_name]['color'])

            ax = axes[figure_index, 0]
            ax.set_facecolor('#212121')

            ax.scatter(img_ids, hfd_values, c=dot_colors, s=500)
            ax.plot(img_ids, hfd_values, color='#0D47A1', linewidth=10)
            ax.tick_params(axis='y', labelcolor='#0D47A1')
            ax.set_ylabel('HFD', color='#0D47A1')

            secondary_ax = ax.twinx()
            secondary_ax.scatter(img_ids, star_indices, c=dot_colors, s=500)
            secondary_ax.plot(img_ids, star_indices, color='#388E3C', linewidth=10)
            secondary_ax.tick_params(axis='y', labelcolor='#388E3C')
            secondary_ax.set_ylabel('Star Index', color='#388E3C')

            ax.set_xlabel('Image Index')
            ax.xaxis.label.set_color('#F5F5F5')
            ax.set_title('HFD and StarIndex Plot ({target})'.format(target=self.running_seq))

            figure_index += 1

        if 'ExposurePlot' in self.configs['sequence_stats_config']:
            ax = axes[figure_index, 0]
            ax.set_facecolor('#212121')
            total_exposure_stat = sequence_stat.exposure_time_stat_dictionary()
            keys = list(total_exposure_stat.keys())
            values = total_exposure_stat.values()
            rectangles = ax.bar(keys, values)
            for i in range(len(keys)):
                color_name = keys[i]
                color = filter_meta[color_name]['color']
                rect = rectangles[i]
                rect.set_color(color)

            ax.bar_label(rectangles, label_type='center', fontsize=48)

            ax.set_ylabel('Exposure Time(s)')
            ax.yaxis.label.set_color('#F5F5F5')
            ax.set_title('Cumulative Exposure Time by Filter ({target})'.format(target=self.running_seq))

            figure_index += 1

        if 'GuidePlot' in self.configs['sequence_stats_config']:
            if len(sequence_stat.guide_x_error_list) < 3:
                print('not possible to calculate mean')
            ax = axes[figure_index, 0]
            ax.set_facecolor('#212121')
            ax.plot(sequence_stat.guide_x_error_list, color='#F44336', linewidth=2)
            ax.plot(sequence_stat.guide_y_error_list, color='#2196F3', linewidth=2)

            abs_x_list = [abs(number) for number in sequence_stat.guide_x_error_list]
            abs_y_list = [abs(number) for number in sequence_stat.guide_y_error_list]
            ax.set_title(
                'Guiding Plot ({target})(avg(abs)/min/max/std)\n'
                'X={x_mean:.03f}/{x_min:.03f}/{x_max:.03f}/{x_std:.03f}\n'
                'Y={y_mean:.03f}/{y_min:.03f}/{y_max:.03f}/{y_std:.03f}'.format(
                    target=self.running_seq,
                    x_mean=mean(abs_x_list), x_min=min(sequence_stat.guide_x_error_list),
                    x_max=max(sequence_stat.guide_x_error_list),
                    x_std=stdev(sequence_stat.guide_x_error_list),
                    y_mean=mean(abs_y_list), y_min=min(sequence_stat.guide_y_error_list),
                    y_max=max(sequence_stat.guide_y_error_list),
                    y_std=stdev(sequence_stat.guide_y_error_list),
                ))
            figure_index += 1
        fig.tight_layout()

        img_bytes = io.BytesIO()
        plt.savefig(img_bytes, format='jpg')
        img_bytes.seek(0)
        base64_img = base64.b64encode(img_bytes.read())
        self.send_image_message(base64_img=base64_img, image_fn='good_night_stats.jpg',
                                msg_text='Statistics for {target}'.format(target=self.running_seq),
                                as_doc=False)
