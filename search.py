
from tkinter import *
from tkinter.ttk import *
import tkinter.filedialog
import time,datetime,os,json,emoji,codecs,re,copy,jieba,traceback,webbrowser,logging
from find_path import Find_path#导入自己写的find_path方法
#下面是词云图要用到的
import numpy as np
from PIL import ImageTk
import PIL.Image as Image
from wordcloud import WordCloud,ImageColorGenerator
import matplotlib.pyplot as plt

'''
3个搜索函数：
search_keyword：搜索回帖内容里的某个关键字
search_author： 搜索回帖人回复过的内容
get_content:   某时间后所有的发帖内容(或全部内容) 格式：'2018-10-25'

运行过程：
》传入Search_tk，调用的部分为：搜索、保存路径/显示搜索进度、结果/插入到tree
》获取所有文件的绝对路径list(self.files)
》运行搜索函数，
》调用装饰器：1.遍历每个文件，循环每一行
             2.正式运行搜索函数的代码(上面3个)
               ——设定储存文件名(set_savefile)
               ——利用find_path，获取匹配后的所有路径
               ——筛选，补全楼层信息后，添加到post_list中
             3.将每个文件搜索的内容 保存到存储文件
             4.合并存储文件内的每一行，并且显示在tree上/生成云图

'''

class Search_tiezi(object):

    def __init__(self,Search_tk):
        self.Search_tk=Search_tk   #直接将整个搜索tk传进来
        self.search_dir=self.Search_tk.search_dir.get().strip() #搜索tk中的搜索路径
        self.save_dir=self.Search_tk.save_dir.get().strip() #搜索tk中的保存路径
        self.files=self.get_files()                         #所有帖子的路径list
        self.save_file = ''                                 #保存文件的绝对路径，在搜索函数中设定

    def get_files(self):
        '''根据存放json文件的文件夹，得到json文件的绝对地址组成的list'''
        file_list = []
        for name in os.listdir(self.search_dir):
            file_path = os.path.join(self.search_dir, name)
            if os.path.isfile(file_path):
                file_list.append(file_path)
        return file_list

    def set_savefile(self,search_type,target_word):
        '''设定保存文件路径，如果已经存在就删除'''
        tieba=os.path.split(self.search_dir)[1]
        self.save_file = self.save_dir+os.sep+'%s~%s：%s.json'%(tieba,search_type,target_word)
        self.save_file.replace(':','：')
        if os.path.exists(self.save_file):  # 返回文件名，如果存在，删掉文件
            os.remove(self.save_file)


    def save(self,data):
        '''将每条搜索结果(dict/list)写入保存文件内'''
        with codecs.open(self.save_file, 'a', encoding='utf-8') as f:
            line = json.dumps(data, ensure_ascii=False) + "\n"
            f.write(line)


    def save_insert(self):
        '''合并保存文件的每一行，并且在Search_tk显示
           PS:之前是符合条件的一行一行写入文件，现在提取文件的所有dict/list都合并到一个list，然后保存 显示
           步骤：搜索后的文件：----存在，》读取每一行，判断类型：----搜索内容：1.将每一行添加到all_data
                                                                       2.在tk的tree插入该行信息(每一行为一个帖子)
                                                          ----获取回复： 只将每一行的post_list添加到all_data
                                      》再次保存
                                      》在tk的board_text上显示搜索结果
                             ----不存在，在tk上提示没有搜索内容
            '''
        #存在搜索文件才进行合并，否则说明所有帖子中没有要搜索的内容
        if os.path.exists(self.save_file):
            all_data=[]
            with open(self.save_file, 'r', encoding='utf-8') as f:
                for one_dict in f.readlines():
                    one_tiezi=json.loads(one_dict)
                    if '搜索条件' in self.save_file:
                        all_data.append(one_tiezi)
                        self.Search_tk.tree_insert(one_tiezi)
                    elif '回帖内容' in self.save_file: #只需 回帖内容content
                        all_data+=one_tiezi['post_list']
            #先删了再保存
            os.remove(self.save_file)
            self.save(all_data)

            #搜索结束后，在label_text上显示搜索结果
            if '搜索条件' in self.save_file:
                content_num=len(self.Search_tk.tree.get_children(''))
            else:
                content_num=len(all_data)
            the_searching=os.path.split(self.save_file)[1].split('.')[0]
            self.Search_tk.board_var.set('%s——完成，共%s条回复'%(the_searching,content_num))
        else:
            self.Search_tk.board_var.set('没有符合条件的搜索结果')

