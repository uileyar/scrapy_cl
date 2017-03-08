# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pymongo
import scrapy
import time
from spiders.util import *
from scrapy.pipelines.images import ImagesPipeline, FilesPipeline
from scrapy.exceptions import DropItem
import httplib2
import shutil


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


def get_file_name(title):
    return title[0:min(80, len(title))].replace('/', '-')


class CltestPipeline(object):
    def __init__(self, mongo_server, mongo_port, mongo_db, file_path, img_path, root_path):
        self.mongo_server = mongo_server
        self.mongo_port = mongo_port
        self.mongo_db = mongo_db
        self.file_path = file_path
        self.img_path = img_path
        self.root_path = root_path

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_server=crawler.settings.get('MONGO_SERVER'),
            mongo_port=crawler.settings.get('MONGO_PORT', 21008),
            mongo_db=crawler.settings.get('MONGO_DB'),
            file_path=crawler.settings.get('FILES_STORE'),
            img_path=crawler.settings.get('IMAGES_STORE'),
            root_path=crawler.settings.get('CL_STORE'),
        )

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
        collection_name = item.__class__.__name__.lower()
        it = self.db[collection_name].find_one({'detail_url': item.get('detail_url')})
        if it and len(item_images) == len(it.get('images', [])) and len(item_files) == len(it.get('files', [])):
            raise DropItem()
        # logging.info('item={0}'.format(item))
        item['create_time'] = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        des_dir = os.path.join(self.root_path, item['create_time'], item.get('type'))
        ensure_dir(des_dir)

        for item_img in item_images:
            src_file = os.path.join(self.img_path, item_img.get('path'))
            des_file = os.path.join(des_dir, get_file_name('title'))
            if img_num > 1:
                des_file += str(img_num)
            try:
                shutil.copy(src_file, '{}.jpg'.format(des_file))
                img_num += 1
            except Exception as e:
                logging.error('error={0}; title_len={1}'.format(e, len(item.get('title'))))

        for item_file in item_files:
            src_file = os.path.join(self.file_path, item_file.get('path'))
            des_file = os.path.join(des_dir, get_file_name('title'))
            try:
                shutil.copy(src_file, '{}.torrent'.format(des_file))
                file_num += 1
            except Exception as e:
                logging.error('error={0}; title_len={1}'.format(e, len(item.get('title'))))

        # get_file(item.get('pic_url'), os.path.join(self.root_path, item.get('title').replace('/', '-') + '.jpg'))
        # get_file(item.get('torrent_url'), os.path.join(self.root_path, item.get('title').replace('/', '-') + '.torrent'))
        if img_num == len(item.get('image_urls', [])) and file_num == len(item.get('file_urls', [])):
            pass
            # self.db[collection_name].insert(dict(item))
        return item


class ClImagePipeline(ImagesPipeline):
    def __init__(self, file_path, img_path, root_path):
        self.file_path = file_path
        self.img_path = img_path
        self.root_path = root_path

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            file_path=crawler.settings.get('FILES_STORE'),
            img_path=crawler.settings.get('IMAGES_STORE'),
            root_path=crawler.settings.get('CL_STORE')
        )

    def get_media_requests(self, item, info):
        for image_url in item['image_urls']:
            logging.info('get image_url={0}'.format(image_url))
            yield scrapy.Request(str(image_url), dont_filter=True)

    def item_completed(self, results, item, info):
        file_paths = [x['path'] for ok, x in results if ok]
        if not file_paths:
            logging.warning('no img results={0}'.format(results))
            raise DropItem("Item contains no image file")

        for file in file_paths:
            src_file = os.path.join(self.img_path, file)
            shutil.copy(src_file, os.path.join(self.root_path, item.get('title').replace('/', '-') + '.jpg'))
        return item


class ClFilePipeline(FilesPipeline):
    def get_media_requests(self, item, info):
        for file_url in item['file_urls']:
            logging.debug('get file_url={0}'.format(file_url))
            yield scrapy.Request(file_url)

    def item_completed(self, results, item, info):
        file_paths = [x['path'] for ok, x in results if ok]
        if not file_paths:
            # logging.warning('no file results={0}, item={1}, info={2}'.format(results, item, info))
            raise DropItem("Item contains no torrent file")

        for file in file_paths:
            shutil.copy(file, os.path.join('/data/scrapy/download', item.get('title').replace('/', '-') + '.torrent'))
        return item
