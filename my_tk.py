
from tkinter import *
from tkinter.ttk import *
import time,os,json,emoji,codecs,re, psutil,webbrowser,subprocess
import tkinter.filedialog
from tieba_log import Open_json
from search import Search_tk


'''tk界面的创建步骤：
   第一步：创建最初始的[选择]界面，然后按下按钮，选择 帖子/贴吧
   第二步：创建对应界面，布局好“贴吧名、页数范围、保存路径、(tid)”
           ————需要提及的是，1.新版ttk的scale滑动条很蛋疼，值都是小数不能设定，得手动绑定函数
                            2.按下“启动、终止”等按钮，其按钮界面发生的改变
                            3.[进度详情] 按钮以及界面的弹出/隐藏
   第三步：创建对应的[进度详情]窗口(具体看类display_window())
   第四步：设定好menu，返回上一层[选择]界面,删除所有痕迹
                        '''
class My_tk():
    def __init__(self,tk):
        self.root=tk
        self.root.title('贴吧爬虫')
        self.defaultpath=None  #默认存放文件路径
        #创建 初始的[选择]界面 有贴吧/帖子按钮(对应相应的创建界面方法)
        self.choice_frame=Frame(self.root)
        self.tieba_button=Button(self.choice_frame,text='爬取贴吧',command=self.show_tieba)
        self.tiezi_button = Button(self.choice_frame,text='爬取帖子', command=self.show_tiezi)
        self.choice_frame.pack()
        self.tieba_button.pack(side=LEFT)
        self.tiezi_button.pack(side=LEFT)
        #创建菜单
        self.creat_menu()

##====================选择爬取帖子/贴吧的命令(回调函数)==================##
    def show_tieba(self):
        #隐藏[选择] 界面，显示为爬取【贴吧】界面，创建【进度详情】窗口
        self.Tid = False
        self.choice_frame.pack_forget()#隐藏选择 界面
        self.build_tieba_frame()    #创建【贴吧】 界面
        self.creat_show()           #根据爬取的是帖子/贴吧，创建【进度详情】窗口

    def show_tiezi(self):
        # 隐藏[选择] 界面，显示为爬取【贴子】界面，创建【进度详情】窗口
        self.Tid = True
        self.choice_frame.pack_forget()  # 隐藏选择 界面
        self.build_tiezi_frame()        # 创建【贴子】 界面
        self.creat_show()           #根据爬取的是帖子/贴吧，创建【进度详情】窗口
##====================选择爬取帖子/贴吧的命令(回调函数)==================##


##====================创建帖子/贴吧的界面==================##
    def build_tieba_frame(self):
        '''贴吧界面'''
        self.tieba_frame=Frame(self.root,height=50, width=100)
        self.tieba_frame.pack(expand=1)
        #grid:贴吧名
        tieba_label=Label(self.tieba_frame,text='贴吧名:')
        self.tiebavar=StringVar()
        tieba_name=Entry(self.tieba_frame,textvariable=self.tiebavar,width=22)
        tieba_label.grid(row=0, column=0,sticky='we')
        tieba_name.grid(row=0, column=1,columnspan=2)

        #grid:贴吧页数
        self.grid_pages(self.tieba_frame,20)
        #grid：存放路径
        self.grid_path(self.tieba_frame)
        #grid：开始按钮等
        self.grid_buttons(self.tieba_frame)

    def build_tiezi_frame(self):
        '''帖子界面
            这个界面，每一层(行)都是用grid，但是第一层是4列(格)，而第二层页数是3列，所以tid里面用pack布局'''
        self.tiezi_frame=Frame(self.root,height=50, width=100)
        self.tiezi_frame.pack(expand=1)
        #frame：贴吧名、帖子tid
        tiezi_frame=Frame(self.tiezi_frame)
        tiezi_frame.grid(columnspan=3,)
        
        #grid:帖子所在的贴吧
        tieba_label = Label(tiezi_frame, text='贴吧名: ',anchor=E)
        self.tiebavar = StringVar()
        tieba_name = Entry(tiezi_frame, width=12,textvariable=self.tiebavar)
        tieba_label.pack(expand=1,fill='both',side=LEFT,anchor='e')
        tieba_name.pack(expand=1,fill='both',side=LEFT)
        #grid:帖子的tid
        tid_label=Label(tiezi_frame,text='  帖子的tid:')
        self.tidvar=IntVar()
        tid_name=Entry(tiezi_frame,width=8,textvariable=self.tidvar)
        tid_label.pack(expand=1,fill='both',side=LEFT)
        tid_name.pack(expand=1,fill='both',side=LEFT)

        #grid:贴吧页数
        self.grid_pages(self.tiezi_frame,1000)
        #grid：存放路径
        self.grid_path(self.tiezi_frame)
        #grid：开始按钮等
        self.grid_buttons(self.tiezi_frame)
