#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from analysis.model.barrageinfo import BarrageInfo
import numpy as np
import analysis.similarity as sim
import logging
from util.fileutil import FileUtil
import os
import codecs

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')


class SimMatrix(object):

    # 根据时间窗口内的词频信息获得每一个时间窗口对应的jaccard相似度矩阵。
    # 将生成的矩阵写入结果文件中。
    @classmethod
    def gen_jaccard_sim_matrix_by_word_frequency(cls, time_window_list):
        jaccard_sim_matrix_list = []
        for time_window in time_window_list:
            logging.info(u"正在生成第 " + str(time_window.time_window_index) + u" 个相似度矩阵")
            sender_id_list = time_window.gen_all_barrage_sender_id()  # 获得该时间窗口下，所有发送弹幕的用户id。
            barrage_sender_count = BarrageInfo.get_barrage_sender_count()
            sim_matrix = np.zeros((barrage_sender_count, barrage_sender_count))
            for sender_id1 in sender_id_list:
                sender_id1_index = BarrageInfo.get_sender_id_index(sender_id1)
                word_frequency_dict1 = time_window.user_word_frequency_dict[sender_id1]
                for sender_id2 in sender_id_list:
                    sender_id2_index = BarrageInfo.get_sender_id_index(sender_id2)
                    word_frequency_dict2 = time_window.user_word_frequency_dict[sender_id2]
                    jaccard_sim = sim.calc_jaccard_similarity_by_word_frequency(word_frequency_dict1,
                                                                                word_frequency_dict2)
                    sim_matrix[sender_id1_index, sender_id2_index] = jaccard_sim
            jaccard_sim_matrix_list.append(sim_matrix)
            cls.__save_similarity_matrix_to_local(sim_matrix, time_window.time_window_index)

    # 将生成的相似度矩阵（相似度矩阵列表）写入项目的矩阵存储路径。
    # 参数：sim_matrix 生成的相似度矩阵
    #      time_window_index 该相似度矩阵对应的时间窗口下标
    @classmethod
    def __save_similarity_matrix_to_local(cls, sim_matrix, time_window_index):
            matrix_file_name = os.path.join(FileUtil.get_similarity_matrix_dir(),
                                            "matrix-" + str(time_window_index) + ".txt")
            with codecs.open(matrix_file_name, "wb", "utf-8") as output_file:
                np.savetxt(fname=output_file, X=sim_matrix, fmt="%.5f", delimiter="\t", newline="\n")
