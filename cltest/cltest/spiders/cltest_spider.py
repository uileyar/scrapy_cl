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

TYPE_YOUMA = 'youma'
TYPE_YOUMA_ZT = 'youmazhuantie'
TYPE_WUMA = 'wuma'
TYPE_WUMA_ZT = 'wumazhuantie'
TYPE_XINSHIDAI = 'xinshidai'
TYPE_GAIDAER = 'gaidaer'
TYPE_DEFAULT = 'hehe'


ad_img_list =[
    'http://imgroom.net/images/2016/03/30/700a2edb.jpg',
]


def get_image_urls_1(div):
    img_list = []
    for src in div.css('img::attr(src)').extract():
        if '.jpg' not in src:
            continue
        if src in ad_img_list:
            continue
        if 'http://oi' in src:
            continue
        img_list.append(str(src))
        break
    return img_list


def get_image_urls_2(div):
    img_list = []
    for src in div.css('input::attr(src)').extract():
        if '.jpg' not in src:
            continue
        if src in ad_img_list:
            continue
        if 'http://oi' in src:
            continue
        img_list.append(str(src))
    #print img_list
    return img_list


def get_image_urls(div, type):
    if type in [TYPE_YOUMA, TYPE_YOUMA_ZT, TYPE_WUMA, TYPE_WUMA_ZT]:
        return get_image_urls_1(div)
    elif type in [TYPE_XINSHIDAI, TYPE_GAIDAER]:
        return get_image_urls_2(div)
    else:
        return []


def get_page(url):
    query = urlparse.urlparse(url).query
    page = urlparse.parse_qs(query, True).get('page')
    if page:
        return int(page[0])
    return 0


def get_type(url):
    query = urlparse.urlparse(url).query
    fid = urlparse.parse_qs(query, True).get('fid')
    if fid[0] == '15':
        return TYPE_YOUMA
    elif fid[0] == '18':
        return TYPE_YOUMA_ZT
    elif fid[0] == '2':
        return TYPE_WUMA
    elif fid[0] == '17':
        return TYPE_WUMA_ZT
    elif fid[0] == '8':
        return TYPE_XINSHIDAI
    elif fid[0] == '16':
        return TYPE_GAIDAER
    return TYPE_DEFAULT


class CltestSpider(scrapy.Spider):
    MAX_PAGE = 2
    name = "cl"
    allowed_domains = ["cl.wrvhb.com"]
    start_urls = [
        'http://cl.wrvhb.com/thread0806.php?fid=15',  #yazhouyouma
        'http://cl.wrvhb.com/thread0806.php?fid=18',  #yazhouyoumazhuantie

        'http://cl.wrvhb.com/thread0806.php?fid=2',  #yazhouwuma
        'http://cl.wrvhb.com/thread0806.php?fid=17',  #yazhouwumazhuantie

        'http://cl.wrvhb.com/thread0806.php?fid=8',  #xinshidai
        'http://cl.wrvhb.com/thread0806.php?fid=16',  #gaidaer
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
            self.logger.debug('detail_url={0}'.format(url))
            meta = {'item': item}
            yield scrapy.Request(url, callback=self.parse_detail, meta=meta)

        for next in response.css('div.pages a'):
            if next.css("::text").extract() and u'下一頁' != next.css("::text").extract()[0]:
                continue
            href = next.css("::attr(href)")
            if not href:
                continue
            url = response.urljoin(href.extract()[0])
            page = get_page(url)
            if page and page <= self.MAX_PAGE:
                self.logger.info('start next url={0}'.format(url))
                yield scrapy.Request(url, callback=self.parse)
                break

    def parse_detail(self, response):
        # save_file(response.url.replace('/', '-'), response.body)
        item = response.meta['item']
        div = response.css('div.tpc_content.do_not_catch')
        if div:
            item['detail_url'] = response.url
            item['image_urls'] = get_image_urls(div, item['type'])
            for a in div.css('a'):
                style = a.css("::attr(style)")
                url = a.css("::text")
                if not style or not url:
                    continue
                url = url.extract()[0]
                style = style.extract()[0]
                if ('http://www.' in url) and ('color:#008000;' in style):
                    self.logger.debug('url={0}, style={1}'.format(url, style))
                    offer = url.find('http://www.')
                    url = url[offer:]
                    item['download_url'] = url
                    meta = {'item': item}
                    #self.logger.debug('detail_url={0}, url={1}'.format(item['detail_url'], url))
                    yield scrapy.Request(url, callback=self.parse_download, meta=meta, dont_filter=True)
        if not item.get('download_url') and item['type'] in [TYPE_WUMA, TYPE_WUMA_ZT, TYPE_YOUMA, TYPE_YOUMA_ZT]:
            self.logger.warning('parse error title={0}, url={1}'.format(item['title'], response.url))
        else:
            yield item


    def parse_download(self, response):
        #save_file(response.url.replace('/', '-'), response.body)
        #print 'item={0},  url={1}'.format(response.meta.get('item'), response.url)
        item = response.meta['item']
        query = {}
        try:
            action = response.css('form::attr(action)').extract()[0]
            for input in response.css('input'):
                query[input.css('::attr(name)').extract()[0]] = input.css('::attr(value)').extract()[0]
            item['file_urls'] = [urlparse.urljoin(response.url, action) + '?' + urllib.urlencode(query)]
        except Exception as e:
            self.logger.error('parse_download fail:url={0}, detail_url={1}'.format(response.url, item['detail_url']))

        #print '{0}{1}?{2}'.format(host, action, urllib.urlencode(query))
        #self.logger.info('item={0}'.format(item))
        yield item