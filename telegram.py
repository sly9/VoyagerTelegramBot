#!/bin/env python3

import json
import base64
import io
import tempfile
from configs import ConfigBuilder
from typing import Dict

import requests
from PIL import Image
import time


class TelegramBot:
    def __init__(self, config_builder: ConfigBuilder = None):
        self.config = config_builder.build()
        self.token = self.config.telegram_setting.bot_token
        self.chat_ids = self.config.telegram_setting.chat_ids
        # print('telegram bot init.')
        # print('\ttoken: {token}\n\tchats: {chat_ids}'.format(token=self.token, chat_ids=self.chat_ids))
        self.urls = {
            'text': 'https://api.telegram.org/bot{token}/sendMessage'.format(token=self.token),
            'doc': 'https://api.telegram.org/bot{token}/sendDocument'.format(token=self.token),
            'edit_message_media': 'https://api.telegram.org/bot{token}/editMessageMedia'.format(token=self.token),
            'pic': 'https://api.telegram.org/bot{token}/sendPhoto'.format(token=self.token),
            'pin_message': 'https://api.telegram.org/bot{token}/pinChatMessage'.format(token=self.token),
            'unpin_message': 'https://api.telegram.org/bot{token}/unpinChatMessage'.format(token=self.token),
            'unpin_all_messages': 'https://api.telegram.org/bot{token}/unpinAllChatMessages'.format(token=self.token),
        }

    def send_text_message(self, message):
        responses = []
        for chat_id in self.chat_ids:
            payload = {'chat_id': chat_id, 'text': message, 'parse_mode': 'html'}
            send_text_response = requests.post(self.urls['text'], data=payload)
            responses.append(send_text_response)
        return responses

    def send_image_message(self, base64_encoded_image, filename: str = '', caption: str = '', as_document: bool = True):
        responses = []
        file_content = base64.b64decode(base64_encoded_image)

        f = tempfile.TemporaryFile()
        f.write(file_content)
        f.seek(0)

        thumb_f = tempfile.TemporaryFile()
        stream = io.BytesIO(file_content)
        img = Image.open(stream).resize((320, 214))
        img.save(thumb_f, "JPEG")
        thumb_f.seek(0)

        for chat_id in self.chat_ids:
            if as_document:
                payload = {'chat_id': chat_id, 'thumb': 'attach://preview_' + filename,
                           'caption': caption}
                files = {'document': (filename, f, 'image/jpeg'),
                         'thumb': ('preview_' + filename, thumb_f, 'image/jpeg')}

                send_image_response = requests.post(self.urls['doc'], data=payload, files=files)
            else:
                payload = {'chat_id': chat_id, 'caption': caption}
                files = {'photo': (filename, f, 'image/jpeg')}
                send_image_response = requests.post(self.urls['pic'], data=payload, files=files)
            responses.append(send_image_response)

        f.close()
        thumb_f.close()
        return responses

    def edit_image_message(self, chat_id: str, message_id: str, base64_encoded_image, filename: str = ''):
        file_content = base64.b64decode(base64_encoded_image)
        f = tempfile.TemporaryFile()
        f.write(file_content)
        f.seek(0)

        payload = {'chat_id': chat_id, 'message_id': message_id,
                   'media': json.dumps({'type': 'photo', 'media': 'attach://media'})}
        files = {'media': (filename, f, 'image/jpeg')}
        send_image_response = requests.post(self.urls['edit_message_media'], data=payload, files=files)

        f.close()
        return send_image_response

    def pin_message(self, chat_id: str, message_id: str) -> bool:
        payload = {'chat_id': chat_id, 'message_id': message_id, 'disable_notification': True}
        pin_message_response = requests.post(self.urls['pin_message'], data=payload)
        result = json.loads(pin_message_response.text)
        return result['ok'] and result['result']

    def unpin_message(self, chat_id: str, message_id: str) -> bool:
        payload = {'chat_id': chat_id, 'message_id': message_id}
        unpin_message_response = requests.post(self.urls['unpin_message'], data=payload)
        result = json.loads(unpin_message_response.text)
        return result['ok'] and result['result']

    def unpin_all_messages(self, chat_id: str) -> bool:
        payload = {'chat_id': chat_id}
        unpin_message_response = requests.post(self.urls['unpin_all_messages'], data=payload)
        result = json.loads(unpin_message_response.text)
        return result['ok'] and result['result']


if __name__ == '__main__':
    c = ConfigBuilder()
    t = TelegramBot(config_builder=c)
    t.send_text_message(message='hello world')
    with open("tests/ic5070.jpg", "rb") as image_file, open("tests/m42.jpg", "rb") as second_image_file:
        encoded_string = base64.b64encode(image_file.read())
        response = t.send_image_message(encoded_string, 'ic5070.jpg')[0]
        response_json = json.loads(response.text)
        print(json.dumps(response_json, indent=4, sort_keys=True))
        chat_id = response_json['result']['chat']['id']
        message_id = response_json['result']['message_id']
        t.pin_message(chat_id=chat_id, message_id=message_id)
        encoded_string = base64.b64encode(second_image_file.read())
        response = t.edit_image_message(chat_id=chat_id, message_id=message_id, base64_encoded_image=encoded_string,
                                        filename='m42.jpg')
        print(response.text)
        t.unpin_message(chat_id=chat_id, message_id=message_id)
