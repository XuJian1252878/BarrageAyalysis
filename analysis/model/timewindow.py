#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import util.loader.dataloader as dataloader
import wordsegment.wordseg as wordseg

"""
记录每个时间窗口内的弹幕分词结果，以及时间窗口划分的配置信息。
"""


class TimeWindow(object):

    __TIME_WINDOW_SIZE = 30  # 时间窗口的大小，以秒为单位
    __SLIDE_TIME_INTERVAL = 10  # 以10s为时间间隔滑动，创建时间窗口，以秒为单位
    __ANALYSIS_UNIT_CAPACITY = 4  # 以多少个时间窗口为单位进行分析zscore的值。

    def __init__(self, time_window_index, start_timestamp, end_timestamp):
        self.time_window_index = time_window_index
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp
        self.barrage_or_seg_list = []  # 该时间窗口内对应的弹幕分词列表，或是原始的弹幕列表。

    @classmethod
    def get_time_window_size(cls):
        return cls.__TIME_WINDOW_SIZE

    @classmethod
    def get_slide_time_interval(cls):
        return cls.__SLIDE_TIME_INTERVAL

    @classmethod
    def get_analysis_unit_capacity(cls):
        return cls.__ANALYSIS_UNIT_CAPACITY

    # 将弹幕的信息按照时间窗口分类
    # 参数：barrage_seg_list 一个已经排好序的，已经切好词的barrage_seg_list列表，或者是原始的未切词的弹幕列表（已排好序）。
    # 返回一个 TimeWindow 列表。
    @classmethod
    def gen_time_window_barrage_info(cls, barrage_or_seg_list):
        time_window_index = 0
        start_timestamp = 0
        end_timestamp = start_timestamp + cls.__TIME_WINDOW_SIZE
        time_window_list = []
        while start_timestamp <= barrage_or_seg_list[-1].play_timestamp:
            temp_seg_list = []
            for barrage_seg in barrage_or_seg_list:
                if (start_timestamp <= barrage_seg.play_timestamp) and (end_timestamp > barrage_seg.play_timestamp):
                    temp_seg_list.append(barrage_seg)
                elif end_timestamp <= barrage_seg.play_timestamp:
                    break
            # 产生一个新的timewindow对象
            time_window = TimeWindow(time_window_index, start_timestamp, end_timestamp)
            time_window.barrage_or_seg_list = temp_seg_list
            time_window_list.append(time_window)

            start_timestamp += cls.__SLIDE_TIME_INTERVAL
            end_timestamp = start_timestamp + cls.__TIME_WINDOW_SIZE
            time_window_index += 1
        return time_window_list


if __name__ == "__main__":
    barrages = dataloader.get_barrage_from_txt_file("../../data/local/920120.txt")
    barrage_seg_list = wordseg.segment_barrages(barrages)
    time_window_list = TimeWindow.gen_time_window_barrage_info(barrage_seg_list)
    for time_window in time_window_list:
        str_info = ''
        for barrage_seg in time_window.barrage_or_seg_list:
            for sentence_seg in barrage_seg.sentence_seg_list:
                str_info += (sentence_seg.word + sentence_seg.flag + u"\t")
        print str(time_window.time_window_index), u"\t", str(time_window.start_timestamp), u"\t",\
            str(time_window.end_timestamp), u"\t", str_info
