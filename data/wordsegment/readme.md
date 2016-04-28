### cid-seg-result.json

1. 文件内容是以json格式存储的，是wordsegment模块下BarrageSeg类实例列表的json数据。是通过wordsegment模块下wordseg.py文件中的save_segment_barrages(save_file_path, barrage_seg_list)函数写入的。
2. 该文件种的数据供后来加载 切词结果 使用。


### test-cid-seg-result.txt
 
1. 该文件是一个弹幕文件的切词结果（已经经过停用词处理、emoji表情替换，弹幕常用词替换）用于查看弹幕的切词效果。