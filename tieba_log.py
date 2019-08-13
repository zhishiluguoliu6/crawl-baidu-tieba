import csv,os,time,codecs,json

'''存放各种所需工具的py文件
    creat_dir：创建所需文件夹
    Log_one_TieBa：爬取【贴吧】结束时记录
    Log_one_TieZi：爬取【帖子】结束时记录
    Log_Large_TieZi：爬取[贴吧]时，当前帖子页数>100，记录下该帖子
    Open_csv：      csv文件写入
    Open_json：     json文件读取、写入等
    Crawling_item_counts：记录理论要爬取item数目
    Record_Crawl：        记录返回item的信息(标题、发帖人等)
    
'''

###=========输入初始时间，返回格式化后(时分秒)的初始、结束、耗时=======#
def log_time(start_time):
    end_time = time.time()
    # 花费时间
    Total_time = end_time - start_time
    m, s = divmod(Total_time, 60)
    h, m = divmod(m, 60)
    elapsed_time = '%d时:%02d分:%02d秒' % (h, m, s)
    # 格式化实际时间
    start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time))
    end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time))
    return start_time,end_time,elapsed_time
###=========输入初始时间，返回格式化后(时分秒)的初始、结束、耗时=======#


###=========需要用上的文件夹，提前创建=======#
def creat_dir():
    dirs=['爬取某个贴吧记录','爬取单个帖子记录','爬取进度详情']
    for one in dirs:
        if os.path.exists(one) is False:
            os.mkdir(one)
creat_dir()
###=========需要用上的文件夹，提前创建========#


###=========爬取【贴吧】时用的log函数========#
class Log_one_TieBa:
    '''实例化时(open_spider)，创建对应的csv文件，写入表头，并记录当前时间
       爬虫结束时，调用log，把这次的爬取信息写入csv文件，并且写入到the_spider_counts，【进度详情】窗口结束时调用'''
    def __init__(self, ):
        #锁定每次爬取保存记录的文件
        self.log_path = r'爬取某个贴吧记录/spider_TieBa.csv'
        if not os.path.isfile(self.log_path):  # 不存文件就创建并写入表头
            header= ['贴吧名字', '页数范围', '理论爬取帖子数','实际爬取帖子数','返回item数量','开始时间', '结束时间', '总花费时间']
            Open_csv(self.log_path).rewrite(header) #写入方式是 'w'

        self.start_time = time.time()

    def log(self,tieba_name, page_range,tiezi_count,actual_count,items_count):
        start_time, end_time, elapsed_time=log_time(self.start_time)

        data=[tieba_name,page_range,tiezi_count,actual_count,items_count,start_time, end_time, elapsed_time]
        Open_csv(self.log_path).add(data)    #写入方式是 ‘a'

        ## #爬虫结束时，调用的结束text
        end_text='此次爬取的贴吧是:【%s】，页数:%s，实际爬取帖子数:%s，耗时:%s'%\
                 (tieba_name,page_range,actual_count,elapsed_time)
        Open_json(r'爬取进度详情/the_spider_counts.json').add(end_text)
###=========爬取【贴吧】时用的log函数========#


###=========爬取【帖子】时用的log函数========#
class Log_one_TieZi:
    '''实例化时(open_spider)，创建对应的csv文件，写入表头，并记录当前时间
       爬虫结束时，调用log，把这次的爬取信息写入csv文件，并且写入到the_spider_counts，【进度详情】窗口结束时调用'''
    def __init__(self):
        # 锁定每次爬取保存记录的文件
        self.log_path = r'爬取单个帖子记录/spider_TieZi.csv'
        if not os.path.isfile(self.log_path):  # 不存文件就创建并写入表头
            header=['贴吧名字', '标题', '发帖人','帖子编号','页数', '爬取页数范围','理论item数','实际item数',
                     '开始时间', '结束时间', '总花费时间']
            Open_csv(self.log_path).rewrite(header)#写入方式是 'w'

        self.start_time = time.time()

    def log(self,kw,tiezi_info,page_range,item_counts,return_items_count):
        start_time, end_time, elapsed_time = log_time(self.start_time)

        data=(kw, tiezi_info['title'],tiezi_info['author'] ,tiezi_info['tid'] ,tiezi_info['pages'],
                 page_range,item_counts,return_items_count,start_time, end_time, elapsed_time)
        Open_csv(self.log_path).add(data)#写入方式是 ‘a'

        #爬虫结束时，调用的结束text
        end_text = '此次爬取的帖子tid为:【%s】，标题:%s，所在贴吧:%s，页数:%s，item数量:%s，耗时:%s' % \
                   (tiezi_info['tid'],tiezi_info['title'],kw, page_range, return_items_count, elapsed_time)
        Open_json(r'爬取进度详情/the_spider_counts.json').add(end_text)
