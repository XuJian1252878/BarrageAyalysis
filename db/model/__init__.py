#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from sqlalchemy import Column, String, Integer, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref

__author__ = "htwxujian@gmail.com"

BASE_MODEL = declarative_base()


# 数据库表的定义。


# 定义movie对象，保存movie的id，标题，以及链接等信息
class Video(BASE_MODEL):
    __tablename__ = "video"

    cid = Column(String(30), primary_key=True)  # 视频对应的弹幕cid
    title = Column(Text, nullable=False)  # 视频的标题信息。
    tags = Column(Text, nullable=False)  # 视频的标签信息，格式为：一级标签\t二级标签...
    aid = Column(String(30), nullable=False)  # 视频的aid
    url = Column(Text, nullable=False)  # 视频的网址链接


# 定义Barrage对象，存储弹幕的全部相关信息
class Barrage(BASE_MODEL):
    __tablename__ = "barrage"

    row_id = Column(String(30), primary_key=True)  # 弹幕在弹幕数据库中rowID 用于“历史弹幕”功能。
    play_timestamp = Column(String(50), nullable=False)  # 弹幕出现的时间 以秒数为单位。
    type = Column(Integer, nullable=False)  # 弹幕的模式1..3 滚动弹幕 4底端弹幕 5顶端弹幕 6.逆向弹幕 7精准定位 8高级弹幕
    font_size = Column(Integer, nullable=False)  # 字号， 12非常小,16特小,18小,25中,36大,45很大,64特别大
    font_color = Column(String(50), nullable=False)  # 字体的颜色 以HTML颜色的十位数为准
    unix_timestamp = Column(String(50), nullable=False)  # Unix格式的时间戳。基准时间为 1970-1-1 08:00:00
    pool = Column(Integer, nullable=False)  # 弹幕池 0普通池 1字幕池 2特殊池 【目前特殊池为高级弹幕专用】
    sender_id = Column(String(20), nullable=False)  # 发送者的ID，用于“屏蔽此弹幕的发送者”功能
    content = Column(Text, nullable=False)  # 弹幕内容
    # 外键信息
    video_cid = Column(String(30), ForeignKey("video.cid"))
    # 这样就可以使用video.barrages获得该视频的所有弹幕信息。
    video = relationship("Video", backref=backref("barrages", uselist=True, cascade="delete, all"))
