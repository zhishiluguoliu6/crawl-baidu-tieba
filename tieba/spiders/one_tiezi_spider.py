import scrapy,re,json,time,copy,os,shutil
from scrapy.http import Request
from scrapy.selector import Selector
from tieba.items import TieziItem
from urllib import parse
from tkinter import messagebox
from tieba_log import Crawling_item_counts,Record_Crawl,Open_json

'''头疼，不知为何爬取单个帖子，老是会出现bug，url会转成别的url，第一次老是出问题，后面在点一次就好了'''
'''
这个是爬取 单个帖子的爬虫
大概思路：
         1.进入该帖子的第1页，获取帖子的初始信息(标题、发帖人、tid、总页数)等
         2.根据总页数，判断输入的起始页-结束页 是否合理，进行修改
         3.对[页数范围]进行分割，做到每100页为一个文件，每10页为一个item，组成request_list  =====>比较难处理的一部分。
         4.分别进入设定好的每个request任务，先爬取帖子内所有楼层信息，
         5.接着根据tid、pid再进入楼内楼，把数据放进对应的楼层里=======>比较难理解一部分，特别是判断锁定楼层next_comment
         6.楼内楼都爬取完毕，返回item，以tid为名保存json'''
'''
要点：
     1.默认每个帖子最多只爬取每个楼内楼前100页
     2.如何设定为每100页为一个文件，特头疼，主要是初始页->100整数页时(比如234-300)
     3.返回每个items时，也把信息保存到info文件，用在tree上
     4.'''

