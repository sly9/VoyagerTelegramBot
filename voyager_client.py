#!/bin/env python3
import base64
import io
from collections import defaultdict
from datetime import datetime
from statistics import mean, stdev

import matplotlib.pyplot as plt

from telegram import TelegramBot

filter_meta = {
    'Ha': {'marker': '+', 'color': '#1f77b4'},
    'SII': {'marker': 'v', 'color': '#ff7f0e'},
    'OIII': {'marker': 'o', 'color': '#2ca02c'},
    'L': {'marker': '+', 'color': 'grey'},
    'R': {'marker': '+', 'color': 'red'},
    'G': {'marker': '+', 'color': 'green'},
    'B': {'marker': '+', 'color': 'blue'},
}

filter_mapping = {
    'H': 'Ha',
    'HA': 'Ha',
    'S': 'SII',
    'S2': 'SII',
    'SII': 'SII',
    'O': 'OIII',
    'O3': 'OIII',
    'OIII': 'OIII',
    'LUM': 'L',
    'L': 'L',
    'R': 'R',
    'G': 'G',
    'B': 'B',
    'RED': 'R',
    'GREEN': 'G',
    'BLUE': 'B',

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

        # stats
        self.total_exposures = defaultdict(float)

        self.hfd_list = list()
        self.star_idx = list()

        self.guide_x = list()
        self.guide_y = list()

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
            url=self.configs['voyager_setting']['url'],
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
        if self.guided:
            self.guided = False
            self.guide_x.append(guide_x)
            self.guide_y.append(guide_y)
            # print('{} G{}-D{} | T{}-S{} | X{} Y{}'.format(timestamp, guide_stat, dither_stat,
            #                                               is_tracking, is_slewing, guide_x, guide_y))

        if running_seq != self.running_seq:
            self.good_night_stats()
            self.running_seq = running_seq

            # reset statistics
            self.total_exposures = defaultdict(float)

            self.hfd_list = list()
            self.star_idx = list()

            self.guide_x = list()
            self.guide_y = list()

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

    def handle_jpg_ready(self, message):
        expo = message['Expo']
        filter_name = message['Filter']
        HFD = message['HFD']
        star_index = message['StarIndex']
        sequence_target = message['SequenceTarget']

        self.total_exposures[filter_name] += expo
        self.hfd_list.append((HFD, filter_name))
        self.star_idx.append((star_index, filter_name))

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

    def good_night_stats(self):
        if len(self.hfd_list) < 2:
            return

        n_figs = len(self.configs['good_night_stats'])
        fig, axs = plt.subplots(n_figs, figsize=(30, 10 * n_figs), squeeze=False)
        fig_idx = 0
        if 'HFDPlot' in self.configs['good_night_stats']:
            n_img = len(self.hfd_list)
            img_ids = range(n_img)
            hfd_values = list()
            dot_colors = list()
            star_idxes = list()
            for idx, (v, f) in enumerate(self.hfd_list):
                hfd_values.append(v)
                star_idxes.append(self.star_idx[idx][0])
                filter_normed = filter_mapping[f.upper()]
                dot_colors.append(filter_meta[filter_normed]['color'])

            ax = axs[fig_idx, 0]

            ax.scatter(img_ids, hfd_values, c=dot_colors)
            ax.plot(img_ids, hfd_values, color='purple')
            ax.tick_params(axis='y', labelcolor='purple')
            ax.set_ylabel('HFD', color='purple')

            secondary_ax = ax.twinx()
            secondary_ax.scatter(img_ids, star_idxes, c=dot_colors)
            secondary_ax.plot(img_ids, star_idxes, color='orange')
            secondary_ax.tick_params(axis='y', labelcolor='orange')
            secondary_ax.set_ylabel('star index', color='orange')

            ax.set_xlabel('image id')
            ax.set_title('HFD and StarIndex Plot ({target})'.format(target=self.running_seq))

            fig_idx += 1

        if 'ExposurePlot' in self.configs['good_night_stats']:
            ax = axs[fig_idx, 0]

            x = [filter_mapping[f] for f in self.total_exposures.keys()]
            v = self.total_exposures.values()
            rect = ax.bar(x, v, width=0.3)
            ax.bar_label(rect, padding=3)

            ax.set_ylabel('Exposure Time(s)')
            ax.set_title('Cumulative Exposure Time by Filter ({target})'.format(target=self.running_seq))

            fig_idx += 1

        if 'GuidePlot' in self.configs['good_night_stats']:
            ax = axs[fig_idx, 0]
            ax.plot(self.guide_x)
            ax.plot(self.guide_y)

            ax.set_title(
                'Guiding Plot ({target})\n'
                'X={x_mean:.03f}/{x_min:.03f}/{x_max:.03f}/{x_std:.03f}\n'
                'Y={y_mean:.03f}/{y_min:.03f}/{y_max:.03f}/{y_std:.03f}'.format(
                    target=self.running_seq,
                    x_mean=mean(self.guide_x), x_min=min(self.guide_x), x_max=max(self.guide_x),
                    x_std=stdev(self.guide_x),
                    y_mean=mean(self.guide_y), y_min=min(self.guide_y), y_max=max(self.guide_y),
                    y_std=stdev(self.guide_y),
                ))

            fig_idx += 1

        fig.tight_layout()

        img_bytes = io.BytesIO()
        plt.savefig(img_bytes, format='jpg')
        img_bytes.seek(0)
        base64_img = base64.b64encode(img_bytes.read())
        self.send_image_message(base64_img=base64_img, image_fn='good_night_stats.jpg',
                                msg_text='Statistics for {target}'.format(target=self.running_seq),
                                as_doc=False)