###====================创建帖子/贴吧的界面==================##


##====================页数、路径、开始按钮 等的布局==================##
    def grid_pages(self,the_frame,end_page):
        '''创建输入页数的文本框、滑动条，设定最大值end_page
            ——————要点：设定文本输入框entry，鼠标离开后，滑动条也跟着改变
                        滑动条默认是小数，得手动设定为整数'''
        pages_label = Label(the_frame, text='爬取页数:')
        #设定页数 文本框、滑条 绑定变量
        self.beginvar=IntVar()#文本框var
        self.endvar = IntVar()
        self.scalevar1 = DoubleVar()#滑动条var
        self.scalevar2 = DoubleVar()
        self.scalevar1.set(1)
        self.scalevar2.set(1)
        self.beginvar.set(1)
        self.endvar.set(1)
        #创建文本框、滑动条，设定回调函数(两者其中一个变动，另外一个也随着更变)
        begin_entry = Entry(the_frame,width=4, textvariable=self.beginvar,validate='focusout',validatecommand=self.set_entry)
        end_entry = Entry(the_frame,width=4, textvariable=self.endvar,validate='focusout',validatecommand=self.set_entry)
        begin_scale=Scale(the_frame,length=120, from_=1, to=end_page, variable=self.scalevar1)
        end_scale = Scale(the_frame,length=120, from_=1, to=end_page, variable=self.scalevar2)
        #!!因为ttk的滑动条不能是整数，所以只能手动设定为整数了！！
        begin_scale.bind("<B1-Motion>", self.set_yeshu)      #拖住左键移动
        begin_scale.bind("<Double-Button-1>", self.set_yeshu)#左击鼠标
        end_scale.bind("<B1-Motion>", self.set_yeshu)
        end_scale.bind("<Double-Button-1>", self.set_yeshu)

        pages_label.grid(row=1, column=0, rowspan=2, sticky='eswn')
        begin_entry.grid(row=1, column=1, sticky='s')
        end_entry.  grid(row=2, column=1, sticky='n')
        begin_scale.grid(row=1, column=2, sticky='s')
        end_scale.  grid(row=2, column=2, sticky='n')

    def grid_path(self,the_frame):
        '''在帖子/贴吧frame中创建【存放路径】的项目'''
        path_label= Label(the_frame, text='存放路径:',anchor='e')
        change_button=Button(the_frame, text='更改:',command=self.set_path)
        self.pathvar=StringVar()
        self.set_defaultpath()#获得当前路径，创建名为[贴吧]的文件夹，设定为默认路径，str显示在路径文本框内
        path_entry = Entry(the_frame, width=25, textvariable=self.pathvar,)

        path_label.grid(row=3, column=0,sticky='w')
        change_button.grid(row=3, column=2,sticky='e')
        path_entry.grid(row=4, column=0, columnspan=3,sticky='we' )

    def grid_buttons(self,the_frame):
        '''在贴吧/帖子frame中创建 【开始、暂停、终止按钮、显示进度text按钮】'''
        self.button_frame=Frame(the_frame) #存放按钮的frame
        self.button_frame.grid(row=5, columnspan=3)

        self.start_button=Button(self.button_frame,text="开始爬取",command=self.run,width=25) #回调函数是 运行scrapy
        self.start_button.pack(side="left", expand="yes", fill="both", padx=5, pady=5)

        self.text_button = Button(self.button_frame, text="显示进度", command=self.display_text, width=8) #回调函数是 弹出爬取详情窗口
        self.text_button.pack(side="right", expand="yes", fill="both", padx=5, pady=5)

        #默认开始时 是隐藏状态的【暂停键、终止键】
        self.pause_button = Button(self.button_frame, text="暂停", command=self.pause, width=11)#这个没有设定了
        self.stop_button = Button(self.button_frame, text="终止", command=self.stop, width=11)  #回调函数是 终止scrapy程序
        self.pause_button.pack_forget()
        self.stop_button.pack_forget()
