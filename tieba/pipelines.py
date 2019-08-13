# -*- coding: utf-8 -*-
import json,os,shutil,scrapy,codecs
from tieba_log import Log_one_TieBa,Log_one_TieZi ,Open_json #用来记录每次爬取信息的py文件



'''
操作步骤：
》open_spider设定多个参数
    》从"config"，获取输入的信息，设定贴吧、存储路径、
    》根据当前是哪个spider，设定页数范围、tid，再实例化Log
    
》返回item时，根据当前是哪个spider，分别保存json
》结束时调用close_spider，把这次爬取的数量时间等log日志'''

class TiebaPipeline(object):

    def process_item(self, item, spider):
        '''保存返回的item，根据spider分别处理'''
        #爬某个贴吧，返回的item都放在各自以tid命名的json文件
        if spider.name == 'one_tieba':
            tid = item['tid']
            path=spider.path + os.sep + str(tid) + '.json'
            with codecs.open(path, 'a', encoding='utf-8') as f:
                line = json.dumps(item, ensure_ascii=False) + "\n"
                f.write(line)

        #爬单个帖子，根据item里面的file_name保存(每100页为一个文件)
        elif spider.name == 'one_tiezi':
            the_tiezi = dict(item)
            path=the_tiezi.pop('file_name')
            with codecs.open(path, 'a', encoding='utf-8') as f:#file_path在spider里设定的
                line = json.dumps(the_tiezi, ensure_ascii=False) + "\n"
                f.write(line)

    def open_spider(self,spider):
        '''设定贴吧名、存储路径、页数等多个数据，传入到spider进行爬取
            实例化log，结束时调用'''

        print('现在运行的spider是：',spider.name)
        config_file=Open_json('config')
        config_info=config_file.read()[0]

        spider.kw=config_info['tieba_name']
        spider.dir_path=config_info['save_path']

        if spider.name=='one_tieba':
            spider.start_kw_page = config_info['the_pages'][0]
            spider.end_kw_page = config_info['the_pages'][1]
            self.Log_one_TieBa=Log_one_TieBa()
        elif spider.name == 'one_tiezi':
            spider.tid = config_info['tid']
            spider.start_tiezi_page = config_info['the_pages'][0]
            spider.end_tiezi_page = config_info['the_pages'][1]
            self.Log_one_TieZi=Log_one_TieZi()


    def close_spider(self, spider):
        '''爬取结束时，log其处理记录'''

        #爬取贴吧的帖子时，记录其实际爬取数量、被删数量等
        if spider.name == 'one_tieba':
            tiezi_count = spider.tiezi_count  # 理论爬取帖子总数
            del_count = spider.del_count  # 帖子第一页发现被删 总数
            unchanged_count = spider.unchanged_count  # 没变动帖子数
            actual_count = tiezi_count - del_count - unchanged_count  # 实际爬取的帖子总数
            
            items_count = spider.return_count  # 把页数分配后(每十页)，实际返回的item总数
            print('被删帖子数:%d，没变动帖子数:%d' % (del_count, unchanged_count))

            page_range = '第%d~%d页' % (spider.start_kw_page,spider.end_kw_page)
            self.Log_one_TieBa.log(spider.kw,page_range,tiezi_count,actual_count,items_count)

        #爬取单个帖子时，记录其信息
        elif spider.name=='one_tiezi':
            page_range= '第%d~%d页' % (spider.start_tiezi_page, spider.end_tiezi_page)
            self.Log_one_TieZi.log(spider.kw,spider.tiezi_info,page_range,spider.item_counts,spider.return_items_count)

