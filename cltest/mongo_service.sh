#! /bin/bash

log_prefix=/data/scrapy
port=21024

start_mongo() {
    echo "Starting mongo..."
    mongod --dbpath $log_prefix/mongo_data --port $port --fork --logpath $log_prefix/mongo_log/mongos.log
    #mongod --config $log_prefix/mongodb.conf
    echo "done."
}

stop_mongo() {
    echo "Stopping mongo..."
    mongo 127.0.0.1:$port/admin --eval "db.shutdownServer()"
    echo "done."
}

init_mongo(){
    echo "Init mongo..."

    echo "done."
}

repair_mongo(){
    #mongod --dbpath /data/db --repair --repairpath /data/db0
    echo "Repair mongo..."

    rm -rf $log_prefix/mongo_data/mongod.lock
    mongod --dbpath $log_prefix/mongo_data --repair

    echo "done."
}


if [ $1 == "start" ]
then
    start_mongo
elif [ $1 == "stop" ]
then
    stop_mongo
elif [ $1 == "init" ]
then
    start_mongo
    init_mongo
elif [ $1 == "repair" ]
then
    repair_mongo
fi