###====================页数、路径、开始按钮 等的布局==================##


##================页数文本框、滑动条的回调函数================##
    def set_yeshu(self,*args):
        #当滑条动时，文本框的页数也改变,用int是因为ttk的滑动条value是float！
        self.beginvar.set(int(self.scalevar1.get()))
        self.endvar.set(int(self.scalevar2.get()))

    def set_entry(self,*args):
        #当手动输入页数时，滑条也会跟着动！
        self.scalevar1.set(self.beginvar.get())
        self.scalevar2.set(self.endvar.get())
        return True
###================页数文本框、滑动条的回调函数================##


##================开始、终止 等按钮的回调函数================##
    def run(self):
        '''运行，启动scrapy爬虫——————ps:具体启动命令在begin文件重新设定
        开始后，隐藏[开始]键，显示[暂停、终止]键'''
        self.start_button.pack_forget()
        self.pause_button.pack(side="left", expand="yes", fill="both", padx=3, pady=5)
        self.stop_button.pack(side="left", expand="yes", fill="both", padx=3, pady=5)

    def stop(self):
        '''点击[终止]键后，显示[开始]键，隐藏[暂停、终止]键
            如果scrapy还在运行，那么结束exe程序'''
        self.pause_button.pack_forget()
        self.stop_button.pack_forget()
        self.start_button.pack(side="left", expand="yes", fill="both", padx=5, pady=5)
        self.stop_scrapy()#结束exe程序

    #-------这2个功能，不知能不能实现！------#
    def pause(self):
        '''点击暂停键后，变为[继续]键'''
        self.pause_button['text']='继续'
        self.pause_button['command']=self.conti
    def conti(self):
        '''点击继续键后，变为[暂停]键'''
        self.pause_button['text'] = '暂停'
        self.pause_button['command'] = self.pause
###================开始、终止 等按钮的回调函数================##


###================如果scrapy还在运行，那么杀死进程================##
    def stop_scrapy(self):
        '''根据pid判断，如果scrapy还在运行，那么结束进程,
          同时设定爬取详情窗口的is_scrapying为False终止tree里的循环'''
        if self.spider_pid in psutil.pids():   #见begin，运行爬虫时设定
            print('scrapy还在运行！')
            time.sleep(1)
            subprocess.Popen("taskkill /pid %s /f" % self.spider_pid, shell=True)
            self.crawling_window.is_scrapying=False
###================如果scrapy还在运行，那么杀死进程================##


###================创建进度详情 的窗口================##
    def creat_show(self):
        #[进度详情] 的弹出窗口，具体操作见 类display_window()，还设定了为默认隐藏，点击按钮才会显示
        self.start_time=time.time() #开始时间，用在详情窗口
        self.show_text=Toplevel()
        self.crawling_window=display_window(self)#进度详情窗口实例化

        self.show_text.withdraw()  #隐藏整个text窗口
        self.show_text.protocol(name='WM_DELETE_WINDOW', func=self.hide_text)#窗口点击关闭时，实际上是隐藏起来了
###================创建进度详情 的窗口================##

