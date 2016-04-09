#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from sqlalchemy import Column, String, Text

from db.model import BASE_MODEL

__author__ = "htwxujian@gmail.com"


# 定义movie对象，保存movie的id，标题，以及链接等信息
class Movie(BASE_MODEL):
    __tablename__ = "movie"

    cid = Column(String(30), primary_key=True)  # 视频对应的弹幕cid
    title = Column(Text, nullable=False)  # 视频的标题信息。
    tags = Column(Text, nullable=False)  # 视频的标签信息，格式为：一级标签\t二级标签...
    mid = Column(String(30), nullable=False)  # 视频的id
    url = Column(Text, nullable=False)  # 视频的网址链接
