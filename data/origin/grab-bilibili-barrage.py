#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

# grab the barrage data of bilibili

import os
import sys
import time
import urllib
import urllib2
import zlib
import re
import codecs
import argparse

class SmartRedirectHandler(urllib2.HTTPRedirectHandler):

  # 关于永久重定向的处理
  def http_error_301(self, req, fp, code, msg, headers):
    result = urllib2.HTTPRedirectHandler.http_error_301(self, req, fp, code, msg, headers)
    result.status = code
    return result

  # 关于临时重定向的处理
  def http_error_302(self, req, fp, code, msg, headers):
    result = urllib2.HTTPRedirectHandler.http_error_302(self, req, fp, code, msg, headers)
    result.status = code
    return result

class BilibiliBarrage:

  def __init__(self):

    self.postData = {}
    self.headers = {
      'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36',
      'Accept-Encoding' : 'gzip, deflate, zlib'
    }
    self.timeout = 60
    self.filesystemencoding = sys.getfilesystemencoding()
    self.barrageCount = 0 # 统计当前弹幕的总条数

  # 构建将要访问的Request对象
  def __construct_request(self, url, postData = {}, headers = {}):

    data = urllib.urlencode(postData)
    return urllib2.Request(url, data = data, headers = headers)

  # 访问网页，获得response响应
  def __access_url(self, request, timeout = 60):

    opener = urllib2.build_opener(SmartRedirectHandler)
    response = opener.open(request, timeout = timeout)
    return response

  # 获得网页源码
  def get_html_content(self, url):

    # 访问网页
    request = self.__construct_request(url, self.postData, self.headers)
    response = self.__access_url(request)
    pageHtml = response.read()
    # 获得的原始网页可能经过压缩，若有压缩需要对其进行解压。
    respInfo = response.info()
    if ("Content-Encoding" in respInfo): # 说明网页源码经过压缩
      print (u"网页：" + unicode(response.url) + u"压缩格式： " + unicode(respInfo["Content-Encoding"])).encode(self.filesystemencoding, "ignore")
    if (respInfo["Content-Encoding"] == "deflate"):
      pageHtml = zlib.decompress(pageHtml, -zlib.MAX_WBITS)
    elif (respInfo["Content-Encoding"] == "gzip"):
      pageHtml = zlib.decompress(pageHtml, zlib.MAX_WBITS|16)
    elif (respInfo["Content-Encoding"] == "zlib"):
      pageHtml = zlib.decompress(pageHtml, zlib.MAX_WBITS)
    pageHtml = pageHtml.decode("utf-8", "ignore")
    return pageHtml

  # 根据获得的网页源代码取得视频的cid信息。
  def get_video_cid(self, pageHtml):
    pattern = re.compile(r'.*?<script.*>EmbedPlayer\(\'player\',.*?"cid=(\d*)&.*?</script>', re.S) # re.S 点任意匹配模式，改变'.'的行为
    match = re.search(pattern, pageHtml)
    if match is not None:
      return match.group(1)
    else:
      return None

  # 根据视频的cid获得该视频的弹幕信息
  def get_vedio_barrage(self, cid):

    # 弹幕xml网页的网址
    barrageUrl = "http://comment.bilibili.tv/" + str(cid) + ".xml"
    # 获取弹幕网页源代码
    barrageHtml = self.get_html_content(barrageUrl)
    # 弹幕出现的播放时间，弹幕类型，字体大小，字体颜色，弹幕出现的unix时间戳，未知，弹幕创建者id，弹幕id
    pattern = re.compile(r'<d p="(.*?),(.*?),(.*?),(.*?),(.*?),(.*?),(.*?),(.*?)">(.*?)</d>', re.S)
    barrages = re.findall(pattern, barrageHtml)
    # 保存弹幕信息
    self.__save_video_barrage(cid, barrages)

  # 判断弹幕文件是否存在，存在返回true，不存在返回false。
  def __barrage_file_exists(self, barrageFilePath):
    if (os.path.isfile(barrageFilePath)):
      return True
    else:
      return False

  # 判断两条弹幕信息收否相同，如果相同，那么返回True，不同返回False。
  # lastBarrages 最后n条弹幕，格式：[content \t content \t content \t content, ...]
  # barrage 单条弹幕，格式：[content, content, content, ...]
  def __is_same_barrage(self, lastBarrages, barrage):
    for lastBarrage in lastBarrages:
      lastBarrage = lastBarrage.split(u"\t")
      if (len(lastBarrage) != len(barrage)):
        print u"Error，弹幕格式有误，无法两条弹幕是否相同。".encode(self.filesystemencoding, "ignore")
        continue
      isSame = True
      for index in xrange(0, len(lastBarrage)):
        if (lastBarrage[index] != barrage[index]):
          isSame = False
          break
      if isSame:
        return True
    return False

  # 获取部分弹幕文件
  def __get_barrage_file_content(self, barrageFile, bufferSize = 65526):
    while True:
      nb = barrageFile.read(bufferSize)
      if not nb:
        break
      yield nb

  # 获取当前弹幕文件的总行数
  def __get_barrage_count(self, barrageFile):
    with open(barrageFile, "rb") as inputFile:
      return sum(line.count("\n") for line in self.__get_barrage_file_content(inputFile))

  # 获得弹幕文件的最后n行弹幕
  def __get_last_n_barrages(self, barrageFile, n=5):
    with open(barrageFile, "rb") as inputFile:
      bufferSize = 1024
      seekTimes = 0
      lineCount = 0
      inputFile.seek(0, 2)
      while inputFile.tell() > 0 and lineCount < (n + 1):
        seekTimes += 1
        inputFile.seek(-seekTimes * bufferSize, 2)
        content = inputFile.read(seekTimes * bufferSize)
        inputFile.seek(-seekTimes * bufferSize, 2)
        lineCount = content.count("\n")
      content = inputFile.read(seekTimes * bufferSize)
    lastBarrages = [barrage for barrage in content.split("\n") if barrage != ""]
    lastBarrages = lastBarrages[len(lastBarrages) - n : len(lastBarrages)]
    for index in xrange(0, len(lastBarrages)):
      lastBarrages[index] = lastBarrages[index].decode("utf-8", "ignore")
    return lastBarrages

  # 获取当前的时间戳
  def __get_current_time_str(self):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))

  # 存储视频弹幕信息
  def __save_video_barrage(self, cid, barrages):

    barrageFilePath = os.path.join(os.path.dirname(os.path.realpath(__file__)), str(cid) + ".txt")
    # 检查该cid的弹幕文件是否存在，如果存在，那么将更新后的弹幕数据append加入弹幕。
    if (self.__barrage_file_exists(barrageFilePath)):
      lastBarrageIndex = -1 # 文件中的最后一条弹幕在此时的弹幕列表的下标。
      self.barrageCount = self.__get_barrage_count(barrageFilePath) # 统计已经存在的弹幕数据的数量
      lastBarrages = self.__get_last_n_barrages(barrageFilePath) # 获取当前弹幕文件中的最后n条评论
      print (u"当前文件的最后n条弹幕：\n" + u"\n".join(lastBarrages)).encode(self.filesystemencoding, "ignore")
      for index in xrange(len(barrages) - 1, -1, -1):
        if (self.__is_same_barrage(lastBarrages, barrages[index])):
          # 获得存储在弹幕文件中的最后一条弹幕，在更新弹幕序列中的位置
          lastBarrageIndex = index
          break
      print unicode(str(lastBarrageIndex)) + u"\t" + unicode(str(len(barrages))).encode(self.filesystemencoding, "ignore")
      if (lastBarrageIndex == len(barrages) - 1):
        barrages = []
        print (unicode(self.__get_current_time_str()) + u"\t" + u"弹幕数据没有更新。").encode(self.filesystemencoding, "ignore") # 说明此时弹幕数据没有更新，那么不进行写入操作
      elif (lastBarrageIndex >= 0): # 说明此时弹幕已经有更新了，值为-1时表示全文更新。
        print (unicode(self.__get_current_time_str()) + u"\t" + u"有弹幕数据更新：" + u"\t" + str(len(barrages) - lastBarrageIndex - 1)).encode(self.filesystemencoding, "ignore")
        barrages = barrages[lastBarrageIndex + 1 : len(barrages)]
      elif (lastBarrageIndex == -1): # 全文都需要更新
        print (unicode(self.__get_current_time_str()) + u"\t" + u"有弹幕数据更新：" + u"\t" + str(len(barrages))).encode(self.filesystemencoding, "ignore")

    self.barrageCount += len(barrages)
    print (unicode(self.__get_current_time_str()) + u" 当前弹幕总条数：" + unicode(self.barrageCount) + u"\n\n").encode(self.filesystemencoding, "ignore")
    if (len(barrages) > 0):
      with codecs.open(barrageFilePath, "ab", "utf-8") as outputFile:
        for barrage in barrages:
          if barrage is not None:
            outputFile.write(u"\t".join(barrage) + u"\n")

  # 处理弹幕数据的主函数
  def start(self, videoUrl):

    videoPageHtml = self.get_html_content(videoUrl)
    cid = self.get_video_cid(videoPageHtml)
    print (u"视频cid：" + str(cid)).encode(self.filesystemencoding, "ignore")
    self.get_vedio_barrage(cid)

if __name__ == '__main__':

  parser = argparse.ArgumentParser(description = "grab the barrages from bilibili videos")
  parser.add_argument("-u", "--url",
                      required=True, metavar = "VIDEO_URL", default = "", dest = "videoUrls",
                      help = "the video url with barrages.")
  parser.add_argument("-i", "--internal",
                      required=False, metavar = "INTERNAL_TIME", default = "5", dest = "internalTime",
                      help = "the internal time to grab barrages from bilibili.")
  opts = parser.parse_args()
  # videoUrl = "http://www.bilibili.com/video/av4007893/?tg"
  videoUrl = opts.videoUrls
  bBarrage = BilibiliBarrage()
  bBarrage.start(videoUrl)
