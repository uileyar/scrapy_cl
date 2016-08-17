#!/usr/bin/env python
# coding:utf-8



if __name__ == '__main__':
    item = CltestItem()
    item['title'] = data.css("::text").extract()[0]
    print item['title']
    item['link'] = data.css("::attr(href)").extract()[0]
    #http://www.rmdown.com/download.php?ref=162f0ef51603cd3933ca4f953fee8f30ad513b024d0&reff=MTQ3MTQ0NTk0MQ%3D%3D&submit=download