###====================================装饰器，循环打开每个文件、读取每一行，再进行搜索====================###
    def read_search(search_func):
        '''装饰器，装饰3种查询方法
            步骤：----遍历所有文件：----在tk上显示搜索进度
                                  ----读取文件：----创建post_list，用以存放符合条件的楼层
                                               ----循环每一行：     》搜索每一行
                                               ----post_list不为空：》每个文件(帖子)作为一行保存到文件中
                 ----合并保存文件的每一行，并且在tk上显示出搜索结果
'''
        def wrapper(self,target_word,):
            # 循环该贴吧的所有文件
            files_num=len(self.files)
            search_num=0
            for one_file in self.files:
                search_num += 1
                label_text='搜索文件进度————%s/%s'%(search_num,files_num)
                self.Search_tk.board_var.set(label_text)
                self.Search_tk.root.update()
                with open(one_file, 'r', encoding='utf-8') as f:
                    post_list = []
                    serach_tiezi = {}
                    # 循环该文件的所有行
                    for one_dict in f.readlines():
                        the_tiezi = json.loads(one_dict)
                        serach_tiezi = {'title': the_tiezi['title'], 'author': the_tiezi['author'],
                                       'tid': the_tiezi['tid']}
                        search_func(self,target_word,the_tiezi,post_list)

                    if post_list != []:  # 该帖子内有符合条件的楼层，才会被保存
                        serach_tiezi['post_list'] = post_list
                        self.save(serach_tiezi)  # 把符合条件的search_tiezi写入保存文件

            self.save_insert()#合并保存文件的每一行，并且在tk上显示出搜索结果
        return wrapper

###====================================装饰器，循环打开每个文件、读取每一行，再进行搜索====================###


