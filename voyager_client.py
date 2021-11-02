#!/bin/env python3

from datetime import datetime

from telegram import TelegramBot


class VoyagerClient:
    def __init__(self, configs):
        self.telegram_bot = TelegramBot(configs=configs['telegram_setting'])
        self.configs = configs

    def send_text_message(self, msg_text: str = ''):
        if self.telegram_bot:
            self.telegram_bot.send_text_message(msg_text)

    def send_image_message(self, base64_img: str = '', image_fn: str = '', msg_text: str = ''):
        new_filename = image_fn[image_fn.rindex('\\') + 1: image_fn.index('.')] + '.jpg'
        if self.telegram_bot:
            self.telegram_bot.send_base64_photo(base64_img, new_filename, msg_text)

    def parse_message(self, event, message):
        if event == 'Version':
            self.handle_version(message)
        elif event == 'NewJPGReady':
            self.handle_jpg_ready(message)
        elif event == 'AutoFocusResult':
            self.handle_focus_result(message)
        elif event == 'LogEvent':
            self.handle_log(message)
        elif event in self.configs['ignored_events']:
            # do nothing
            message.pop('Event', None)
            message.pop('Host', None)
            message.pop('Inst', None)
            print('.', end='', flush=True)
        else:
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
        sequence_target = message['SequenceTarget']
        HFD = message['HFD']
        star_index = message['StarIndex']
        base64_photo = message['Base64Data']
        telegram_message = 'Exposure of %s for %dsec using %s filter. HFD: %.2f, StarIndex: %.2f' % (
            sequence_target, expo, filter_name, HFD, star_index)
        if expo >= self.configs['exposure_limit']:
            fit_filename = message['File']
            self.send_image_message(base64_photo, fit_filename, telegram_message)
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
