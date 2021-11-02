#!/bin/env python3

import base64
import io
import tempfile
from typing import Dict

import requests
from PIL import Image


class TelegramBot:
    def __init__(self, configs: Dict = None):
        self.token = configs['bot_token']
        self.chat_ids = configs['chat_ids']
        print('telegram bot init.')
        print('\ttoken: {token}\n, subscribed chats: {chat_ids}'.format(token=self.token, chat_ids=self.chat_ids))

    def send_text_message(self, message):
        url = 'https://api.telegram.org/bot{token}/sendMessage'.format(token=self.token)
        for chat_id in self.chat_ids:
            myobj = {'chat_id': chat_id, 'text': message, 'parse_mode': 'html'}
            requests.post(url, data=myobj)

    def send_base64_photo(self, base64_encoded_image, filename, caption=''):
        file_content = base64.b64decode(base64_encoded_image)
        f = tempfile.TemporaryFile()
        f.write(file_content)
        f.seek(0)
        thumb_f = tempfile.TemporaryFile()
        stream = io.BytesIO(file_content)
        img = Image.open(stream).resize((320, 214))
        img.save(thumb_f, "JPEG")
        thumb_f.seek(0)
        url = 'https://api.telegram.org/bot{token}/sendDocument'.format(token=self.token)
        for chat_id in self.chat_ids:
            myobj = {'chat_id': chat_id, 'thumb': 'attach://preview_' + filename,
                     'caption': caption}
            files = {'document': (filename, f, 'image/jpeg'),
                     'thumb': ('preview_' + filename, thumb_f, 'image/jpeg')}
            print(requests.post(url, data=myobj, files=files).text)
        f.close()
        thumb_f.close()


if __name__ == '__main__':
    #     #TelegramBot.send_text_message('''<pre>+--------+-------+--------+
    # | Symbol | Price | Change |
    # +--------+-------+--------+
    # | ABC    | 20.85 |  1.626 |
    # | DEF    | 78.95 |  0.099 |
    # | GHI    | 23.45 |  0.192 |
    # | JKL    | 98.85 |  0.292 |
    # +--------+-------+--------+</pre>''')

    # TelegramBot.send_text_message('hello world')
    with open("Iris.jpg", "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
        TelegramBot.send_base64_photo(encoded_string, 'Iris.jpg')
