
echo "Starting mongo..."
start /b mongod --dbpath H:/data/scrapy/mongo_data --port 21024 --logpath H:/data/scrapy/mongo_log/mongos.log
echo "mongo done."

pause