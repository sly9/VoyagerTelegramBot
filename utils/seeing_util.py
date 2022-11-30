

from io import BytesIO
from random import random

import requests
from PIL import Image


def seeing():
    url = f'https://dsnm.crowson.com/rh/seeing/SeeingGraph.png?{random()}'
    print(url)
    response = requests.get(url)
    stream = BytesIO(response.content)
    image = Image.open(stream).convert("RGBA")
    stream.close()
    pixels = image.load()

    result_x, result_y = None, None
    for x in range(760, 40, -1):
        if not result_x:
            for y in range(45, 320):
                pixel = pixels[x, y]
                if pixel[0] > 200 and pixel[1] > 200 and pixel[2] > 200:
                    result_x = x
                    result_y = y
                    break
    # 320 => 0
    # 40 => 7
    image.close()
    return (320 - result_y) / (320 - 40) * 7
