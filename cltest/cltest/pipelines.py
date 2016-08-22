# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pymongo
from spiders.util import *
from scrapy.exceptions import DropItem
import httplib2


def get_file(url, file_path):
    http = httplib2.Http(timeout=60)
    for retry in range(3):
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
            root_path=crawler.settings.get('FILES_STORE')
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

        get_file(item.get('pic_url'), os.path.join(self.root_path, item.get('title').replace('/', '-') + '.jpg'))
        get_file(item.get('torrent_url'), os.path.join(self.root_path, item.get('title').replace('/', '-') + '.torrent'))
        # self.db[collection_name].insert(dict(item))
        return item
