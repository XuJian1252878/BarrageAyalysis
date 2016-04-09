#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import urllib
import urllib2
import re
import json
import uuid
import hashlib
import socket
import sys
import time
import threading
import codecs

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

class DouyuBarrageClient:

  # liveUrl 主播的链接地址
  def __init__(self, liveUrl):

    self.liveHtmlCode = self.__grab_html_code(liveUrl) # 必须首先调用

    self.barrageServers = "" # 弹幕服务器
    self.loginAuthServers = self.__init_auth_servers() # 登陆验证服务器

    self.loginUserName = "" # 登陆用户名
    self.liveStat = "" # 登陆状态字段
    self.weight = "" # 主播财产
    self.fansCount = "" # 直播间粉丝数量
    
    self.room = self.__init_room_info() # 主播房间信息
    self.grpId = "" # 用户在直播间的组id
    self.devId = str(uuid.uuid4()).replace("-", "").upper()
    self.ver = "20150929" # 发送协议中表示版本号，固定值
    self.socketBufferSize = 4096

    self.fileSystemEncoding = sys.getfilesystemencoding()

    self.barrage_auth_socket = "" # 用于验证登陆的socket
    self.barrage_socket = "" # 用于获取弹幕的socket

  # 登陆弹幕服务器
  def do_login(self):

    # 挑选一对验证服务器地址和端口
    authServer = self.loginAuthServers[0]["ip"]
    authPort = int(self.loginAuthServers[0]["port"])
    self.barrage_auth_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.barrage_auth_socket.connect((authServer, authPort))
    # 向验证服务器发送验证请求，获得username, rid, gid信息。
    self.do_login_auth()
    # 向弹幕服务器发送登陆请求
    barrageServer = self.barrageServers[0][0]
    barragePort = int(self.barrageServers[0][1])
    self.barrage_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.barrage_socket.connect((barrageServer, barragePort))
    self.do_login_barrage()

  # 保持心跳数据
  def keeplive(self):

    print u"启动 KeepLive 线程"
    while True:
      self.send_auth_keeplive_req()
      self.send_barrage_keeplive_req()
      time.sleep(40)

  def send_auth_keeplive_req(self):

    content = "type@=keeplive/tick@=" + self.__timestamp() + "/vbw@=0/k@=19beba41da8ac2b4c7895a66cab81e23/"
    msg = self.__protocol_msg(content)
    self.barrage_auth_socket.send(msg)

  def send_barrage_keeplive_req(self):

    content = "type@=keeplive/tick@=" + self.__timestamp() + "/"
    msg = self.__protocol_msg(content)
    self.barrage_socket.send(msg)

  # 向验证服务器发送登陆请求
  def do_login_auth(self):
    self.__send_auth_loginreq_req()
    self.__parse_auth_loginreq_resp()

  # 向弹幕服务器发送登陆请求
  def do_login_barrage(self):

    self.__send_barrage_loginreq_req() # 发送登陆弹幕服务器请求
    # 这时的回应信息没有用处
    self.barrage_socket.recv(self.socketBufferSize)
    # 向服务器发送加入群组的信息
    self.__send_barrage_join_grp_req()
    # 这两条请求发送完成之后就可以接受弹幕了

  # 向验证登陆服务器发送验证登陆信息
  def __send_auth_loginreq_req(self):

    rt = self.__timestamp() # 发送协议中包含的字段，值为以秒为单位的时间戳
    vk = self.__vk(rt, self.devId)
    # 开始构建发送包的内容部分
    content = "type@=loginreq/username@=/ct@=0/password@=1234567890123456/roomid@=" + self.room["id"] + "/devid@=" + self.devId + "/rt@=" + rt + "/vk@=" + vk + "/ver@=" + self.ver + "/"
    msg = self.__protocol_msg(content)
    self.barrage_auth_socket.send(msg)

  # 解析验证服务器返回的两个信息
  # 在第一个回馈信息中可获得username
  # 在第二个回馈信息中可获得 弹幕服务器列表、主播房间编号，用户在直播间的组编号
  def __parse_auth_loginreq_resp(self):

    # 获得之后的登陆用户名
    serverResp = self.barrage_auth_socket.recv(self.socketBufferSize)
    serverResp = self.__filter_escape_character(serverResp)
    pattern = re.compile(r'username@=(.*?)/.*?live_stat@=(.*?)/', re.S)
    match = re.search(pattern, serverResp)
    self.loginUserName = match.group(1)
    self.liveStat = match.group(2)

    # 获得弹幕服务器列表
    serverResp = self.barrage_auth_socket.recv(self.socketBufferSize)
    serverResp = self.__filter_escape_character(serverResp)
    pattern = re.compile(r'id@A=.*?ip@A=(.*?)/port@A=(.*?)/', re.S)
    self.barrageServers = re.findall(pattern, serverResp)
    print serverResp

    # 获得房间编号 rid，以及用户分组编号gid
    pattern = re.compile(r'type@=setmsggroup/rid@=(.*?)/gid@=(.*?)/.*?weight@=(.*?)/.*?fans_count@=(.*?)/', re.S)
    match = re.search(pattern, serverResp)
    self.room["id"] = match.group(1)
    self.grpId = match.group(2)
    self.weight = match.group(3)
    self.fansCount = match.group(4)

  # 向弹幕服务器发送登陆信息
  def __send_barrage_loginreq_req(self):

    content = "type@=loginreq/username@=" + self.loginUserName + "/password@=1234567890123456/roomid@=" + self.room["id"] + "/"
    msg = self.__protocol_msg(content)
    self.barrage_socket.send(msg)

  # 向弹幕服务器发送加入直播室群组的信息
  def __send_barrage_join_grp_req(self):

    # gid=-9999 表示未分组，接受所有的弹幕信息
    content = "type@=joingroup/rid@=" + self.room["id"] + "/gid@=-9999/"
    msg = self.__protocol_msg(content)
    self.barrage_socket.send(msg)

  # 过滤掉转义字符串
  def __filter_escape_character(self, myStr):

    return myStr.replace("@A", "@").replace("@S", "/")

  # 构建请求协议信息
  def __protocol_msg(self, content):

    return DouyuProtocolMsg(content).get_bytes()

  # 获得网页源代码信息
  def __grab_html_code(self, liveUrl):

    request = urllib2.Request(liveUrl)
    response = urllib2.urlopen(request)
    return response.read()

  # 检查获得的json信息是否有效
  def __valid_json(self, myJson):

    try:
      jsonObject = json.loads(myJson)
    except ValueError as e:
      print e
      return False
    return jsonObject

  # 获得主播房间信息
  def __init_room_info(self):

    # 为什么 var\s\$ROOM\s=\s({.*}) 这个正则表达式可以，r'var\s\$ROOM\s=\s{(.*)}' 就不行
    roomInfoJson = re.search('var\s\$ROOM\s=\s({.*})', self.liveHtmlCode).group(1)
    roomInfoJsonFormat = self.__valid_json(roomInfoJson)
    room = {}
    if roomInfoJsonFormat != False:
      js = roomInfoJsonFormat
      room["id"] = str(js["room_id"])
      room["name"] = js["room_name"]
      room["ggShow"] = js["room_gg"]["show"]
      room["ownerUid"] = str(js["owner_uid"])
      room["ownerName"] = js["owner_name"]
      room["roomUrl"] = js["room_url"]
      room["nearShowTime"] = js["near_show_time"]
      room["tags"] = js["all_tag_list"]
    return room

  # 打印主播房间的信息
  def print_room_info(self):

    if self.room == {} or self.room == None:
      print u"暂未获得主播房间信息"
    else:
      print u"================================================"
      print u"= 直播间信息"
      print u"================================================"
      print u"= 房间：" + self.room["name"] + u"\t编号：" + self.room["id"]
      print u"= 主播：" + self.room["ownerName"] + u"\t编号：" + self.room["ownerUid"]
      tags = u""
      for key in self.room["tags"]:
        tags += (self.room["tags"][key]["name"] + u"\t")
      print (u"= 标签：" + tags).encode(self.fileSystemEncoding, "ignore")
      print u"= 粉丝：" + self.fansCount
      print u"= 财产：" + self.weight
      # <[^<]+?>  这个正则表达式什么意思？
      print (u"= 公告：" + re.sub("\n+", "\n", re.sub("<[^<]+?>", "", self.room["ggShow"]))).encode(self.fileSystemEncoding, "ignore")
      print u"================================================"

  # 获得验证服务器的列表
  def __init_auth_servers(self):

    pattern = re.compile(r'"server_config":"(.*?)","', re.S)
    match = re.search(pattern, self.liveHtmlCode)
    oriUrls = match.group(1)
    oriUrls = urllib.unquote(oriUrls)
    return json.loads(oriUrls)

  # 构建以秒为单位的时间戳
  def __timestamp(self):

    return str(int(time.time()))

  # 获得发送协议中vk的值
  def __vk(self, timestamp, devId):

    return hashlib.md5(timestamp + "7oE9nPEG9xXV69phU31FYCLUagKeYtsF" + devId).hexdigest()

  # 获得弹幕信息
  def get_barrage(self, outputFile):

    try:
      # 文集的 open 操作如果在此处，那么文件打开操作太过频繁，导致弹幕写入不了文件
      serverResp = self.barrage_socket.recv(4000)
      serverResp = self.__filter_escape_character(serverResp).decode("utf-8", "ignore")
      msgType = re.search(r"type@=(.*?)/", serverResp).group(1)
      if msgType == "chatmsg":
        rid = re.search(r"rid@=(.*?)/", serverResp).group(1) # 房间id
        uid = re.search(r"uid@=(.*?)/", serverResp).group(1) # 发送者id
        nn = re.search(r"nn@=(.*?)/", serverResp).group(1) # 发送者昵称
        txt = re.search(r"txt@=(.*?)/", serverResp).group(1) # 弹幕文本内容
        cid = re.search(r"cid@=(.*?)/", serverResp).group(1) # 弹幕唯一id
        level = re.search(r"level@=(.*?)/", serverResp).group(1) # 用户等级
        outputFile.write(unicode(str(time.time())) + u"\t" + rid + u"\t" + uid + u"\t" + nn + u"\t" + txt + u"\t" + cid + u"\t" + level + u"\n")
        print (unicode(str(time.time())) + u"\t" + rid + u"\t" + uid + u"\t" + nn + u"\t" + txt + u"\t" + cid + u"\t" + level + u"\n").encode(self.fileSystemEncoding, "ignore")
      elif msgType == "chatmessage":
        rid = re.search(r"rid@=(.*?)/", serverResp).group(1) # 房间id
        sender = re.search(r"sender@=(.*?)/", serverResp).group(1) # 发送者id
        snick = re.search(r"snick@=(.*?)/", serverResp).group(1) # 发送者昵称
        content = re.search(r"content@=(.*?)/", serverResp).group(1) # 弹幕文本内容
        chatmsgid = re.search(r"chatmsgid@=(.*?)/", serverResp).group(1) # 弹幕唯一id
        level = re.search(r"level@=(.*?)/", serverResp).group(1) # 用户等级
        outputFile.write(unicode(str(time.time())) + u"\t" + rid + u"\t" + sender + u"\t" + snick + u"\t" + content + u"\t" + chatmsgid + u"\t" + level + u"\n")
        print (unicode(str(time.time())) + u"\t" + rid + u"\t" + sender + u"\t" + snick + u"\t" + content + u"\t" + chatmsgid + u"\t" + level + u"\n").encode(self.fileSystemEncoding, "ignore")
    except AttributeError as e:
      print e

  def start(self):
    self.do_login() # 登陆验证服务器，以及弹幕服务器
    if self.liveStat == 0:
      print u"主播离线中，正在退出…………"
    else: # 主播在线的状态
      print u"主播在线中，准备获取弹幕…………"
      self.print_room_info()
      keepliveThread = threading.Thread(target = self.keeplive)
      keepliveThread.setDaemon(True)
      keepliveThread.start()
      # 保存弹幕数据
      barrageFileName = self.room["id"] + "_" + time.strftime("%Y-%m-%d") + ".txt"
      with codecs.open(barrageFileName, "ab", "utf-8") as outputFile:
        while True:
          self.get_barrage(outputFile)

if __name__ == "__main__":
  liveUrl = sys.argv[1]
  dc = DouyuBarrageClient(liveUrl)
  dc.start()