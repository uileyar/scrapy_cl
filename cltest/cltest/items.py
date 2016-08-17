# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class CltestItem(scrapy.Item):
    # define the fields for your item here like:
    title = scrapy.Field()
    detail_url = scrapy.Field()
    pic_url = scrapy.Field()
    local_pic_path = scrapy.Field()
    download_url = scrapy.Field()
    torrent_url = scrapy.Field()
    pass
