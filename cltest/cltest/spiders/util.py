#!/usr/bin/env python
# coding:utf-8
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import hashlib
import os
import logging
import logging.config

import json


def md5checksum(filename):
    m = hashlib.md5()
    try:
        with open(filename, 'rb') as fp:
            while True:
                blk = fp.read(1024 * 1024 * 1)
                if not blk: break
                m.update(blk)
    except Exception as e:
        logging.error('error=%s',str(e))
    return m.hexdigest()


def ensure_dir(directory):
    if not os.path.exists(directory):
        logging.info("Creating directory: %s" % directory)
        try:
            os.makedirs(directory)
        except OSError, e:
            logging.debug("makedirs Faild: %s", str(e))


def file_walk(root):
    wuf_list = []
    for rt, dirs, files in os.walk(root):
        # print('({0}) ({1}) ({2})'.format(rt, dirs, files))
        for f in files:
            wuf_list.append(os.path.join(rt, f))
    logging.info("total file num = %d", len(wuf_list))
    return wuf_list


def split_file(file):
    '''
    :param file: /clip/id/korean drama/Batman vs Superman/1-1.mp4
    :return:
    '''
    file_type = language_type = video_type = video_name = item_name = ''
    fs = file.split(os.sep)
    if len(fs) < 4:
        logging.error("error file = %s", file)
    elif len(fs) == 5:
        file_type =  fs[0]
        language_type = fs[1]
        video_type = fs[2]
        video_name = fs[3]
        item_name = fs[4]
    else:
        language_type = fs[0]
        video_type = fs[1]
        video_name = fs[2]
        item_name = fs[3]
    return file_type, language_type, video_type, video_name, item_name


def relative_file_path(abs_file_path, abs_dir=None):
    if not abs_dir:
        rel_file_path = abs_file_path
    else:
        rel_file_path = abs_file_path.split(abs_dir)[1]
    if rel_file_path and rel_file_path[0] in '\\/':
        rel_file_path = rel_file_path[1:]
    return rel_file_path


def print_map(prefix_str, in_map, max_num=sys.maxint):
    i = 1
    if len(in_map) <= max_num:
        for v in in_map:
            logging.info('{0} {1}: {2}={3}'.format(prefix_str, i, v, in_map[v]))
            i+=1
    else:
        logging.error('{0} too much {1} > {2}, will no show detail info !!!'.format(prefix_str, len(in_map), max_num))
    logging.info('%s num = %d', prefix_str, len(in_map))


def print_list(prefix_str, in_list, max_num=sys.maxint):
    i = 1
    if len(in_list) <= max_num:
        for v in in_list:
            logging.info('{0} {1}: {2}'.format(prefix_str, i, v))
            i+=1
    else:
        logging.error('{0} too much {1} > {2}, will no show detail info !!!'.format(prefix_str, len(in_list), max_num))
    logging.info('%s num = %d', prefix_str, len(in_list))


def save_to_json(file_path, data):
    f=open(file_path, 'wb')
    if not f:
        return
    f.write(json.dumps(data, sort_keys=True, indent=2))
    f.close()


def load_json(file_path):
    f=open(file_path)
    if not f:
        return
    data = json.loads(f.read())
    f.close()
    #b = json.loads('{"mimeType": "video/mp4", "name": "Yong-Pal Episode 1(Part 4)-360p.MP4", "webContentLink": "https://docs.google.com/uc?id=0B0VS8-zQCcJmZmo5TUJnRndnRGs&export=download", "parents": ["0B0VS8-zQCcJmSVlrNEd0QWt2bHc"], "shared": false, "id": "0B0VS8-zQCcJmZmo5TUJnRndnRGs", "md5Checksum": "3f1e406b0adaede73d59cf579cff8077"}')
    return data


def save_file(file_path, data):
    ensure_dir(os.path.dirname(file_path))
    with open(file_path, 'wb') as f:
        f.write(data)


def main():
    # file_walk(ROOT_PATH)
    print md5checksum('/data/Descendants of the Sun E01(Part 1)-360p.MP4')
    #print get_item_title('Heroes Reborn Season 1 E1-5-360p.MP4', FILE_TYPE_US_DRAMA)
    #print get_item_title('Heroes Reborn Season 1 E1&2-5-360p.MP4', FILE_TYPE_US_DRAMA)


if __name__ == '__main__':
    main()
