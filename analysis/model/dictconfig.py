#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import os
from util.fileutil import FileUtil
import codecs
import logging

"""
保存所用字典的信息，停用词词典，情感词典等等。
"""

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')


class DictConfig(object):

    # 停用词词典信息
    __STOP_WORDS = set([" ", "\r", "\n"])  # 停用词集合信息
    __STOP_WORDS_PATH_SET = set([os.path.join(FileUtil.get_dict_dir(), "stopwords-dict.txt")])  # 停用词词典的加载路径，用户可以自定义添加。
    # 替换词词典信息
    __REPLACE_WORDS = {}
    __REPLACE_WORDS_PATH_SET = set([os.path.join(FileUtil.get_dict_dir(), "replace-dict.txt")])

    @classmethod
    def get_stopwords_set(cls):
        return cls.__STOP_WORDS

    @classmethod
    def get_stopwords_dict_path_set(cls):
        return cls.__STOP_WORDS_PATH_SET

    @classmethod
    def get_replace_words_dict(cls):
        return cls.__REPLACE_WORDS

    # 初始化填充停用词列表信息。
    @classmethod
    def __init_stopwords(cls):
        for stopwords_dict_path in cls.__STOP_WORDS_PATH_SET:
            with codecs.open(stopwords_dict_path, "rb", "utf-8") as input_file:
                for line in input_file:
                    stopwords = line.strip()
                    cls.__STOP_WORDS.add(stopwords)
        logging.debug(u"停用词词典构建完成！！！")

    @classmethod
    def __init_replace_words(cls):
        for replace_words_path in cls.__REPLACE_WORDS_PATH_SET:
            with codecs.open(replace_words_path, "rb", "utf-8") as input_file:
                for line in input_file:
                    split_info = line.strip().split("\t")
                    word_pattern = split_info[0]
                    replace_word = split_info[1]
                    if word_pattern not in cls.__REPLACE_WORDS.keys():
                        cls.__REPLACE_WORDS[word_pattern] = replace_word
        logging.debug(u"替换词词典构建完成！！！")

    # 初始化所有的字典信息。
    @classmethod
    def build_dicts(cls):
        # 初始化停用词列表
        cls.__init_stopwords()
        # 初始化替换词词典
        cls.__init_replace_words()


if __name__ == "__main__":
    DictConfig.build_dicts()
    stopwords_set = DictConfig.get_stopwords_set()
    for stopwords in stopwords_set:
        print stopwords
