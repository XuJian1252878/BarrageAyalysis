#!/usr/bin/env python2.7
# -*- coding:utf-8 -*-

import codecs
import json

import jieba.posseg as pseg
import wordsegment.filterwords as filterwords

from util.consoleutil import ConsoleUtil
import logging


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')


"""
记录弹幕的分词结果信息，格式为词，以及词的词性。
"""


# class __WordSeg(object):
#     def __init__(self, word, flag):
#         self.word = word
#         self.flag = flag
#
#     @staticmethod
#     def dict2wordseg(word_seg_dict):
#         word = word_seg_dict["word"]
#         flag = word_seg_dict["flag"]
#         word_seg = __WordSeg(word, flag)  # 为什么私有类的静态方法调用私有类的构造函数会报错。
#         return word_seg


# 记录一个词的词性以及词本身。
class WordSeg(object):
    def __init__(self, word, flag):
        self.word = word
        self.flag = flag

    @staticmethod
    def dict2wordseg(word_seg_dict):
        word = word_seg_dict["word"]
        flag = word_seg_dict["flag"]
        word_seg = WordSeg(word, flag)
        return word_seg


# 记录一个弹幕的切词结果。
class BarrageSeg(object):
    def __init__(self, play_timestamp, sender_id, row_id):
        self.play_timestamp = float(play_timestamp)
        self.row_id = row_id
        self.sender_id = sender_id
        self.sentence_seg_list = []  # 弹幕切词结果列表，列表中的对象为__WordSeg。

    @staticmethod
    def dict2barrageseg(barrage_seg_dict):
        play_timestamp = float(barrage_seg_dict["play_timestamp"])
        row_id = barrage_seg_dict["row_id"]
        sender_id = barrage_seg_dict["sender_id"]
        barrage_seg = BarrageSeg(play_timestamp, row_id, sender_id)
        sentence_seg_list = barrage_seg_dict["sentence_seg_list"]
        for word_seg_dict in sentence_seg_list:
            word_seg = WordSeg.dict2wordseg(word_seg_dict)
            barrage_seg.sentence_seg_list.append(word_seg)
        return barrage_seg

    @staticmethod
    def dict2barrageseglist(barrage_seg_list_dict):
        barrage_seg_list = []
        for barrage_seg_dict in barrage_seg_list_dict:
            barrage_seg = BarrageSeg.dict2barrageseg(barrage_seg_dict)
            barrage_seg_list.append(barrage_seg)
        return barrage_seg_list


# 对弹幕的内容进行分词。
# 参数：barrages 读取的弹幕列表，以播放时间的升序排序。
# 返回：WordSeg 列表（包含弹幕的row_id, play_timestamp, sender_id）
def segment_barrages(barrages):
    barrage_seg_list = []
    for barrage in barrages:
        barrage_seg = BarrageSeg(barrage.play_timestamp, barrage.sender_id, barrage.row_id)
        sentence_seg = __segment_sentence(barrage.content)
        barrage_seg.sentence_seg_list = sentence_seg
        barrage_seg_list.append(barrage_seg)
    return barrage_seg_list


# 对一个句子进行分词。
# 参数：sentence 需要进行分词的句子。
# 返回：包含该句子分词结果的列表，列表中的对象为WordSeg对象。
def __segment_sentence(sentence):
    sentence_seg = []
    logging.info(u"正在分词：" + sentence)
    words = pseg.cut(sentence)
    for word, flag in words:
        if filterwords.is_stopwords(word):  # 判断该词是否是停用词，不是停用词才给予收录。
            continue
        # 如果词语在替换词词典中，那么返回(True, 替换之后的词)，否则返回(Flase, 原词)
        flag, replace_word = filterwords.format_word(word)
        sentence_seg.append(WordSeg(replace_word, flag))
    return sentence_seg


# 将切词的结果写入文件中，json的形式。
# 参数：save_file_path 切词结果写入的文件位置。
#      barrage_seg_list 切词结果list
def save_segment_barrages(save_file_path, barrage_seg_list):
    json_str = json.dumps(barrage_seg_list, default=lambda obj: obj.__dict__)
    with codecs.open(save_file_path, "wb", "utf-8") as output_file:
        output_file.write(json_str)


# 将切词结果从文件中读出，文件中的字符串为json的格式
def load_segment_barrages(file_path):
    json_data = []
    with codecs.open(file_path, "rb", "utf-8") as input_file:
        for line in input_file:
            json_data.append(line)
    json_str = u"".join(json_data)
    barrage_seg_list_json = json.loads(json_str)
    barrage_seg_list = BarrageSeg.dict2barrageseglist(barrage_seg_list_json)
    return barrage_seg_list
