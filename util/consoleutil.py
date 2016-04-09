#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import sys

"""
向终端输出各种提示信息。
"""

__author__ = "htwxujian@gmail.com"


class ConsoleUtil(object):
    FILESYSTEMENCODING = sys.getfilesystemencoding()

    @classmethod
    def print_console_info(cls, unicode_str_msg):
        if unicode_str_msg is None:
            print None
        else:
            # print unicode_str_msg
            print unicode_str_msg.encode(cls.FILESYSTEMENCODING, "ignore")
