#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import codecs
import re
import sys

fileSystemEncoding = sys.getfilesystemencoding()

with codecs.open("2016-03-12_result.txt", "wb", "utf-8") as outputFile:
  with open("2016-03-12.txt", "rb") as inputFile:
    for line in inputFile:
      splitInfo = line.split("\t")
      if (len(splitInfo) < 2):
        continue
      timeSpan = splitInfo[0]
      serverResp = splitInfo[1]
      serverResp = serverResp.replace("@A", "@").replace("@S", "/").decode("utf-8", "ignore")
      try:
        msgType = re.search(r"type@=(.*?)/", serverResp).group(1)
        if msgType == "chatmsg":
          rid = re.search(r"rid@=(.*?)/", serverResp).group(1) # ����id
          uid = re.search(r"uid@=(.*?)/", serverResp).group(1) # ������id
          nn = re.search(r"nn@=(.*?)/", serverResp).group(1) # �������ǳ�
          txt = re.search(r"txt@=(.*?)/", serverResp).group(1) # ��Ļ�ı�����
          cid = re.search(r"cid@=(.*?)/", serverResp).group(1) # ��ĻΨһid
          level = re.search(r"level@=(.*?)/", serverResp).group(1) # �û��ȼ�
          outputFile.write(unicode(timeSpan) + u"\t" + rid + u"\t" + uid + u"\t" + nn + u"\t" + txt + u"\t" + cid + u"\t" + level + u"\n")
          print (unicode(timeSpan) + u"\t" + rid + u"\t" + uid + u"\t" + nn + u"\t" + txt + u"\t" + cid + u"\t" + level + u"\n").encode(fileSystemEncoding, "ignore")
        elif msgType == "chatmessage":
          rid = re.search(r"rid@=(.*?)/", serverResp).group(1) # ����id
          sender = re.search(r"sender@=(.*?)/", serverResp).group(1) # ������id
          snick = re.search(r"snick@=(.*?)/", serverResp).group(1) # �������ǳ�
          content = re.search(r"content@=(.*?)/", serverResp).group(1) # ��Ļ�ı�����
          chatmsgid = re.search(r"chatmsgid@=(.*?)/", serverResp).group(1) # ��ĻΨһid
          level = re.search(r"level@=(.*?)/", serverResp).group(1) # �û��ȼ�
          outputFile.write(unicode(timeSpan) + u"\t" + rid + u"\t" + sender + u"\t" + snick + u"\t" + content + u"\t" + chatmsgid + u"\t" + level + u"\n")
          print (unicode(timeSpan) + u"\t" + rid + u"\t" + sender + u"\t" + snick + u"\t" + content + u"\t" + chatmsgid + u"\t" + level + u"\n").encode(fileSystemEncoding, "ignore")
      except AttributeError as e:
        print e