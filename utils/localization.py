#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gettext
import os
from typing import Callable

os.environ['PYTHONIOENCODING'] = 'utf-8'
get_translated_text_impl: Callable[[str], str] = gettext.gettext


def get_translated_text(message: str) -> str:
    return get_translated_text_impl(message)


# en = gettext.translation('base', localedir='locales', languages=['en'])
cn = gettext.translation('base', localedir='locales', languages=['cn'], codeset='utf8')


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
