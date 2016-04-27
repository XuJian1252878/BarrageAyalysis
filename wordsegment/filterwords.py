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


# 对弹幕中的颜表情进行替换，如果颜表情在替换词词典中，那么返回(True, 替换之后的词, 替换后的词性)，否则返回(Flase, 原词, 原词词性)
# replace_emoji_to_word函数中会将匹配上的 单个 emoji 表情的词语属性 替换成emoji。
def replace_emoji_to_word(word, flag):
    emoji_replace_dict = DictConfig.get_emoji_replace_dict()
    emoji_set = emoji_replace_dict.keys()
    for emoji in emoji_set:
        if word == emoji:
            if len(word) == 1:
                return True, emoji_replace_dict[emoji], "emoji"
            return True, emoji_replace_dict[emoji], flag
    return False, word, flag


# 判断一个词的词性是否为接受的词性，若是，那么返回true；否则返回false。
def is_accept_nominal(nominal):
    accept_nominal_set = DictConfig.get_accept_nominal_set()
    for accept_nominal in accept_nominal_set:
        # 因为词性都是大类之内再分为小类，如w、n等等；结巴分词的结果可能直接把小类分了出来，如wp、wn等等
        # 所以词性判断需要使用startwith来判断。
        if accept_nominal.startswith(nominal):
            return True
    return False


# 由于结巴分词会将颜文字表情识别为一个个的单一标点符号，使原来的颜文字表情信息无法表示出来。
# 这里做一个整合，当发现一个 连续的标点符号串 ， 并且长度大于等于2的时候，那么我们认为这个标点符号串是一个emoji颜文字表情。
# 这时我们将这一串的 连续标点符号串 作为一个词语，属性为emoji。
# 但是 ❤ 这种颜文字只有一个字符，这样的话在这里我们就不能将它标注为emoji。因为上面的限制一旦放宽到大于等于1，
# 那么，。这种无意义的单个标点也会被识别为emoji，这不可取。（这里待改进）。但是影响不大，因为在replace_emoji_to_word函数中，根据词典
# 都能替换成情感词，另外replace_emoji_to_word函数中会将匹配上的 单个 emoji 表情的词语属性 替换成emoji。
# 输入参数：words为一个句子的结巴分词结果。
def distinguish_emoji(words):
    # 找到连续的标点符号（长度大于等于2），作为emoji表情
    punctuation_index_list = []
    punctuation_list = []
    emoji_replace_list = []
    result_words = []  # 用于返回的结果列表
    words_index = -1
    for word, flag in words:
        words_index += 1
        result_words.append((word, flag))  # 存储分词结果列表，作为返回结果
        if flag == "x":  # 如果当前词性是标点符号
            if len(punctuation_index_list) <= 0:
                punctuation_list.append(word)
            elif words_index - punctuation_index_list[-1] == 1:
                # 表明是连续的标点符号
                punctuation_list.append(word)
            punctuation_index_list.append(words_index)
        else:
            # 当前词性不是标点符号的时候
            if len(punctuation_list) > 0:
                if len(punctuation_list) >= 2:
                    # 说明此时已经识别出了一个emoji表情
                    emoji_pic = u"".join(punctuation_list)
                    emoji_replace_list.append((punctuation_index_list[0], punctuation_index_list[-1], emoji_pic))
                # 清空原来的记录信息（punctuation_list 可能是emoji表情或者是单个标点符号）
                punctuation_index_list = []
                punctuation_list = []
    # emoji刚好在最末尾的时候
    if len(punctuation_list) >= 2:
        # 说明此时已经识别出了一个emoji表情
        emoji_pic = u"".join(punctuation_list)
        emoji_replace_list.append((punctuation_index_list[0], punctuation_index_list[-1], emoji_pic))
    # 开始替换emoji表情
    for index in xrange(len(emoji_replace_list) - 1, -1, -1):
        replace_start_index = emoji_replace_list[index][0]
        replace_end_index = emoji_replace_list[index][1]
        emoji_pic = emoji_replace_list[index][2]
        result_words = result_words[0: replace_start_index] + \
                       [(emoji_pic, "emoji")] + result_words[replace_end_index + 1: len(result_words)]
    return result_words


if __name__ == "__main__":
    DictConfig.build_dicts()
    print format_word("22333333")
