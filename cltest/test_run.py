#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from optparse import OptionParser
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


def _run_spiders(spider_name):
    process = CrawlerProcess(get_project_settings())
    process.crawl(spider_name)
    process.start()
    process.stop()


def main():
    parser = OptionParser("myprog[ -m <mode>]", version="%prog 1.0")
    parser.add_option("-n", "--name", action="store", dest="name", default='cl', help="cl")
    (options, args) = parser.parse_args()

    spider_name = options.name

    try:
        _run_spiders(spider_name)
    except Exception as e:
        print('{}: error={}'.format(spider_name, e))


if __name__ == '__main__':
    main()
