#!/bin/bash

CURDIR=$(cd `dirname $0`; pwd)
BARRAGE_ANALYSIS_HOME=$(cd "${CURDIR}/../.."; pwd)
SPIDER_HOME=${BARRAGE_ANALYSIS_HOME}/spider
DATA_HOME=${BARRAGE_ANALYSIS_HOME}/data
SPIDER_LOG_HOME=${SPIDER_HOME}/log
VIDEO_LIST_FILE=${SPIDER_HOME}/video-list.txt
LOCAL_BARRAGE_HOME=${DATA_HOME}/local

if [ ! -d ${SPIDER_LOG_HOME} ]; then
  mkdir -p ${SPIDER_LOG_HOME}
fi

if [ ! -d ${LOCAL_BARRAGE_HOME} ]; then
  mkdir -p ${LOCAL_BARRAGE_HOME}
fi

BILI_SPIDER_LOG=${SPIDER_LOG_HOME}/bili-spider.log

# 将python项目根目录赋值PYTHONPATH，否则会报Import Error错误。
export PYTHONPATH=${BARRAGE_ANALYSIS_HOME}
PYTHON=`which python`
# 获得b站视频信息的弹幕列表。
VIDEO_ARGS=`cat ${VIDEO_LIST_FILE} | awk -F "\t" 'BEGIN{args="";} {args=args" -u "$0;} END{print substr(args, 1);}'`
echo ${VIDEO_ARGS}
# 运行b站的爬虫脚本
${PYTHON} ${SPIDER_HOME}/bilibilispider.py ${VIDEO_ARGS} >> ${BILI_SPIDER_LOG} 2>&1
