#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from db.dbutil import DBUtil
from db.model.video import Video

"""
对movie数据库表进行存取操作
"""

__author__ = "htwxujian@gmail.com"


class VideoDao(DBUtil):
    # 初始化数据库的相关信息。
    DBUtil.init_db()

    @staticmethod
    def add_video(cid, title, tags, aid, url):
        print "video info before"
        print cid, title, tags, aid, url
        video_info = Video(cid=cid, title=title, tags=tags, aid=aid, url=url)
        print "video info after"
        session = DBUtil.open_session()
        try:
            session.add(video_info)
            session.commit()
            return True
        except Exception as e:
            print e
            session.rollback()
            return False
        finally:
            DBUtil.close_session(session)

    @staticmethod
    def get_video_by_cid(cid):
        if cid is None:
            return None
        session = DBUtil.open_session()
        # 根据主键查询
        video_query = session.query(Video).filter(Video.cid == cid)
        if video_query.count() <= 0:
            DBUtil.close_session(session)
            return None
        else:
            video_info = video_query.one()
            DBUtil.close_session(session)
            return video_info


if __name__ == "__main__":
    video = VideoDao.get_video_by_cid("6684033")
    print video.title