##================弹出进度详情窗口 按钮 的回调函数================##
    def display_text(self):
        '''弹出 隐藏的进度详情窗口，改变[显示进度]的命令跟text'''
        self.show_text.deiconify()#隐藏的进度详情窗口 再次显示，
        self.text_button['text']='隐藏窗口'
        self.text_button['command']=self.hide_text
    def hide_text(self):
        '''隐藏 进度详情窗口，改变[显示进度]的命令跟text'''
        self.show_text.withdraw()  # 将进度窗口 隐藏，
        self.text_button['text'] = '显示进度'
        self.text_button['command']=self.display_text
###================弹出进度详情窗口 按钮 的回调函数================##


##================设定当前路径等的 函数================##
    def set_defaultpath(self):
        '''获得当前路径，创建名为[贴吧]的文件夹，设定为默认路径，显示在路径文本框内'''
        self.the_path=os.path.split(os.path.realpath(__file__))[0]#获取当前所在的文件夹绝对路径
        self.defaultpath = self.the_path + os.sep + '贴吧'
        if os.path.exists(self.defaultpath) is False:       #创建存放帖子json文件的文件夹
            os.mkdir(self.defaultpath)
        self.pathvar.set(self.defaultpath)                  #设定文本框内的路径

    def set_path(self):
        '''弹出选择路径窗口，设定文件保存的路径
            选择好了文件夹，那该路径显示在文本框内，否则 设定为默认的文件夹'''
        a=tkinter.filedialog.askdirectory(initialdir=self.the_path)
        if a != '':
            self.pathvar.set(a)
        else:
            self.pathvar.set(self.defaultpath)
###================设定当前路径等的 函数================##


###====================返回选择贴吧/帖子界面的菜单/搜索界面==================##
    def creat_menu(self):
        '''创建菜单栏，设定【返回】命令'''
        menubar = Menu(self.root)  # 先在root创建一个初始menu框框
        self.root['menu'] = menubar  # 固定，相当于pack
        menubar.add_command(label="返回", command=self.back)
        menubar.add_command(label="搜索", command=lambda :Search_tk(Toplevel()))

    def back(self):
        '''返回上一级选择界面，把关于贴吧/帖子 界面的信息、控件全部删除(ps:不然再进入时会有痕迹)'''
        if 'tieba_frame' in dir(self):
            self.tieba_frame.destroy()#删除贴吧界面(控件)
            self.show_text.destroy() #删除进度详情 窗口
            delattr(self,'tieba_frame')#彻底删除属性
        elif 'tiezi_frame' in dir(self):
            self.tiezi_frame.destroy()#删除贴子界面(控件)
            self.show_text.destroy()  # 删除进度详情 窗口
            delattr(self, 'tiezi_frame') #彻底删除属性

        self.choice_frame.pack()        #显示最初始的选择贴吧/帖子 界面
        self.stop_scrapy()              # 结束exe程序

###====================返回选择贴吧/帖子界面的菜单/搜索界面==================##


'''显示爬取帖子进度，流程是：
    在spider里，每爬取完一段(每个帖子，或者每10页)，返回item时，就把帖子标题、发帖人等信息写入info.json
    然后tree会不停的打开这个文件，当spider更新数据时，就添加到tree里
    在循环里，每15秒检查scrapy是否还在运行，一旦不在了，就终止循环
              还有打开the_spider_counts，更新理论爬取的item数量，一旦tree达到这个数量，也会中断循环'''

'''这个类是toplevel进度详情窗口的布局：
    难点有几个：1.爬取[帖子]/[贴吧] label显示的文字内容不同、tree的布局也不同，所以在init里设定了
                2.更新tree 已爬取的item 比较费劲，具体看show_it，(ps:如果多次按下按钮，其方法也会调用多次！)
    ##3个读取数据的json文件：
              1."config"，tk上输入爬取 贴吧/帖子 的贴吧名/页数/存放路径 的信息
              2."爬取进度详情/TieXx_info.json",在spider返回item时，帖子标题、发帖人等信息
              3.“爬取进度详情/the_spider_counts”，在spider上获取的理论爬取item总数，
                 而当结束时，就会加多一行，这次爬取的总信息 贴吧名、页数、时间等
    '''
