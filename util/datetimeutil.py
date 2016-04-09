#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import time

"""
文件存取的操作，将弹幕数据写入本地文件中。
"""

__author__ = "htwxujian@gmail.com"


class DateTimeUtil(object):
    # 获得当前的时间戳
    @staticmethod
    def get_cur_timestamp(time_format):
        return time.strftime(time_format, time.localtime(time.time()))
