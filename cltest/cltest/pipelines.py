# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pymongo
import scrapy
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


class CltestPipeline(object):
    def __init__(self, mongo_server, mongo_port, mongo_db, root_path):
        self.mongo_server = mongo_server
        self.mongo_port = mongo_port
        self.mongo_db = mongo_db
        self.root_path = root_path

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_server=crawler.settings.get('MONGO_SERVER'),
            mongo_port=crawler.settings.get('MONGO_PORT', 21005),
            mongo_db=crawler.settings.get('MONGO_DB'),
            root_path=crawler.settings.get('CL_STORE')
        )

    def open_spider(self, spider):
        logging.info('open CltestPipeline')
        self.connection = pymongo.MongoClient(self.mongo_server, self.mongo_port, tz_aware=True)
        self.db = self.connection[self.mongo_db]

    def close_spider(self, spider):
        logging.info('close CltestPipeline')
        self.connection.close()

    def process_item(self, item, spider):
        collection_name = item.__class__.__name__.lower()
        it = self.db[collection_name].find_one({'detail_url': item.get('detail_url')})
        if it:
            raise DropItem()
        logging.info('open CltestPipeline:process_item: url={0}'.format(item.get('detail_url')))
        #get_file(item.get('pic_url'), os.path.join(self.root_path, item.get('title').replace('/', '-') + '.jpg'))
        #get_file(item.get('torrent_url'), os.path.join(self.root_path, item.get('title').replace('/', '-') + '.torrent'))
        # self.db[collection_name].insert(dict(item))
        return item


class ClImagePipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        logging.info('open ClImagePipeline:get_media_requests')
        for image_url in item['image_urls']:
            yield scrapy.Request(image_url)

    def item_completed(self, results, item, info):
        logging.info('open ClImagePipeline:item_completed')
        file_paths = [x['path'] for ok, x in results if ok]
        if not file_paths:
            raise DropItem("Item contains no image file")

        for file in file_paths:
            shutil.copy(file, os.path.join('/data/scrapy/download', item.get('title').replace('/', '-') + '.jpg'))
        return item


class ClFilePipeline(FilesPipeline):
    def get_media_requests(self, item, info):
        logging.info('open ClFilePipeline:get_media_requests')
        for file_url in item['file_urls']:
            yield scrapy.Request(file_url)

    def item_completed(self, results, item, info):
        logging.info('open ClFilePipeline:item_completed')
        file_paths = [x['path'] for ok, x in results if ok]
        if not file_paths:
            raise DropItem("Item contains no torrent file")

        for file in file_paths:
            shutil.copy(file, os.path.join('/data/scrapy/download', item.get('title').replace('/', '-') + '.torrent'))
        return item