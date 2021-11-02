#!/bin/env python3

import requests
import base64
import tempfile
from PIL import Image
import io
import PIL
import os

class TelegramBot:
    TELEGRAM_BOT_TOKEN = '1917049368:AAH01i_vzlz2_5ZCzFAXoRH8IB9vZl8n-s0'
    GROUP_CHAT_ID = '-650246590'

    def send_text_message(message):
        url = 'https://api.telegram.org/bot%s/sendMessage' % TelegramBot.TELEGRAM_BOT_TOKEN
        myobj = {'chat_id': TelegramBot.GROUP_CHAT_ID, 'text': message,'parse_mode':'html'}
        requests.post(url, data = myobj)
        
    def send_base64_photo(base64_encoded_image, filename, caption = ''):
        file_content=base64.b64decode(base64_encoded_image)
        f =  tempfile.TemporaryFile()
        f.write(file_content)
        f.seek(0)
        thumb_f =  tempfile.TemporaryFile()
        stream = io.BytesIO(file_content)
        img = Image.open(stream).resize((320,214))
        img.save(thumb_f, "JPEG")
        thumb_f.seek(0)
        url = 'https://api.telegram.org/bot%s/sendDocument' % TelegramBot.TELEGRAM_BOT_TOKEN
        myobj = {'chat_id': TelegramBot.GROUP_CHAT_ID,'thumb':'attach://preview_'+filename,'caption':caption}
        files = {'document':(filename, f, 'image/jpeg'),
                 'thumb':('preview_'+filename, thumb_f, 'image/jpeg')}
        print(requests.post(url, data = myobj, files=files).text)
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
      TelegramBot.send_base64_photo(encoded_string,'Iris.jpg')