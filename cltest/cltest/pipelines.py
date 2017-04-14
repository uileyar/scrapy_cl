#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import pymongo
import scrapy
import time
from spiders.util import *
from scrapy.pipelines.images import ImagesPipeline, FilesPipeline
from scrapy.exceptions import DropItem
import httplib2
import shutil

from scrapy.http import Request
from scrapy.utils.python import to_bytes

MAX_FILE_LEN = 96


def get_file(url, file_path):
    http = httplib2.Http(timeout=60)
    for retry in range(5):
        try:
            (resp, content) = http.request(url, "GET")
            if resp['status'] != '200':
                for (k, v) in resp.items():
                    logging.error("%s: %s", k, v)
                continue
            save_file(file_path, content)
            return True
        except Exception, e:
            logging.error("fail:{0}".format(e))
    return False


def get_file_name(str_name, suffix_num, max_len=MAX_FILE_LEN):
    if isinstance(str_name, unicode):
        pass
        # logging.info('{} is unicode'.format(str_name))
    if isinstance(str_name, str):
        pass
        # logging.info('{} is str'.format(str_name))
    if suffix_num > 0:
        max_len -= 1
    new_name = str_name[0:min(max_len, len(str_name))].replace('/', '-')
    if suffix_num > 0:
        new_name += u'{}'.format(suffix_num)
    return new_name


class CltestPipeline(object):
    def __init__(self, mongo_server, mongo_port, mongo_db, file_path, img_path, root_path):
        self.mongo_server = mongo_server
        self.mongo_port = mongo_port
        self.mongo_db = mongo_db
        self.file_path = file_path
        self.img_path = img_path
        self.root_path = root_path
        self.connection = None
        self.db = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_server=crawler.settings.get('MONGO_SERVER'),
            mongo_port=crawler.settings.get('MONGO_PORT', 21024),
            mongo_db=crawler.settings.get('MONGO_DB'),
            file_path=crawler.settings.get('FILES_STORE'),
            img_path=crawler.settings.get('IMAGES_STORE'),
            root_path=crawler.settings.get('CL_STORE'), )

    def open_spider(self, spider):
        logging.info('open CltestPipeline')
        self.connection = pymongo.MongoClient(self.mongo_server, self.mongo_port, tz_aware=True)
        self.db = self.connection[self.mongo_db]

    def close_spider(self, spider):
        logging.info('close CltestPipeline')
        self.connection.close()

    def process_item(self, item, spider):
        img_num = file_num = 0
        item_images = item.get('images', [])
        item_files = item.get('files', [])
        item_title = item.get('title')
        collection_name = item.__class__.__name__.lower()
        it = self.db[collection_name].find_one({'detail_url': item.get('detail_url')})
        if it and len(item_images) == len(it.get('images', [])) and len(item_files) == len(it.get('files', [])):
            raise DropItem()
        # logging.info('item={0}'.format(item))
        item['create_time'] = time.strftime('%y%m%d', time.localtime(time.time()))
        des_dir = os.path.join(self.root_path, item['create_time'], item.get('type'))
        ensure_dir(des_dir)

        for item_img in item_images:
            src_file = os.path.join(self.img_path, item_img.get('path'))
            max_len = MAX_FILE_LEN
            while True:
                try:
                    shutil.copy(src_file, u'{}.jpg'.format(os.path.join(des_dir, get_file_name(item_title, img_num, max_len=max_len))))
                    img_num += 1
                    break
                except Exception as e:
                    # logging.error('img error={}; title="{}", len={}, m_len={}'.format(repr(e), item_title, len(item_title), max_len))
                    max_len -= 2

        for item_file in item_files:
            src_file = os.path.join(self.file_path, item_file.get('path'))
            max_len = MAX_FILE_LEN
            while True:
                try:
                    shutil.copy(src_file, u'{}.torrent'.format(os.path.join(des_dir, get_file_name(item_title, file_num, max_len=max_len))))
                    file_num += 1
                    break
                except Exception as e:
                    # logging.error('file error={}; title="{}", len={}, m_len={}'.format(repr(e), item_title, len(item_title), max_len))
                    max_len -= 2

        # get_file(item.get('pic_url'), os.path.join(self.root_path, item.get('title').replace('/', '-') + '.jpg'))
        # get_file(item.get('torrent_url'), os.path.join(self.root_path, item.get('title').replace('/', '-') + '.torrent'))
        if img_num == len(item.get('image_urls', [])) and file_num == len(item.get('file_urls', [])):
            pass
            self.db[collection_name].insert(dict(item))
        return item


class ClFilePipeline(FilesPipeline):
    def file_path(self, request, response=None, info=None):
        if not isinstance(request, Request):
            url = request
        else:
            url = request.url
        # logging.error('url={}'.format(url))

        media_guid = hashlib.sha1(to_bytes(url)).hexdigest()
        media_ext = os.path.splitext(url)[1].replace('?', '-')
        # logging.error('media_guid={}, media_ext={}'.format(media_guid, media_ext))
        return 'full/%s%s' % (media_guid, media_ext)


class ClFilePipeline2(FilesPipeline):
    def __init__(self, file_path, img_path, root_path):
        logging.error('file_path={}, img_path={}, root_path={}'.format(file_path, img_path, root_path))
        self.file_path = file_path
        self.img_path = img_path
        self.root_path = root_path

    @classmethod
    def from_crawler(cls, crawler):
        return cls(file_path=crawler.settings.get('FILES_STORE'), img_path=crawler.settings.get('IMAGES_STORE'),
            root_path=crawler.settings.get('CL_STORE'))

    def __get_media_requests(self, item, info):
        # logging.error('item={}, info={}'.format(item, info))
        for file_url in item.get('file_urls', []):
            logging.error('get file_url={}'.format(file_url))
            yield scrapy.Request(file_url)

    def __item_completed(self, results, item, info):
        for ok, x in results:
            if not ok:
                logging.error('x={}'.format(x))
        # logging.error('results={}'.format(results))
        file_paths = [x['path'] for ok, x in results if ok]
        if not file_paths:
            logging.warning('no files results={0}'.format(results))
            raise DropItem("Item contains no image file")
        logging.error('file_paths={}'.format(file_paths))
        for file in file_paths:
            src_file = os.path.join(self.img_path, file)
            shutil.copy(src_file, os.path.join(self.root_path, item.get('title').replace('/', '-') + '.jpg'))
        return item
