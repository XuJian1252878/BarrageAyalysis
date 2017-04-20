#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import codecs
import os

import math

import wordsegment.wordseg as wordseg
from analysis.model.timewindow import TimeWindow
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
        self.time_window_size = time_window_size  # 时间窗口的大小
        self.slide_time_interval = slide_time_interval  # 滑动时间窗口的大小
        self.analysis_unit_capacity = analysis_unit_capacity
        # 获得做好分词处理、替换词处理、停词过滤、颜文字替换的弹幕分词列表
        self.barrage_seg_list = wordseg.load_segment_barrages(cid)
        self.barrage_count = len(self.barrage_seg_list)
        # 弹幕数量最多的时间窗口对应的弹幕数量，在__adjust_zscore_by_barrage_count_in_timewindow中填充。
        self.max_barrage_count = 0
        # 读入matlab处理过后的zscore文件，该文件中是没有前 analysis_unit_capacity 个时间窗口的值的
        with codecs.open(zscore_file_path, "rb", "utf-8") as input_file:
            time_window_index = analysis_unit_capacity - 1  # 时间窗口的下标是从0开始的
            for line in input_file:
                if line is None:
                    continue
                split_info = line.strip().split(u"\t")
                # zscore 值域 [0,1]， matlab中计算出的是 1 - 相似度分数，这里我们直接要相似度分数
                zscore = 1 - float(split_info[1])
                self.zscore_list.append((time_window_index, zscore))
                time_window_index += 1
        self.__adjust_zscore_by_barrage_count_in_timewindow()

    def __zscore_normalization(self, zscore_list):
        max_zscore = 0
        min_zscore = 0
        for index in xrange(0, len(zscore_list)):
            zscore = zscore_list[index][1]
            if zscore > max_zscore:
                max_zscore = zscore
            if zscore < min_zscore:
                min_zscore = zscore
        zscore_range = max_zscore - min_zscore
        for index in xrange(0, len(zscore_list)):
            zscore = zscore_list[index][1]
            zscore_list[index][1] = abs(zscore - min_zscore) / zscore_range
        return zscore_list

    # 对读入的zscore信息再进行处理，考虑到每个时间窗口的弹幕数量影响
    def __adjust_zscore_by_barrage_count_in_timewindow(self):
        time_window_list = TimeWindow.gen_time_window_barrage_info(self.barrage_seg_list, self.cid)
        adjust_zscore_list = []
        temp_zscore_list = []
        # 获取弹幕最多时间窗口中的弹幕数量。
        for time_window in time_window_list:
            if time_window.barrage_count > self.max_barrage_count:
                self.max_barrage_count = time_window.barrage_count
        # 对于前 analysis_unit_capacity - 1 个时间窗口来说，他们是没有zscore的
        for index in xrange(0, len(self.zscore_list)):
            zscore = float(self.zscore_list[index][1])
            time_window_index = index + self.analysis_unit_capacity - 1

            barrage_density = time_window_list[time_window_index].barrage_count / TimeWindow.get_time_window_size()
            adjust_zscore = zscore * math.log(1 + barrage_density)

            # barrage_percent = time_window_list[time_window_index].barrage_count / (1.0 * self.max_barrage_count)
            # adjust_zscore = 1 * zscore + 0 * barrage_percent  # 以整数的形式出现，不然都是小数
            adjust_zscore_list.append([time_window_index, adjust_zscore, zscore, barrage_density,
                                       time_window_list[time_window_index].barrage_count, self.barrage_count,
                                       DateTimeUtil.format_barrage_play_timestamp(time_window_index * 10)])
            temp_zscore_list.append(
                [time_window_index, adjust_zscore, time_window_list[time_window_index].barrage_count])
        # 按照调整之后的zscore值进行排序。
        adjust_zscore_list = self.__sort_zscore_list(adjust_zscore_list, reverse=True, sort_index=1)
        temp_zscore_list = self.__sort_zscore_list(temp_zscore_list, reverse=False, sort_index=0)
        # 替换原来的self.zscore_list
        self.zscore_list = temp_zscore_list
        # 归一化zscore
        self.zscore_list = self.__zscore_normalization(self.zscore_list)
        adjust_zscore_list = self.__zscore_normalization(adjust_zscore_list)
        with codecs.open(self.cid + "-adjust-zscore.txt", "wb", "utf-8") as output_file:
            for item in adjust_zscore_list:
                output_file.write(unicode(str(item[0])) + u"\t" + unicode(str(item[1])) + u"\t" +
                                  unicode(str(item[2])) + u"\t" + unicode(str(item[3])) + u"\t" +
                                  unicode(str(item[4])) + u"\t" + unicode(str(item[5])) + u"\t" +
                                  unicode(str(item[6])) + u"\n")

    # 对zscore数组进行排序（默认按照升序进行排列）
    # 参数： reverse 值为False 时，zscore按照升序排序，值为True时，zscore按照降序排序。
    def __sort_zscore_list(self, zscore_list=None, reverse=False, sort_index=1):
        if zscore_list is None:
            zscore_list = self.zscore_list
        return sorted(zscore_list, key=lambda zscore_tuple: zscore_tuple[sort_index], reverse=reverse)

    # 参数： threshold_value 过滤阈值，只有大于 threshold_value 的zscore才能被输出。
    # 生成zscore排序结果文件，文件中包括3列：
    # 时间窗口的下标，以0开始；该时间窗口对应的zscore值；该时间窗口格式化后的时间戳 xx minutes  xx seconds 的格式
    def gen_sorted_zscore_file(self, threshold_value=1.0):
        sorted_zscore_file_name = FileUtil.get_cid_from_barrage_file_path(self.zscore_file_path) + "-sorted-zscore.txt"
        with codecs.open(sorted_zscore_file_name, "wb", "utf-8") as output_file:
            for time_window_index, zscore in self.zscore_list:
                if zscore < threshold_value:
                    continue
                total_seconds = time_window_index * self.slide_time_interval  # 时间窗口起始地秒数
                zscore_info = unicode(str(time_window_index)) + u"\t" + unicode(
                    str(zscore)) + u"\t" + DateTimeUtil.format_barrage_play_timestamp(total_seconds) + u"\n"
                # logger.debug(zscore_info)
                output_file.write(zscore_info)

    # 根据 zscore 的值（对片段进行左右拼接）产生可能的 强烈情感 片段。这里的zscore 值越大片段越相似。
    # 参数：global_zscore_threshold 找出大于 global_zscore_threshold的zscore值
    #      left_zscore_threshold 左边时间窗口与当前时间窗口的 zscore 差值 阈值
    #      right_zscore_threshould 右边时间窗口与当前时间窗口的 zscore 差值 阈值
    #      其实直接遍历 self.zscore_list 就好，没必要这么复杂
    def gen_possible_high_emotion_clips(self, global_zscore_threshold=0.3, left_zscore_threshold=0.3,
                                        right_zscore_threshould=0.3):
        high_emotion_clips = []  # 其中的元素为[时间窗口起始下标、结束下标、起始时间、结束时间、zscore值]
        # False 表示当前的zscore_tuple没有被选入 high_emotion_clips
        my_zscore_dict = {}
        for time_window_index, zscore, barrage_count in self.zscore_list:
            if zscore < global_zscore_threshold:
                continue
            my_zscore_dict[time_window_index] = [zscore, False, barrage_count]
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
            # 首先标记当前片段
            my_zscore_dict[time_window_index][1] = True  # 将当前片段收入情感强烈片段
            # 单个时间窗口也是可以作为一个精彩片段的。
            left_border_seconds = left_border * 10  # 以秒为单位
            right_border_seconds = right_border * 10 + 30  # 以秒为单位
            temp_high_emotion_clip = [left_border, right_border,
                                      DateTimeUtil.format_barrage_play_timestamp(left_border_seconds),
                                      DateTimeUtil.format_barrage_play_timestamp(right_border_seconds)]
            temp_zscore = 0
            temp_barrage_count = 0
            for index in xrange(left_border, right_border + 1, 1):
                temp_zscore += my_zscore_dict[index][0]
                temp_barrage_count += my_zscore_dict[index][2]
            time_window_count = right_border - left_border + 3
            # temp_high_emotion_clip.append(my_zscore_dict[index][0])  # 将每一个时间窗口zscore的值也记录下来
            temp_high_emotion_clip.append(temp_zscore / (1.0 * time_window_count))  # 这里的zscore是调整之后的zscore
            temp_high_emotion_clip.append(temp_barrage_count)
            high_emotion_clips.append(temp_high_emotion_clip)
        # 将 high_emotion_clips 相关信息写入本地文件，精彩片段是由平均相似度分数由高到低排序的。
        high_emotion_clips = sorted(high_emotion_clips, key=lambda high_emotion_clip: high_emotion_clip[4],
                                    reverse=True)
        self.__save_high_emotion_clips_to_file(high_emotion_clips, global_zscore_threshold,
                                               left_zscore_threshold, right_zscore_threshould)
        return high_emotion_clips

    # 抽取精彩片段（另一种方式）
    def gen_possible_high_emotion_clips_another(self, base_line=0.1):
        is_high_emotion_clip = False
        high_emotion_clips = []  # 其中的元素为[时间窗口起始下标、结束下标、起始时间、结束时间、zscore值]
        start_border = -1
        end_border = -1
        for index in xrange(0, len(self.zscore_list)):
            time_window_index = self.zscore_list[index][0]
            zscore = self.zscore_list[index][1]
            barrage_count = self.zscore_list[index][2]
            # 记录是否变化点。
            if (zscore < base_line) and (index >= 1):
                last_zscore = self.zscore_list[index - 1][1]
                if last_zscore > base_line:  # 说明刚进入变化点。
                    is_high_emotion_clip = (not is_high_emotion_clip)
                    # 看看是否在记录精彩片段
                    if start_border != -1:
                        # 记录下当前的结束片段
                        end_border = time_window_index - 1

                        zscore_mean = 0
                        barrage_mean = 0
                        # 获得平均的zscore值
                        for sub_index in xrange(start_border, end_border + 1):
                            zscore_mean += self.zscore_list[sub_index][1]
                            barrage_mean += self.zscore_list[sub_index][2]
                        zscore_mean /= (end_border - start_border + 1)
                        barrage_mean /= (end_border - start_border + 3)  # 弹幕密度，每十秒内的弹幕数量
                        high_emotion_clips.append((start_border, end_border,
                                                   DateTimeUtil.format_barrage_play_timestamp(start_border * 10),
                                                   DateTimeUtil.format_barrage_play_timestamp(end_border * 10 + 30),
                                                   zscore_mean, barrage_mean))
                        start_border = -1
                        end_border = -1
            # 检测是否潜在的精彩片段
            if is_high_emotion_clip:
                if (zscore > base_line) and (index >= 1):
                    last_zscore = self.zscore_list[index - 1][1]
                    if last_zscore < base_line:
                        start_border = time_window_index
        high_emotion_clips = sorted(high_emotion_clips, key=lambda high_emotion_clip: high_emotion_clip[4],
                                    reverse=True)
        # 将精彩片段信息写入文件。
        self.__save_high_emotion_clips_to_file(high_emotion_clips, -1, -1, -1)
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
        file_path = os.path.join(FileUtil.get_zscore_dir(), cid + "-high-emotion-clips-lda.txt")
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
    zscore = Zscore("4547002", os.path.join(FileUtil.get_zscore_dir(), "agzz-zscore-result-lda.txt"), 30, 10, 4)
    # zscore.gen_sorted_zscore_file(threshold_value=5)
    # # zscore.gen_possible_high_emotion_clips()
    high_emotion_clips = zscore.gen_possible_high_emotion_clips()
    for emotion_clip in high_emotion_clips:
        str_info = u""
        for item in emotion_clip:
            str_info += (unicode(str(item)) + u"\t")
        str_info = str_info[0: len(str_info) - 1]
        str_info += u"\n"
        print str_info
