#!/bin/env python3
# -*- coding: utf-8 -*-

import json
from pathlib import Path
import codecs
import base64
import webbrowser
import io

from PIL import Image


class HTMLTelegramBot:
    def __init__(self):
        Path("./replay/images").mkdir(parents=True, exist_ok=True)
        self.html_file = codecs.open('./replay/index.html', 'w', encoding='utf-8')
        self.write_header()
        self.image_count = 0
        self.event_sequence = 0

    def write_header(self):
        self.html_file.write('''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title></title>
  <link href="style.css" rel="stylesheet" />
</head>
<body>
  <script src="http://ajax.googleapis.com/ajax/libs/jquery/1/jquery.min.js"></script>
  <script>
  </script>
  <style>
  td{
  border:1px solid
  }
  </style>
  <table id="table">
    <tbody>
        <thead>
            <th>Event Sequence</th>
            <th>Type</th>
            <th>Details</th>
            <th>DateTime</th>                        
        </thead>
''')

    def write_footer(self):
        self.html_file.write('''</tbody></table></body></html>''')
        url = 'file://' + str(Path(self.html_file.name).absolute())
        self.html_file.flush()
        self.html_file.close()
        webbrowser.open(url, new=2)

    def send_text_message(self, message):
        self.html_file.write(f'<tr><td>{self.event_sequence}</td><td>Text Message</td><td>{message}</td></tr>\n')
        self.event_sequence += 1

    def edit_image_message(self, chat_id: str, message_id: str, base64_encoded_image, filename: str = ''):
        f = open(f'replay/images/image_{self.image_count}.jpg', 'wb')
        file_content = base64.b64decode(base64_encoded_image)
        f.write(file_content)
        f.close()

        stream = io.BytesIO(file_content)
        img = Image.open(stream).resize((300, 200))

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()
        base64_encoded_thumbnails = base64.b64encode(img_byte_arr).decode('ascii')
        self.html_file.write(
            f'''<tr><td>{self.event_sequence}</td><td>Edit Image</td>
            <td>
            A previously posted image [{message_id}] was updated, new image is:
            <br>
            <a href="images/image_{self.image_count}.jpg">
            <img style="width:300px;height:200px" src="data:image/jpeg;base64, {base64_encoded_thumbnails}" />
            </a></td></tr>\n''')
        self.event_sequence += 1
        self.image_count += 1

    def pin_message(self, chat_id: str, message_id: str) -> bool:
        message = f'Pinning messages for room [{chat_id}], message id: [{message_id}]'
        self.html_file.write(f'<tr><td>{self.event_sequence}</td><td>Pin Message</td><td>{message}</td></tr>\n')
        self.event_sequence += 1

    def unpin_message(self, chat_id: str, message_id: str) -> bool:
        message = f'Unpinning messages for room [{chat_id}], message id: [{message_id}]'
        self.html_file.write(f'<tr><td>{self.event_sequence}</td><td>Unpin Message</td><td>{chat_id}</td></tr>\n')
        self.event_sequence += 1

    def unpin_all_messages(self, chat_id: str) -> bool:
        message = f'Unpinning all messages for room [{chat_id}]'
        self.html_file.write(f'<tr><td>{self.event_sequence}</td><td>Unpin all Messages</td><td>N/A</td></tr>\n')
        self.event_sequence += 1

    def send_image_message(self, base64_encoded_image, filename: str = '', caption: str = '',
                           as_document: bool = True):
        f = open(f'replay/images/image_{self.image_count}.jpg', 'wb')
        file_content = base64.b64decode(base64_encoded_image)
        f.write(file_content)
        f.close()

        stream = io.BytesIO(file_content)
        img = Image.open(stream).resize((300, 200))

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()
        base64_encoded_thumbnails = base64.b64encode(img_byte_arr).decode('ascii')
        self.html_file.write(
            f'''<tr><td>{self.event_sequence}</td><td>Send Image</td>
            <td><a href="images/image_{self.image_count}.jpg">
            <img style="width:300px;height:200px" src="data:image/jpeg;base64, {base64_encoded_thumbnails}" />
            </a></td></tr>\n''')
        self.image_count += 1
        self.event_sequence += 1

        return 'dummy_chat_id', 'dummy_message_id'
