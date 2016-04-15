#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from analysis.model.dictconfig import DictConfig
import re

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


if __name__ == "__main__":
    DictConfig.build_dicts()
    print format_word("22333333")