###===================================搜索回帖内容/ 搜索回帖人==========================###
    @read_search
    def search_keyword(self, target_word,the_tiezi=None,post_list=None,):
        '''输入关键字，运行find_path，获取在the_tiezi的路径后，补全楼层信息后添加到post_list中
            :param target_word: 回帖内容里的关键字
            :param the_tiezi: 帖子文件内的一行帖子内容dict
            :param post_list: 存放所有楼层的list
            :return:
                '''
        if self.save_file=='':
            self.set_savefile('搜索条件—关键字', target_word) #设定保存文件名

        a = Find_path(the_tiezi)
        all_path = a.in_value_path(target_word)  # 包含匹配，搜索内容包含关键字的路径

        self.sort_path(all_path)  # 将路径排序，保证楼内楼所在的楼层在前
        # 循环所有路径
        for one_path in all_path:
            # 提出 字典的key与列表的元素位置
            indexex = re.findall(r'\[(.*?)\]', one_path) # one_path格式：楼层--"['post_list'][2]['content']"，，楼内楼--"['post_list'][2]['comment_list'][38]['content']"
            indexex = [eval(index) for index in indexex]
            # 只保留 是回帖内容的搜索结果 路径
            if indexex[-1] == 'content'and len(indexex)>1:
                self.add_post(indexex, the_tiezi, post_list)#将路径对应的楼层/楼内楼 的发帖人、时间等信息补充完整为dict，添加到post_list

    @read_search
    def search_author(self, author, the_tiezi=None, post_list=None, ):
        '''输入回帖人昵称，运行find_path，获取在the_tiezi的路径后，补全楼层信息后添加到post_list中
        :param author: 回帖人
        :param the_tiezi: 帖子文件内的一行帖子内容dict
        :param post_list: 存放所有楼层的list
        :return:
        '''
        if self.save_file == '':
            self.set_savefile('搜索条件—发帖人', author)  # 设定保存文件名

        a = Find_path(the_tiezi)
        all_path = a.the_value_path(author) #完全匹配，搜索结果就是author的路径

        self.sort_path(all_path)  # 将路径排序，保证楼内楼所在的楼层在前
        # 循环所有路径
        for one_path in all_path:
            # 提出 字典的key与列表的元素位置
            indexex = re.findall(r'\[(.*?)\]', one_path)
            indexex = [eval(index) for index in indexex]
            # 只保留 是回帖人的搜索结果 路径
            if indexex[-1] == 'author' and len(indexex)>1:
                self.add_post(indexex, the_tiezi, post_list)  # 将路径对应的楼层/楼内楼 的发帖人、时间等信息补充完整为dict，添加到post_list


    def sort_path(self, all_path):
        '''将所有路径排序，保证楼内楼所位于的楼层排列在前
            缘由：因为在读取搜索时，返回的路径有时候顺序是打乱的，楼内楼在其所在的楼层之前，后面add_post添加楼层时就混乱，所以排序
            '''

        def sort_key(one_path, index):
            # 如果index=3，那么楼层排序key就是0，自然就在最前面
            # one_path格式：楼层--"['post_list'][2]['content']"，
            #              楼内楼--"['post_list'][2]['comment_list'][38]['content']"
            indexex = re.findall(r'\[(.*?)\]', one_path)
            indexex = [eval(index) for index in indexex]
            if len(indexex) > index:
                return indexex[index]
            else:
                return 0

        all_path.sort(key=lambda one_path: sort_key(one_path, 3))  # 先按楼内楼顺序排列，因为楼层只有3个元素，所以都在最前面
        all_path.sort(key=lambda one_path: sort_key(one_path, 1))  # 最后按楼层顺序排列


    def add_post(self, indexex, the_tiezi, post_list):
        '''根据楼层/楼内楼 的路径，获取其 回帖时间、内容、回帖人等，组成dict，添加到post_list中
           过程：1.楼层是直接添加，
                2.当是楼内楼时，判断该楼内楼所在的楼层就是post_list最后的楼层，不是的话，添加一个新的楼层，再把该楼内楼添加进去
        :param indexex: 路径，如['post_list',2,'comment_list',38,content']
        :param the_tiezi: 帖子文件内的一行帖子内容dict
        :param post_list:
        :return: 存放所有楼层的list
        保存结构：
                {贴吧名、发帖人、tid、
                'post_list':[{楼层1post，楼层2post,····}]}

                楼层post:
                          当前路径是楼层：包含的键值有
                                       {floor、page、url、author、content、time、comment_list:[]}
                                    或：{floor、page、url、                    、comment_list:[]}
                          楼内楼comment：
                                      当前路径是楼内楼，包含的键值有
                                                  {author、content、time、comment_page}
     '''

        # 锁定 当前楼层/楼内楼所在的楼层
        target_post = the_tiezi['post_list'][indexex[1]]
        url = 'http://tieba.baidu.com/p/%s?pid=%s#%s' % (
        the_tiezi['tid'], target_post['pid'], target_post['pid'])  # 该楼层指向的url

        # 此路径是楼层，直接添加到post_list
        if len(indexex) == 3:
            search_post = copy.deepcopy(target_post)
            search_post.pop('comment_num')  # 删除楼内楼数量
            search_post.pop('pid')  # 删除pid
            search_post['comment_list'] = []  # 楼内楼list先为空
            search_post['url'] = url
            post_list.append(search_post)

        # 此路径是楼内楼
        elif len(indexex) == 5:
            # 当前楼内楼所在的楼层不符合条件被收录，只存在楼内楼，那么创建该楼层
            if post_list == [] or post_list[-1]['floor'] != target_post['floor']:
                search_post = {}
                search_post['floor'] = target_post['floor']
                #search_post['page'] = target_post['page']
                search_post['comment_list'] = []  # 楼内楼list先为空
                search_post['url'] = url
                post_list.append(search_post)
            # 锁定最后一个楼层，添加楼内楼
            comment_dict = target_post['comment_list'][indexex[3]]  # 目的楼内楼
            comment_dict.pop('spid')
            post_list[-1]['comment_list'].append(comment_dict)  # 将楼内楼添加到post_list最后的楼层

###===================================搜索回帖内容/ 搜索回帖人==========================###



