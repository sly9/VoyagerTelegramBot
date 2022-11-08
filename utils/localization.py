#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gettext
import os
from typing import Callable
import sys

os.environ['PYTHONIOENCODING'] = 'utf-8'
get_translated_text_impl: Callable[[str], str] = gettext.gettext


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
        print('base path: ' + base_path)
    except Exception:
        base_path = os.path.abspath(".")
        print('base path fallback: ' + base_path)
    print(os.path.join(base_path, relative_path))
    return os.path.join(base_path, relative_path)


def get_translated_text(message: str) -> str:
    return get_translated_text_impl(message)


# en = gettext.translation('base', localedir='locales', languages=['en'])
cn = gettext.translation('base', localedir=resource_path('locales'), languages=['cn'], codeset='utf8')


def echo(msg: str) -> str:
    return msg


def select_locale(locale: str = 'en'):
    '''
    Select current locale.. only english and chinese are supported at the moment
    :param locale:
    :return:
    '''
    global get_translated_text_impl
    if locale == 'cn' or locale == 'zh-CN':
        cn.install()
        get_translated_text_impl = cn.gettext
    else:
        # en.install()
        get_translated_text_impl = echo