###=========爬取【帖子】时用的log函数========#


###=========爬取【贴吧】发现当前帖子页数>100时调用，记录========#
class Log_Large_TieZi:
    def __init__(self):
        self.log_path = r'爬取某个贴吧记录/Large_TieZi.csv'
    def log(self,kw,the_tiezi):
        # 创建每次爬取保存记录的文件
        if not os.path.isfile(self.log_path):  # 不存文件就写入表头
            header= ['贴吧名字', '标题', '发帖人','帖子编号','回复数量','页数', '最后回复时间', '最后回复人']
            Open_csv(self.log_path).rewrite(header)

        data=(kw, the_tiezi['title'], the_tiezi['author'], the_tiezi['tid'], the_tiezi['reply_num'], the_tiezi['pages'],
         the_tiezi['last_reply_time'], the_tiezi['last_reply_author'])
        Open_csv(self.log_path).add(data)
###=========爬取【贴吧】发现当前帖子页数>100时调用，记录========#


###=======================自写的csv包，====================#
#方法有: rewrite创建文件重写内容；add添加新的一行
class Open_csv():
    '''只适用于以excel格式写入csv文件'''
    def __init__(self,file):
        self.file=file

    def rewrite(self,data):
        with open(self.file, 'w', encoding='utf-8', newline='') as f:  # 爬取贴吧日志 写入具体内容
            csvwriter = csv.writer(f, dialect="excel")
            csvwriter.writerow(data)

    def add(self,data):
        with open(self.file, 'a', encoding='utf-8', newline='') as f:  # 爬取贴吧日志 写入具体内容
            csvwriter = csv.writer(f, dialect="excel")
            csvwriter.writerow(data)
###=================自写的csv包================#

###=======================自写的json包=====================#
'''方法有：
        read 返回文件的所有内容，为list
        rewrite 创建文件重写内容
        add     添加新的一行
        clear 清空所有内容'''
class Open_json():
    '''只适用于json文件，读取read，写入/覆盖rewrite,添加新的行'''
    def __init__(self,file):
        self.file=file

    def read(self):
        with codecs.open(self.file, 'r', encoding='utf-8') as f:
            data=[json.loads(line) for line in f.readlines()]
        return data

    def rewrite(self,data):
        with codecs.open(self.file, 'w', encoding='utf-8') as f:
            line = json.dumps(data, ensure_ascii=False)+"\n"
            f.write(line)

    def add(self,data):
        with codecs.open(self.file, 'a', encoding='utf-8') as f:
            line = json.dumps(data, ensure_ascii=False)+"\n"
            f.write(line)
    def clear(self):
        a = open(self.file, 'w')
        a.close()
###=======================自写的json包=====================#


###===============记录当前 理论爬取item的数量，用在进度条上================#
class Crawling_item_counts():
    '''初始item数设为50，  调用update_items更新数量(初次调用时需-50)'''
    def __init__(self,file_path):
        self.file=Open_json(file_path)
        self.file.rewrite(50)

    def update_items(self,count):
        old_count=self.file.read()[0]
        old_count+=count
        self.file.rewrite(old_count)
###===============记录当前 理论爬取item的数量，用在进度条上================#


###===============记录爬取完毕 返回的item信息，================#
#写入到文件，【进度详情】tree再调用显示
class Record_Crawl():
    def __init__(self,file_path):
        self.file=Open_json(file_path)
        self.file.clear()

    def tiezi_info(self,the_tiezi,situation=None):
        '''实际记录其爬取记录的帖子情况有3种
            1.被删：①帖子没进去第一页就被删；②再一次进入第一页被删
            2.帖子爬过，没有变动
            3.爬完了返回item'''
        #爬完的帖子是没有设定situation的，而且有post_list
        if situation==None:
            start_page=the_tiezi['post_list'][0]['page']
            end_page = the_tiezi['post_list'][-1]['page']
            situation='此次爬取的页数是：% s~ %s'%(start_page,end_page)
            #被删/爬过的帖子，是没有post_list的，所以删掉
            the_tiezi.pop('post_list')

        #补全帖子的信息
        the_tiezi.update({'situation':situation})
        #写入文件
        self.file.add(the_tiezi)
###===============记录爬取完毕 返回的item信息，================#
