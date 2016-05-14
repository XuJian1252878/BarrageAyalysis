#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import codecs
import logging
import os

from gensim import corpora, models

import util.loader.dataloader as dataloader
import wordsegment.wordseg as wordseg
from util.datetimeutil import DateTimeUtil
from util.fileutil import FileUtil

"""
记录每个时间窗口内的弹幕分词结果，以及时间窗口划分的配置信息。
"""


class TimeWindow(object):

    __TIME_WINDOW_SIZE = 30  # 时间窗口的大小，以秒为单位
    __SLIDE_TIME_INTERVAL = 10  # 以10s为时间间隔滑动，创建时间窗口，以秒为单位
    __ANALYSIS_UNIT_CAPACITY = 4  # 以多少个时间窗口为单位进行分析zscore的值。

    def __init__(self, cid, time_window_index, start_timestamp, end_timestamp):
        self.cid = cid
        self.time_window_index = time_window_index
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp
        self.barrage_count = 0  # 该时间窗口内弹幕的数量
        self.valid_barrage_word_count = 0  # 该时间窗口内弹幕词语的数量
        self.barrage_seg_list = []  # 该时间窗口内对应的弹幕分词列表，或是原始的弹幕列表。
        self.user_word_frequency_dict = {}  # dict {key=user_id, value = {key=word, value="frequency"}}
        self.user_token_tfidf_dict = {}  # dict {key=user_id, value={key=token, value="tfidf weight"}}
        self.user_topic_lda_dict = {}  # dict {key=user_id, value={key=topic, value="topic percent"}}

    @classmethod
    def get_time_window_size(cls):
        return cls.__TIME_WINDOW_SIZE

    @classmethod
    def get_slide_time_interval(cls):
        return cls.__SLIDE_TIME_INTERVAL

    @classmethod
    def get_analysis_unit_capacity(cls):
        return cls.__ANALYSIS_UNIT_CAPACITY

    # 将时间窗口的下标、开始结束时间戳、弹幕数量、有用词数量保存入文件中，便于今后的zscore分析
    @classmethod
    def __save_time_window_info_to_file(cls, cid, time_window_list):
        file_path = os.path.join(FileUtil.get_zscore_dir(), str(cid) + "-time-window-info.txt")
        with codecs.open(file_path, "wb", "utf-8") as output_file:
            for time_window in time_window_list:
                time_window_info = unicode(str(time_window.time_window_index)) + u"\t" \
                                   + DateTimeUtil.format_barrage_play_timestamp(time_window.start_timestamp) + u"\t" \
                                   + DateTimeUtil.format_barrage_play_timestamp(time_window.end_timestamp) + u"\t" \
                                   + unicode(str(time_window.barrage_count)) + u"\t" \
                                   + unicode(str(time_window.valid_barrage_word_count)) + u"\n"
                output_file.write(time_window_info)

    # 对于时间窗口本身，在其barrage_or_seg_list 被填充的情况下，统计词频。
    # 返回：dict {key=user_id, value = {key=word, value="frequency"}} 格式的字典
    def gen_user_word_frequency(self):
        user_word_frequency = {}
        for barrage_seg in self.barrage_seg_list:
            user_id = barrage_seg.sender_id
            word_frequency_dict = {}  # key为词语，value为词频的字典。
            if user_id in user_word_frequency.keys():
                word_frequency_dict = user_word_frequency[user_id]
            else:
                user_word_frequency[user_id] = word_frequency_dict
            for word_seg in barrage_seg.sentence_seg_list:
                word = word_seg.word
                word_count = 0
                if word in word_frequency_dict.keys():
                    word_count = word_frequency_dict[word]
                else:
                    word_frequency_dict[word] = word_count
                word_frequency_dict[word] = word_count + 1  # 统计词频
            user_word_frequency[user_id] = word_frequency_dict
        self.user_word_frequency_dict = user_word_frequency
        return user_word_frequency

    # 对于时间窗口本身，在其barrage_or_seg_list 被填充的情况下，统计该词频下的tfidf信息。
    # 前提：需要在 user_word_frequency_dict 变量被填充之后调用。
    # 参数：dictionary 语料库词典信息 id 与 词语相互对应
    #      tfidf_model 由语料库语料训练的tf-idf模型
    # 返回：dict {key=user_id, value={key=token, value="tfidf weight"}}
    def gen_user_token_tfidf(self, dictionary, tfidf_model):
        for user_id, word_frequency in self.user_word_frequency_dict.items():
            token_frequency_list = []
            for word, frequency in word_frequency.items():
                token = dictionary.token2id[word]
                token_frequency_list.append((token, frequency))
            # 由(token, frequency) 根据训练出的模型转化为 (toekn, tf-idf value)
            tfidf_weight_list = tfidf_model[token_frequency_list]
            tfidf_weight_dict = {}
            for item in tfidf_weight_list:
                tfidf_weight_dict[str(item[0])] = float(item[1])
            self.user_token_tfidf_dict[user_id] = tfidf_weight_dict

    # 对于时间窗口本身，在其barrage_seg_list 被填充的情况下，获得其主题分布信息。
    # 前提：需要在 user_word_frequency_dict 变量被填充之后调用。
    # 参数：dictionary 语料库词典信息 id 与 词语相互对应
    #      tfidf_model 由语料库语料训练的tf-idf模型
    # 返回：dict {key=user_id, value={key=topic, value="topic-percent"}}
    def gen_user_topic_lda(self, dictionary, lda_model):
        for user_id, word_frequency in self.user_word_frequency_dict.items():
            token_frequency_list = []
            for word, frequency in word_frequency.items():
                token = dictionary.token2id[word]
                token_frequency_list.append((token, frequency))
            # 由用户的词频信息训练lda模型，获得这句话在每个主题下的分布
            # [(0, 0.033333333995221079), (1, 0.033333334144388306), (2, 0.033333334802166097),
            #  (3, 0.033333334805368119), (4, 0.033333333648844644), (5, 0.033333334814035144),
            #  (6, 0.69999999225328124), (7, 0.033333333995047759), (8, 0.033333333893201054),
            #  (9, 0.033333333648446671)]
            lda_topic_list = lda_model[token_frequency_list]
            lda_topic_dict = {}
            for item in lda_topic_list:
                lda_topic_dict[str(item[0])] = float(item[1])
            self.user_topic_lda_dict[user_id] = lda_topic_dict

    # 获得该时间窗口内 所有弹幕信息 发送用户的id。
    def gen_all_barrage_sender_id(self):
        sender_id_list = []
        for barrage_seg in self.barrage_seg_list:
            if barrage_seg.sender_id not in sender_id_list:
                sender_id_list.append(barrage_seg.sender_id)
        return sender_id_list

    # 将弹幕的信息按照时间窗口分类
    # 参数：barrage_seg_list 一个已经排好序的，已经切好词的barrage_seg_list列表，或者是原始的未切词的弹幕列表（已排好序）。
    # 返回一个 TimeWindow 列表。
    @classmethod
    def gen_time_window_barrage_info(cls, barrage_or_seg_list, cid):
        time_window_index = 0
        start_timestamp = 0
        end_timestamp = start_timestamp + cls.__TIME_WINDOW_SIZE
        time_window_list = []
        while start_timestamp <= barrage_or_seg_list[-1].play_timestamp:
            temp_seg_list = []
            valid_barrage_word_count = 0
            for barrage_seg in barrage_or_seg_list:
                if (start_timestamp <= barrage_seg.play_timestamp) and (end_timestamp > barrage_seg.play_timestamp):
                    temp_seg_list.append(barrage_seg)
                    valid_barrage_word_count += len(barrage_seg.sentence_seg_list)
                elif end_timestamp <= barrage_seg.play_timestamp:
                    break
            logging.info(u"建立第 " + str(time_window_index) + u" 个时间窗口！！")
            # 产生一个新的timewindow对象
            time_window = TimeWindow(cid, time_window_index, start_timestamp, end_timestamp)
            time_window.barrage_seg_list = temp_seg_list
            time_window.barrage_count = len(temp_seg_list)  # 记录该时间窗口下的弹幕数量
            time_window.valid_barrage_word_count = valid_barrage_word_count  # 记录该时间窗口下有效的弹幕词语的数量
            time_window_list.append(time_window)

            start_timestamp += cls.__SLIDE_TIME_INTERVAL
            end_timestamp = start_timestamp + cls.__TIME_WINDOW_SIZE
            time_window_index += 1
        # 将时间窗口的相关数据信息写入zscore文件中
        cls.__save_time_window_info_to_file(cid, time_window_list)
        return time_window_list

    # 获得每一个时间窗口内，以用户为维度，统计用户所发弹幕词语的词频。
    # 参数：已经按照play_timestamp升序排序好的弹幕（已做好中文分词）列表。
    # 返回：time_window列表，每个TimeWindow对象中的 user_word_frequency 用户词频信息已被填充。
    @classmethod
    def gen_user_word_frequency_by_time_window(cls, barrage_seg_list, cid):
        time_window_list = TimeWindow.gen_time_window_barrage_info(barrage_seg_list, cid)
        for time_window in time_window_list:
            time_window.gen_user_word_frequency()  # 产生该时间窗口内的用户词频信息。
        return time_window_list

    # 获得每一个时间窗口内，以用户为维度，统计用户所发弹幕词语的tfidf权重。
    # 参数：已经按照play_timestamp升序排序好的弹幕（已做好中文分词）列表。
    # 返回：time_window列表，每个TimeWindow对象中的 user_token_tfidf_dict 用户词频信息已被填充。
    @classmethod
    def gen_user_token_tfidf_by_time_window(cls, barrage_seg_list, cid):
        dictionary = corpora.Dictionary.load(os.path.join(FileUtil.get_train_model_dir(),
                                                          str(cid) + "-barrage-words.dict"))
        tfidf_model = models.TfidfModel.load(os.path.join(FileUtil.get_train_model_dir(),
                                                          str(cid) + "-barrage-tfidf.model"))
        time_window_list = TimeWindow.gen_time_window_barrage_info(barrage_seg_list, cid)
        for time_window in time_window_list:
            time_window.gen_user_word_frequency()  # 产生该时间窗口内的用户词频信息。
            time_window.gen_user_token_tfidf(dictionary, tfidf_model)  # 产生该时间窗口内的用户所发词语的tfidf权重信息。
        return time_window_list

    # 获得每一个时间窗口内，以用户为维度，统计用户所发弹幕文本的主题分布。
    # 参数：已经按照play_timestamp升序排序好的弹幕（已做好中文分词）列表。
    # 返回：time_window列表，每个TimeWindow对象中的 user_topic_lda_dict 用户词频信息已被填充。
    @classmethod
    def gen_user_topic_lda_by_time_window(cls, barrage_seg_list, cid):
        dictionary = corpora.Dictionary.load(os.path.join(FileUtil.get_train_model_dir(),
                                                          str(cid) + "-barrage-words.dict"))
        lda_model = models.TfidfModel.load(os.path.join(FileUtil.get_train_model_dir(),
                                                        str(cid) + "-barrage-lda.model"))
        time_window_list = TimeWindow.gen_time_window_barrage_info(barrage_seg_list, cid)
        for time_window in time_window_list:
            time_window.gen_user_word_frequency()  # 产生该时间窗口内的用户词频信息。
            time_window.gen_user_topic_lda(dictionary, lda_model)  # 产生该时间窗口内的用户所发词语的tfidf权重信息。
        return time_window_list


