#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import os

"""
文件存取的操作，将弹幕数据写入本地文件中。
"""

__author__ = "htwxujian@gmail.com"


class FileUtil(object):
    # 如果路径存在，并且是一个文件夹，那么返回true；否则返回false。
    @staticmethod
    def is_dir_exists(dir_path):
        if os.path.isdir(dir_path):
            return True
        else:
            return False

    # 如果路径存在，并且是一个文件，那么返回true；否则返回false。
    @staticmethod
    def is_file_exists(file_path):
        if os.path.isfile(file_path):
            return True
        else:
            return False

    # 如果文件夹不存在，那么创建该文件夹，路径链中的文件夹若不存在也将会一同被创建。
    @staticmethod
    def create_dir_if_not_exist(dir_path):
        if FileUtil.is_dir_exists(dir_path) is False:
            os.makedirs(dir_path)

    # 获得当前脚本的运行目录。
    @staticmethod
    def _get_cur_dir():
        return os.path.dirname(os.path.realpath(__file__))

    # 获得项目的根路径。
    @staticmethod
    def get_project_root_path():
        (project_root_path, util_path) = os.path.split(FileUtil._get_cur_dir())
        return project_root_path

    # 获得本地数据目录。
    @staticmethod
    def get_local_data_dir():
        base_path = FileUtil.get_project_root_path()
        local_data_path = os.path.join(base_path, "data", "local")
        FileUtil.create_dir_if_not_exist(local_data_path)
        return local_data_path

    # 获得弹幕文件的路径。
    @staticmethod
    def get_barrage_file_path(cid):
        return os.path.join(FileUtil.get_local_data_dir(), cid + ".txt")

    # 分块读取文件的内容。
    @staticmethod
    def __read_file_by_block(input_file, buffer_size=65536):
        while True:
            nb = input_file.read(buffer_size)
            if not nb:
                break
            yield nb

    # 获得当前文件的总行数。
    @staticmethod
    def get_file_line_count(file_path):
        if not FileUtil.is_file_exists(file_path):
            return False
        with open(file_path, "rb") as input_file:
            # 返回一个迭代器，对迭代器中的数据汇总。
            return sum(line.count("\n") for line in FileUtil.__read_file_by_block(input_file))

    # 获得文件最后几行的内容。
    @staticmethod
    def get_file_last_n_line_content(file_path, last_n=5, buffer_size=1024):
        with open(file_path, "rb") as input_file:
            seek_times = 0
            line_count = 0
            # 文件指针首先调到文件末尾。
            input_file.seek(0, 2)
            # 从文件末尾向前seek，统计末尾内容的换行符数量。
            while input_file.tell() > 0 and line_count < (last_n + 1):
                seek_times += 1
                input_file.seek(-seek_times * buffer_size, 2)
                content = input_file.read(seek_times * buffer_size)
                input_file.seek(-seek_times * buffer_size, 2)
                line_count = content.count("\n")
            content = input_file.read(seek_times * buffer_size)
        # 得到文本的最后几行内容。
        last_lines = [line for line in content.split("\n") if line != ""]
        if len(last_lines) > last_n:
            last_lines = last_lines[len(last_lines) - last_n: len(last_lines)]
        for index in xrange(0, len(last_lines)):
            last_lines[index] = last_lines[index].decode("utf-8", "ignore")
        return last_lines


if __name__ == "__main__":
    print FileUtil.get_local_data_dir()
