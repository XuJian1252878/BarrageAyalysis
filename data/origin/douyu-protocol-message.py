#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

class DouyuProtocolMsg(object):

  # contentΪЭ�����������
  def __init__(self, content):

    self.msgType = bytearray([0xb1, 0x02, 0x00, 0x00])
    # python3 �е�byte���ͣ���Ӧ2.x�汾�İ�λ��
    self.content = bytes(content.decode("utf-8", "ignore"))
    # ���ݰ������� \0 ��β
    self.end = bytearray([0x00])
    self.length = bytearray([len(self.content) + 9, 0x00, 0x00, 0x00])
    self.code = self.length

  # �������Э�����byte����
  def get_bytes(self):

    return bytes(self.length + self.code + self.msgType + self.content + self.end)

if __name__ == "__main__":
  print(DouyuProtocolMsg("type").get_bytes())