class display_window():
    def __init__(self,my_tk):
        self.my_tk=my_tk     #总的tk界面
        self.root=self.my_tk.show_text#当前的 [进度详情] 界面
        self.root.title('爬取进度')
        self.root.geometry('850x500+400+0')

        #当前的界面是【贴吧】，设定tree的头、Label显示的文字、需要打开的info.json
        if self.my_tk.Tid==False:
            self.columns = ("title", "author", "reply_num", "pages", "tid", "last_reply_author", "last_reply_time", "situation")
            self.the_head = ("标题", "发帖人", "回复数量", "总页数", "tid", "最后回复人", "最后回复时间", "爬取详情")
            self.widths = (350, 100, 35, 35, 70, 100, 120, 160)
            start_labeltext='当前选中的是爬取--------------┠贴吧┨'
            self.start_LabelText="'正准备爬取┠贴吧┨——————————————→『%s』'%self.tieba_name"
            self.crawing_LabelText="'正在爬取:某个贴吧『{}』——————进度:〔%s/%s〕——————耗时：%02d分:%02d秒'.format(self.tieba_name)"
            self.tiezi_info_path=r'爬取进度详情/TieBa_info.json'
            self.tid_posi=4    #tid在value的位置
        else: #当前的界面是【帖子】
            self.columns = ("title", "author",  "pages", "tid",  "situation")
            self.the_head = ('标题', '发帖人', "总页数", "tid", '爬取页数范围')
            self.widths = (400, 100, 00, 109,  200)
            start_labeltext = '当前选中的是爬取--------------┠帖子┨'
            self.start_LabelText="'正准备爬取┠帖子┨——————————————→『tid:%s』'%self.tid"
            self.crawing_LabelText="'正在爬取:单个帖子『{}』——————进度:〔%s/%s〕——————耗时：%02d分:%02d秒'.format(self.tid)"
            self.tiezi_info_path=r'爬取进度详情/TieZi_info.json'
            self.tid_posi = 3   #tid在value的位置

        Button(self.root, text='进度条', command=self.show_it).pack()
        #创建 提示爬取详情的text、进度条、treeview
        self.creat_label()
        self.creat_propresbar()
        self.creat_treeview()

        self.label['text']=start_labeltext      #Label的初始文字
        self.is_scrapying = True               #中断循环的依据
        self.treeview.bind("<Double-1>", self.open_url) #双击帖子，打开浏览器进入帖子的页面
        self.creat_CopyMenu()                              #创建右击时弹出的菜单
        self.treeview.bind("<Button-3>", self.copy_value)  # 右击帖子，选择复制帖子的标题/发帖人/tid


    def show_it(self):
        ''' 初始：按下按钮，清空tree，更改labe文字，
            创建一个循环语句，scrapy还在运行时，
                        获取已经爬取的帖子数量，跟tree里显示的帖子数量比较，如果tiezi_counts > tree_counts，就更新tree等
                        更新进度条、检查item是否已经爬取完毕(tiezi_counts==tree_counts)
                        每15秒检测一次scrapy是否还在运行，更新进度条最大值等
            结束循环后，改变label文字

            ！！中断循环的2个条件：1.帖子爬取完，tree显示item与理论item相等，中断
                                2.每15秒检测scrapy是否在运行，没有则中断'''


        self.ready()  # 清空tree
        self.is_scrapying = True
        time1=self.my_tk.start_time #启动时的时间戳
        working_time=-1   #检查scrapy的时间点
        now_time=0      #每次循环中的时间点

        while self.is_scrapying:
            #获取已经爬取帖子的信息、数量、tree中存在的行数
            tiezi_infos, tiezi_counts=self.get_tiezi_info()
            tree_counts = len(self.treeview.get_children())  # treeview已经存在的行数

            #=====帖子数量>tree显示数量，更新tree里显示的帖子
            if tiezi_counts > tree_counts:
                self.update_tree(tree_counts, tiezi_counts, tiezi_infos)
              
            
            self.update_crawingText(now_time, tiezi_counts)         #更新进度条、label文字
            if tiezi_counts == self.item_counts: self.is_scrapying = False  # 爬完了立马中断循环
            # ========#!!!原来不让他卡，关键在于此！！！update()不能处于上面那个循环之中！！
            self.root.update()

            #设定了，每15秒一次检查scrapy是否还在运行、更新理论要爬取的item数量、进度条等
            now_time=int(time.time()-time1)
            if now_time%15==0 and working_time<now_time:
                working_time =now_time
                print('耗费时间：',working_time,'   scrapy的pid：',self.my_tk.spider_pid)

                self.update_config()#获取贴吧名、理论item数、tid，更新进度条、tree高度
                self.is_scrapying=self.scrapying() #检查scrapy是否在运行，停止就返回False中断循环

        self.End_LabelText()#scrapy结束时会在the_spider_counts中添加一行，如果存在，那就改变label文字

