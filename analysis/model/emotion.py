#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

"""
根据情感词词典的方式，分析情感强烈片段的情感信息。
"""

import codecs
import os

import wordsegment.wordseg as wordseg
from analysis.model.timewindow import TimeWindow
from util.fileutil import FileUtil
from util.loggerutil import Logger
from zscore import Zscore

logger = Logger(console_only=True).get_logger()


class Emotion(object):
    # 参数： cid 电影对应的cid号，对哪一步电影进行情感分析
    def __init__(self, cid):
        self.cid = cid
        self.high_emotion_clips, self.global_zscore_threshold, \
        self.left_zscore_threshold, self.right_zscore_threshould = Zscore.load_high_emotion_clips_from_file(cid)
        self.barrage_seg_list = wordseg.load_segment_barrages(cid)
        emotion_dict_path = os.path.join(FileUtil.get_dict_dir(), "emotion-dict.txt")  # 分类情感词典的路径
        # 加载分类情感词典
        self.emotion_dict = {}
        with codecs.open(emotion_dict_path, "rb", "utf-8") as input_file:
            for line in input_file:
                split_info = line.strip().split("\t")
                if len(split_info) < 2:
                    continue  # 情感分类词词典， 绝对有两列，第一列是类别，第二列是词语，第三列是词语的说明（可有可无）
                category = split_info[0]
                word = split_info[1]
                if category in self.emotion_dict.keys():
                    self.emotion_dict[category].add(word)
                else:
                    self.emotion_dict[category] = set([word])
        logger.debug(u"多维情感分类词典加载成功！！！！")

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
    emotion.gen_clips_emotion()
