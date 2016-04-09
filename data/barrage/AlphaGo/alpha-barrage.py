#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import os
import sys
import codecs
import re
import glob

class BilibiliBarrageOperate(object):

  def __init__(self):

    self.curdir = os.getcwd()
    self.oriDataPath = os.path.join(self.curdir, "origin", "bilibili")
    self.resDataPath = os.path.join(self.curdir, "result", "bilibili")
    self.fileSystemEncoding = sys.getfilesystemencoding()
    # 确保结果文件存在
    self.__gen_barrage_folders()

  # 获得当前弹幕文件产生的日期，根据弹幕文件的名称获得。
  def get_barrage_date(self, oriDataFile):

    (filePath, fileName) = os.path.split(oriDataFile)
    fileName = fileName.split(".")[0]
    return fileName

  # 检查 bilibili 弹幕数据的相关文件夹是否存在。
  def __gen_barrage_folders(self):

    if (not os.path.exists(self.oriDataPath)):
      os.makedirs(self.oriDataPath)
    if (not os.path.exists(self.resDataPath)):
      os.makedirs(self.resDataPath)

  # 对每行的弹幕数据进行处理，返回格式：时间戳\t弹幕作者\t弹幕内容
  def format_barrage(self, barrage, barrageDate):

    barrage = barrage.strip(u"\r\n ") # 弹幕结尾有一个\r的符号
    if not u"收到彈幕:" in barrage:
      print barrage.encode(self.fileSystemEncoding, "ignore")
      return None
    pattern = re.compile(r'(.*?)\s(.*?)\s:\s.*?:(.*?)\s.*?\s(.*?)$')
    match = re.search(pattern, barrage)
    if match is None:
      return None
    content = match.group(4) # 弹幕内容
    author = match.group(3) # 弹幕作者
    timeSplit = match.group(2).split(u":") # 12进制的时间表示
    timeSpan = match.group(1) # 上午、下午
    if (timeSpan == u"下午") and timeSplit[0] != u"12":
      timeSplit[0] = str(int(timeSplit[0]) + 12)
    timeInfo = barrageDate + u" " + u":".join(timeSplit)
    return timeInfo + u"\t" + author + u"\t" + content


  # 处理文件内容
  def start(self):

    # 开始格式化 origin 文件夹中的弹幕原始数据
    oriDataFiles = glob.glob(os.path.join(self.oriDataPath, "*.txt"))
    for oriDataFile in oriDataFiles:
      barrageDate = self.get_barrage_date(oriDataFile)
      resDataFile = os.path.join(self.resDataPath, barrageDate + ".txt")
      with codecs.open(resDataFile, "wb", "utf-8") as outputFile:
        with codecs.open(oriDataFile, "rb", "utf-8") as inputFile:
          for line in inputFile:
            barrage = self.format_barrage(line, barrageDate)
            if barrage is None:
              continue
            outputFile.write(barrage + u"\n")

if __name__ == "__main__":
  bbo = BilibiliBarrageOperate()
  bbo.start()