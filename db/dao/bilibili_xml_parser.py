#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import codecs
import os
import re

from db.dao.barragedao import BarrageDao

"""
对b站的弹幕xml本地文件进行解析。
"""

__author__ = "htwxujian@gmail.com"


class BilibiliXmlParser(object):
    # 文件名称必须是以 cid.xml命名的，否则无法读取弹幕信息。
    @staticmethod
    def get_cid(xml_file_path):
        (base_path, xml_file_name) = os.path.split(xml_file_path)
        cid = xml_file_name.split(".")[0]
        return cid

    # 解析出xml文件中的弹幕信息，文件名称必须是以 cid.xml命名的，否则无法读取弹幕信息。
    @staticmethod
    def parse_xml(xml_file_path):
        # 获取xml文件中的全部内容。
        with codecs.open(xml_file_path, "rb", "utf-8") as input_file:
            content = []
            for line in input_file:
                content.append(line)
        content = u"\n".join(content)
        # 弹幕出现的播放时间，弹幕类型，字体大小，字体颜色，弹幕出现的unix时间戳，弹幕池，弹幕创建者id，弹幕id
        pattern = re.compile(r'<d p="(.*?),(.*?),(.*?),(.*?),(.*?),(.*?),(.*?),(.*?)">(.*?)</d>', re.S)
        barrages = re.findall(pattern, content)
        if len(barrages) <= 0:
            return None
        return barrages

    # 将xml文件里的弹幕信息存储入数据库中。
    @staticmethod
    def save_xml_barrage_to_db(xml_file_path):
        barrages = BilibiliXmlParser.parse_xml(xml_file_path)
        cid = BilibiliXmlParser.get_cid(xml_file_path)
        return BarrageDao.add_barrages(barrages, cid)
