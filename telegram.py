#!/bin/env python3

import base64
import io
import tempfile
from typing import Dict

import requests
from PIL import Image
import time


class TelegramBot:
    def __init__(self, configs: Dict = None):
        self.configs = configs
        self.token = configs['bot_token']
        self.chat_ids = configs['chat_ids']
        # print('telegram bot init.')
        # print('\ttoken: {token}\n\tchats: {chat_ids}'.format(token=self.token, chat_ids=self.chat_ids))
        self.urls = {
            'text': 'https://api.telegram.org/bot{token}/sendMessage'.format(token=self.token),
            'doc': 'https://api.telegram.org/bot{token}/sendDocument'.format(token=self.token),
            'pic': 'https://api.telegram.org/bot{token}/sendPhoto'.format(token=self.token),
        }

    def send_text_message(self, message):
        for chat_id in self.chat_ids:
            myobj = {'chat_id': chat_id, 'text': message, 'parse_mode': 'html'}
            if self.configs['debugging']:
                print(message)
            else:
                requests.post(self.urls['text'], data=myobj)

    def send_image_message(self, base64_encoded_image, filename: str = '', caption: str = '', as_document: bool = True):
        if self.configs['debugging']:
            time.sleep(5)
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
                myobj = {'chat_id': chat_id, 'thumb': 'attach://preview_' + filename,
                         'caption': caption}
                files = {'document': (filename, f, 'image/jpeg'),
                         'thumb': ('preview_' + filename, thumb_f, 'image/jpeg')}

                requests.post(self.urls['doc'], data=myobj, files=files)
            else:
                myobj = {'chat_id': chat_id, 'caption': caption}
                files = {'photo': (filename, f, 'image/jpeg')}
                requests.post(self.urls['pic'], data=myobj, files=files)

        f.close()
        thumb_f.close()


if __name__ == '__main__':
    TelegramBot.send_text_message('hello world')
    with open("Iris.jpg", "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
        TelegramBot.send_image_message(encoded_string, 'Iris.jpg')