class One_tieziSpider(scrapy.Spider):
    name = "one_tiezi"
    allowed_domains = ["tieba.baidu.com"]
    print(name)

    #设定贴吧
    kw = '国际米兰'

    #所爬取帖子的标题、发帖人等信息，用来log记录的
    tiezi_info=None

    # # 设定存放总文件、贴吧对应文件夹、及其旧帖子文件夹
    dir_path = None
    path = None
    old_file_path = None


    #设定帖子的开始页跟结束页
    start_tiezi_page=1
    end_tiezi_page=100#(此参数是几，那就是前几页)


    #设定每个楼内楼爬取前N页
    max_comment_page=9

    #返回item数
    return_items_count=0

    # 把所有帖子标题、发帖人等信息记录，用在treeview进度条上显示详情
    log_Crawling = Record_Crawl(r'爬取进度详情/TieZi_info.json')


    def start_requests(self):
        '''设定初始爬取页数，进入某个帖子的第一页'''
        url = 'https://tieba.baidu.com/p/%s' % self.tid
        yield Request(url, callback=self.get_tiezi, dont_filter=True,)

    def get_tiezi(self, response):
        '''根据tid进入帖子的第一页，判断是否已经爬过了，爬过的就扔到旧文件夹，
        对页数范围进行分类，分批(每十页)真正开始爬取，相当于choice_tiezi这一步'''
        print(response.request.headers)
        url_alive = response.xpath('//title/text()').extract_first()
        if url_alive == '贴吧404':
            messagebox.showerror("帖子不对!!", "这是个空的帖子：『%s』" % self.tid)
            print('tid为:%s 的帖子被删了吧' % self.tid)
        else:
            the_tiezi=self.the_tiezi(response) #方法：返回标题、发帖人等信息组成的 dict
            pages=the_tiezi['pages']
            print(self.start_tiezi_page,self.end_tiezi_page)
            if self.start_tiezi_page>pages:
                messagebox.showerror("页数不对!!", "要爬取的页数超过帖子的总页数!!『%s』" % pages)
                print('要爬取的页数超过帖子的总页数!!!')
                return
            if self.end_tiezi_page>pages:#如果设定的最大页数>最后一页，那么end_tiezi_page为最后一页
                self.end_tiezi_page=pages

            #
            self.build_dir()  # 创建该贴吧所需的文件夹等
            all_request=self.add_request(the_tiezi)  #根据 目标页数 分文件、分范围创建request任务

            # 用于log
            self.tiezi_info=copy.deepcopy(the_tiezi) #结束时，pipeline调用log
            self.item_counts=len(all_request)        #理论返回的item总数
            Crawling_item_counts(r'爬取进度详情/the_spider_counts.json').update_items(self.item_counts-50) #理论返回items数

            #开始爬取每10页组成的item
            for one in all_request:
                print(one.meta['the_tiezi']['file_name'],one.meta['the_page'],one.meta['end_page'])
                yield one

    def add_request(self,the_tiezi):
        '''重点说说这个循环，其实很简单
            就是每100页为一个文件；每个文件，有10行(item)；每个item内容是10页
            ps：如果想爬取234~1346，那么大循环就是range(201,1346+1,100)
                1.因为初始时234，所以实际file_start_page,file_end_page(每个文件页数范围)就是[234,300] [301~400]···[1301~1346]
                2.接着就是细分每个item的页数范围，此时初始循环就是range(231,300,10)
                  那么页数范围range_pages就是[234, 240] [241, 250]····[291, 300]

            然而如果初始页self.start_tiezi_page是10的整数(如果230,120)之类，那么实际爬取就是121、231，所以最后得加回去

            最后，根据每个item所在的文件名(每100页一个文件),页数范围range_pages，
            还把第一页爬取的信息the_tiezi(title、发帖人等)创建request，最后执行'''
        all_request=[]
        start_page=(self.start_tiezi_page//100)*100+1 #起始页是234，那么循环开始数是231
        for i in range(start_page,self.end_tiezi_page+1,100):
            file_start_page,file_end_page=i,i+99
            if i<self.start_tiezi_page:
                file_start_page=self.start_tiezi_page
            if i+99>self.end_tiezi_page:
                file_end_page=self.end_tiezi_page

            #print('每隔100页',file_start_page,file_end_page)
            #设定为每100页一个文件，并以此命名，如果文件已经存在了，就移到旧文件夹里
            file_name=self.set_file_name(file_start_page,file_end_page)

            if file_start_page==self.start_tiezi_page:          #目的是从个位数是1的页数开始进入循环
                file_start_page=(self.start_tiezi_page//10)*10+1
            for the_page in range(file_start_page,file_end_page+1,10):
                range_pages = [the_page, the_page + 9]
                if the_page < self.start_tiezi_page:
                    range_pages = [self.start_tiezi_page, the_page + 9]
                #print(range_pages)
                the_tiezi['file_name']=file_name
                the_request=self.post_request(the_tiezi, self.post_list, range_pages)
                all_request.append(the_request)
        #上面的循环，没有考虑到初始页是10的整数时，所以后面得加回去
        if self.start_tiezi_page%10==0:
            file_name = self.set_file_name(self.start_tiezi_page, self.start_tiezi_page)
            the_tiezi['file_name'] = file_name
            frist_request=self.post_request(the_tiezi, self.post_list, [self.start_tiezi_page,self.start_tiezi_page])
            all_request.insert(0, frist_request)

        return all_request
        #其实我觉得这一段写得很蠢，，，，不知有什么最简单的写法没有。。


    def set_file_name(self,file_start_page,file_end_page):
        '''设定为每100页一个文件，并以此命名，如果文件已经存在了，就移到旧文件夹里'''
        file_name=self.path + os.sep + '%s范围：第%d~%d页.json' % (self.tid, file_start_page, file_end_page)
        #print(file_name)
        if os.path.exists(file_name):
            shutil.move(file_name, r'%s/%s' % (self.old_file_path, os.path.split(file_name)[1]))
        return file_name


    def post_request(self,the_tiezi,post_list,range_pages):
        '''作用：进入 某个帖子 的第N页
        设定好需要request的url、处理的parse、及其需要的meta'''
        #print('准备爬取——第%d~%d页'%(range_pages[0],range_pages[1]))
        url = 'https://tieba.baidu.com/p/%s?pn=%d' % (the_tiezi['tid'], range_pages[0])
        request = Request(url,  callback=post_list,dont_filter=True,
                          meta={'end_page': range_pages[1],
                                'the_tiezi': copy.deepcopy(the_tiezi), 'the_page': range_pages[0]})
        return request


    def post_list(self,response):
        '''作用：添加/修改楼层数据(新旧楼都行，不包含楼内楼)，根据情况进入下一页或者开始爬取楼内楼
        传入meta的三个参数
        the_tiezi ：整个帖子数据
        end_page ：该帖子的结束页数
        the_page ：当前页数
        操作步骤：判断帖子被删：···被删，进入下一步，爬取楼内楼
                             ···没被删，得到楼层数据，添加新楼层，修改旧楼层
                                判断当前是不是最后一页：---是，进入下一步，爬取楼内楼
                                                     ---不是，调用自身，进入下一页
        '''
        sep = Selector(response)
        the_tiezi = response.meta['the_tiezi']
        end_page = response.meta['end_page']
        the_page = response.meta['the_page']
        tid = the_tiezi['tid']

        #帖子没被删，那就进行操作
        url_alive = sep.xpath('//title/text()').extract_first()
        if url_alive != '贴吧404':
            #可能爬的过程中页数变动，所以每次进入帖子都更新页数
            pages = sep.xpath('//li[@class="l_reply_num"]/span[2]/text()').extract_first()
            the_tiezi['pages'] = int(pages)

            # 指向存放楼层的post_list,
            the_post_list = the_tiezi['post_list']

            # 已经爬取的楼层的pid组成的list，没爬过的帖子为空，得设定
            # 用于判断这个楼层是否已经被爬取过了(1.旧json的，包含楼内楼 2.可能中途被删楼，所以重复了)
            if the_post_list==[]:
                all_pids=[]
            else:
                all_pids = [post['pid'] for post in the_post_list]

            #当前url的所有楼层
            all_post = sep.xpath('//div[@class="l_post l_post_bright j_l_post clearfix  "]')

            #循环所有楼层，对post_list进行添加(新楼层)，修改(旧楼层)
            for one_post in all_post:
                new_post_dict = self.post_dict(one_post, tid, the_page)  # 方法：得到该楼层发帖人、时间、内容等组成的dict，除了楼内楼

                # 此楼层是新楼层，那把new_post_dict整个放进post_list
                if new_post_dict['pid'] not in all_pids:
                    the_post_list.append(new_post_dict)

                # 该楼层已经存在了，先找出它，
                else:
                    # 锁定已经存在的楼层(根据pid)
                    old_post_dict = [the_post for the_post in the_post_list if the_post['pid'] == new_post_dict['pid']][0]
                    # 更新该楼层的page、楼内楼回复数量
                    old_post_dict['page'] = the_page
                    old_post_dict['comment_num'] = new_post_dict['comment_num']

            #添加下一页
            the_page = the_page + 1

            # 爬好的楼层是10，那么此时page是11>10，或者page>最大页数时，那么就开始爬楼内楼，进入下一个parse
            if the_page > end_page or the_page > self.end_tiezi_page:
                # post_list里楼层总数量
                post_count = len(the_tiezi['post_list'])
                #方法：循环楼层，有楼内楼回复的才需要进入下一个parse，如果直接到最后一个回复，就保存
                request = self.next_comment(the_tiezi, tid, 0, post_count)
                yield request

            # 此时还没爬够10页 或者没到最后一页,循环调用自身(相当于进入下一页，继续添加补全the_tiezi)
            else:
                url = 'https://tieba.baidu.com/p/%s?pn=%d' % (tid, the_page)
                request = Request(url,  callback=self.post_list,dont_filter=True,
                                  meta={'end_page': end_page, 'the_tiezi': copy.deepcopy(the_tiezi),
                                        'the_page': the_page})
                yield request

        # 爬到一半，帖子被删了,那么就开始爬楼内楼，进入下一个parse
        else:
            post_count = len(the_tiezi['post_list'])
            # 方法：循环楼层，有楼内楼回复的才需要进入下一个parse，如果直接到最后一个回复，就保存
            request = self.next_comment(the_tiezi, tid, 0, post_count)
            yield request



    def comment_list(self,response):
        '''作用：锁定楼层后添加楼内楼，分情况进入下一页或者下一楼层继续爬取楼内楼
        传入meta的三个参数
        the_tiezi ：整个帖子数据
        posi ：当前楼层所在的位置，用于锁定添加楼内楼的楼层
        pn ：当前楼层的楼内楼的页数
        post_count：总楼层数
        先定位各个参数
        操作步骤：判断是否空楼内楼：···空的，进入下一楼层的楼内楼
                                 ···非空，得到楼内楼数据，添加新楼内楼
                                    判断是不是最后一页了：---是，进入下一楼层的楼内楼
                                                        ---不是，调用自身，进入下一页'''
        post_count=response.meta['post_count']
        posi = response.meta['posi']
        pn = response.meta['pn']
        the_tiezi = response.meta['the_tiezi']

        #定位对应楼层、及其楼内楼list
        post_dict=the_tiezi['post_list'][posi]
        comment_list=post_dict['comment_list']
        pid         =post_dict['pid']
        tid = the_tiezi['tid']

        # 当前页面每个楼内楼回复 组成的list
        sep = Selector(response)
        comments = sep.xpath('//div[@class="lzl_cnt"]')

        # 没有内容时，跳出，循环判断下一个有楼内楼的楼层
        if comments == []:
            request=self.next_comment(the_tiezi,tid,posi,post_count)
            yield request
        else:
            # 循环楼内楼的每个回复
            for one_comment in comments:
                comment_dict = self.comment_dict(one_comment, pn,tid)  # 方法：得到该楼内楼发帖人、时间、内容等组成的dict

                # 当此楼内楼没爬过时，就放到该楼层的楼内楼
                if comment_dict not in comment_list:
                    comment_list.append(comment_dict)

            comment_pages = sep.xpath('//li[@class="lzl_li_pager j_lzl_l_p lzl_li_pager_s"]/p').xpath('string(.)').extract()[0]

            # 当尾页不在页数里面时，说明此楼内楼已经结束了/页数是10页了， 这2种情况出现一种，那就进入下一个楼内楼
            if '尾页' not in comment_pages or pn>self.max_comment_page:
                request = self.next_comment(the_tiezi, tid, posi, post_count)
                yield request

            #继续循环这个楼层的楼内楼，页数+1，进入下一页的楼内楼
            else:
                pn=pn+1
                url = 'https://tieba.baidu.com/p/comment?tid=%s&pid=%s&pn=%s' % (tid, pid, pn)
                yield Request(url,  callback=self.comment_list,dont_filter=True,
                              meta={'the_tiezi': copy.deepcopy(the_tiezi), 'posi': posi,
                                    'pn': pn,'post_count':post_count})


    def next_comment(self,the_tiezi,tid,posi,post_count):
        '''作用：只用于楼内楼，循环楼层，若有楼内楼则进入parse爬取数据，直到最后一楼，然后保存
        the_tiezi：整个帖子的数据
        posi：已经添加了的楼内楼的楼层在post_list的位置，
        post_count：楼层总数，

        假设post_count共4个，posi是0,1,2,3 ；range(0,4)实际是0,1,2,3
        爬完最后一个，posi=3，而循环的话，肯定得3+1代表从下一个元素开始，
        rang(4,4)是没有元素的，所以结果是range(posi +1, post_count + 1)
        此时i==4==post_count，完成了，保存

        判断楼层总数：···为0，帖子没爬到，直接保存
                    ···以posi+1，post_count+1为循环，判断是否爬完：---最后一个，返回item进入pipelines保存
                                                                ---没爬完，是否有楼内楼：***有，中断循环，设定为第一页进入楼内楼parse爬取数据
                                                                                       ***没有，继续循环'''

        posi=posi + 1

        #没有楼层，那就是帖子刚爬了标题就被删了，return直接中断保存
        if post_count == 0:
            print('帖子没爬就被删了')
            the_tiezi['file_name']=the_tiezi['file_name'].replace(str(self.tid),r'被删了：'+str(self.tid))
            return the_tiezi

        for i in range(posi , post_count + 1):
            #是否是最后一个
            # (比如共10个楼层，post_list那就是0~9，最后一个时，传入的posi=9，循环是range(10,11)，此时i=post_count=10,结束)
            if i == post_count:
                self.return_items_count+=1   #实际返回的item 总数
                self.log_Crawling.tiezi_info(copy.deepcopy(the_tiezi))  # 需要deep.copy不然the_tiezi会被修改
                print('爬完了该帖子的第%s个十页'%self.return_items_count)
                return the_tiezi

            else:
                #此楼层有楼内楼时，就会return中断循环，进入楼内楼parse，否则跳过继续循环
                #此时i就是该楼层在post_list的位置
                if the_tiezi['post_list'][i]['comment_num'] > 0:
                    # 没爬过的楼层得添加楼内楼list
                    if the_tiezi['post_list'][i].get('comment_list')  is  None:
                        the_tiezi['post_list'][i]['comment_list'] = []

                    pid = the_tiezi['post_list'][i]['pid']
                    #进入下一个parse，注意的meta是位置posi，第一页
                    url = 'https://tieba.baidu.com/p/comment?tid=%s&pid=%s&pn=%s' % (tid, pid, 1)
                    request=Request(url,  callback=self.comment_list,dont_filter=True,
                                  meta={'the_tiezi': copy.deepcopy(the_tiezi), 'posi': i, 'pn': 1,
                                        'post_count': post_count})
                    return request


#==========================================================================================================
    def build_dir(self):
        # 设定贴吧文件夹，不存在就创建
        self.path = self.dir_path + os.sep +self.kw
        if os.path.exists(self.path) is False:
            os.mkdir(self.path)
        # 设定里面的旧帖子文件夹，不存在就创建
        self.old_file_path = self.path + os.sep + '旧帖子'
        if os.path.exists(self.old_file_path) is False:
            os.mkdir(self.old_file_path)


    def the_tiezi(self,response):
        '''输入的是帖子的第一页的response，定位到标题等数据
            返回标题、发帖人等信息组成的 dict'''
        tiezi = TieziItem()
        pages = response.xpath('//li[@class="l_reply_num"]/span[2]/text()').extract_first()  # 该帖子有多少页
        title = response.xpath('//h3[@class="core_title_txt pull-left text-overflow  "]/text()').extract_first()
        reply_num = response.xpath('//li[@class="l_reply_num"]/span[1]/text()').extract_first()
        one_post = response.xpath('//div[@class="l_post l_post_bright j_l_post clearfix  "]')
        data = json.loads(one_post.xpath("@data-field").extract_first())  # 相当于大纲吧
        author = data['author']['user_name']  # 发帖人,原ID
        tiezi['title'] = title
        tiezi['author'] = author
        tiezi['tid'] = int(self.tid)
        tiezi['pages'] = int(pages)
        tiezi['reply_num'] = int(reply_num)
        tiezi['post_list'] = []

        kw=response.xpath('//a[@class="card_title_fname"]/text()').extract_first()
        self.kw=re.findall(r'(\S*)吧',kw)[0]#重新设定所在的贴吧
        config_file = Open_json('config')
        config = config_file.read()[0]
        config['tieba_name']=self.kw
        config_file.rewrite(config)
        return dict(tiezi)


    def post_dict(self,one_post,tid,page):
        '''输入的是单个楼层的原始信息，
            返回楼层的 发帖人、时间、内容等组成的 dict'''
        post_dict = {}
        data = json.loads(one_post.xpath("@data-field").extract_first())  # 相当于大纲吧
        author = data['author']['user_name']  # 发帖人,原ID
        pid = data['content']['post_id']  # pid 楼层的id
        comment_num = data['content']['comment_num']  # 楼内回复数量
        floor = one_post.xpath('.//div[@class="post-tail-wrap"]/span[last()-1]/text()').extract_first()  # 第几楼
        p_time = one_post.xpath('.//div[@class="post-tail-wrap"]/span[last()]/text()').extract_first()  # 回复时间

        the_content = one_post.xpath('.//div[@class="d_post_content j_d_post_content "]')  # 定位帖子内容
        # 文字跟图片、自定义表情提取(忽略了表情)
        content = the_content.xpath(
            './text()|./img[@class="BDE_Image"]/@src|./img[@class="BDE_Meme"]/@src').extract()
        content = ' '.join(content).strip()  # 提取的内容list转为字符串

        post_dict['author'] = author
        post_dict['floor'] = floor
        post_dict['time'] = p_time
        post_dict['page'] = page
        post_dict['pid'] = pid
        post_dict['comment_num'] = int(comment_num)
        post_dict['content'] = content

        voice = the_content.xpath('.//a[@class="voice_player_inner"]').extract()  # 如果有语音回复，就不为空
        if voice != []:
            post_dict['voice'] = 'https://tieba.baidu.com/voice/index?tid=%s&pid=%s' % (tid, pid)  # 语音回复的url
        return post_dict

    def comment_dict(self,one_comment,pn,tid):
        '''输入的是单个楼内楼的原始信息，
             返回楼内楼的 发帖人、时间、内容等组成的 dict'''
        comment_dict = {}
        author = one_comment.xpath('.//a[@class="at j_user_card "]/text()').extract()[0]  # 发帖人，原ID
        content = one_comment.xpath('span[@class="lzl_content_main"]').xpath('string(.)').extract()[0].strip()  # 内容
        reply_time = one_comment.xpath('.//span[@class="lzl_time"]/text()').extract()[0]  # 发帖时间
        spid = one_comment.xpath('../a/@name').extract()[0]  # spid

        comment_dict['author'] = author
        comment_dict['content'] = content
        comment_dict['time'] = reply_time
        comment_dict['spid'] = spid
        comment_dict['page'] = pn
        voice = one_comment.xpath(
            'span[@class="lzl_content_main"]//a[@class="voice_player_inner"]').extract()  # 如果有语音回复，就不为空
        if voice != []:
            comment_dict['voice'] = 'https://tieba.baidu.com/voice/index?tid=%s&pid=%s' % (tid, spid)  # 语音回复的url
        return comment_dict


