#!/usr/bin/env python2.7
# -*- coding:utf-8 -*-

"""
    对输出的七维情感值信息进行标准化。
"""

import codecs

from scipy import spatial
from sklearn.metrics.pairwise import cosine_similarity


def normalize_emotion_value(file_path):
    with codecs.open(file_path + '.normolize', 'wb', 'utf-8') as output_file:
        with codecs.open(file_path, 'rb', 'utf-8') as input_file:
            for line in input_file:
                info = line.strip().split('\t')[0: -1]

                start_time = str(int(info[0]) * 10 / 60) + ":" + str(int(info[0]) * 10 % 60)
                end_time = str(int(info[1]) * 10 / 60) + ":" + str(int(info[1]) * 10 % 60)

                emotion_list = [float(item) for item in line.strip().split('\t')[-1].split(', ')]

                sum_num = sum(emotion_list)
                for index in range(len(emotion_list)):
                    emotion_list[index] = emotion_list[index] / sum_num
                data = info + [start_time, end_time] + [", ".join([str(item) for item in emotion_list])]
                # print data
                output_file.write(u'\t'.join(data) + u'\n')


if __name__ == "__main__":
    # normalize_emotion_value("../2171229-emotion-result-lda.txt")
    # normalize_emotion_value("../2065063-emotion-result.txt")
    vector_first = [0.40943629091, 0.134169008639, 0.0, 0.155016282286, 0.0, 0.301378418165, 0.0]
    vector_second = [0.4, 0, 0, 0.3, 0, 0.3, 0]

    cosine_similarity(vector_first, vector_second)
    result = 1 - spatial.distance.cosine(vector_first, vector_second)

    # sum = 0
    # for index in range(len(vector_first)):
    #     sum += (abs(vector_first[index] - vector_second[index]))
    # sum /= 7
    print result
