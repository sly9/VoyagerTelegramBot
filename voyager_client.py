#!/bin/env python3
import base64
import io
from collections import defaultdict
from datetime import datetime

import matplotlib.pyplot as plt

from configs import Configs
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

        self.total_exposures = defaultdict(float)
        self.hfd_list = list()
        self.ignored_counter = 0

    def send_text_message(self, msg_text: str = ''):
        if self.telegram_bot:
            self.telegram_bot.send_text_message(msg_text)

    def send_image_message(self, base64_img: bytes = None, image_fn: str = '', msg_text: str = ''):
        if self.telegram_bot:
            self.telegram_bot.send_base64_photo(base64_img, image_fn, msg_text)

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
        self.total_exposures[filter_name] += expo

        sequence_target = message['SequenceTarget']
        HFD = message['HFD']
        star_index = message['StarIndex']
        base64_photo = message['Base64Data']
        telegram_message = 'Exposure of %s for %dsec using %s filter. HFD: %.2f, StarIndex: %.2f' % (
            sequence_target, expo, filter_name, HFD, star_index)

        if expo >= self.configs['exposure_limit']:
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
        n_figs = len(self.configs['good_night_stats'])
        fig, axs = plt.subplots(n_figs, figsize=(5, 3 * n_figs), squeeze=False)
        fig_idx = 0
        if 'HFDPlot' in self.configs['good_night_stats']:
            # self.send_image_message()
            print('hfd', self.hfd_list)

            n_img = len(self.hfd_list)
            img_ids = range(n_img)
            hfd_values = list()
            dot_colors = list()
            dot_markers = list()
            for idx, (v, f) in enumerate(self.hfd_list):
                hfd_values.append(v)
                filter_normed = filter_mapping[f.upper()]
                dot_colors.append(filter_meta[filter_normed]['color'])

            axs[fig_idx, 0].scatter(img_ids, hfd_values, c=dot_colors)
            axs[fig_idx, 0].plot(img_ids, hfd_values)
            axs[fig_idx, 0].set_title('HFD Plot')

            # plt.show()
            fig_idx += 1

        if 'ExposurePlot' in self.configs['good_night_stats']:
            print('exposure')
            filters = [filter_mapping[f.upper()] for f in self.total_exposures.keys()]
            cum_exposures = self.total_exposures.values()

            axs[fig_idx, 0].bar(filters, cum_exposures)
            axs[fig_idx, 0].set_title('Cumulative Exposure Time by Filter')

            fig_idx += 1

        img_bytes = io.BytesIO()
        plt.savefig(img_bytes, format='jpg')
        img_bytes.seek(0)
        base64_img = base64.b64encode(img_bytes.read())
        self.send_image_message(base64_img=base64_img, image_fn='good_night_stats.jpg',
                                msg_text='Statistics for last night')


if __name__ == '__main__':
    test_client = VoyagerClient(configs=Configs().configs)
    test_client.hfd_list = [(1.1, 'H'),
                            (1.2, 'H'),
                            (1.4, 'S'),
                            (1.1, 'Ha'),
                            (1.2, 'S'),
                            (1.4, 'SII'),
                            (1.1, 'O'),
                            (1.2, 'OIII'),
                            (1.4, 'O3'),
                            (1.1, 'L'),
                            (1.2, 'L'),
                            (1.4, 's')]

    test_client.total_exposures = {'H': 1000, 'S': 500, 'L': 300}

    test_client.good_night_stats()
