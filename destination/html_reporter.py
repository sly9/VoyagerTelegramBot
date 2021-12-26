#!/bin/env python3
# -*- coding: utf-8 -*-

import base64
import codecs
import io
import webbrowser
from pathlib import Path
from typing import Tuple, Dict

from PIL import Image

from event_emitter import ee
from event_names import BotEvent


class HTMLReporter:
    def __init__(self):
        Path("./replay/images").mkdir(parents=True, exist_ok=True)
        self.html_file = codecs.open('./replay/index1.html', 'w', encoding='utf-8')
        self.write_header()
        self.image_count = 0
        self.event_sequence = 0
        ee.on(BotEvent.SEND_TEXT_MESSAGE.name, self.send_text_message)
        ee.on(BotEvent.SEND_IMAGE_MESSAGE.name, self.send_image_message)
        ee.on(BotEvent.EDIT_IMAGE_MESSAGE.name, self.edit_image_message)
        ee.on(BotEvent.PIN_MESSAGE.name, self.pin_message)
        ee.on(BotEvent.UNPIN_MESSAGE.name, self.unpin_message)
        ee.on(BotEvent.UNPIN_ALL_MESSAGE.name, self.unpin_all_messages)
        ee.on(BotEvent.UPDATE_SEQUENCE_STAT_IMAGE.name, self.update_sequence_stat_image)

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

    def send_text_message(self, message) -> Tuple[str, Dict]:
        self.html_file.write(f'<tr><td>{self.event_sequence}</td><td>Text Message</td><td>{message}</td></tr>\n')
        self.event_sequence += 1

    def edit_image_message(self, chat_id: str, message_id: str,
                           image_data:bytes, filename: str = '') -> Tuple[str, Dict]:
        f = open(f'replay/images/image_{self.image_count}.jpg', 'wb')

        f.write(image_data)
        f.close()

        stream = io.BytesIO(image_data)
        img = Image.open(stream)
        basewidth = 300
        wpercent = (basewidth / float(img.size[0]))
        hsize = int((float(img.size[1]) * float(wpercent)))

        img.thumbnail((basewidth, hsize))

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
            <img src="data:image/jpeg;base64, {base64_encoded_thumbnails}" />
            </a></td></tr>\n''')
        self.event_sequence += 1
        self.image_count += 1

        return 'OK', {'chat_id': '19052485', 'message_id': '19091585'}

    def pin_message(self, chat_id: str, message_id: str) -> Tuple[str, Dict]:
        message = f'Pinning messages for room [{chat_id}], message id: [{message_id}]'
        self.html_file.write(f'<tr><td>{self.event_sequence}</td><td>Pin Message</td><td>{message}</td></tr>\n')
        self.event_sequence += 1

        return 'OK', dict()

    def unpin_message(self, chat_id: str, message_id: str) -> Tuple[str, Dict]:
        message = f'Unpinning messages for room [{chat_id}], message id: [{message_id}]'
        self.html_file.write(f'<tr><td>{self.event_sequence}</td><td>Unpin Message</td><td>{chat_id}</td></tr>\n')
        self.event_sequence += 1

        return 'OK', dict()

    def unpin_all_messages(self, chat_id: str) -> Tuple[str, Dict]:
        message = f'Unpinning all messages for room [{chat_id}]'
        self.html_file.write(f'<tr><td>{self.event_sequence}</td><td>Unpin all Messages</td><td>N/A</td></tr>\n')
        self.event_sequence += 1

        return 'OK', dict()

    def update_sequence_stat_image(self, sequence_stat_image: bytes, sequence_name: str):
        self.send_image_message(image_data=sequence_stat_image, filename='SequenceStats.jpg',
                                caption=sequence_name, as_document=False)

    def send_image_message(self, image_data: bytes, filename: str = '', caption: str = '',
                           as_document: bool = True) -> Tuple[str, Dict]:
        f = open(f'replay/images/image_{self.image_count}.jpg', 'wb')
        f.write(image_data)
        f.close()

        stream = io.BytesIO(image_data)
        img = Image.open(stream)
        basewidth = 300
        wpercent = (basewidth / float(img.size[0]))
        hsize = int((float(img.size[1]) * float(wpercent)))

        img.thumbnail((basewidth, hsize))

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()
        base64_encoded_thumbnails = base64.b64encode(img_byte_arr).decode('ascii')
        self.html_file.write(
            f'''<tr><td>{self.event_sequence}</td><td>Send Image</td>
            <td><a href="images/image_{self.image_count}.jpg">
            <img src="data:image/jpeg;base64, {base64_encoded_thumbnails}" />
            </a></td></tr>\n''')
        self.image_count += 1
        self.event_sequence += 1

        return 'OK', {'chat_id': '19052485', 'message_id': '19091585'}
