# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class TiebaItem(scrapy.Item):

    title=scrapy.Field()
    author = scrapy.Field()
    tid = scrapy.Field()
    pages = scrapy.Field()
    reply_num = scrapy.Field()
    last_reply_author = scrapy.Field()
    last_reply_time = scrapy.Field()
    post_list = scrapy.Field()
    #page_range = scrapy.Field()

class TieziItem(scrapy.Item):

    title=scrapy.Field()
    author = scrapy.Field()
    tid = scrapy.Field()
    pages = scrapy.Field()
    reply_num = scrapy.Field()
    post_list = scrapy.Field()
    file_name = scrapy.Field()
    #last_reply_time = scrapy.Field()
    #page_range = scrapy.Field()


