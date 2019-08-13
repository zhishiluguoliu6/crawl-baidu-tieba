# crawl-baidu-tieba
本项目是tkinter写出界面，基于scrapy爬虫，爬取指定贴吧/某个帖子，能通过treeview显示爬取进度，并且可以搜索关键字、发帖人等，并且根据发帖内容，生成词云图。 还可以将此项目打包成exe，直接运行

  
爬取指定贴吧思路：  
1.进入该贴吧第N页-第M页，获取所有帖子的初始信息  
2.分别进入每个帖子，先爬取楼层回复  
3.根据tid（帖子id）、pid（楼层id），爬取各自的楼内楼  
4.楼内楼爬完了，返回item，以tid为名保存json  
难点：  
如果该帖子爬过了，那是直接重新爬取覆盖旧文件吗？如果该帖子的某些内容被删了，再爬取没有了，不是可惜吗？或者该帖子没有新回复，不是浪费时间吗?  
--这部分真的折腾，我现实获取旧文件的内容，作为底子，然后爬取帖子，一旦是新楼层，就添加，楼层爬完后，再爬各自的楼内楼，一旦新的回复，就添加到对应的楼层  
（具体见 贴吧思路图片，有很详细的步骤）  
  
爬取某个帖子思路：  
前面爬取整个贴吧设定了最多只爬帖子的前100页，所以才有爬取单个帖子的spider。  
此爬虫根据你要爬取的页数范围后，先是将页数划分范围(每100页保存为一个文件）  
注：懒得再提取旧文件进行爬取了  
  
  
本scrapy运行过程：  
》初始的begin.py   ，打开tk界面，输入各个参数，保存在config文件，点击运行  
》先进入pipeleines.py，调用open_spider，获取config里的数据，设定spider各个参数  
》回到spider.py，正式开始运行parse  
》程序结束时，再调用pipeleines.py的close_spider，log此次爬取日志  
  
  
  
  
运行爬虫自动创建的文件：  
config：tk界面填入的参数 贴吧名、页数范围等数据所存放的文件  
  
爬取进度详情(文件夹)  
	/the_spider_counts.json：记录此次爬取的理论item数量  
        /TieBa_info.json：爬取贴吧时，记录所有帖子标题、发帖人等信息，用在treeview进度条上显示详情  
	/TieZi_info.json：爬取单个帖子时，每爬完10页返回item时，记录其页数，用在treeview进度条上显示详情  
  
  
爬取某个贴吧记录(文件夹)  
	/spider_TieBa.csv：爬取任务结束时，记录此次爬取的贴吧名、页数范围、帖子总数等  
	/Large_TieZi.csv：爬取过程中，发现某个帖子页数超过100(只记录前100页），就会把该帖子的信息记录下来  
  
  
爬取单个帖子记录(文件夹)  
	/spider_tiezi.csv：爬取任务结束时，记录此次爬取帖子的页数范围、帖子总数、花费时间等  
  
日志：只显示warning以上级别的信息  
  
  
自写的py文件：  
begin.py：总开关，调用my_tk.py里的tk代码，启动tk界面，输入参数后，运行scrapy  
my_tk.py：tkinter代码，包含爬取界面跟进度界面  
search.py：tk代码，搜索页面  
find_path：获取 搜索元素的路径(search调用)  
  
tieba_log.py：存放各种所需工具的py文件  
    creat_dir：创建所需文件夹  
    Log_one_TieBa：爬取【贴吧】结束时记录  
    Log_one_TieZi：爬取【帖子】结束时记录  
    Log_Large_TieZi：爬取[贴吧]时，当前帖子页数>100，记录下该帖子  
    Open_csv：      csv文件写入  
    Open_json：     json文件读取、写入等  
    Crawling_item_counts：记录理论要爬取item数目  
    Record_Crawl：        记录返回item的信息(标题、发帖人等)  
  
  
爬取结果：  
保存文件结构：  
贴吧(文件夹)  
	/贴吧名1(文件夹)  
		/旧帖子(文件夹)  
			/帖子tid.json  
		/帖子1.json  
		/帖子2.json  
		/····  
	/贴吧名2  
	/···  
注：每个帖子默认最多爬100页，每10页作为一个dict保存到json文件中，每个文件最多10行dict  
  
dict的格式如下：  
tiezi={'title':    '标题',  
       'author':   '发帖人',  
       'tid':      '帖子的编号',  
       'reply_num':'回复数量',  
       'last_reply_time':'最后回复时间',  
       'last_reply_author':'最后回复人',  
       'pages':          '共多少页',  
   #帖子里的具体内容，每一层楼  
       'post_list': ['1楼',  
                     '2楼',  
                     '3楼',  
                     '4楼',  
                     '.....'  
                     ]  
   }  
  
#每一层楼的list  
post_list=[ #1楼  
                {  
                 'page':      '所在页数',  
                 'author':    '发帖人',  
                 'floor':     '楼层',  
                 'time':'回复时间',  
                 'pid':       '该楼层的编号',  
                 'content':   '回帖内容(包含了文字、图片、自定义表情)',  
                 'voice':     '如果有语音的话，就有',  
                 'comment_num':'楼内楼回复数量',  
                 'comment_list':    #如果上面不为0，就有  
                               ['回复1',  
                                '回复2',  
                                '回复3']  
                 },  
                 {'2楼'},  
                 {'3楼'}  
                ]  
#楼内楼  
comment_list=[#回复1  
         {'page':      '所在楼内楼页数',  
          'author':    '发帖人',  
          'time':'回复时间',  
          'pid':       '该楼层的编号',  
          'content':   '回帖内容(包含了文字)',  
          'voice':     '如果有语音的话，就有',  
          },  
  
          {'回复2'},  
          {'回复3'},  
        ]  
  
  
打包为exe文件：  
  
所需配置文件：    
scrapy(文件夹)  
	/mime.types  
	/VERSION  
scrapy.cfg  
  
begin.spec   
  
wordcloud  (文件夹)：  
	/stopwords  
	/simsun.ttc字体文件  
  
  
注：  
scrapy打包是很费劲的，启动代码不能用常规的execute("scrapy crawl XX".split())，得用scrapy的源代码CrawlerProcess(get_project_settings())  
还得scrapy配置文件，本次还有我写的几个py文件，如果用常规的打包方法，显得很笨拙，需要自己手动复制文件，所以我就用了spec来打包，通过data设定好要转移的文件，还设置为不需要控制台  
  
最后只需输入命令：pyinstaller begin.spec即可  
  
  
注意几点：  
1.tk运行时，按动按钮，如果对于的回调函数没有执行完毕，整个程序都会卡住，所以我用了多进程运行scrapy，这样的话，就可以通过爬取进度tk看到爬取进度，而且还能中断程序(暂停做不到）  
2.楼内楼的爬取，最多只有100页  
3.搜索界面里的生成词云图，注意显示的词语数目、大小，还有字体文件  
4.打包时，wordcloud会报错，需要在生成后的wordcloud文件夹里，复制stopwords这个文件进去，我直接在spec文件里的data操作了  
5.scrapy没有设定ip跟UA，爬取指定贴吧的一页起码5分钟，如果想加快速度，得自己搞随机ip跟UA


详细可见我的csdn专栏：https://blog.csdn.net/qq_38282706/column/info/41793
#![image](https://github.com/zhishiluguoliu6/crawl-baidu-tieba/blob/master/%E5%9B%BE%E7%89%87/%E5%BC%80%E5%A7%8B.jpg)
#![image](https://github.com/zhishiluguoliu6/crawl-baidu-tieba/blob/master/%E5%9B%BE%E7%89%87/%E8%B4%B4%E5%90%A7%E7%95%8C%E9%9D%A2.jpg)
#![image](https://github.com/zhishiluguoliu6/crawl-baidu-tieba/blob/master/%E5%9B%BE%E7%89%87/%E5%B8%96%E5%AD%90%E7%95%8C%E9%9D%A2.jpg)
#![image](https://github.com/zhishiluguoliu6/crawl-baidu-tieba/blob/master/%E5%9B%BE%E7%89%87/%E7%88%AC%E5%8F%96%E8%BF%9B%E5%BA%A6.jpg)
#![image](https://github.com/zhishiluguoliu6/crawl-baidu-tieba/blob/master/%E5%9B%BE%E7%89%87/%E6%90%9C%E7%B4%A2.jpg)
#![image](https://github.com/zhishiluguoliu6/crawl-baidu-tieba/blob/master/%E5%9B%BE%E7%89%87/%E7%94%9F%E6%88%90%E8%AF%8D%E4%BA%91%E5%9B%BE.jpg)



