### 说明
1. 用于存放本地弹幕txt文件的处理结果，文件名称命名规律为cid-seg-result.txt。
2. 文件内容是以json格式存储的，是wordsegment模块下BarrageSeg类实例列表的json数据。是通过wordsegment模块下wordseg.py文件中的save_segment_barrages(save_file_path, barrage_seg_list)函数写入的。
