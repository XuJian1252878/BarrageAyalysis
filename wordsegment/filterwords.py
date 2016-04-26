#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import re

from analysis.model.dictconfig import DictConfig

"""
对于一个句子来说，分词之后会有很多个词语，需要在这些词语中将不需要的词语过滤出去，
这个模块里的函数主要提供这样的过滤功能。
"""


# 判断一个词语是否是停用词，是则返回true，不是则返回false。
def is_stopwords(word):
    stopwords_set = DictConfig.get_stopwords_set()
    if word in stopwords_set:
        return True
    else:
        return False


# 如果词语在替换词词典中，那么返回(True, 替换之后的词)，否则返回(Flase, 原词)
def format_word(word):
    replace_word_dict = DictConfig.get_replace_words_dict()
    replace_pattern_set = replace_word_dict.keys()
    for replace_pattern in replace_pattern_set:
        pattern = re.compile(replace_pattern)
        if re.match(pattern, word) is not None:
            return True, replace_word_dict[replace_pattern]
    return False, word


# 对弹幕中的颜表情进行替换，如果颜表情在替换词词典中，那么返回(True, 替换之后的词)，否则返回(Flase, 原词)
def replace_emoji_to_word(word):
    emoji_replace_dict = DictConfig.get_emoji_replace_dict()
    emoji_set = emoji_replace_dict.keys()
    for emoji in emoji_set:
        if word == emoji:
            return True, emoji_replace_dict[emoji]
    return False, word


# 判断一个词的词性是否为接受的词性，若是，那么返回true；否则返回false。
def is_accept_nominal(nominal):
    accept_nominal_set = DictConfig.get_accept_nominal_set()
    for accept_nominal in accept_nominal_set:
        # 因为词性都是大类之内再分为小类，如w、n等等；结巴分词的结果可能直接把小类分了出来，如wp、wn等等
        # 所以词性判断需要使用startwith来判断。
        if accept_nominal.startswith(nominal):
            return True
    return False


if __name__ == "__main__":
    DictConfig.build_dicts()
    print format_word("22333333")
