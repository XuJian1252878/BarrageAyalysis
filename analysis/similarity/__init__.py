#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import numpy as np
import logging

"""
主要定义一些计算相似度的方法。
"""

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')


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


# 根据余弦定理计算文本的相似度信息。
# 输入参数：word_info_dict 可能为：{key=word, value=frequency} 或者是 {key=token, value=weight} （tfidf处理之后的）
# http://www.ruanyifeng.com/blog/2013/03/cosine_similarity.html
def calc_cosine_similarity(word_info_dict1, word_info_dict2):
    logging.debug(word_info_dict1)
    logging.debug(word_info_dict2)
    # 1. 列出所有的词
    word_set = set()
    for word, frequency in word_info_dict1.items():
        word_set.add(word)
    for word, frequency in word_info_dict2.items():
        word_set.add(word)
    # 2. 计算词频，得到两个向量词频
    frequency_vector1 = []
    frequency_vector2 = []
    for word in word_set:
        frequency1 = 0
        frequency2 = 0
        if word in word_info_dict1.keys():
            frequency1 = word_info_dict1[word]
        if word in word_info_dict2.keys():
            frequency2 = word_info_dict2[word]
        frequency_vector1.append(frequency1)
        frequency_vector2.append(frequency2)
    # 3. 计算cos相似度
    frequency_matrix1 = np.mat(frequency_vector1)
    frequency_matrix2 = np.mat(frequency_vector2)
    cosine_similarity = np.dot(frequency_matrix1,
                               frequency_matrix2.T)/np.linalg.norm(frequency_matrix1)/np.linalg.norm(frequency_matrix2)
    cosine_similarity = cosine_similarity.item(0)
    return cosine_similarity


if __name__ == "__main__":
    word_frequency_dict1 = {"token1": 1, "token2": 2, "token3": 3}
    word_frequency_dict2 = {"token1": 4, "token2": 5, "token3": 6}
    print calc_cosine_similarity(word_frequency_dict1, word_frequency_dict2)
