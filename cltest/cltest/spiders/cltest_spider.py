#!/usr/bin/env python
# coding:utf-8
import sys

reload(sys)
sys.setdefaultencoding('utf-8')
import scrapy
from cltest.items import CltestItem
from util import *


class CltestSpider(scrapy.Spider):
    name = "cl"
    allowed_domains = ["cl.wrvhb.com"]
    start_urls = [
        "http://cl.wrvhb.com/thread0806.php?fid=15",

    ]

    def parse(self, response):
        # save_file(response.url.split("/")[-2] + '.html', response.body)
        print 'in parse'
        for sel in response.css('tbody:last-of-type tr.tr3.t_one'):
            data = sel.css('td h3 a')
            if not data:
                continue
            item = CltestItem()
            item['title'] = data.css("::text").extract()[0]
            url = data.css("::attr(href)").extract()[0]
            url = response.urljoin(url)
            # print url
            meta = {'item': item}
            yield scrapy.Request(url, callback=self.parse_detail, meta=meta)

    def parse_detail(self, response):
        # save_file(response.url.replace('/', '-'), response.body)
        item = response.meta['item']
        #print 'title={0}, url={1}'.format(item['title'], response.url)
        div = response.css('div.tpc_content.do_not_catch')
        if div:
            item['detail_url'] = response.url
            item['pic_url'] = div.css('img::attr(src)').extract()[0]
            for a in div.css('a'):
                for url in a.css("::text").extract():
                    if 'http://www.' in url:
                        item['download_url'] = url
                        meta = {'item': item}
                        yield scrapy.Request(url, callback=self.parse_download, meta=meta, dont_filter=True)
        if not item.get('download_url'):
            pass
            #print 'parse error title={0}, url={1}'.format(item['title'], response.url)


    def parse_download(self, response):
        #print 'item={0},  url={1}'.format(response.meta.get('item'), response.url)
        item = response.meta['item']
        save_file(response.url.replace('/', '-'), response.body)
        return item