import sys
sys.path.append('../')
from pymongo import MongoClient
import conf


# mongo object already threadpool, so just create the mongo instance instead of using singleton schema
def get_mongo_conn2coaldb():
    return MongoClient(conf.mongo_url)[conf.mongo_db_name]