###===================================获取所有回复(回帖内容)==========================###
    @read_search
    def get_content(self, time='无', the_tiezi=None, content_list=None, ):
        '''输入特定时间，获取该时间点后所有的回复内容(默认为无，获取所有回复)
        :param time:     指定时间
        :param the_tiezi: 帖子文件内的一行帖子内容dict
        :param content_list: 存放所有回复内容的list
        :return:
        '''

        #设定保存文件名
        if self.save_file == '':
            the_time=re.sub(r':','：',time)
            self.set_savefile('回帖内容—某时间后', the_time)  # 设定保存文件名

        timestamp = self.get_timestamp(time)#将输入的日期时间转换为时间戳
        if timestamp is not None:#输入格式不对的时间或其他内容，则忽略
            a = Find_path(the_tiezi)
            time_paths = a.the_key_path('time')#键匹配，获取所有time路径

            for the_time in time_paths :
                send_time = eval('the_tiezi' + the_time)
                send_timestamp = self.get_timestamp(send_time)#将发送时间转化为时间戳
                #指定时间之后的回复则添加到content_list中
                if send_timestamp > timestamp:
                    content_path = the_time.replace('time', 'content')
                    content=eval('the_tiezi' + content_path)
                    self.filter_content(content_list, content) #过滤部分内容，添加到list中

    @staticmethod
    def get_timestamp(date_time='无'):
        '''将输入的日期时间转换为时间戳，方便比对大小，若没有输入时间，那就返回0'''
        if re.match(r'\d*-\d*-\d* \d*:\d*', date_time):
            return time.mktime(time.strptime(date_time, "%Y-%m-%d %H:%M"))
        elif re.match(r'\d*-\d*-\d*', date_time):
            return time.mktime(time.strptime(date_time , "%Y-%m-%d"))
        elif date_time == '无':
            return 0

    def filter_content(self,content_list,content):
        '''单纯提取回复内容时，过滤掉url、楼内楼回复中的前缀“回复 xxx :”，因为有些回复是表情，所以为空，也要过滤掉
           然后把回复添加到list中'''
        re_url = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        re_reply = re.compile(r'回复.*:')
        content=re.sub(re_reply, '', content)
        content = re.sub(re_url, '', content)
        if content!='':
            content_list.append(content)
###===================================获取所有回复(回帖内容)==========================###






'''构造：
        toplevel：——notebook，2个页面：
                             ----搜索回复内容(search_frame):---选择文件夹部分(dir_fr):搜索、保存文件夹，搜索进度
                                                           ---搜索回复(search_fr)：关键字、回帖人
                                                           ---显示回复(value_text): 显示点击的帖子内容
                                                           ---tree
                             ----获取回复内容(content_frame):---选择文件夹部分(dir_fr):搜索、保存文件夹，搜索进度
                                                            ---设定部分(content_fr)：输入时间后搜索、
                                                                                    设定帖子回复文件、模板图片、屏蔽词
                                                            ---显示词云图(wc_label)
                            '''

