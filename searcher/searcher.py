import sys
import os
curdir = os.path.dirname(__file__)
sys.path.append(os.path.join(curdir,'../'))
import logging
import json
import random
import time
from collections import defaultdict
import datamanager
from datamanager.dataprepare import RawDataPrepare
from datamanager.dataprepare import Segmenter
from datamanager.dataprepare import MemoryIndexer
# from datamanager.myutils import get_mongo_conn2coaldb


class Searcher(object):
    def __init__(self,_indexer,_data_prepare,_segmenter):
        self.indexer = _indexer
        self.segmenter = _segmenter
        self.data_prepare = _data_prepare

    def query(self,query_phrase):
        seg_words_tuple = self.segmenter.segment_for_query(query_phrase)
        topk_tuple_list = self.retrive_topk(seg_words_tuple)
        #----------------------------------------
        # here we should rank the topk futher!
        #----------------------------------------
        # print(topk_tuple_list)
        
        _id_list = [item[1] for item in topk_tuple_list]
        res_docs = self.data_prepare.getdocsbyids(_id_list)
        # for doc in res_docs:
        #     print(doc['title'],doc['url'])
        return res_docs
            



    def retrive_topk(self,word_tuple_list,k=20):
        res_dict = defaultdict(float) # {'word':grade}
        for word,stop in word_tuple_list:
            stop_grade = 0.1 if stop==0 else 1
            word_index_list = self.indexer.get(word)
            word_len = len(word)
            for index_item in word_index_list:
                _id,title_num,text_num = index_item['_id'],index_item['title_num'],index_item['text_num']
                grade = (title_num * 10 + min(text_num,10))* stop_grade * word_len
                res_dict[_id] += grade
        res_list = []
        for key,value in res_dict.items():
            res_list.append((value,key))
        def mykey(x):
            return x[0]
        res_list = sorted(res_list,key=mykey,reverse=True)
        return res_list[:k]

        
        

if __name__ == '__main__':
    sys.path.append('../')
    import conf  
    mongo_url = conf.mongo_url 
    mongo_dbname = conf.mongo_db_name
    mongo_accident_case = conf.mongo_collection_rawdata
    mongo_accident_case_seg  = conf.mongo_collection_seg_rawdata
    indexer = MemoryIndexer('../data/index.txt')
    data_prepare = RawDataPrepare(conf.mongo_collection_rawdata)
    segmenter = Segmenter(_path_vocab='../data/vocab/vocab_0.txt',_path_stopwords='../data/vocab/stopwords_0.txt')
    searcher = Searcher(indexer,data_prepare,segmenter)
    searcher.query('瓦斯爆炸')

    

    

    