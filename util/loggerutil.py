#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import logging
import sys

"""
向终端输出各种提示信息。
"""

__author__ = "htwxujian@gmail.com"

format_dict = {
    1: logging.Formatter('%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s'),
    2: logging.Formatter('%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s'),
    3: logging.Formatter('%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s'),
    4: logging.Formatter('%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
}


class Logger(object):

    FILESYSTEMENCODING = sys.getfilesystemencoding()

    @classmethod
    def print_console_info(cls, unicode_str_msg):
        if unicode_str_msg is None:
            print None
        else:
            print unicode_str_msg
            # print unicode_str_msg.encode(cls.FILESYSTEMENCODING, "ignore")

    # log_name log的文件名称 log_level 指明输出哪一种格式的log信息 logger_name logger的名称
    def __init__(self, log_name, log_level=1, logger_name="default_logger"):
        """
            指定保存日志的文件路径，日志级别，以及调用文件
            将日志存入到指定的文件中
        """

        # 创建一个log
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.DEBUG)
        # 创建一个handler，用于写入日志文件
        file_handler = logging.FileHandler(log_name)
        file_handler.setLevel(logging.DEBUG)
        # 创建一个handler，用于输出到控制台
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        # 定义handler的输出格式
        formatter = format_dict[int(log_level)]
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        # 给logger添加handler
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def get_logger(self):
        return self.logger
