#!/usr/bin/env python
# coding:utf-8

from urllib import parse
import scrapy
from cltest.items import CltestItem
from cltest.spiders.util import *

# scrapy crawl cl -L INFO

CLTEST_HOST = 'cl.62k.site'
CL_MAX_PAGE = 4

TYPE_DEFAULT = 'hh'
FOLDER_MAP = {
    # 'wm': {'fid': '2', 'num': 1, 'max_page': CL_MAX_PAGE, 'intro': 'yazhouwuma'},
    # 'xsd': {'fid': '8', 'num': 999, 'max_page': 1, 'd_url': False, 'intro': 'xinshidai'},
    'ym': {'fid': '15', 'num': 1, 'max_page': CL_MAX_PAGE, 'intro': 'yazhouyouma'},
    # 'gder': {'fid': '16', 'num': 999, 'max_page': 1, 'd_url': False, 'intro': 'gaidaer'},
    'gcyc': {'fid': '25', 'num': 8, 'max_page': CL_MAX_PAGE, 'intro': 'guochanyuanchuang'},
    'zzyc': {'fid': '26', 'num': 1, 'max_page': CL_MAX_PAGE*2, 'intro': 'zhongziyuanchuang'},
    TYPE_DEFAULT: {'fid': 'default', 'num': 1, 'max_page': CL_MAX_PAGE, 'intro': 'default'},
}

ad_img_list = [
    'http://imgroom.net/images/2016/03/30/700a2edb.jpg',
    'http://kk.51688.cc/ya/xv92.jpg',
    'http://kk.51688.cc/ya/283076.jpg',
    'http://dio66.net/images/olo_1000x80.jpg',
    # 'http://dio889.net/images/blr-880-80-4.jpg',
]


def get_page(url):
    query = parse.urlparse(url).query
    page = parse.parse_qs(query, True).get('page')
    if page:
        return int(page[0])
    return 0


def get_type(url):
    query = parse.urlparse(url).query
    fid = parse.parse_qs(query, True).get('fid')[0]
    for f_type, v in FOLDER_MAP.items():
        if v.get('fid') == fid:
            return f_type
    return TYPE_DEFAULT


class CltestSpider(scrapy.Spider):
    name = "cl"
    allowed_domains = [CLTEST_HOST]

    def get_image_urls(self, div, f_type):
        num = FOLDER_MAP.get(f_type).get('num')
        img_list = []
        temp_srcs = []
        for data_src in div.css('img::attr(data-src)').extract():
            temp_srcs.append(data_src)
            src = data_src.replace('.th.jpg', '.jpg')
            if src in ad_img_list:
                continue
            if ('http://www.xoimg.club' in src) or ('http://oi' in src) or ('http://kk.51688.cc' in src) or ('http://dio889.net/images' in src):
                continue
            # self.logger.info('image src={}'.format(src))
            if ('.jpg' in src) or ('.jpeg' in src):
                img_list.append(str(src))
            if len(img_list) >= num:
                break
        if not img_list:
            for src in div.css('input::attr(src)').extract():
                if src in ad_img_list:
                    continue
                if ('.jpg' in src) or ('.jpeg' in src):
                    img_list.append(str(src))
                if len(img_list) >= num:
                    break
        if not img_list:
            self.logger.error('parse imgs={}'.format(temp_srcs))
        return img_list

    def start_requests(self):
        for f_type, v in FOLDER_MAP.items():
            url = 'http://{}/thread0806.php?fid={}'.format(CLTEST_HOST, v.get('fid'))
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        # save_file(response.url.split("/")[-2] + '.html', response.body)
        # self.logger.info('start url={0}'.format(response.url))
        f_type = get_type(response.url)
        max_page = FOLDER_MAP.get(f_type).get('max_page')
        for sel in response.css('tbody:last-of-type tr.tr3.t_one'):
            data = sel.css('td h3 a')
            if not data:
                continue
            item = CltestItem()
            item['title'] = data.css("::text").extract()[0]
            item['type'] = f_type
            url = data.css("::attr(href)").extract()[0]
            url = response.urljoin(url)
            # self.logger.debug('detail_url={0}'.format(url))
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
            if page and page <= max_page:
                # self.logger.info('start next url={0}'.format(url))
                yield scrapy.Request(url, callback=self.parse)
                break

    def parse_detail(self, response):
        # save_file(os.path.basename(response.url), response.body)
        item = response.meta['item']
        div = response.css('div.tpc_content.do_not_catch')
        if div:
            item['detail_url'] = response.url
            item['image_urls'] = self.get_image_urls(div, item['type'])
            download_urls = []
            for a in div.css('a'):
                style = a.css("::attr(style)")
                referer_url = a.css("::attr(href)")
                text = a.css("::text")
                if not style or not referer_url or not text:
                    continue
                style = style.extract()[0]
                referer_url = referer_url.extract()[0]
                text = text.extract()[0]
                if ('color:#008000;' in style) or ('rgb(0, 128, 0)' in style):
                    if 'http://' not in text:
                        if 'rmdown' in referer_url:
                            referer_query = parse.urlparse(referer_url).query
                            referer_query = parse.urlparse(referer_query).query
                            hash_data = parse.parse_qs(referer_query, True).get('hash')
                            if not hash_data:
                                continue
                            download_urls.append('http://www.rmdown.com/link.php?hash={}'.format(hash_data[0]))
                            # logging.error('k1 text={}, url={}'.format(text.encode('gb18030'), url))
                            # logging.error('k1 text={}, url={}'.format(text, url))
                        else:
                            continue
                    else:
                        download_urls.append(text)
            if download_urls:
                item['download_url'] = download_urls[-1]
                meta = {'item': item}
                # self.logger.info('detail_url={0}, url={1}'.format(item['detail_url'], url))
                yield scrapy.Request(item['download_url'], headers={'Referer': referer_url}, callback=self.parse_download, meta=meta, dont_filter=True)
        if not item.get('download_url') and FOLDER_MAP.get(item['type']).get('d_url', True):
            self.logger.error('parse fail, url={}  title="{}"'.format(response.url, item['title']))
        else:
            yield item

    def parse_download(self, response):
        # save_file(os.path.join('/data', response.url.replace('/', '-')), response.body)
        # print('item={0},  url={1}'.format(response.meta.get('item'), response.url))
        # print(response.body)
        item = response.meta['item']
        query = {}
        try:
            action = response.css('form::attr(action)').extract()[0]
            for input in response.css('input'):
                query[input.css('::attr(name)').extract()[0]] = input.css('::attr(value)').extract()[0]
            item['file_urls'] = [parse.urljoin(response.url, action) + '?' + parse.urlencode(query)]
        except Exception as e:
            self.logger.error(f'parse_download fail:error={str(e)}, url={response.url}, detail_url={item["detail_url"]}')
        yield item
