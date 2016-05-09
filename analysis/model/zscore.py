#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import codecs
import os

from util.datetimeutil import DateTimeUtil
from util.fileutil import FileUtil
from util.loggerutil import Logger

"""
主要对于matlab计算出的zscore信息进行处理，找出相应的zscore对应的时间窗口，
找出zscore较高的视频片断区间等等。
"""

logger = Logger("zscore.log").get_logger()


class Zscore(object):
    # 初始化函数，构建zscore数据。
    # 参数： time_window_size 时间窗口的大小，以秒为单位
    #       slide_time_interval 以多少秒为时间间隔滑动，创建时间窗口，以秒为单位
    #       analysis_unit_capacity 以多少个时间窗口为单位进行分析zscore的值。
    #       zscore_file_path  以cid-zscore.txt命名
    def __init__(self, cid, zscore_file_path, time_window_size, slide_time_interval, analysis_unit_capacity):
        self.cid = cid  # b站视频对应的cid信息
        self.zscore_file_path = zscore_file_path
        self.zscore_list = []  # 其中的元素为 (time_window_index, zscore) 这样的元组信息
        self.time_window_size = time_window_size
        self.slide_time_interval = slide_time_interval
        self.analysis_unit_capacity = analysis_unit_capacity
        # 读入matlab处理过后的zscore文件，该文件中是没有前 analysis_unit_capacity 个时间窗口的值的
        with codecs.open(zscore_file_path, "rb", "utf-8") as input_file:
            time_window_index = analysis_unit_capacity
            for line in input_file:
                if line is None:
                    continue
                zscore = float(line.strip())
                self.zscore_list.append((time_window_index, zscore))
                time_window_index += 1
        self.__sort_zscore_list()

    # 对zscore数组进行排序（默认按照升序进行排列）
    # 参数： reverse 值为False 时，zscore按照升序排序，值为True时，zscore按照降序排序。
    def __sort_zscore_list(self, reverse=False):
        self.zscore_list = sorted(self.zscore_list, key=lambda zscore_tuple: zscore_tuple[1], reverse=reverse)

    # 参数： threshold_value 过滤阈值，只有小于 threshold_value 的zscore才能被输出。
    # 生成zscore排序结果文件，文件中包括3列：
    # 时间窗口的下标，以0开始；该时间窗口对应的zscore值；该时间窗口格式化后的时间戳 xx minutes  xx seconds 的格式
    def gen_sorted_zscore_file(self, threshold_value=1):
        sorted_zscore_file_name = FileUtil.get_cid_from_barrage_file_path(self.zscore_file_path) + "-sorted-zscore.txt"
        with codecs.open(sorted_zscore_file_name, "wb", "utf-8") as output_file:
            for time_window_index, zscore in self.zscore_list:
                if zscore >= threshold_value:
                    continue
                total_seconds = time_window_index * self.slide_time_interval  # 时间窗口起始地秒数
                zscore_info = unicode(str(time_window_index)) + u"\t" + unicode(
                    str(zscore)) + u"\t" + DateTimeUtil.format_barrage_play_timestamp(total_seconds) + u"\n"
                # logger.debug(zscore_info)
                output_file.write(zscore_info)

    # 根据 zscore 的值（对片段进行左右拼接）产生可能的 强烈情感 片段。这里的zscore 是 Z = 1 - UTL的版本，值越小片段越相似。
    # 参数：global_zscore_threshold 找出小于 global_zscore_threshold的zscore值
    #      left_zscore_threshold 左边时间窗口与当前时间窗口的 zscore 差值 阈值
    #      right_zscore_threshould 右边时间窗口与当前时间窗口的 zscore 差值 阈值
    #      其实直接遍历 self.zscore_list 就好，没必要这么复杂
    def gen_possible_high_emotion_clips(self, global_zscore_threshold=0.5, left_zscore_threshold=0.25,
                                        right_zscore_threshould=0.25):
        high_emotion_clips = []  # 其中的元素为[时间窗口起始下标、结束下标、起始时间、结束时间、zscore值]
        # False 表示当前的zscore_tuple没有被选入 high_emotion_clips
        my_zscore_dict = {}
        for time_window_index, zscore in self.zscore_list:
            if zscore >= global_zscore_threshold:
                continue
            my_zscore_dict[time_window_index] = [zscore, False]
        # 开始寻找可能的 情感强烈 片段
        for time_window_index, zscore_tuple in my_zscore_dict.items():
            zscore = zscore_tuple[0]
            flag = zscore_tuple[1]
            if flag is True:
                # 说明这个片段已经被加入 high_emotion_clips 中，那么跳过。
                continue
            # 向左寻找片段
            left_window_index = time_window_index - 1
            right_window_index = time_window_index + 1
            left_border = time_window_index
            right_border = time_window_index
            while left_window_index in my_zscore_dict.keys():
                left_zscore = my_zscore_dict[left_window_index][0]
                left_flag = my_zscore_dict[left_window_index][1]
                if left_flag is True:
                    # 说明这个片段已经被加入 high_emotion_clips 中，那么跳过。
                    break
                if abs(zscore - left_zscore) <= left_zscore_threshold:
                    left_border = left_window_index
                    my_zscore_dict[left_window_index][1] = True  # 该片段已经加入 high_emotion_clips 中
                    left_window_index -= 1
                else:
                    break
            # 向右寻找片段
            while right_window_index in my_zscore_dict.keys():
                right_zscore = my_zscore_dict[right_window_index][0]
                right_flag = my_zscore_dict[right_window_index][1]
                if right_flag is True:
                    # 说明这个片段已经被加入 high_emotion_clips 中，那么跳过。
                    break
                if abs(zscore - right_zscore) <= right_zscore_threshould:
                    right_border = right_window_index
                    my_zscore_dict[right_window_index][1] = True  # 该片段已经加入 high_emotion_clips 中
                    right_window_index += 1
                else:
                    break
            # 记录寻找到的片段信息
            if abs(left_border - right_border) > 0:
                # 首先标记当前片段
                my_zscore_dict[time_window_index][1] = True  # 将当前片段收入情感强烈片段
                # 那么说明找到了 情感强烈 的片段
                left_border_seconds = left_border * 10  # 以秒为单位
                right_border_seconds = right_border * 10 + 30  # 以秒为单位
                temp_high_emotion_clip = [left_border, right_border,
                                          DateTimeUtil.format_barrage_play_timestamp(left_border_seconds),
                                          DateTimeUtil.format_barrage_play_timestamp(right_border_seconds)]
                for index in xrange(left_border, right_border + 1, 1):
                    temp_high_emotion_clip.append(my_zscore_dict[index][0])  # 将每一个时间窗口zscore的值也记录下来
                high_emotion_clips.append(temp_high_emotion_clip)
        # 将 high_emotion_clips 相关信息写入本地文件
        self.__save_high_emotion_clips_to_file(high_emotion_clips, global_zscore_threshold,
                                               left_zscore_threshold, right_zscore_threshould)
        return high_emotion_clips

    # 将 可能的 high_emotion_clips 信息存储到本地文件中
    # 参数：high_emotion_clips [(left_border, right_border, left_border_seconds, right_border_seconds)]
    #      global_zscore_threshold 找出小于 global_zscore_threshold的zscore值
    #      left_zscore_threshold 左边时间窗口与当前时间窗口的 zscore 差值 阈值
    #      right_zscore_threshould 右边时间窗口与当前时间窗口的 zscore 差值 阈值
    def __save_high_emotion_clips_to_file(self, high_emotion_clips, global_zscore_threshold,
                                          left_zscore_threshold, right_zscore_threshould):
        file_path = os.path.join(FileUtil.get_zscore_dir(), self.cid + "-high-emotion-clips.txt")
        with codecs.open(file_path, "wb", "utf-8") as output_file:
            output_file.write(unicode(str(global_zscore_threshold)) + u"\t" +
                              unicode(str(left_zscore_threshold)) + u"\t" +
                              unicode(str(right_zscore_threshould)) + u"\n")
            for emotion_clip in high_emotion_clips:
                str_info = u""
                for item in emotion_clip:
                    str_info += (unicode(str(item)) + u"\t")
                str_info = str_info[0: len(str_info) - 1] + u"\n"
                output_file.write(str_info)

    # 从本地文件中获取 某一个cid视频 对应的 high_emotion_clips信息
    # 参数：cid 该视频的cid信息
    # 返回：(high_emotion_clips, global_zscore_threshold, left_zscore_threshold, right_zscore_threshould) 的元组
    #       high_emotion_clips [(left_border, right_border, left_border_seconds, right_border_seconds)]
    @classmethod
    def load_high_emotion_clips_from_file(cls, cid):
        file_path = os.path.join(FileUtil.get_zscore_dir(), cid + "-high-emotion-clips.txt")
        first_line_flag = True
        high_emotion_clips = []
        global_zscore_threshold = 0
        left_zscore_threshold = 0
        right_zscore_threshould = 0
        with codecs.open(file_path, "rb", "utf-8") as input_file:
            for line in input_file:
                split_info = line.strip().split("\t")
                if first_line_flag:
                    first_line_flag = False
                    global_zscore_threshold = split_info[0]
                    left_zscore_threshold = split_info[1]
                    right_zscore_threshould = split_info[2]
                    continue
                high_emotion_clips.append(split_info)
        return high_emotion_clips, global_zscore_threshold, left_zscore_threshold, right_zscore_threshould


if __name__ == "__main__":
    zscore = Zscore("2065063", os.path.join(FileUtil.get_zscore_dir(), "zArrayWF.txt"), 30, 10, 4)
    # zscore.gen_sorted_zscore_file(threshold_value=0.5)
    # zscore.gen_possible_high_emotion_clips()
    high_emotion_clips = zscore.gen_possible_high_emotion_clips(global_zscore_threshold=0.6)
    for emotion_clip in high_emotion_clips:
        str_info = u""
        for item in emotion_clip:
            str_info += (unicode(str(item)) + u"\t")
        str_info = str_info[0: len(str_info) - 1]
        str_info += u"\n"
        print str_info
