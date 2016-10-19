#!/usr/bin/env bash

DUMP=/usr/bin/mongodump #mongodump备份文件执行路径
ROOT_DIR=/data/scrapy/db_bak
DB_HOSTS="127.0.0.1:21024"
DAYS=7 #DAYS=7代表删除7天前的备份，即只保留最近7天的备份

OUT_DIR=$ROOT_DIR/tmp #临时备份目录
TAR_DIR=$ROOT_DIR/list #备份存放路径

DATE=`date +%Y%m%d%H%M` #获取当前系统时间
TAR_BAK="_$DATE.tar.gz" #最终保存的数据库备份文件名

cd $OUT_DIR

for host in $DB_HOSTS;do
rm -rf $OUT_DIR/*
mkdir -p $OUT_DIR/$DATE
$DUMP -h $host -o $OUT_DIR/$DATE #备份全部数据库
tar -zcvf $TAR_DIR/$host$TAR_BAK $OUT_DIR/$DATE #压缩为.tar.gz格式
find $TAR_DIR/ -mtime +$DAYS -delete #删除7天前的备份文件

done

#还原数据：mongorestore -h 127.0.0.1:27017 -d $bak_db_name --directoryperdb 2014122310/$bak_db_name
#59 23 * * * sh ~/shell/mongo_bak.sh >>/data/logs/cron/logs.txt
