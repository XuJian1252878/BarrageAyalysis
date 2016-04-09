#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

class DouyuProtocolMsg(object):

  # content为协议的数据内容
  def __init__(self, content):

    self.msgType = bytearray([0xb1, 0x02, 0x00, 0x00])
    # python3 中的byte类型，对应2.x版本的八位串
    self.content = bytes(content.decode("utf-8", "ignore"))
    # 数据包必须以 \0 结尾
    self.end = bytearray([0x00])
    self.length = bytearray([len(self.content) + 9, 0x00, 0x00, 0x00])
    self.code = self.length

  # 获得整个协议包的byte数组
  def get_bytes(self):

    return bytes(self.length + self.code + self.msgType + self.content + self.end)

if __name__ == "__main__":
  print(DouyuProtocolMsg("type").get_bytes())