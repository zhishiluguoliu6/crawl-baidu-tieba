
import os,multiprocessing,time,logging
from tkinter import *
from tkinter import messagebox
from tieba_log import Open_json #自写的打开json文件
from my_tk import My_tk         #自写的tk界面

#设定log的输出设置
logging.basicConfig(level=logging.WARNING,
                    format='asctime:        %(asctime)s \n'  # 时间
                           'bug_line:       line:%(lineno)d \n'  # 文件名_行号
                           'level:          %(levelname)s \n'  # log级别
                           'message:        %(message)s \n',  # log信息
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='日志.log',  # sys.path[1]获取当前的工作路径
                    filemode='a')  # 如果模式为'a'，则为续写（不会抹掉之前的log）


#用以启动爬虫
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from tieba.spiders.one_tieba_spider import One_tiebaSpider
from tieba.spiders.one_tiezi_spider import One_tieziSpider

'''
本scrapy的运行顺序：
》初始的begin.py   ，打开tk界面，输入各个参数，保存在config文件，点击运行
》先进入pipeleines.py，调用open_spider，获取config里的数据，设定spider各个参数
》回到spider.py，正式开始运行parse
》程序结束时，再调用pipeleines.py的close_spider，log此次爬取日志'''

#继承my_tk，完善run函数
class strat_scrapy(My_tk):
    def __init__(self,tk):
        super(strat_scrapy, self).__init__(tk)#继承已经设定好的tkinter界面
        self.spider_pid=11111               #设定初始pid(没什么卵用，不让程序报错而已)

    #点击【爬取】按钮调用的函数
    def run(self):
        # 对输入的参数进行筛查检测，填好了才能启动爬虫
        if self.to_assert():
            the_args=self.to_assert()
            print('设定了爬取条件：',the_args)
            if os.path.exists('爬虫日志'):  # 如果存在日志，删掉
                os.remove('爬虫日志')
            super().run()  #调用原先my_tk里的方法
            # 启动爬虫！
            self.start()

            self.display_text()#弹出进度窗口
            self.root.update() #刷新tk窗口
            self.start_time = time.time()  # 启动时的时间戳
            time.sleep(4)
            self.crawling_window.show_it()#tk的进度详情窗口，显示爬取进度

    def to_assert(self):
        '''对爬虫需要用的参数 进行判断整理，没问题时存放到list，4个参数齐全时，保存到config文件，然后返回list
            否则弹出窗口，提示 参数可能有一个有问题'''
        the_args=[]
        # 排序输入的页数
        the_pages = sorted([abs(int(self.beginvar.get())), abs(int(self.endvar.get()))])
        the_args.append(the_pages)

        #爬取的贴吧名不为空
        if self.tiebavar.get()!='':
            the_args.append(self.tiebavar.get())

        #保存路径不存在，用回默认路径
        if os.path.exists(self.pathvar.get()):
            the_args.append(self.pathvar.get())

        #选择爬取单个帖子的话，Tid=True，此时输入的tid没问题，就放进the_args
        #如果是爬取贴吧，tid为None
        if self.Tid:#762788222
            if isinstance(self.tidvar.get(), int) and self.tidvar.get()!=0 \
                    and len(str(abs(self.tidvar.get())))>8:
                the_args.append(self.tidvar.get())
        else:
            the_args.append('None') 

        #4个参数齐全，就保存 爬取信息 到config文件内
        if len(the_args)>3:
            kw = ['the_pages', 'tieba_name', 'save_path', 'tid']
            config = dict(zip(kw, the_args))
            config_file = Open_json('config')
            config_file.rewrite(config)
            return the_args
        else:
            messagebox.showerror("爬取条件有问题", "请正确输入贴吧名/保存路径/tid！！")
            


    def start(self):
        '''多进程启动sracpy'''
        if self.Tid:
            spider=One_tieziSpider
        else:
            spider =One_tiebaSpider
        self.the_scrapy = multiprocessing.Process(target=start_crawl,args=(spider,))
        self.the_scrapy.start()
        self.spider_pid=self.the_scrapy.pid  #设定pid，爬取窗口用以判断程序是否还在运行



def start_crawl(spider):
    '''根据爬取贴吧/帖子 启动不同的scrapy'''
    process = CrawlerProcess(get_project_settings())
    process.crawl(spider)
    process.start()

def begin():
    #启动tk
    root=Tk()
    strat_scrapy(root)
    root.mainloop()

if __name__ == '__main__':
    # pyinstaller 打包多进程得有下面代码
    multiprocessing.freeze_support()
    begin()