class Search_tk():
    def __init__(self,my_tk):
        self.root=my_tk
        self.root.title('搜索贴吧')
        self.root.geometry('920x650+400+0')
        
        self.search_dir = StringVar() #要搜索的文件夹路径
        self.save_dir = StringVar()   #搜索后保存的文件路径
        self.board_var=StringVar()    #显示搜索进度的label
        self.set_defaultpath()       #设定的好默认的路径
        
        self.creat_notebook()       #创建notebook及其2个页面
        self.creat_search_frame()
        self.creat_content_frame()



    def creat_notebook(self):
        '''创建notebook，生成2个页面：1.存放搜索帖子内容  2.获取回复生成云图'''
        self.notebook=Notebook(self.root)
        self.notebook.pack()
        #搜索回复内容页面frame
        self.search_frame = Frame(self.root)
        self.search_frame.pack()
        #获取所有回复页面frame
        self.content_frame = Frame(self.root)
        self.content_frame.pack()

        self.notebook.add(self.search_frame, text="搜索页面",sticky='E')
        self.notebook.add(self.content_frame, text="获取回复")

    def creat_dirframe(self,frame):
        '''创建2个页面的共同部分：1.所要搜索的文件夹、2.保存文件的文件夹、3.显示遍历文件进度
            '''
        dir_fr=Frame(frame)
        dir_fr.pack()
        path_label1 = Label(dir_fr, text='目标贴吧:', anchor='e')
        change_button1 = Button(dir_fr, text='更改', command=lambda:self.set_dirpath(self.search_dir))
        search_dir_entry=Entry(dir_fr,width=45, textvariable=self.search_dir)
        path_label1.grid(row=1, column=0)
        search_dir_entry.grid(row=1, column=1)
        change_button1.grid(row=1, column=2)

        path_label2 = Label(dir_fr, text='保存路径:', anchor='e')
        change_button2 = Button(dir_fr, text='更改', command=lambda: self.set_dirpath(self.save_dir))
        save_dir_entry = Entry(dir_fr, width=45, textvariable=self.save_dir)
        path_label2.grid(row=2, column=0)
        save_dir_entry.grid(row=2, column=1)
        change_button2.grid(row=2, column=2)


        self.board_text=tkinter.Label(dir_fr,width=60,font=('system', 14, 'bold'),foreground='blue',background='Wheat',textvariable=self.board_var)
        self.board_var.set('请设定要搜索的文件夹以及搜索条件！！')
        self.board_text.grid(row=4, column=0,columnspan=3)
        tkinter.Label(dir_fr, height=1).grid(row=5, column=0)

    def creat_content_frame(self):
        '''获取所有回复页面，共6部分
           1.选择文件夹部分(共用)
           2.输入搜索时间，获取该时间点后的所有回复
           3.包含所有回复的文件，搜索完成后会自动填入，也可手选
           4.选择词云图所用的模板图片，不设定/设定错误，直接生成为方形
           5.添加屏蔽词，设定词云图不显示的词语
           6.显示词云图label
           '''
        self.creat_dirframe(self.content_frame)# 创建 搜索保存文件夹部分

        content_fr = Frame(self.content_frame)
        content_fr.pack()

        self.the_time = StringVar()
        now_time = datetime.datetime.now()
        yes_time = now_time + datetime.timedelta(days=-1)
        yes_time = yes_time.strftime('%Y-%m-%d %H:%M')
        self.the_time.set(yes_time)     #默认时间设定为当前时间的前一天
        time_label = Label(content_fr, text='输入时间:', anchor='e')
        time_button = Button(content_fr, text='获取回复', command=self.get_content)
        time_combobox = Combobox(content_fr, width=20, textvariable=self.the_time,values=['获取所有内容'])
        format_label=Label(content_fr, text='格式:2018-10-25或2018-10-25 15:00', foreground='gray',anchor='e')
        time_label.grid(row=0, column=0)
        time_combobox.grid(row=0, column=1)
        time_button.grid(row=0, column=3)
        format_label.grid(row=0, column=2)

        self.content_file = StringVar()
        cfile_label = Label(content_fr, text='回复文件:', anchor='e')
        cfile_button = Button(content_fr, text='更改文件',command= lambda:self.set_filepath(self.content_file))
        cfile_entry = Entry(content_fr, width=55, textvariable=self.content_file)
        cfile_label.grid(row=1, column=0)
        cfile_entry.grid(row=1, column=1,columnspan=2)
        cfile_button.grid(row=1, column=3)

        self.pic_file = StringVar()
        pic_label = Label(content_fr, text='模板图片:', anchor='e')
        pic_button = Button(content_fr, text='选择文件', command= lambda:self.set_filepath(self.pic_file))
        pic_entry = Entry(content_fr, width=55, textvariable=self.pic_file)
        pic_label.grid(row=2, column=0)
        pic_entry.grid(row=2, column=1, columnspan=2)
        pic_button.grid(row=2, column=3)

        self.add_stopword = StringVar()
        self.add_stopword.set('就是, 不是, 现在, 没有, 可以, 还是, 这个, 怎么, 什么, 自己, 一个')
        stopword_label = Label(content_fr, text='添加屏蔽词:', anchor='e')
        stopword_entry = Entry(content_fr, width=55, textvariable=self.add_stopword)
        wc_button=Button(content_fr, text='生成图片', command=self.generate_pic)
        stopword_label.grid(row=3, column=0)
        stopword_entry.grid(row=3, column=1, columnspan=2)
        wc_button.grid(row=3, column=3)

        #插入图片的label
        self.wc_label=Label(self.content_frame)
        self.wc_label.pack()

    def creat_search_frame(self):
        '''搜索帖子回复部分，共5部分：
           1.选择文件夹部分(共用)
           2.根据 关键字 搜索回复内容
           3.根据 回帖人 搜索回复内容
           4.text，显示tree中你所点的某个回复
           5.tree，搜索结束后，插入搜索内容
'''

        self.creat_dirframe(self.search_frame)# 创建 搜索保存文件夹部分

        # 搜索关键字/回帖人部分
        search_fr = Frame(self.search_frame)
        search_fr.pack()

        self.target_word = StringVar()
        sword_label = Label(search_fr, text='搜索回复内容----关键字:', anchor='e')
        sword_button = Button(search_fr, text='搜索', command=self.search_keyword)
        sword_entry = Entry(search_fr, width=20, textvariable=self.target_word)
        sword_label.grid(row=0, column=0)
        sword_entry.grid(row=0, column=1)
        sword_button.grid(row=0, column=2)

        self.author = StringVar()
        sauthor_label = Label(search_fr, text='搜索回复内容----回帖人:', anchor='e')
        sauthor_button = Button(search_fr, text='搜索', command=self.search_author)
        sauthor_entry = Entry(search_fr, width=20, textvariable=self.author)
        sauthor_label.grid(row=1, column=0)
        sauthor_entry.grid(row=1, column=1)
        sauthor_button.grid(row=1, column=2)

        # 显示tree所选的item帖子内容
        self.value_text = Text(self.search_frame, width=120, height=3, )
        self.value_text.pack()
        self.value_text.tag_config('default', font=('system', 10))

        #创建tree
        self.creat_tree()

