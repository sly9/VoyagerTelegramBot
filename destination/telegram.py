#!/bin/env python3

import io
import json
import tempfile
from typing import Tuple, Dict, Any

import requests
from PIL import Image

from configs import ConfigBuilder
from console import main_console
from data_structure.log_message_info import LogMessageInfo
from event_emitter import ee
from event_names import BotEvent
from throttler import throttle


class Telegram:
    def __init__(self, config=None):
        self.config = config
        self.token = self.config.telegram_setting.bot_token
        self.chat_id = self.config.telegram_setting.chat_id
        self.image_chat_id = self.config.telegram_setting.image_chat_id

        self.urls = {
            'text': f'https://api.telegram.org/bot{self.token}/sendMessage',
            'doc': f'https://api.telegram.org/bot{self.token}/sendDocument',
            'edit_message_media': f'https://api.telegram.org/bot{self.token}/editMessageMedia',
            'pic': f'https://api.telegram.org/bot{self.token}/sendPhoto',
            'pin_message': f'https://api.telegram.org/bot{self.token}/pinChatMessage',
            'unpin_message': f'https://api.telegram.org/bot{self.token}/unpinChatMessage',
            'unpin_all_messages': f'https://api.telegram.org/bot{self.token}/unpinAllChatMessages',
        }

        self.sequence_name_to_message_id_map = {}

        ee.on(BotEvent.SEND_TEXT_MESSAGE.name, self.send_text_message)
        ee.on(BotEvent.SEND_IMAGE_MESSAGE.name, self.send_image_message)
        ee.on(BotEvent.EDIT_IMAGE_MESSAGE.name, self.edit_image_message)
        ee.on(BotEvent.UPDATE_SEQUENCE_STAT_IMAGE.name, self.update_sequence_stat_image)
        ee.on(BotEvent.PIN_MESSAGE.name, self.pin_message)
        ee.on(BotEvent.UNPIN_MESSAGE.name, self.unpin_message)
        ee.on(BotEvent.UNPIN_ALL_MESSAGE.name, self.unpin_all_messages)

    def update_sequence_stat_image(self, sequence_stat_image: bytes, sequence_name: str, sequence_stat_message: str):
        known_message_id = self.sequence_name_to_message_id_map.get(sequence_name, '')
        if known_message_id:
            status, info_dict = self.edit_image_message(chat_id=self.image_chat_id,
                                                        message_id=known_message_id,
                                                        image_data=sequence_stat_image,
                                                        filename=sequence_name + '_stat.jpg')
            if status == 'ERROR':
                ee.emit(BotEvent.APPEND_ERROR_LOG.name,
                        error=LogMessageInfo(type='ERROR', message='EditMessage: ' + info_dict["description"]))
        else:
            status, info_dict = self.send_image_message(image_data=sequence_stat_image,
                                                        filename='good_night_stats.jpg',
                                                        caption=f'Statistics for {sequence_name}',
                                                        send_as_file=False)
            message_id = info_dict.get('message_id', '')
            self.sequence_name_to_message_id_map[sequence_name] = message_id

            if status == 'OK' and message_id:
                status, info_dict = self.pin_message(chat_id=self.image_chat_id, message_id=message_id)
                if status == 'ERROR':
                    ee.emit(BotEvent.APPEND_ERROR_LOG.name,
                            error=LogMessageInfo(type='ERROR', message='PinMessage: ' + info_dict["description"]))
            else:
                ee.emit(BotEvent.APPEND_ERROR_LOG.name,
                        error=LogMessageInfo(type='ERROR', message='send_image_message: ' + info_dict["description"]))

    # Avoids text message spew caused by talky Voyager
    # Limits from Telegram API:
    # To a particular chat, <= 1 message per second.
    # To multiple users, <= 30 messages per second.
    # To a group, <=20 messages per minute.
    #
    # Limit text message rate to 15 per minute and save 5 more for other types (e.g. image message)
    # @throttle(rate_limit=15, period=60.0)
    # async def send_text_message(self, message: str = '', silent: bool = False) -> Tuple[str, Dict[str, Any]]:
    def send_text_message(self, message: str = '', silent: bool = False) -> Tuple[str, Dict[str, Any]]:
        payload = {'chat_id': self.chat_id, 'text': message, 'parse_mode': 'html', 'disable_notification': silent}
        send_text_message_response = requests.post(self.urls['text'], data=payload)
        response_json = json.loads(send_text_message_response.text)

        if response_json['ok']:
            info_dict = {
                'chat_id': str(response_json['result']['chat']['id']),
                'message_id': str(response_json['result']['message_id'])
            }
            return 'OK', info_dict
        else:
            response_json.pop('ok')
            return 'ERROR', response_json

    def send_image_message(self, image_data: bytes,
                           filename: str = '',
                           caption: str = '',
                           send_as_file: bool = True) -> Tuple[str, Dict[str, Any]]:
        with tempfile.TemporaryFile() as f, tempfile.TemporaryFile() as thumb_f:
            f.write(image_data)
            f.seek(0)

            stream = io.BytesIO(image_data)
            img = Image.open(stream).resize((320, 214))
            img.save(thumb_f, "JPEG")
            thumb_f.seek(0)

            if send_as_file:
                payload = {'chat_id': self.image_chat_id, 'thumb': 'attach://preview_' + filename,
                           'caption': caption}
                files = {'document': (filename, f, 'image/jpeg'),
                         'thumb': ('preview_' + filename, thumb_f, 'image/jpeg')}

                send_image_response = requests.post(self.urls['doc'], data=payload, files=files)
            else:
                payload = {'chat_id': self.image_chat_id, 'caption': caption}
                files = {'photo': (filename, f, 'image/jpeg')}
                send_image_response = requests.post(self.urls['pic'], data=payload, files=files)

            response_json = json.loads(send_image_response.text)

            stream.close()

            if response_json['ok']:
                info_dict = {
                    'chat_id': str(response_json['result']['chat']['id']),
                    'message_id': str(response_json['result']['message_id'])
                }
                return 'OK', info_dict
            else:
                response_json.pop('ok')
                return 'ERROR', response_json

    def edit_image_message(self, chat_id: str,
                           message_id: str,
                           image_data: bytes,
                           filename: str = '') -> Tuple[str, Dict[str, Any]]:

        with tempfile.TemporaryFile() as f:
            f.write(image_data)
            f.seek(0)

            payload = {'chat_id': chat_id, 'message_id': message_id,
                       'media': json.dumps({'type': 'photo', 'media': 'attach://media'})}
            files = {'media': (filename, f, 'image/jpeg')}

            edit_image_message_response = requests.post(self.urls['edit_message_media'], data=payload, files=files)
            response_json = json.loads(edit_image_message_response.text)

            if response_json['ok']:
                info_dict = {
                    'chat_id': str(response_json['result']['chat']['id']),
                    'message_id': str(response_json['result']['message_id'])
                }
                return 'OK', info_dict
            else:
                response_json.pop('ok')
                return 'ERROR', response_json

    def pin_message(self, chat_id: str, message_id: str) -> Tuple[str, Dict[str, Any]]:
        payload = {'chat_id': chat_id, 'message_id': message_id, 'disable_notification': True}
        pin_message_response = requests.post(self.urls['pin_message'], data=payload)
        response_json = json.loads(pin_message_response.text)

        if response_json['ok']:
            return 'OK', dict()
        else:
            response_json.pop('ok')
            return 'ERROR', response_json

    def unpin_message(self, chat_id: str, message_id: str) -> Tuple[str, Dict[str, Any]]:
        payload = {'chat_id': chat_id, 'message_id': message_id}
        unpin_message_response = requests.post(self.urls['unpin_message'], data=payload)
        response_json = json.loads(unpin_message_response.text)

        if response_json['ok']:
            return 'OK', dict()
        else:
            response_json.pop('ok')
            return 'ERROR', response_json

    def unpin_all_messages(self, chat_id: str = '') -> Tuple[str, Dict[str, Any]]:
        if not chat_id:
            chat_id = self.image_chat_id
        payload = {'chat_id': chat_id}
        unpin_message_response = requests.post(self.urls['unpin_all_messages'], data=payload)
        response_json = json.loads(unpin_message_response.text)

        if response_json['ok']:
            self.sequence_name_to_message_id_map = {}
            return 'OK', dict()
        else:
            return 'ERROR', response_json


if __name__ == '__main__':
    c = ConfigBuilder()
    c.validate()
    t = Telegram(config=c.build())
    response = t.send_text_message(message='hello world')
    main_console.print(response)

    with open("tests/ic5070.jpg", "rb") as image_file, open("tests/m42.jpg", "rb") as second_image_file:
        response = t.send_image_message(image_file.read(), 'ic5070.jpg')
        main_console.print(response)

        the_chat_id = response[1]['chat_id']
        the_message_id = response[1]['message_id']

        response = t.pin_message(chat_id=the_chat_id, message_id=the_message_id)
        main_console.print(response)

        response = t.edit_image_message(chat_id=the_chat_id, message_id=the_message_id,
                                        image_data=second_image_file.read(),
                                        filename='m42.jpg')
        main_console.print(response)

        response = t.unpin_message(chat_id=the_chat_id, message_id=the_message_id)
        main_console.print(response)

    # Test message spew
    import asyncio
    import time

    async def spew(count: int = 20):
        message_spew = [t.send_text_message('message_spew {id}'.format(id=msg_id)) for msg_id in range(count)]
        for message in message_spew:
            _ = await message
            main_console.print('Timestamp: {}'.format(time.time()))


    asyncio.run(spew(20))
