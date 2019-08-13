# -*- mode: python -*-

import sys
sys.setrecursionlimit(5000)

block_cipher = None



a = Analysis(["begin.py"],
             pathex=["C:\\Users\\Administrator\\Desktop\\tieba"],

             binaries=[],

             datas=[(".\\scrapy","scrapy"),(".\\scrapy.cfg","."),(".\\tieba","tieba"),
                    (".\\my_tk.py","."),(".\\tieba_log.py","."),(".\\search.py","."),(".\\find_path.py","."),
                    (".\\wordcloud","wordcloud")],

             hiddenimports = ["scrapy.spiderloader",
                 "scrapy.statscollectors",
                 "scrapy.logformatter",
                 "scrapy.dupefilters",
                 "scrapy.squeues",
                 "scrapy.extensions.spiderstate",
                 "scrapy.extensions.corestats",
                 "scrapy.extensions.telnet",
                 "scrapy.extensions.logstats",
                 "scrapy.extensions.memusage",
                 "scrapy.extensions.memdebug",
                 "scrapy.extensions.feedexport",
                 "scrapy.extensions.closespider",
                 "scrapy.extensions.debug",
                 "scrapy.extensions.httpcache",
                 "scrapy.extensions.statsmailer",
                 "scrapy.extensions.throttle",
                 "scrapy.core.scheduler",
                 "scrapy.core.engine",
                 "scrapy.core.scraper",
                 "scrapy.core.spidermw",
                 "scrapy.core.downloader",
                 "scrapy.downloadermiddlewares.stats",
                 "scrapy.downloadermiddlewares.httpcache",
                 "scrapy.downloadermiddlewares.cookies",
                 "scrapy.downloadermiddlewares.useragent",
                 "scrapy.downloadermiddlewares.httpproxy",
                 "scrapy.downloadermiddlewares.ajaxcrawl",
                 "scrapy.downloadermiddlewares.chunked",
                 "scrapy.downloadermiddlewares.decompression",
                 "scrapy.downloadermiddlewares.defaultheaders",
                 "scrapy.downloadermiddlewares.downloadtimeout",
                 "scrapy.downloadermiddlewares.httpauth",
                 "scrapy.downloadermiddlewares.httpcompression",
                 "scrapy.downloadermiddlewares.redirect",
                 "scrapy.downloadermiddlewares.retry",
                 "scrapy.downloadermiddlewares.robotstxt",
                 "scrapy.spidermiddlewares.depth",
                 "scrapy.spidermiddlewares.httperror",
                 "scrapy.spidermiddlewares.offsite",
                 "scrapy.spidermiddlewares.referer",
                 "scrapy.spidermiddlewares.urllength",
                 "scrapy.pipelines",
                #"scrapy.pipelines.images",
                 "scrapy.core.downloader.handlers.http",
                 "scrapy.core.downloader.contextfactory",
                  "json", "csv", "re","scrapy",'copy','codecs',
                  'emoji','webbrowser','subprocess','shutil','urllib',
                  'numpy','PIL','wordcloud','matplotlib','datetime',
                  'jieba','traceback','subprocess','shutil','urllib'
                 ],


             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)


pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name="begin",
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False)
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name="begin")