###==========================获取回复内容，生成词云图所用函数========================#
    def generate_pic(self):
        '''回调函数，生成词云图
           运行过程：1.获取文件路径、屏蔽词等
                    2.判断包含回复的文件路径:---正确，判断模板图片路径:---正确，根据模板图片生成词云图
                                                                  ---不对，直接生成方形图
                                          ---不对，报错'''
        pic_list=['.jpg', '.png', '.jpeg', '.bmp']
        pic_file=self.pic_file.get().strip()
        content_file = self.content_file.get().strip()

        #屏蔽词，过滤逗号等符号，转换为list
        stopword=self.add_stopword.get().strip()
        stopword=re.sub(r'[(\s)(,)(，)(\\)(/\)]', ' ', stopword)
        stopword=stopword.split()

        #判断包含回复的文件路径正确与否
        if os.path.exists(content_file) and os.path.splitext(content_file)[1]=='.json':
            try:
                #判断模板图片路径正确与否
                if os.path.exists(pic_file) and os.path.splitext(pic_file)[1] in pic_list :
                    self.board_var.set('根据模板图片生成词云图.......')
                    self.root.update()
                    wc_file=self.generate_wc(stopword,content_file,pic_file)    #生成词云图
                else:
                    self.board_var.set('没有正确选择模板图片，生成方形云图.......')
                    self.root.update()
                    wc_file=self.generate_wc(stopword,content_file)
                self.board_var.set('已生成词云图！！！！')

                #将词云图显示在tk上
                img = Image.open(wc_file)  # 打开图片
                self.wc_label.img = ImageTk.PhotoImage(img)  # 用PIL模块的PhotoImage打开
                self.wc_label['image'] = self.wc_label.img

            except Exception as e:
                logging.error("ERROR：%s\n"
                              "%s" % (e, traceback.format_exc()))
                self.board_var.set('生成词云图出现问题！！')

        else:
            self.board_var.set('回复内容文件选择不对！！')

    def generate_wc(self,stopword,list_file, pic=None):
        '''生成词云图，               PS:图片路径为空，直接生成方形词云图
        :param stopword:屏蔽词
        :param list_file:里面是list的json文件
        :param pic:模板图片路径
        :return:返回生成的词云图路径
        '''
        if pic:
            pic = np.array(Image.open(pic))  # 解析图片

        with open(list_file, 'r', encoding='utf-8') as f:
            words = f.read()
            words = json.loads(words)
        text = "".join(words)  # 将list转换为str

        # 使用jieba将词语分割       false直接将句子分割，他 来到 上海交通大学；True会出现相同的字 ，他 来到 上海 上海交通大学 交通 大学
        jieba_text = jieba.cut(text, cut_all=False)  #
        wc_text = " ".join(jieba_text)

        # 屏蔽词
        stopwords = set()
        if stopword!=[]:stopwords.update(stopword)

        wc = WordCloud(background_color='white',  # 背景颜色
                       max_words=500,  # 要显示的词的最大个数
                       width=900,  # 图片的宽
                       height=400,  # 图片的长
                       mask=pic,  # 以该参数值作图绘制词云，这个参数不为空时，width和height会被忽略
                       max_font_size=100,  # 显示字体的最大值，对应就是min最小值
                       stopwords=stopwords,  # 使用内置的屏蔽词，
                       font_path=r"wordcloud\simsun.ttc",  # 解决显示口字型乱码问题，可进入C:/Windows/Fonts/目录更换字体
                       random_state=42,  # 为每个词返回一个PIL颜色
                       scale=1,  # 按照比例进行放大画布，如设置为1.5，则长和宽都是原来画布的1.5倍

                       )

        wc.generate(wc_text)

        # 这2行代码，就是将云图里的字体颜色设定跟所选图片一致
        if pic is not None:
            image_colors = ImageColorGenerator(pic)
            plt.imshow(wc.recolor(color_func=image_colors), interpolation="bilinear")  # interpolation不太懂

        plt.imshow(wc)
        plt.axis("off")  # 不显示坐标轴
        #plt.show()  # 弹出图片，显示

        wc_file=self.content_file.get().replace('json','jpg').strip()
        wc.to_file(wc_file)  # 保存文件
        return wc_file
###==========================获取回复内容，生成词云图所用函数========================#