###====================按下按钮后，循环前，要运用的函数==================##
    def ready(self):
        '''清空tree，进度条设定回0,更改显示的label文字，'''
        items =self.treeview.get_children()
        [self.treeview.delete(item) for item in items]
        self.progresbar.config(value=0)
        self.update_config()#获取贴吧名、理论item数、tid，更新进度条、tree高度

        self.label['text'] = eval(self.start_LabelText)
###====================按下按钮后，循环前，要运用的函数==================##


####====================进入循环，要运用的函数==================##
    def update_config(self):
        '''读取记录数量json，获取贴吧名、理论item数、tid，更新进度条、tree高度'''
        self.item_counts=Open_json(r'爬取进度详情/the_spider_counts.json').read()[0]
        self.tieba_name = Open_json(r'config').read()[0]['tieba_name']
        self.tid = Open_json(r'config').read()[0]['tid']

        self.progresbar.config(maximum=self.item_counts)
        self.treeview.config(height=self.item_counts)

    def get_tiezi_info(self):
        '''spider运行时，返回每次爬取完的帖子信息、数量'''
        tiezi_infos=Open_json(self.tiezi_info_path).read()
        tiezi_counts = len(tiezi_infos)
        return tiezi_infos,tiezi_counts

    def update_tree(self,tree_counts, tiezi_counts,tiezi_infos):
        '''更新tree里显示的帖子,插入没有显示在tree里的帖子信息'''
        for i in range(tree_counts, tiezi_counts):
            # 第i个帖子dict里面的value组成的list
            the_value = [tiezi_infos[i][heading] for heading in self.columns]
            # 插入，因为有可能是emoji表情，所以得用try过滤掉(写法有缺陷，前后都是表情，文本直接被干掉)
            try:
                self.treeview.insert('', i, text=i + 1, value=the_value)
            except:

                the_value = [re.sub(r':.*?:', '', emoji.demojize(str(one))) for one in the_value]  # 有时候title里有表情，得去掉
                co = re.compile(u'[\U00010000-\U0010ffff]')                 #有时候什么表情都不是，也会报错，所以还得过滤掉
                the_value = [co.sub('', one) for one in the_value]

                self.treeview.insert('', i, text=i + 1, value=the_value)

            self.treeview.see(self.treeview.get_children()[-1])  # 让tree显示最新的帖子


    def update_crawingText(self,now_time,tiezi_counts):
        '''更新进度条、label文字'''
        self.progresbar.config(value=tiezi_counts)  # 更新进度条
        fen, miao = divmod(now_time, 60)  # 每次更新了帖子数量，才会
        self.label['text'] = eval(self.crawing_LabelText) % (tiezi_counts, self.item_counts, fen, miao)


    def scrapying(self):
        '''检测scrapy是否还在运行，是返回True，停止了就返回False'''
        if self.my_tk.spider_pid in psutil.pids():  # 见begin，运行爬虫时设定
            return True
        else:
            return False
