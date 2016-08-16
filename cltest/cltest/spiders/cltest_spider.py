#!/usr/bin/env python
# coding:utf-8

import scrapy
from cltest.items import CltestItem


class CltestSpider(scrapy.Spider):
    name = "cl"
    allowed_domains = ["cl.wrvhb.com"]
    start_urls = [
        "http://cl.wrvhb.com/thread0806.php?fid=15",

    ]

    def parse(self, response):
        # filename = response.url.split("/")[-2] + '.html'
        # with open(filename, 'wb') as f:
        #    f.write(response.body)
        print 'in parse'
        for sel in response.css('tbody:last-of-type tr.tr3.t_one'):
            data = sel.css('td h3 a')
            if not data:
                continue
            item = CltestItem()
            item['title'] = data.css("::text").extract()[0]
            item['link'] = data.css("::attr(href)").extract()[0]
            yield item