###==========================搜索/获取所有帖子文件，实例化Search_tiezi后进行遍历==========#
    def search_keyword(self):
        '''回帖函数，搜索关键字
           先清空tree，再实例化Search_tiezi 进行搜索
           搜索结果直接该实例中插入到tree
        '''
        search_dir = self.search_dir.get().strip()
        target_word=self.target_word.get().strip()

        if target_word!='':
            items = self.tree.get_children()
            [self.tree.delete(item) for item in items]#清空tree

            aa=Search_tiezi(self)
            try:
                aa.search_keyword(target_word)
            except Exception as e:
                self.board_var.set('请正确选择要搜索的文件夹')
                logging.error("ERROR：%s\n"
                              "%s" % (e, traceback.format_exc()))
        
    def search_author(self):
        '''回帖函数，搜索回帖人
            先清空tree，再实例化Search_tiezi 进行搜索
            搜索结果直接该实例中插入到tree
        '''
        search_dir = self.search_dir.get().strip()
        author = self.author.get().strip()

        if author!='':
            items = self.tree.get_children()
            [self.tree.delete(item) for item in items]#清空tree
            aa=Search_tiezi(self)
            try:
                aa.search_author(author)
            except Exception as e:
                self.board_var.set('请正确选择要搜索的文件夹')
                logging.error("ERROR：%s\n"
                              "%s" % (e, traceback.format_exc()))

    def get_content(self):
        '''回帖函数，获取所有回复
            调用get_timestamp，判断所输入的日期格式
            正确后，再实例化Search_tiezi，
            若有符合条件的内容，保存下来后会其路径显示在content_file中
        '''
        search_dir = self.search_dir.get().strip()
        the_time = self.the_time.get().strip()

        if the_time=='获取所有内容':the_time='无'
        right_time=Search_tiezi.get_timestamp(the_time)
        if right_time is not None:
            aa = Search_tiezi(self)
            try:
                aa.get_content(the_time)
            except Exception as e:
                self.board_var.set('请正确选择要搜索的文件夹')
                logging.error("ERROR：%s\n"
                              "%s" % (e, traceback.format_exc()))
            else:
                if os.path.exists(aa.save_file):
                    self.content_file.set(aa.save_file)
                else:
                    self.board_var.set('没有符合的回复，请正确输入时间！！')
        else:
            self.board_var.set('请正确输入时间！！')
###==========================搜索/获取所有帖子文件，实例化Search_tiezi后进行遍历==========#


###=========================创建tree，以及其所用到的函数=======================#
    def creat_tree(self):
        '''创建tree
           1.创建tree与滚动条
           2.绑定列头、双击、选择item时的回调函数'''

        columns=['title','floor','type','page','author','content','time','url']
        self.tree = Treeview(self.search_frame, columns=columns,show='headings' ,height=50)
        heads=("标题", '楼层','回帖',"页数",  "回帖人", "回复内容", "回复时间",'url')
        widths = ( 230, 50,50,40, 100, 270, 110,35)

        for i in range(len(columns)):
            self.tree.heading(columns[i], text=heads[i])
            self.tree.column(columns[i], width=widths[i], minwidth=widths[i], anchor='center')
            #绑定点击tree列头时，所有内容排序
            self.tree.heading(columns[i], command=lambda _col=columns[i]: self.treeview_sort_column(self.tree, _col, True))

        ysb = Scrollbar(self.search_frame,orient=VERTICAL, command=self.tree.yview)#滚动条
        self.tree.configure(yscrollcommand=ysb.set)
        self.tree.pack(side=LEFT)
        ysb.pack(side=RIGHT,fill=Y)

        self.tree.bind('<<TreeviewSelect>>',self.show_value)#选中的帖子，其内容显示在value_text中
        self.tree.bind("<Double-1>", self.open_url)         #双击打开在浏览器打开选中的帖子

    def treeview_sort_column(self,tv, col, reverse):  # Treeview、列名、排列方式
        '''列头的回调函数，
           让每个帖子的item与col对应的值 构成映射关系，以值作为排列依据(发帖时间、楼层转换为数字作为比较)，
           排列后，根据其顺序，用tree的move重新排列所有帖子'''

        #构造映射关系，l:[(该列对应的值1,item1)，(该列对应的值2,item2).....]
        l=[]
        for item in tv.get_children(''):
            value=tv.set(item,col)
            if col=='time':
                value = time.mktime(time.strptime(value, "%Y-%m-%d %H:%M"))
            elif col=='floor':
                value=re.findall(r'(\d*)楼',value)[0]
                value=int(value)
            l.append((value,item))

        # 根据第一个元素(时间戳)排序！
        l.sort(reverse=reverse)

        # 根据排序后索引移动
        for index, (value, item) in enumerate(l):
           tv.move(item, '', index)
        # 重写标题，使之成为再点倒序的标题
        tv.heading(col, command=lambda: self.treeview_sort_column(tv, col, not reverse))
        
    def filter(self,the_value):
        '''过滤插入tree中的表情、特殊符号'''
        the_value = [re.sub(r':.*?:', '', emoji.demojize(str(one))) for one in the_value]  # 有时候title里有表情，得去掉
        co = re.compile(u'[\U00010000-\U0010ffff]')  # 有时候什么表情都不是，也会报错，所以还得过滤掉
        the_value = [co.sub('', one) for one in the_value]
        return the_value
    
    def tree_insert(self,one_tiezi):
        '''tree中插入帖子的楼层、楼内楼回复
           插入内容："标题", '楼层','回帖',"页数",  "回帖人", "回复内容", "回复时间",'url
           因为有些楼层只存在楼内楼，所以只有len(3)>3时，才能插入楼层信息，接着循环其楼内楼'''

        title=one_tiezi['title']
        for post in one_tiezi['post_list']:
            floor=post['floor']
            url=post['url']
            if len(post)>3:
                post_value=(title,floor,'楼层',post['page'],post['author'],post['content'],post['time'],url)
                post_value = self.filter(post_value)
                self.tree.insert('', 'end', value=post_value)
            for comment in post['comment_list']:
                comment_value=(title,floor,'楼内楼',comment['page'], comment['author'], comment['content'], comment['time'],url)
                comment_value = self.filter(comment_value)
                self.tree.insert('', 'end', value=comment_value)