if __name__ == "__main__":
    barrage_file_path = "../../data/local/2453759.txt"
    # "../../data/local/9.txt" "../../data/AlphaGo/bilibili/2016-03-09.txt" "../../data/local/2065063.txt"
    barrages = dataloader.get_barrage_from_txt_file(barrage_file_path)
    # barrages = dataloader.get_barrage_from_live_text_file(barrage_file_path)
    cid = FileUtil.get_cid_from_barrage_file_path(barrage_file_path)
    barrage_seg_list = wordseg.segment_barrages(barrages, cid)
    # time_window_list = TimeWindow.gen_time_window_barrage_info(barrage_seg_list)
    # for time_window in time_window_list:
    #     str_info = ''
    #     for barrage_seg in time_window.barrage_or_seg_list:
    #         for sentence_seg in barrage_seg.sentence_seg_list:
    #             str_info += (sentence_seg.word + sentence_seg.flag + u"\t")
    #     print str(time_window.time_window_index), u"\t", str(time_window.start_timestamp), u"\t",\
    #         str(time_window.end_timestamp), u"\t", str_info

    # time_window_list = TimeWindow.gen_user_word_frequency_by_time_window(barrage_seg_list)
    # with codecs.open(FileUtil.get_word_segment_result_file_path(cid), "wb", "utf-8") as output_file:
    #     for time_window in time_window_list:
    #         str_info = str(time_window.time_window_index) + u"\t"
    #         for user_id, word_frequency in time_window.user_word_frequency_dict.items():
    #             str_info += (user_id + u"\t")
    #             for word, frequency in word_frequency.items():
    #                 str_info += (word + u"\t" + str(frequency) + u"\t")
    #         print str_info
    #         output_file.write(str_info + u"\n")

    # time_window_list = TimeWindow.gen_user_word_frequency_by_time_window(barrage_seg_list, cid)
    # SimMatrix.gen_jaccard_sim_matrix_by_word_frequency(time_window_list)

    # time_window_list = TimeWindow.gen_user_token_tfidf_by_time_window(barrage_seg_list, cid)
    # SimMatrix.gen_cosine_sim_matrix(time_window_list, 2)
