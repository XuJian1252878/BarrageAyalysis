#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

"""
根据情感词词典的方式，分析情感强烈片段的情感信息。
"""

import codecs
import os

import wordsegment.wordseg as wordseg
from analysis.model.dictconfig import DictConfig
from analysis.model.timewindow import TimeWindow
from util.fileutil import FileUtil
from util.loggerutil import Logger
from wordsegment.wordseg import BarrageSeg, WordSeg
from zscore import Zscore

logger = Logger(console_only=True).get_logger()


class Emotion(object):
    __EMOTION_CATEGORY_DICT = {u"乐": 0, u"好": 1, u"怒": 2, u"哀": 3, u"惧": 4, u"恶": 5, u"惊": 6}

    # 参数： cid 电影对应的cid号，对哪一步电影进行情感分析
    def __init__(self, cid):
        self.cid = cid
        # load_high_emotion_clips_from_file
        # 返回：(high_emotion_clips, global_zscore_threshold, left_zscore_threshold, right_zscore_threshould) 的元组
        #       high_emotion_clips [(left_border, right_border, left_border_seconds, right_border_seconds)]
        self.high_emotion_clips, self.global_zscore_threshold, self.left_zscore_threshold, self.right_zscore_threshould = Zscore.load_high_emotion_clips_from_file(
            cid)
        self.barrage_seg_list = wordseg.load_segment_barrages(cid)
        self.emotion_dict = DictConfig.load_emotion_dict()
        self.degree_adverb_dict = DictConfig.load_degree_adverb_dict()
        # emotion_dict_path = os.path.join(FileUtil.get_dict_dir(), "emotion-dict.txt")  # 分类情感词典的路径
        # # 加载分类情感词典
        # self.emotion_dict = {}
        # with codecs.open(emotion_dict_path, "rb", "utf-8") as input_file:
        #     for line in input_file:
        #         split_info = line.strip().split("\t")
        #         if len(split_info) < 2:
        #             continue  # 情感分类词词典， 绝对有两列，第一列是类别，第二列是词语，第三列是词语的说明（可有可无）
        #         category = split_info[0]
        #         word = split_info[1]
        #         if category in self.emotion_dict.keys():
        #             self.emotion_dict[category].add(word)
        #         else:
        #             self.emotion_dict[category] = set([word])
        logger.debug(u"多维情感分类词典加载成功！！！！")

    # 判断当前词语是不是在情感词典中（即是不是情感词）
    # 返回：如果word在情感字典中，那么返回 (True, (category, emotion_word, degree, level))
    #      如果word不在情感字典中，那么返回 (False, None)
    def __is_emotion_words(self, word):
        for category, word_info_set in self.emotion_dict.items():
            for emotion_word, degree, level in word_info_set:
                if emotion_word == word:
                    return True, (category, emotion_word, degree, level)
        return False, None

    # 将一条弹幕的词语列表按情感词来分组。
    # barrage_seg 一条分好词的弹幕，其中的词组是按照其在原文中出现的位置为顺序的（jieba分词的结果）
    # 返回：若弹幕中无任何情感词，那么认为弹幕无情感倾向 (False, None, None)
    #      若弹幕中出现情感词，那么认为弹幕中有情感倾向 (True, 分好的词组列表，词组对应情感词的信息列表)
    def __divide_barrage_into_groups_by_emotion_words(self, barrage_seg):
        word_groups = []  # 弹幕划分好的词组
        emotion_word_info_list = []  # word_groups 中每一个词组对应的情感词信息
        # sentence_seg_list 里的分词信息是按照 原句的位置 排好序的
        temp_word_group = []
        for word_seg in barrage_seg.sentence_seg_list:
            word = word_seg.word
            is_emotion_word, emotion_word_info = self.__is_emotion_words(word)
            if is_emotion_word:
                # 找到了一个情感词
                emotion_word_info_list.append(emotion_word_info)
                temp_word_group.append(word_seg)  # 向当前词组中加入作为分界的情感词
                word_groups.append(temp_word_group)  # 将当前的词语分组记录下来
                temp_word_group = []
            else:
                temp_word_group.append(word_seg)
        # 在处理完一条弹幕信息后，如果 emotion_word_info_list 中无情感词，那么说明当前弹幕无任何情感倾向
        if len(emotion_word_info_list) <= 0:
            return False, None, None
        else:
            return True, word_groups, emotion_word_info_list

    # 寻找出弹幕 子词组 中的所有程度副词
    # 返回：(程度副词的个数, 程度副词的列表) 如果无程度副词，程度副词列表则为空
    def __find_degree_adverb_in_word_group(self, word_group):
        degree_adverb_list = []
        for word_seg in word_group:
            flag = word_seg.flag
            if flag == u"adverb":
                degree_adverb_list.append(word_seg)
        return degree_adverb_list

    # 寻找出弹幕 子词组 中的所有的否定词，分为词组中有程度副词和词组中无程度副词的情况
    # 参数：word_group 一条弹幕信息的某一个词组
    #      degree_adverb 作为否定词分界的 程度副词
    # 返回：当存在程度副词时：(程度副词前否定词个数, 程度副词后否定词个数)
    #      当不存在程度副词时：(否定词总个数, 0)
    def __find_negative_in_word_group(self, word_group, degree_adverb=None):
        negative_before_count = 0
        negative_after_count = 0
        if degree_adverb is None:  # 词组中不存在程度副词
            for word_seg in word_group:
                flag = word_seg.flag
                if flag == u"negative":
                    negative_before_count += 1
        else:
            is_before = True
            degree_adverb_word = degree_adverb.word
            for word_seg in word_group:
                word = word_seg.word
                flag = word_seg.flag
                if word == degree_adverb_word:
                    is_before = False
                if flag == u"negative":
                    if is_before:
                        negative_before_count += 1
                    else:
                        negative_after_count += 1
        return negative_before_count, negative_after_count

    # 计算一条弹幕的情感值信息
    def calc_barrage_emotion_info(self, barrage_seg):
        is_emotion_barrage, word_groups, emotion_word_info_list = \
            self.__divide_barrage_into_groups_by_emotion_words(barrage_seg)
        emotion_value = [0, 0, 0, 0, 0, 0, 0]  # 情感强度表示，因为有七个类别的情感，所以用一行七列的数组表示
        level_value = 0  # 情感极性的表示
        if not is_emotion_barrage:
            return emotion_value, level_value  # 弹幕中没有情感词的情况下，认为这条弹幕的情感属性是中性的
        for index in xrange(0, len(word_groups)):
            word_group = word_groups[index]
            # 获得对应情感词的相关信息
            emotion_category = emotion_word_info_list[index][0]  # 当前分组对应的情感词的类别
            emotion_category_index = Emotion.__EMOTION_CATEGORY_DICT[emotion_category]  # 情感词类别对应的下标
            emotion_degree = float(emotion_word_info_list[index][2])  # 情感词的强度
            emotion_level = float(emotion_word_info_list[index][3])  # 情感词的极性
            # 寻找词组中的副词信息
            degree_adverb_list = self.__find_degree_adverb_in_word_group(word_group)
            if len(degree_adverb_list) > 1:  # 有大于1的程度副词，认为这个词组有语病
                continue
            degree_adverb = None
            degree_adverb_count = len(degree_adverb_list)
            degree_adverb_weight = 1  # 若无程度副词，那么权重默认为1，不受影响
            if len(degree_adverb_list) == 1:  # 句中仅有一个程度副词
                degree_adverb = degree_adverb_list[0]  # 是 word_seg 的对象
                degree_adverb_weight = self.degree_adverb_dict[degree_adverb.word]  # 获取程度副词的权重
            # 获得 word_group 中 否定词 的分布情况
            negative_before_count, negative_after_count = self.__find_negative_in_word_group(word_group, degree_adverb)
            if degree_adverb_count <= 0:  # 句中无程度副词，不管否定词个数
                emotion_value[emotion_category_index] += \
                    (((-1) ** (negative_before_count + negative_after_count)) * emotion_degree)
                level_value += (((-1) ** (negative_before_count + negative_after_count)) * emotion_level)
            elif (negative_before_count + negative_after_count <= 0) and (degree_adverb_count == 1):
                # 句中存在副词，但是无否定词
                emotion_value[emotion_category_index] += (degree_adverb_weight * emotion_degree)
                level_value += (degree_adverb_weight * emotion_level)
            elif (negative_before_count + negative_after_count > 0) and (degree_adverb_count == 1):
                # 否定词跟程度副词都出现的情况
                adjust_weight = 0.5
                # 1 否定词全部位于程度副词之后
                if negative_before_count <= 0:
                    emotion_value[emotion_category_index] += \
                        (((-1) ** negative_after_count) * degree_adverb_weight * emotion_degree)
                    level_value += (((-1) ** negative_after_count) * degree_adverb_weight * emotion_level)
                else:
                    emotion_value[emotion_category_index] += \
                        (((-1) ** (negative_before_count + 1)) * adjust_weight * degree_adverb_weight *
                         ((-1) ** negative_after_count) * emotion_degree)
                    level_value += (((-1) ** (negative_before_count + 1)) * adjust_weight * degree_adverb_weight *
                                    ((-1) ** negative_after_count) * emotion_level)
        return emotion_value, level_value

    # 统计每个 强烈情感片段 的每一维的情感词语有哪些，high_emotion_clips barrage_seg_list 相关。
    def gen_clips_emotion(self):
        # 首先对从文件中载入的弹幕切词信息进行时间窗口的划分
        time_window_list = TimeWindow.gen_time_window_barrage_info(self.barrage_seg_list, self.cid)
        # 没有匹配上的词语列表
        not_match_word_list = []
        # emotion匹配结果列表
        emotion_match_result_list = []
        # 开始对 情感强烈 片段中的词语进行匹配。
        for emotion_clip in self.high_emotion_clips:
            # 前两个域分别是 开始时间窗口下标 结束时间窗口下标
            start_window_index = int(emotion_clip[0].strip())
            end_window_index = int(emotion_clip[1].strip())
            temp_not_match_list = [emotion_clip[0], emotion_clip[1]]
            emotion_clip_match_dict = {}
            barrage_count = 0  # 该段视频内 弹幕的 总数量
            valid_barrage_word_count = 0  # 该段视频内切词的总数量
            for index in xrange(start_window_index, end_window_index + 1):
                if index >= len(time_window_list):
                    continue
                barrage_count += time_window_list[index].barrage_count
                valid_barrage_word_count += time_window_list[index].valid_barrage_word_count
                for barrage_seg in time_window_list[index].barrage_seg_list:
                    # --------------------------------------------------------------------
                    # 每句弹幕的情感强度以及情感极性判断
                    # --------------------------------------------------------------------
                    for word_seg in barrage_seg.sentence_seg_list:
                        # 这里今后  可能要对 emoji 表情 做*2处理，加大emoji表情的权重。
                        word = word_seg.word
                        not_match_emotion = True
                        for emotion_category in self.emotion_dict.keys():
                            if word in self.emotion_dict[emotion_category]:
                                not_match_emotion = False
                                if emotion_category in emotion_clip_match_dict.keys():
                                    emotion_clip_match_dict[emotion_category] += 1
                                else:
                                    emotion_clip_match_dict[emotion_category] = 1
                                break
                        if not_match_emotion:
                            temp_not_match_list.append(word)
                            # --------------------------------------------------------------------
            not_match_word_list.append(temp_not_match_list)
            emotion_match_result_list.append((start_window_index, end_window_index, barrage_count,
                                              valid_barrage_word_count, emotion_clip_match_dict))
        # 将分析结果写入文件中。
        emotion_file_path = os.path.join(FileUtil.get_emotion_dir(), self.cid + "-emotion-match.txt")
        with codecs.open(emotion_file_path, "wb", "utf-8") as output_file:
            for emotion_match in emotion_match_result_list:
                str_info = unicode(str(emotion_match[0])) + u"\t" + unicode(str(emotion_match[1])) + u"\t" + \
                           unicode(str(emotion_match[2])) + u"\t" + unicode(str(emotion_match[3])) + u"\t"
                emotion_clip_match_dict = emotion_match[4]
                for emotion_category, word_count in emotion_clip_match_dict.items():
                    str_info += (emotion_category + u"\t" + unicode(str(word_count)))
                str_info += u"\n"
                output_file.write(str_info)
        # 将未匹配到的词语写入文件中。
        not_match_word_file_path = os.path.join(FileUtil.get_emotion_dir(), "not-match-word.txt")
        with codecs.open(not_match_word_file_path, "wb", "utf-8") as output_file:
            for not_match_word in not_match_word_list:
                output_file.write(u"\t".join(not_match_word) + u"\n")


