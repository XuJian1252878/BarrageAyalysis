#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import os
from util.fileutil import FileUtil
import codecs

"""
保存所用字典的信息，停用词词典，情感词典等等。
"""


class DictConfig(object):

    __STOP_WORDS = set([])  # 停用词集合信息
    __STOP_WORDS_DICT_PATH = set([os.path.join(FileUtil.get_dict_dir(), "stopwords-dict.txt")])  # 停用词词典的加载路径，用户可以自定义添加。

    @classmethod
    def get_stopwords_set(cls):
        return cls.__STOP_WORDS

    @classmethod
    def get_stopwords_dict_path_set(cls):
        return cls.__STOP_WORDS_DICT_PATH

    # 初始化填充停用词列表信息。
    @classmethod
    def __init_stopwords(cls):
        for stopwords_dict_path in cls.__STOP_WORDS_DICT_PATH:
            with codecs.open(stopwords_dict_path, "rb", "utf-8") as input_file:
                for line in input_file:
                    stopwords = line.strip()
                    cls.__STOP_WORDS.add(stopwords)

    # 初始化所有的字典信息。
    @classmethod
    def build_dicts(cls):
        # 初始化停用词列表
        cls.__init_stopwords()


if __name__ == "__main__":
    DictConfig.build_dicts()
    stopwords_set = DictConfig.get_stopwords_set()
    for stopwords in stopwords_set:
        print stopwords
