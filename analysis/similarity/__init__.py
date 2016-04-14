#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

"""
主要定义一些计算相似度的方法。
"""


# 根据用户的弹幕词频来计算用户之间的jaccard相似度
def calc_jaccard_similarity_by_word_frequency(word_frequency_dict1, word_frequency_dict2):
    word_set = set()
    word_frequency = 0
    common_word_frequency = 0
    for word, frequency in word_frequency_dict1.items():
        word_set.add(word)
        word_frequency += frequency
    for word, frequency in word_frequency_dict2.items():
        if word in word_set:
            common_word_frequency += (frequency + word_frequency_dict1[word])
        word_set.add(word)
        word_frequency += frequency
    return common_word_frequency / (1.0 * word_frequency)
