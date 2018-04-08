import sys
sys.path.append('../')
from pymongo import MongoClient
import conf
from bson.objectid import ObjectId


# mongo object already threadpool, so just create the mongo instance instead of using singleton schema
def get_mongo_conn2coaldb():
    return MongoClient(conf.mongo_url)[conf.mongo_db_name]

def insert2mongo(collect, _id, doc):
    try:
        doc['_id'] = ObjectId(_id)
        collect.insert(doc)
    except Exception as e:
        print('insert %s failed, for %s' %(_id, str(e)))
        return False
    return True
        
    