#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import codecs
import os

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
    def __init__(self, zscore_file_path, time_window_size, slide_time_interval, analysis_unit_capacity):
        self.zscore_file_path = zscore_file_path
        self.zscore_list = []  # 其中的元素为 (time_window_index, zscore) 这样的元组信息
        self.time_window_size = time_window_size
        self.slide_time_interval = slide_time_interval
        self.analysis_unit_capacity = analysis_unit_capacity
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
    def __sort_zscore_list(self, reverse=False):
        self.zscore_list = sorted(self.zscore_list, key=lambda zscore_tuple: zscore_tuple[1], reverse=reverse)

    # 生成zscore排序结果文件，文件中包括3列：
    # 时间窗口的下标，以0开始；该时间窗口对应的zscore值；该时间窗口格式化后的时间戳 xx minutes  xx seconds 的格式
    def gen_sorted_zscore_file(self):
        sorted_zscore_file_name = FileUtil.get_cid_from_barrage_file_path(self.zscore_file_path) + "-sorted-zscore.txt"
        with codecs.open(sorted_zscore_file_name, "wb", "utf-8") as output_file:
            for time_window_index, zscore in self.zscore_list:
                total_seconds = time_window_index * self.slide_time_interval  # 时间窗口起始地秒数
                minutes = unicode(str(total_seconds / 60))
                seconds = unicode(str(total_seconds % 60))
                zscore_info = unicode(str(time_window_index)) + u"\t" + unicode(
                    str(zscore)) + u"\t" + minutes + u" minutes " + seconds + u" seconds" + u"\n"
                # logger.debug(zscore_info)
                output_file.write(zscore_info)


if __name__ == "__main__":
    zscore = Zscore(os.path.join(FileUtil.get_zscore_dir(), "zArrayWF.txt"), 30, 10, 4)
    zscore.gen_sorted_zscore_file()
