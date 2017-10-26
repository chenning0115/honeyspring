# This file include Segmenter and Indexer
import os
import sys
import bs4
import logging
import datetime as dt
import json
import random
import time
import pymongo
from pymongo import MongoClient
import jieba
import pprint
from collections import defaultdict
sys.path.append(os.path.dirname(__file__))
from myutils import get_mongo_conn2coaldb
from bson.objectid import ObjectId



class Segmenter(object):
    def __init__(self,_path_vocab = None,_path_stopwords = None):
        self.path_vocab = _path_vocab
        self.path_stopwords = _path_stopwords

        if  self.path_vocab:
            jieba.load_userdict(self.path_vocab)
        self.set_stopwords = set()
        if self.path_stopwords:
            with open(self.path_stopwords,'r') as fin:
                print('start to load stop words!')
                line = fin.readline()
                while(line!=''):
                    self.set_stopwords.add(line.strip())
                    line = fin.readline()
            print('load stop words successfully!')
    # segment the given context for search engien. stopwords will be removed if True
    def segment_for_search(self,context,stopwords=False):
        seg_gen = jieba.cut_for_search(context)
        res = []
        if stopwords:
            for w in seg_gen:
                if w not in self.set_stopwords:
                    res.append(w)
        else:
            res = list(seg_gen)
        return res
    
    # which method is the best query segmentation method?
    def segment_for_query(self,context):
        seg_gen = jieba.cut(context)
        res = []
        for w in seg_gen:
            if w in self.set_stopwords:
                res.append((w,0))
            else:
                res.append((w,1))
        return res
        
    
    
    def _get_seg_sequence(self,seg_list):
        d = {}
        for s in seg_list:
            if s not in d:
                d[s] = 1
            else:
                d[s] += 1
        return json.dumps(d)

    def segment_rawdata(self,collection_rawdata,collection_target):
        db_mongo = get_mongo_conn2coaldb()
        rawdata_gen = db_mongo[collection_rawdata].find()
        for index,item in enumerate(rawdata_gen):
            tmp__id,tmp_id,tmp_title,tmp_text = item['_id'],item['id'],item['title'],item['content']['text']
            if tmp_title.strip()=='' or tmp_text.strip() == '':
                continue
            res_title_seg = self.segment_for_search(tmp_title)
            res_text_seg = self.segment_for_search(tmp_text)
            db_mongo[collection_target].insert_one(
                {
                    "_id":tmp__id,
                    "id":tmp_id,
                    "title_seg":res_title_seg,
                    "title_seg_sequence":self._get_seg_sequence(res_title_seg),
                    "text_seg":res_text_seg,
                    "text_seg_sequence":self._get_seg_sequence(res_text_seg)
                }
            )
            if index % 100 == 0:
                print('success segment and insert %d' % index)

            

    


# now use json(about 50MB), and we can use redis database instead!!!
class MemoryIndexer(object):
    def __init__(self,_data_path = None):
        #key format is string(word)
        #value format is [{_id:ObjectId("59e418c92f773270ae125f3d"),title_num: 10,text_num: 11 "} ,...]
        self.data_path = _data_path
        if self.data_path:
            self.loads_indexes_json()
        else:
            self.indexes = defaultdict(list) 


    #  format is ['_id,title_num,text_num','',...]
    def _index_one_doc_seg_rawdata(self,__id,_seg_seq_title,_seg_seq_text):
        seg_set = set(list(_seg_seq_title.keys())+list(_seg_seq_text.keys()))

        for word in seg_set:
            seq_title = _seg_seq_title[word] if word in _seg_seq_title else 0
            seq_text = _seg_seq_text[word] if word in _seg_seq_text else 0
            self.indexes[word].append(
                {
                    "_id":str(__id),
                    "title_num":seq_title,
                    "text_num":seq_text
                }
            )
        return True

    
    def index_docs_from_mongo(self,collection_seg_rawdata):
        db_mongo = get_mongo_conn2coaldb()
        docs_gen = db_mongo[collection_seg_rawdata].find()
        for index,doc in enumerate(docs_gen):
            __id,_seg_seq_title,_seg_seq_text = doc['_id'],json.loads(doc['title_seg_sequence']),\
            json.loads(doc['text_seg_sequence'])
            self._index_one_doc_seg_rawdata(__id,_seg_seq_title,_seg_seq_text)
            # print(__id,_seg_seq_title,_seg_seq_text)
            if index % 100 == 0:
                print('success index %d' % index)
        
    
    def dumps_indexes_json(self,path):
        data = json.dumps(self.indexes)
        with open(path,'w') as fout:
            fout.write(data)
            fout.flush()
        
    
    def loads_indexes_json(self):
        with open(self.data_path,'r') as fin:
            self.indexes = json.loads(fin.read())
            
    # return format [{_id:ObjectId("59e418c92f773270ae125f3d"),title_num: 10,text_num: 11 "} ,...]
    def get(self,keyword):
        if keyword in self.indexes:
            return self.indexes[keyword]
        else:
            return []
        



class RawDataPrepare(object):
    def __init__(self,collection_rawdata_name):
        self.collection_rawdata_name = collection_rawdata_name
        self.mongo_conn = get_mongo_conn2coaldb()
    def getdocsbyids(self,id_list):
        res = []
        for _id in id_list:
            res.append(self.mongo_conn[self.collection_rawdata_name].find_one({"_id":ObjectId(_id)}))
        return res
            





if __name__ == "__main__":
    sys.path.append('../')
    import conf
    mongo_url = conf.mongo_url 
    mongo_dbname = conf.mongo_db_name
    mongo_accident_case = conf.mongo_collection_rawdata
    mongo_accident_case_seg  = conf.mongo_collection_seg_rawdata
    r = RawDataPrepare(conf.mongo_collection_rawdata)
    print(r.getdocsbyids(['59e418ca2f773270ae12666c']))
    seg = Segmenter(_path_vocab='../data/vocab/vocab_0.txt',_path_stopwords='../data/vocab/stopwords_0.txt')
    # seg.segment_rawdata(mongo_url,mongo_dbname,mongo_accident_case,mongo_accident_case_seg)
    # indexer = MemoryIndexer('../data/index.txt')
    # indexer.index_docs_from_mongo(mongo_url,mongo_dbname,mongo_accident_case_seg)
    # indexer.dumps_indexes_json('../data/index.txt')
    # indexer.loads_indexes_json('../data/index.txt')
    # print(indexer.get('四川'))
    print(seg.segment_for_query('中国是个大国家！'))
    # print(list(seg.set_stopwords)[:100])
    print('大' in seg.set_stopwords)


    
    
