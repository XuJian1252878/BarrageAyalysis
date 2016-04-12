#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import codecs
from decimal import Decimal, getcontext

import wordsegment.wordseg as wordseg
from db.model.barrage import Barrage
from util.fileutil import FileUtil

"""
从本地的txt弹幕文件（本地项目根目录data/local/文件夹下。）中加载弹幕数据。或者是从数据库中加载弹幕数据。
"""


def __sort_barrages_by_play_timestamp(barrage):
    # 由于play_timestamp字符串时间戳的小数位置不定，所以用Decial将字符串转化为数字
    # 将 decimal 的精度设置为30
    getcontext().prec = 30
    return Decimal(barrage.play_timestamp)


# order_flag：True 按照play_timestamp降序排列
# order_flag：False 按照play_timestamp升序排列
def sort_barrages(barrages, order_flag=False):
    barrages = sorted(barrages, key=__sort_barrages_by_play_timestamp, reverse=order_flag)
    return barrages


# 从本地的txt文件中读取弹幕的信息，
# 参数：txt_file_path  本地弹幕文件的路径。
#      order_flag True 返回的按照play_timestamp降序排列；False 按照play_timestamp升序排列
def get_barrage_from_txt_file(txt_file_path, order_flag=False):
    barrages = []
    with codecs.open(txt_file_path, "rb", "utf-8") as input_file:
        for barrage in input_file:
            # 弹幕信息的格式：play_timestamp type font_size font_color unix_timestamp pool sender_id row_id content
            split_info = barrage.strip().split(u"\t")
            if len(split_info) < 9:
                # 有些弹幕数据没有内容(content)这一列的内容，对于这些弹幕过滤掉。
                continue
            barrage = Barrage(split_info[0], split_info[1], split_info[2], split_info[3], split_info[4], split_info[5],
                              split_info[6], split_info[7], split_info[8])
            barrages.append(barrage)
    barrages = sort_barrages(barrages, order_flag)
    # barrages = sorted(barrages, key=lambda barrage: barrage.play_timestamp)
    return barrages


if __name__ == "__main__":
    barrages = get_barrage_from_txt_file("../../data/local/9.txt")
    file_path = FileUtil.get_word_segment_result_file_path("../../data/local/9.txt")
    barrage_seg_list = wordseg.segment_barrages(barrages)
    wordseg.save_segment_barrages(file_path, barrage_seg_list)
    barrage_seg_list = wordseg.load_segment_barrages(file_path)
    for barrage_seg in barrage_seg_list:
        print str(barrage_seg.play_timestamp), u"\t", u"\t".join([seg.word + u"\t" + seg.flag for seg
                                                                  in barrage_seg.sentence_seg_list])
