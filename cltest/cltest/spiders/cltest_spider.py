#!/usr/bin/env python
# coding:utf-8
import sys
import urllib
import urlparse

reload(sys)
sys.setdefaultencoding('utf-8')
import scrapy
from cltest.items import CltestItem
from util import *

# scrapy crawl cl -L INFO


ad_img_list =[
    'http://imgroom.net/images/2016/03/30/700a2edb.jpg',
]

def get_type(url):
    if 'fid=15' in url:
        return 'youma'
    elif 'fid=2' in url:
        return 'wuma'
    return 'hehe'

def get_pic_url(div):
    for src in div.css('img::attr(src)').extract():
        if '.jpg' not in src:
            continue
        if src in ad_img_list:
            continue
        if 'http://oi' in src:
            continue
        return str(src)


class CltestSpider(scrapy.Spider):
    name = "cl"
    allowed_domains = ["cl.wrvhb.com"]
    start_urls = [
        "http://cl.wrvhb.com/thread0806.php?fid=15",
        'http://cl.wrvhb.com/thread0806.php?fid=2',

    ]

    def parse(self, response):
        #save_file(response.url.split("/")[-2] + '.html', response.body)
        self.logger.info('start url={0}'.format(response.url))

        for sel in response.css('tbody:last-of-type tr.tr3.t_one'):
            data = sel.css('td h3 a')
            if not data:
                continue
            item = CltestItem()
            item['title'] = data.css("::text").extract()[0]
            item['type'] = get_type(response.url)
            url = data.css("::attr(href)").extract()[0]
            url = response.urljoin(url)
            # print url
            meta = {'item': item}
            yield scrapy.Request(url, callback=self.parse_detail, meta=meta)

        for next in response.css('div.pages a'):
            href = next.css("::attr(href)")
            if href and ('javascript' not in href.extract()[0]):
                url = response.urljoin(href.extract()[0])
                try:
                    num = int(next.css("::text").extract()[0])
                except Exception as e:
                    continue
                if num < 3:
                    self.logger.info('start next url={0}'.format(url))
                    yield scrapy.Request(url, callback=self.parse)
                break

    def parse_detail(self, response):
        # save_file(response.url.replace('/', '-'), response.body)
        item = response.meta['item']
        #print 'title={0}, url={1}'.format(item['title'], response.url)
        div = response.css('div.tpc_content.do_not_catch')
        if div:
            item['detail_url'] = response.url
            item['pic_url'] = get_pic_url(div)
            item['image_urls'] = [item['pic_url']]
            for a in div.css('a'):
                for url in a.css("::text").extract():
                    if 'http://www.' in url:
                        offer = url.find('http://www.')
                        url = url[offer:]
                        item['download_url'] = url
                        meta = {'item': item}
                        #self.logger.debug('detail_url={0}, url={1}'.format(item['detail_url'], url))
                        yield scrapy.Request(url, callback=self.parse_download, meta=meta, dont_filter=True)
        if not item.get('download_url'):
            self.logger.warning('parse error title={0}, url={1}'.format(item['title'], response.url))


    def parse_download(self, response):
        #save_file(response.url.replace('/', '-'), response.body)
        #print 'item={0},  url={1}'.format(response.meta.get('item'), response.url)
        item = response.meta['item']
        query = {}
        try:
            action = response.css('form::attr(action)').extract()[0]
            for input in response.css('input'):
                query[input.css('::attr(name)').extract()[0]] = input.css('::attr(value)').extract()[0]
            item['torrent_url'] = urlparse.urljoin(response.url, action) + '?' + urllib.urlencode(query)
            item['file_urls'] = [item['torrent_url']]
        except Exception as e:
            self.logger.error('parse_download fail:url={0}'.format(response.url))

        #print '{0}{1}?{2}'.format(host, action, urllib.urlencode(query))
        #self.logger.info('item={0}'.format(item))
        return item