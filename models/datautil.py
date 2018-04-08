import os
import sys
import bs4
import logging
import datetime as dt
import json
import re
import random
import time
import pymongo
from pymongo import MongoClient
from collections import Counter
import jieba
import pprint
from collections import defaultdict
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join('..',os.path.dirname(__file__)))
from datamanager.myutils import get_mongo_conn2coaldb
from bson.objectid import ObjectId
import conf
from conf import data_index_all_data_sign
from conf import data_index_json_file
from sklearn import feature_extraction  
from sklearn.feature_extraction.text import TfidfTransformer  
from sklearn.feature_extraction.text import CountVectorizer


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
    
    # which method is the best query segmentation method?
    def segment_for_query(self,context):
        seg_gen = jieba.cut(context)
        res = set()
        i = 0
        for w in seg_gen:
            if w not in self.set_stopwords and self.is_chinese(w) and len(w) >= 2:
                res.add(w)
            # print(res)
        print(res)
        return res
        
    def is_chinese(self,uchar):
        """判断一个unicode是否是汉字"""
        if uchar >= u'\u4e00' and uchar <= u'\u9fa5':
            return True
        else:
            return False

    def get_m(self,i):
        j = 0
        while (i//10)!=0:
            i /=10
            j += 1
        return j+1
    def segment_rawdata(self,collection_rawdata):
        counter = Counter()
        title_docs = []
        content_docs = []
        db_mongo = get_mongo_conn2coaldb()
        rawdata_gen = db_mongo[collection_rawdata].find()
        for index,item in enumerate(rawdata_gen):
            tmp__id,tmp_id,tmp_title,tmp_text = item['_id'],item['id'],item['title'],item['content']['text']
            if tmp_title.strip()=='' or tmp_text.strip() == '' :
                continue
            self.extract_date(tmp_text)
            self.extract_place(tmp_text)

            res_title_seg = self.segment_for_query(tmp_title)
            res_text_seg = self.segment_for_query(tmp_text)

            title_docs.append(' '.join(title_docs))
            content_docs.append(' '.join(res_text_seg))
            # print(content_docs)
        if index % 100 ==0:
            print(index)    
        
        return title_docs, content_docs

    def extract_date(self,text):
        regex = re.compile(r".*[\d{2,4}年]\d{1,2}月[\d{1,2}日]")
        return regex.match(text)

    def extract_place(self,text):
        regex = re.compile(r".*[煤矿|公司]")
        return regex.match(text)
class TFIDF(object):
    def __init__(self):
        self.path_vocab = conf.data_vocab_vocab_file
        self.path_stopwords = conf.data_vocab_stopwords_file
        self.seger = Segmenter(self.path_vocab, self.path_stopwords)
        
    def _tfidf(self,content_list):
        vectorizer=CountVectorizer()
        transformer=TfidfTransformer()
        tfidf_=transformer.fit_transform(vectorizer.fit_transform(content_list))
        print(vectorizer.get_feature_names())
    def calculate(self):
        corpus_title, corpus_content = self.seger.segment_rawdata(conf.mongo_collection_rawdata)
        self._tfidf(corpus_title)





if __name__ == "__main__":
    tfidf = TFIDF()
    tfidf.calculate()
        
        