###====================进入循环，要运用的函数==================##



###====================结束时，要运用的函数==================##
    def get_end_message(self):
        '''scrapy结束时会在记录数量json中添加一行，如果存在，就返回'''
        infos=Open_json(r'爬取进度详情/the_spider_counts.json').read()

        if len(infos)>1:
            end_message=infos[1]
            return end_message

    def End_LabelText(self):
        # scrapy结束时会在记录数量json中添加一行，如果存在，那就改变label文字
        print('end!!')
        time.sleep(2)
        if self.get_end_message():
            self.label['text'] = '爬取完成=====》%s' % (self.get_end_message())
        else:
            self.label['text'] = 'scrapy爬取被强行中断了!!'
        time.sleep(1)
        self.my_tk.stop()  # 重新显示为开始按钮
###====================结束时，要运用的函数==================##


###====================创建labe、进度条、tree==================##
    def creat_label(self):
        self.label = Label(self.root)
        self.label.pack()
    # 创建进度条
    def creat_propresbar(self):
        self.progresbar = Progressbar(self.root, length=400, maximum=50)
        self.progresbar.pack()

    # 创建treeview
    def creat_treeview(self):
        '''根据帖子/贴吧 不同内容创建列，设定宽度、列头，然后绑定滚动条'''
        self.treeview = Treeview(self.root, columns=self.columns, height=100)  # 表格
        self.treeview.column("#0", width=0,minwidth=35, anchor='sw')
        for i in range(len(self.columns)):
            self.treeview.column(self.columns[i],  width=0,minwidth=self.widths[i],anchor='center')

        for i in range(len(self.columns)):
            self.treeview.heading(self.columns[i], text=self.the_head[i])

        ysb = Scrollbar(self.root,orient=VERTICAL, command=self.treeview.yview)
        xsb = Scrollbar(self.root,orient=HORIZONTAL, command=self.treeview.xview)
        self.treeview.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)


        ysb.pack(side=RIGHT, fill=Y)
        xsb.pack(side=BOTTOM,fill=X)
        self.treeview.pack(expand=1, fill=BOTH)
###====================创建labe、进度条、tree==================##


###====================鼠标点击tree某一行时的调用的操作函数==================##
    def open_url(self,event):
        '''点击选中帖子，打开浏览器进入对应的url'''
        info = self.get_values()#选中单元的value
        tt = re.compile(r'此次爬取的页数是\：(\d*)\~')
        #获取当前帖子的页数
        if tt.match(info[-1]):
            page=tt.findall(info[-1])[0]
        else:#没动过/被删了，所以设定为第一页
            page=1
        url='https://tieba.baidu.com/p/%s?pn=%s'%(info[self.tid_posi],page)
        webbrowser.open_new(url)


    def creat_CopyMenu(self):
        #创建右击的菜单，设定每个命令的回调函数
        self.CopyMenu = Menu(self.treeview, tearoff=0)
        self.CopyMenu.add_command(label="复制“tid”",command=lambda :self.Copy_info(self.tid_posi) )
        self.CopyMenu.add_command(label="复制“发帖人”",command=lambda :self.Copy_info(1) )
        self.CopyMenu.add_command(label="复制“标题”",command=lambda :self.Copy_info(0) )

    def copy_value(self,event):
        #发生点击事件，就会弹出右击菜单
        self.CopyMenu.post(event.x_root, event.y_root)

    def Copy_info(self,the_posi):
        #回调函数，获取选中单元的信息
        values = self.get_values() #选中单元的value
        info=values[the_posi]
        self.root.clipboard_clear()    #清空粘贴板
        self.root.clipboard_append(info)#复制信息到粘贴板

    def get_values(self):
        # 选中单元的value
        item = self.treeview.selection()[0]
        values = self.treeview.item(item, "values")
        return values
###====================鼠标点击tree某一行时的调用的操作函数==================##

