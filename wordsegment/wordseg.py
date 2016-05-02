#!/usr/bin/env python2.7
# -*- coding:utf-8 -*-

import codecs
import json
import os

import jieba.posseg as pseg

import wordsegment.filterwords as filterwords
from analysis.model.dictconfig import DictConfig
from util.fileutil import FileUtil
from util.loggerutil import Logger

logger = Logger(console_only=True).get_logger()


"""
记录弹幕的分词结果信息，格式为词，以及词的词性。
"""


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
#      is_corpus 是否对语料库中的弹幕信息进行分词，True表示是，False表示对需要分析的弹幕文件进行分词
def segment_barrages(barrages, cid=None, is_corpus=False):
    barrage_seg_list = []
    for barrage in barrages:
        barrage_seg = BarrageSeg(barrage.play_timestamp, barrage.sender_id, barrage.row_id)
        sentence_seg = __segment_sentence(barrage.content)
        barrage_seg.sentence_seg_list = sentence_seg
        barrage_seg_list.append(barrage_seg)
    if is_corpus is False:
        # 将分词结果写入测试文件中，检查分词情况
        __save_segment_word_to_file(barrage_seg_list, cid)
        # 将分词的结果以json的形式写入文件中，以供今后分析zscore的时候调用。
        save_segment_barrages(barrage_seg_list, cid)
        # 建立 tf-idf 相关的词典信息
        DictConfig.gen_tfidf_dict(barrage_seg_list)
    return barrage_seg_list


# 对一个句子进行分词。
# 参数：sentence 需要进行分词的句子。
# 返回：包含该句子分词结果的列表，列表中的对象为WordSeg对象。
def __segment_sentence(sentence):
    sentence_seg = []
    logger.info(u"正在分词：" + sentence)
    words = pseg.cut(sentence)
    # 首先对可能出现的emoji表情进行识别
    # 由于结巴分词会将颜文字表情识别为一个个的单一标点符号，使原来的颜文字表情信息无法表示出来。
    words = filterwords.distinguish_emoji(words)
    for word, flag in words:
        if flag == "eng":
            # 如果切出来的词语是英文，那么需要将其转换成小写，因为替换词典中所有关于英文的模式都是小写的。
            word = word.lower()
        if filterwords.is_stopwords(word):  # 判断该词是否是停用词，不是停用词才给予收录。
            continue
        # 如果词语在替换词词典中，那么返回(True, 替换之后的词)，否则返回(Flase, 原词)
        # 这个必须先于replace_emoji_to_word调用，因为存在QQWWWWWWQQQ这样的颜表情，需要替换为QWQ之后，再替换为对应情感色彩的汉字。
        origin_word = word
        is_word_replace, word, flag = filterwords.format_word(word, flag)
        if is_word_replace:
            logger.debug(u" word " + origin_word + u" 替换成功：" + word)
        # 查看该词是否颜文字表情，进行颜文字表情的替换操作
        origin_word = word
        is_emoji_replace, emoji_list = filterwords.replace_emoji_to_word(word, flag)
        if is_emoji_replace:
            for emoji_info in emoji_list:
                emoji = emoji_info[0]
                emoji_flag = emoji_info[1]
                sentence_seg.append(WordSeg(emoji, emoji_flag))
                logger.debug(u"emoji" + origin_word + u" 替换成功：" + emoji)
            continue
        elif (not is_emoji_replace) and (emoji_list is None):
            continue  # 当前词语是一个违背识别的符号串，直接舍弃。
        # 过滤无意义的数字，标点，（英文字符暂时没有被过滤）信息。
        if filterwords.is_num_or_punctuation(word, flag):
            continue
        sentence_seg.append(WordSeg(word, flag))
    return sentence_seg


# 将分词的结果写入文件中，可以查看分词的效果。主要用于测试。
def __save_segment_word_to_file(barrage_seg_list, cid):
    # barrage_seg_list -> barrage_seg -> sentence_seg_list -> sentence_seg
    word_segment_file = os.path.join(FileUtil.get_word_segment_dir(),
                                     "test-" + cid + "-seg-result.txt")
    with codecs.open(word_segment_file, "wb", "utf-8") as output_file:
        for barrage_seg in barrage_seg_list:
            for word_seg in barrage_seg.sentence_seg_list:
                output_file.write(word_seg.word + u"\t" + word_seg.flag + u"\n")


# 将切词的结果写入文件中，json的形式。
# 参数：cid  弹幕来源的cid名称，用来构建弹幕切词结果的存储路径，格式如：cid-seg-result.json
#      barrage_seg_list 切词结果list
def save_segment_barrages(barrage_seg_list, cid):
    save_file_path = FileUtil.get_word_segment_result_file_path(cid)
    json_str = json.dumps(barrage_seg_list, default=lambda obj: obj.__dict__)
    with codecs.open(save_file_path, "wb", "utf-8") as output_file:
        output_file.write(json_str)


# 将切词结果从文件中读出，文件中的字符串为json的格式
def load_segment_barrages(cid):
    json_data = []
    file_path = FileUtil.get_word_segment_result_file_path(cid)
    with codecs.open(file_path, "rb", "utf-8") as input_file:
        for line in input_file:
            json_data.append(line)
    json_str = u"".join(json_data)
    barrage_seg_list_json = json.loads(json_str)
    barrage_seg_list = BarrageSeg.dict2barrageseglist(barrage_seg_list_json)
    return barrage_seg_list


if __name__ == "__main__":
    DictConfig.build_dicts()
    sentence_list = [u"你终于承认完全不懂了！！！！！！！！！！", u"哈哈哈哈哈哈哈哈哈", u"(´▽｀)ノ♪(´▽｀)ノ♪(´▽｀)ノ♪(´▽｀)ノ♪", u"(╬ﾟдﾟ)▄︻┻┳═一(╬ﾟдﾟ)▄︻",
                     u"(╬ﾟдﾟ)▄︻┻┳═一呀(╬ﾟдﾟ)▄︻",
                     u"哈(╬ﾟдﾟ)▄︻┻┳═一不(╬ﾟдﾟ)▄︻", u"你是不是傻(╬ﾟдﾟ)▄︻┻┳═一(╬ﾟдﾟ)▄︻",
                     u"123"]
    for sentence in sentence_list:
        sentence_seg = __segment_sentence(sentence)
        for word_seg in sentence_seg:
            print word_seg.word, u"\t", word_seg.flag
