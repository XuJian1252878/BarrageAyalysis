#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import codecs
import logging
import os

import jieba
from gensim import corpora, models

from util.fileutil import FileUtil

"""
保存所用字典的信息，停用词词典，情感词典等等。
"""

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')


class DictConfig(object):

    # 停用词词典信息
    __STOP_WORDS = set([" ", "\r", "\n", "\t"])  # 停用词集合信息
    # 停用词词典的加载路径，用户可以自定义添加。
    __STOP_WORDS_PATH_SET = set([os.path.join(FileUtil.get_dict_dir(), "stopwords-zh-dict.txt"),
                                 os.path.join(FileUtil.get_dict_dir(), "stopwords-en-dict.txt")])
    # 替换词词典信息
    # 替换词词典的替换词次序十分重要，所以用了list。例如 !{1,3}这个替换规则就应该在!!!!+这个替换规则后面。
    __REPLACE_WORDS = []
    __REPLACE_WORDS_PATH_SET = set([os.path.join(FileUtil.get_dict_dir(), "replace-dict.txt")])
    # 替换颜表情词典信息
    __REPLACE_EMOJI = {}
    __REPLACE_EMOJI_PATH_SET = set([os.path.join(FileUtil.get_dict_dir(), "emoji-dict.txt")])
    # 接受词性词典
    __ACCEPT_NOMINAL = set([])
    __ACCEPT_NOMINAL_PATH_SET = set([os.path.join(FileUtil.get_dict_dir(), "accept-nominal-dict.txt")])
    # 拒绝接受的单个标点符号词典
    __REJECT_PUNCTUATION = set([])
    __REJECT_PUNCTUATION_PATH_SET = set([os.path.join(FileUtil.get_dict_dir(), "reject-punctuation-dict.txt")])

    @classmethod
    def get_stopwords_set(cls):
        return cls.__STOP_WORDS

    @classmethod
    def get_stopwords_dict_path_set(cls):
        return cls.__STOP_WORDS_PATH_SET

    @classmethod
    def get_replace_words_list(cls):
        return cls.__REPLACE_WORDS

    @classmethod
    def get_accept_nominal_set(cls):
        return cls.__ACCEPT_NOMINAL

    @classmethod
    def get_emoji_replace_dict(cls):
        return cls.__REPLACE_EMOJI

    @classmethod
    def get_reject_punctuation_dict(cls):
        return cls.__REJECT_PUNCTUATION

    # 初始化填充停用词列表信息。
    @classmethod
    def __init_stopwords(cls):
        cls.__STOP_WORDS = set([" ", "\r", "\n", "\t"])
        for stopwords_dict_path in cls.__STOP_WORDS_PATH_SET:
            with codecs.open(stopwords_dict_path, "rb", "utf-8") as input_file:
                for line in input_file:
                    stopwords = line.strip()
                    cls.__STOP_WORDS.add(stopwords)
        logging.debug(u"停用词词典构建完成！！！")

    @classmethod
    def __init_replace_words(cls):
        cls.__REPLACE_WORDS = []
        for replace_words_path in cls.__REPLACE_WORDS_PATH_SET:
            with codecs.open(replace_words_path, "rb", "utf-8") as input_file:
                for line in input_file:
                    split_info = line.strip().split("\t")
                    word_pattern = split_info[0]
                    replace_word = split_info[1]
                    replace_flag = split_info[2]  # 替换词的词性，因为今后将会用到 过滤数字 和 无用标点的选项
                    cls.__REPLACE_WORDS.append((word_pattern, replace_word, replace_flag))
        logging.debug(u"替换词词典构建完成！！！")

    @classmethod
    def __init_accept_nominal(cls):
        cls.__ACCEPT_NOMINAL = set([])
        for accept_nominal_path in cls.__ACCEPT_NOMINAL_PATH_SET:
            with codecs.open(accept_nominal_path, "rb", "utf-8") as input_file:
                for line in input_file:
                    split_info = line.strip().split("\t")
                    accept_nominal = split_info[0]
                    cls.__ACCEPT_NOMINAL.add(accept_nominal)
        logging.debug(u"接受词性词典加载成功！！！")

    @classmethod
    def __init_emoji_replace_dict(cls):
        cls.__REPLACE_EMOJI = {}
        for emoji_dict_path in cls.__REPLACE_EMOJI_PATH_SET:
            with codecs.open(emoji_dict_path, "rb", "utf-8") as input_file:
                for line in input_file:
                    split_info = line.strip().split("\t")
                    if len(split_info) < 2:
                        # 一般情况下emoji表情都包含两列，一列为表情，另一列为替换词，这两列必须有；第三列为表情说明，可有可无。
                        continue
                    # emoji替换词典里的表情是可能重复的，因为表情太复杂来不及检查，这里将会出现以最后一个定义为准。
                    emoji = split_info[0]
                    replace_word = split_info[1]
                    cls.__REPLACE_EMOJI[emoji] = replace_word
        logging.debug(u"emoji 替换词典加载完成！！！")

    # 加载拒绝的单个标点词的词典
    @classmethod
    def __init_reject_punctuation_set(cls):
        cls.__REJECT_PUNCTUATION = set([])
        for reject_punctuation_path in cls.__REJECT_PUNCTUATION_PATH_SET:
            with codecs.open(reject_punctuation_path, "rb", "utf-8") as input_file:
                for line in input_file:
                    punctuation = line.strip()
                    cls.__REJECT_PUNCTUATION.add(punctuation)
        logging.debug(u"弃用标点符号词典加载完成！！！")

    # 根据分好词的barrage_seg_list（分好词、过滤好停词）
    @classmethod
    def gen_tfidf_dict(cls, barrage_seg_list):
        # 获得每条弹幕分好之后的词语
        texts = []
        for barrage_seg in barrage_seg_list:
            text = []
            for word_seg in barrage_seg.sentence_seg_list:
                text.append(word_seg.word)
            texts.append(text)
        # 为文本中的每一个词语赋予一个数字下标
        dictionary = corpora.Dictionary(texts)
        # store the dictionary, for future reference
        dictionary.save(os.path.join(FileUtil.get_tfidf_dir(), "barrage-words.dict"))
        print str(type(logging))
        logging.debug("生成 tfidf 弹幕词语词典！！！")
        logging.debug(dictionary.token2id)
        # 根据生成的字典，生成语料库信息（语料的词用id表示，后面对应的是count。）
        corpus = [dictionary.doc2bow(text) for text in texts]
        # store to disk, for later use
        corpora.MmCorpus.serialize(os.path.join(FileUtil.get_tfidf_dir(), 'barrage-corpus.mm'), corpus)
        # let’s initialize a tfidf transformation:
        tfidf = models.TfidfModel(corpus)
        tfidf.save(os.path.join(FileUtil.get_tfidf_dir(), "barrage-tfidf.model"))

    # 初始化所有的字典信息。
    @classmethod
    def build_dicts(cls):
        # 载入自定义的弹幕词典，优化弹幕特有词语的切词，以及颜表情的切词
        jieba.load_userdict(os.path.join(FileUtil.get_dict_dir(), "barrage-word-dict.txt"))
        logging.debug(u"自定义弹幕词典加载成功！！！")
        # 初始化停用词列表
        cls.__init_stopwords()
        # 初始化替换词词典
        cls.__init_replace_words()
        # 初始化接受词性的词典
        cls.__init_accept_nominal()
        # 初始化emoji替换词典
        cls.__init_emoji_replace_dict()
        # 初始化弃用标点符号词典
        cls.__init_reject_punctuation_set()


if __name__ == "__main__":
    DictConfig.build_dicts()
    stopwords_set = DictConfig.get_stopwords_set()
    for stopwords in stopwords_set:
        print stopwords
