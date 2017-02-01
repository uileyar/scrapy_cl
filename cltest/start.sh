#! /bin/bash


start_cl() {
    echo "start_cl"
    scrapyd --pidfile /data/scrapy/scrapyd.pid -l /var/log/scrapyd/scrapyd.log &
    sleep 10
    curl http://localhost:6800/schedule.json -d project=cltest -d spider=cl
    echo "done."
}

retry_cl() {
    echo "retry_cl"
    curl http://localhost:6800/schedule.json -d project=cltest -d spider=cl
    echo "done."
}

if [ $1 == "start" ]
then
    start_cl
elif [ $1 == "retry" ]
then
    retry_cl
fi