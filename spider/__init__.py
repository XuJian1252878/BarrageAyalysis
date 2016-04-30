#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import sys
import urllib
import urllib2
import zlib

from util.loggerutil import Logger

"""
提供爬虫类使用到的一些基本方法。
"""

__author__ = "htwxujian@gmail.com"


class SmartRedirectHandler(urllib2.HTTPRedirectHandler):
    def __init__(self):
        self.result = ""

    def http_error_301(self, req, fp, code, msg, headers):
        self.result = urllib2.HTTPRedirectHandler.http_error_301(self, req, fp, code, msg, headers)
        self.result.status = code
        return self.result

    def http_error_302(self, req, fp, code, msg, headers):
        self.result = urllib2.HTTPRedirectHandler.http_error_302(self, req, fp, code, msg, headers)
        self.result.status = code
        return self.result


class BarrageSpider(object):
    FILESYSTEMENCODING = sys.getfilesystemencoding()

    def __init__(self):
        self.post_data = {}
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)' +
                          ' Chrome/48.0.2564.116 Safari/537.36',
            'Accept-Encoding': 'gzip, deflate, zlib, sdch'
        }
        self.timeout = 60
        self.try_times = 5

    @staticmethod
    def __construct_req(site_url, post_data, headers):
        post_data = urllib.urlencode(post_data)
        return urllib2.Request(site_url, data=post_data, headers=headers)

    def __access_url_internal(self, req, timeout=60, try_times=1):
        try:
            if try_times <= self.try_times:
                opener = urllib2.build_opener(SmartRedirectHandler)
                resp = opener.open(req, timeout=timeout)
                return resp
            else:
                return False
        except urllib2.HTTPError as exception:
            print exception
            Logger.print_console_info(u"连接失败！" + unicode(str(try_times)) + u" ，正在重新连接……")
            # # 发现发生 HTTPError 502 错误时，重试链接并没有效果。
            # if exception.code == 502:
            #     time.sleep(10)  # 还是没有用
            self.__access_url_internal(req, timeout, try_times + 1)
        except urllib2.URLError as exception:
            print exception
            Logger.print_console_info(u"连接失败！" + unicode(str(try_times)) + u" ，正在重新连接……")
            # 发现发生 HTTPError 502 错误时，重试链接并没有效果。
            self.__access_url_internal(req, timeout, try_times + 1)
        except Exception as exception:
            print exception
            Logger.print_console_info(u"连接失败！" + unicode(str(try_times)) + u" ，正在重新连接……")
            # 发现发生 HTTPError 502 错误时，重试链接并没有效果。
            self.__access_url_internal(req, timeout, try_times + 1)

    def __access_url(self, req, timeout=60):
        resp = self.__access_url_internal(req, timeout)
        if resp is False:
            Logger.print_console_info(u"无法连接：" + unicode(req.get_full_url()))
            return None
        else:
            return resp

    def get_html_content(self, site_url, post_data=None, headers=None):
        if post_data is None:
            post_data = self.post_data
        if headers is None:
            headers = self.headers
        req = self.__construct_req(site_url, post_data, headers)
        resp = self.__access_url(req, self.timeout)
        # 获得返回网页的相关信息
        if resp is None:
            return ""
        page_html = resp.read()
        resp_info = resp.info()
        if "Content-Encoding" in resp_info:
            Logger.print_console_info(
                u"网页：" + unicode(resp.url) + u"\t压缩格式： " + unicode(resp_info["Content-Encoding"]))
            try:
                if resp_info["Content-Encoding"] == "deflate":
                    page_html = zlib.decompress(page_html, -zlib.MAX_WBITS)
                elif resp_info["Content-Encoding"] == "gzip":
                    page_html = zlib.decompress(page_html, zlib.MAX_WBITS | 16)
                elif resp_info["Content-Encoding"] == "zlib":
                    page_html = zlib.decompress(page_html, zlib.MAX_WBITS)
            except zlib.error as e:
                print e
                return None
        page_html = page_html.decode("utf-8", "ignore")
        return page_html


if __name__ == "__main__":
    bSpider = BarrageSpider()
    url = "http://comment.bilibili.tv/6461"
    # url = "http://www.bilibili.com/video/av4122999/"
    Logger.print_console_info(bSpider.get_html_content(url))
