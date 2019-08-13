import scrapy.commands.crawl as crawl
from scrapy.exceptions import UsageError
from scrapy.commands import ScrapyCommand
import os
'''
设定步骤：
》add_options添加可输入的参数(帖子tid、页数范围、存储路径)
》run设定spider.setting里的各个参数，启动对应的spider
    》设定贴吧名
    》设定多个参数(set_args)：设定tid、存储路径、页数范围
    》根据tid，来启动贴吧spider/帖子spider'''

class Command(crawl.Command):
    def syntax(self):
        return "<tieba_name> "

    def short_desc(self):
        return "Crawl tieba"

    def long_desc(self):
        return "Crawl baidu tieba data or one tiezi data."

        # 上面的好像没什么用，相当于log把

    def add_options(self, parser):
        ScrapyCommand.add_options(self, parser)
        parser.add_option("-a", dest="spargs", action="append", default=[], metavar="NAME=VALUE",
                          help="set spider argument (may be repeated)")
        parser.add_option("-o", "--output", metavar="FILE",
                          help="dump scraped items into FILE (use - for stdout)")
        parser.add_option("-t", "--output-format", metavar="FORMAT",
                          help="format to use for dumping items with -o")
        # 点评
        # -a就是常规的设定传入参数了  -a后 接  url='www.baidu.com'
        # -o -t 就是设定输出的格式
        # cmdline.execute("scrapy crawl lianxi -o info.csv -t csv".split())


        # 下面这些就是自己自定义的了
        # dest应该是调用时opts的属性
        # nargs 应该是参数数量？
        # action="store_true" 这是爬虫过程中才能用？还是说后面不需要跟参数？
        parser.add_option("-t", "--tid", nargs=1,  dest="tid", default=None,
                          help="设定爬取帖子的tid")
        parser.add_option("-p", "--pages", nargs=2, type="int", dest="pages", default=[],
                          help="设定爬取贴吧或者某个帖子的页数范围")
        parser.add_option("-d", "--dirpath", type="str", dest="dir_path", default="",
                          help='设定爬取的json文件存放路径')

    def run(self, args, opts):
        #设定要爬的贴吧
        opts.tid=eval(opts.tid)

        #设定页数、存放文件等
        self.set_args(args, opts)

        #设定了tid，那就是爬单个帖子了，否则就启动爬某个贴吧
        if opts.tid:
            self.crawler_process.crawl('one_tiezi', **opts.spargs)
        else:
            self.crawler_process.crawl('one_tieba', **opts.spargs)
        self.crawler_process.start()


    def set_args(self, args, opts):
        '''设定贴吧名、tid、dir_path、pages放进settings中'''

        #设定贴吧名
        self.settings.set('tieba_name', args[0], priority='cmdline')#优先权是给cmdline？

        #如果传入tid，那就设定好爬取帖子的页数
        #否则，传入的页数范围，就是所爬取贴吧的页数

        if opts.tid:
            self.settings.set('tid', opts.tid, priority='cmdline')
            self.settings.set('start_tiezi_page', opts.pages[0], priority='cmdline')
            self.settings.set('end_tiezi_page', opts.pages[1], priority='cmdline')
        else:
            self.settings.set('start_kw_page', opts.pages[0], priority='cmdline')
            self.settings.set('end_kw_page', opts.pages[1], priority='cmdline')

        #没设定存放路径，那就设定为贴吧，如果不存在，那就创建
        self.settings.set('dir_path', opts.dir_path, priority='cmdline')

    #     #设定爬取贴吧的页数或者是爬取帖子的页数
    #     self.set_pages(opts.tid,opts.pages)
    #
    #
    # def set_pages(self, tid,pages):
    #     '''对页数范围进行规范，然后根据是爬取贴吧，还是爬取帖子设定页数'''
    #     if len(pages) != 2:
    #         raise UsageError("特么的你输入页数范围啊！!!")
    #     else:
    #         begin_page = pages[0]
    #         end_page = pages[1]
    #     if begin_page <= 0:
    #         raise UsageError("初始页起码是第一页！!")
    #     if begin_page > end_page:
    #         raise UsageError("初始页应该小于最后一页!")
    #
    #     #存在tid，那就是爬取某个帖子，设定为该帖子的页数范围，否则就是某个贴吧的页数范围
    #     if tid:
    #         self.settings.set('start_tiezi_page', begin_page, priority='cmdline')
    #         self.settings.set('end_tiezi_page', end_page, priority='cmdline')
    #     else:
    #         self.settings.set('start_kw_page', begin_page, priority='cmdline')
    #         self.settings.set('end_kw_page', end_page, priority='cmdline')
    #     # 这是把page放进settings的步骤，priority='cmdline' 优先权是给cmdline？
    #
    #