###=========================创建tree，以及其所用到的函数=======================#


###=======================tree鼠标操作bind绑定的函数=========================#

    def show_value(self, event):
        '''bind绑定函数，
           选中的帖子，其内容显示在value_text中 '''
        values = self.get_values()
        self.value_text['state'] = NORMAL
        title = '标题：%s' % values[0]
        author = '回帖人：%s' % values[4]
        content = '回复内容：%s' % values[5]
        self.value_text.delete('1.0', 'end')
        self.value_text.insert("end", '%s\n%s\n%s' % (title, author, content), )
        self.value_text['state'] = DISABLED  # 让text栏不可修改

    def open_url(self, event):
        '''bind绑定函数，双击打开在浏览器打开选中的帖子'''
        values = self.get_values()
        url = values[-1]
        webbrowser.open_new(url)

    def get_values(self):
        '''获取选中item的value'''
        item = self.tree.selection()[0]
        values = self.tree.item(item, "values")
        return values
###=======================tree鼠标操作bind绑定的函数=========================#
    

##================设定当前路径等的 函数================##
    #文本框默认显示的路径：含贴吧那个------保存、选择贴吧，都一样
    #更改路径，输入文本框变量，分别设定
    def set_defaultpath(self):
        '''获得当前路径，创建名为[贴吧]的文件夹，设定为默认路径，显示在路径文本框内'''
        self.the_path=os.path.split(os.path.realpath(__file__))[0]#获取当前所在的文件夹绝对路径
        self.defaultpath = self.the_path + os.sep + '贴吧'
        if os.path.exists(self.defaultpath) is False:       #创建存放帖子json文件的文件夹
            os.mkdir(self.defaultpath)
        self.search_dir.set(self.defaultpath)                  #设定搜索文本框内的路径
        self.save_dir.set(self.defaultpath)                     #设定保存文本框内的路径

    def set_dirpath(self,dir):
        '''弹出选择路径窗口，设定文件保存的路径
            选择好了文件夹，那该路径显示在文本框内，否则 设定为默认的文件夹'''
        a=tkinter.filedialog.askdirectory(initialdir=self.defaultpath)
        if a != '':
            dir.set(a)
        elif a == '' and dir.get().strip() == '':
            dir.set(self.defaultpath)

    def set_filepath(self, file):
        '''弹出选择路径窗口，设定文件保存的路径(这是选择文件，而不是文件夹)
            选择好了文件夹，那该路径显示在文本框内，否则 设定为默认的文件夹'''
        a = tkinter.filedialog.askopenfilename(initialdir=self.defaultpath)
        if a == '' and file.get().strip()=='':
            file.set(self.defaultpath)
        elif a != '':
            file.set(a)
###================设定当前路径等的 函数================##






# root=Tk()
# #root.Search_tk=Toplevel()
# Search_tk(root)
# root.mainloop()