if __name__ == "__main__":
    emotion = Emotion("2065063")
    # emotion.gen_clips_emotion()
    word_seg1 = WordSeg(u"我", "xx", 0, 0)
    word_seg2 = WordSeg(u"不", "negative", 0, 0)
    word_seg3 = WordSeg(u"开心", "emotion", 0, 0)  # 5 index 0
    word_seg4 = WordSeg(u"不是", "negative", 0, 0)
    word_seg5 = WordSeg(u"很", "adverb", 0, 0)  # 2
    word_seg6 = WordSeg(u"十分", "adverb", 0, 0)  # 3
    word_seg7 = WordSeg(u"伤心", "emotion", 0, 0)  # 5  index 3
    # barrage_seg1 = BarrageSeg("0", "0", "0")
    # barrage_seg1.sentence_seg_list.append(word_seg1)
    # barrage_seg1.sentence_seg_list.append(word_seg2)
    # barrage_seg1.sentence_seg_list.append(word_seg3)
    # barrage_seg1.sentence_seg_list.append(word_seg1)
    # barrage_seg1.sentence_seg_list.append(word_seg6)
    # barrage_seg1.sentence_seg_list.append(word_seg7)

    barrage_seg2 = BarrageSeg("0", "0", "0")
    barrage_seg2.sentence_seg_list.append(word_seg1)
    barrage_seg2.sentence_seg_list.append(word_seg4)
    barrage_seg2.sentence_seg_list.append(word_seg2)
    barrage_seg2.sentence_seg_list.append(word_seg5)
    barrage_seg2.sentence_seg_list.append(word_seg2)
    barrage_seg2.sentence_seg_list.append(word_seg3)
    print emotion.calc_barrage_emotion_info(barrage_seg2)
