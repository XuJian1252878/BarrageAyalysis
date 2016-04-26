#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

"""
获取 http://www.yanwenzi.com/  颜文字网页上的颜文字信息。
"""

import codecs
import re
import sys
import urllib2

filesystemencoding = sys.getfilesystemencoding()


def get_html_content(link):
    # myurl = "http://www.yanwenzi.com/"
    print link
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36"}
    request = urllib2.Request(link, headers=headers)
    response = urllib2.urlopen(request)
    page_html = response.read().decode("utf-8", "ignore")
    # print page_html.encode(filesystemencoding, "ignore")
    return page_html


# 获得每一页表情的链接
def get_emoji_page_link(link):
    page_html = get_html_content(link)
    # 首先获得该表情有多少页
    page_link_list = [link]
    pattern = re.compile(r'<div class="page">(.*?)</div>', re.S)
    match = re.search(pattern, page_html)
    if match is None:
        print "this emoji has only one page!!!"
        return page_link_list
    page_html_content = match.groups(1)[0]
    pattern = re.compile(r'<a href="(.*?)">(\d+)</a>', re.S)
    page_list = re.findall(pattern, page_html_content)
    if page_list is None:
        print "get emoji page list error!!"
    else:
        for item in page_list:
            page_link = link + item[0][2:]
            page_link_list.append(page_link)
        return page_link_list


# 获得每一类颜文字表情的链接
myurl = "http://www.yanwenzi.com/"
page_html = get_html_content(myurl)
emoji_category_dict = {}
pattern = re.compile(r'<div class="tabs" id="tabs">.*?<ul class="nav" id="nav">(.*?)</ul>.*?</div>', re.S)
match = re.search(pattern, page_html)
category_html = None
if match is None:
    print "can't find category html content"
else:
    category_html = match.groups(1)[0]
    print category_html
pattern = re.compile(r'<li><a href="(.*?)">(.*?)</a></li>', re.S)
emoji_category_list = re.findall(pattern, category_html)
if emoji_category_list is None:
    print "not find emoji category"
else:
    for item in emoji_category_list:
        category_name = item[1]
        category_link = item[0]
        if "active" in category_link:
            category_link = category_link.split('"')[0]
        category_link = myurl + category_link[1:]
        if category_name not in emoji_category_dict.keys():
            emoji_category_dict[category_name] = category_link
            print category_name, u"\t", category_link, u"\n"

# 接下来分链接去获得表情信息
with codecs.open("emoji-all.txt", "wb", "utf-8") as all_output_file:
    for category, link in emoji_category_dict.items():
        page_link_list = get_emoji_page_link(link)
        print page_link_list
        # 对每一页的表情信息进行提取
        emoji_dict = {}
        file_name = category + ".txt"
        emoji_count = 0
        with codecs.open(file_name, "wb", "utf-8") as output_file:
            for page_link in page_link_list:
                page_html = get_html_content(page_link)
                pattern = re.compile(r'<li>.*?<p>(.*?)</p>.*?<div>(.*?)</div>.*?</li>', re.S)
                emoji_list = re.findall(pattern, page_html)
                for emoji in emoji_list:
                    emoji_count += 1
                    emoji_pic = emoji[0]
                    emoji_name = emoji[1]
                    if emoji_name in emoji_dict.keys():
                        emoji_dict[emoji_name].add(emoji_pic)
                    else:
                        emoji_dict[emoji_name] = set([emoji_pic])
            print category, u"\t", str(emoji_count)
            # 收集完成一个类别的信息之后，将类别信息写入文件中
            for emoji_name, emoji_pic_set in emoji_dict.items():
                for emoji_pic in emoji_pic_set:
                    output_file.write(emoji_pic + u"\t" + emoji_name + u"\n")
                    all_output_file.write(emoji_pic + u"\t" + emoji_name + u"\n")
