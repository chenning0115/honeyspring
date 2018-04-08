import os
import sys
import bs4
import logging
import datetime as dt
import json
import re
import random
import math
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
from datamanager.myutils import insert2mongo
from bson.objectid import ObjectId
import conf
from conf import data_index_all_data_sign
from conf import data_index_json_file
from sklearn import feature_extraction  
from sklearn.feature_extraction.text import TfidfTransformer  
from sklearn.feature_extraction.text import CountVectorizer
from collections import OrderedDict
import math_utils as mutils
import numpy as np

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
        res = []
        i = 0
        for w in seg_gen:
            if w not in self.set_stopwords and self.is_chinese(w) and len(w) >= 2: # filter
                res.append(w)
            # print(res)
        # print(res)
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


    


class TFIDF(object):
    '''
    本类用于实现TF-IDF算法，需要用户输入TF-IDF词典和文档，以及提供一个segment来辅助文档的分词功能
    '''
    def __init__(self, _path_vocab = None,_path_stopwords = None, _path_output_vocab = None):
        self.segmenter = Segmenter(_path_vocab, _path_stopwords)
        self.path_output_vocab = _path_output_vocab

        #[index, word, freq, idf_counter[word], doc_num, math.log(doc_num / (idf_counter[word]))]
        self.tfidf_vocab = [] #tf-idf 词典
        
        
    def generate_tfidf_vocab(self,collection_rawdata):
        counter = Counter()
        # tf_counter_dict = {} #统计每个文档中的词频  用于计算tf 
        idf_counter = Counter() # 统计词出现的文档个数 用于计算idf 
        doc_num = 0

        db_mongo = get_mongo_conn2coaldb()
        tf_collect = db_mongo[conf.mongo_collection_tfdata] # 存储文档的 tf data
        rawdata_gen = db_mongo[collection_rawdata].find()
        for index,item in enumerate(rawdata_gen):
            tmp__id,tmp_id,tmp_title,tmp_text = item['_id'],item['id'],item['title'],item['content']['text']
            if tmp_title.strip()=='' or tmp_text.strip() == '' :
                continue
            tf_counter = Counter()
            doc_word_count = 0
            res_title_seg = self.segmenter.segment_for_query(tmp_title)
            doc_word_count += len(res_title_seg)
            for seg in res_title_seg:
                tf_counter[seg] += 1
                counter[seg] += 1

            res_text_seg = self.segmenter.segment_for_query(tmp_text)
            doc_word_count += len(res_text_seg)
            for seg in res_text_seg:
                tf_counter[seg] += 1
                counter[seg] += 1
            
            #利用tf_counter修正idf数据
            for k in tf_counter:
                idf_counter[k] += 1
            doc_num += 1

            #开始计算tf数据，并插入到mongodb中
            def _cal_tf_dict(tf_counter, word_count):
                tf_dict = {}
                for w,f in tf_counter.items():
                    tf_dict[w] = f / float(word_count)
                return tf_dict
            tf_dict = {
                "word_count": doc_word_count,
                "word_freq_str": json.dumps(tf_counter),
                "word_tf_str" : json.dumps(_cal_tf_dict(tf_counter, doc_word_count)),
                "type" : "title_and_content"
            }
            insert2mongo(tf_collect, tmp__id, tf_dict)
            
            # print(content_docs)
            if index % 50 ==0:
                print("%d has been done!" % index)   
        self.od = OrderedDict(counter.most_common())
        self.tfidf_vocab = []
        assert len(idf_counter) == len(counter) #确保两者长度一致
        with open(self.path_output_vocab, 'w') as fout:
            i = 0
            for word, freq in self.od.items():
                vals = [i ,word, freq, idf_counter[word], doc_num, math.log(doc_num / (idf_counter[word]))]
                fout.write("%d\t%s\t%s\t%s\t%s\t%s\n" % tuple(vals))
                self.tfidf_vocab.append(vals)
                i += 1
            fout.flush()
        print('generate tf idf vocabulary done!')

    

    def generate_vector(self, doc_tf):
        vec = [0] * len(self.tfidf_vocab)
        for index, word, freq, idf_num, doc_num, idf in self.tfidf_vocab:
            word_tf = doc_tf[word] if word in doc_tf else 0
            vec[index] = word_tf * idf
        return vec

    def cal_tf_idf(self):
        print('start to cal tf idf ..')
        db_mongo = get_mongo_conn2coaldb()
        tf_collect = db_mongo[conf.mongo_collection_tfdata] # 存储文档的 tf data
        for index,item in enumerate(tf_collect.find()):
            doc_tf = json.loads(item['word_tf_str'])
            vec = self.generate_vector(doc_tf)
            tf_collect.update({"_id":item['_id']},{"$set":{"vec":vec}})
            
            if index%100 == 0:
                print('cal_tf_idf %d done!' % index)
        print('finish cal tf idf...')
        
    def cal_distance(self, method):
        db_mongo = get_mongo_conn2coaldb()
        tf_collect_dis = db_mongo[conf.mongo_collection_distance]
        tf_collect_idf = db_mongo[conf.mongo_collection_tfdata]
        id_index = {}
        data = []

        index = 0
        for item in tf_collect_idf.find():
            id_index[str(item['_id'])] = index
            data.append(item['vec'])
            index += 1
            # data_dict.append([item['_id'], item['vec']])
        print('get data done! start to cal distance...')
        ndres = mutils.cal_euler_distance_by_matrix(data)
        print('cal euler dis done!')
        doc = {
            "method":method,
            "index":id_index,
            "dis":ndres,
        }
        # tf_collect_dis.insert(doc)
        save_path = conf.data_distance_path + "/" + method
        with open(save_path, 'w') as fout:
            fout.write(json.dumps(doc))
            fout.flush()
        print('cal tfidf distance done!')
                
            
        

def tfidf_run():
    path_vocab = conf.data_vocab_vocab_file
    path_stopwords = conf.data_vocab_stopwords_file
    path_output_vocab = conf.path_output_vocab
    tfidf = TFIDF(path_vocab, path_stopwords, path_output_vocab)
    tfidf.generate_tfidf_vocab(conf.mongo_collection_rawdata)
    tfidf.cal_tf_idf()

def cal_distance_tfidf():
    path_vocab = conf.data_vocab_vocab_file
    path_stopwords = conf.data_vocab_stopwords_file
    path_output_vocab = conf.path_output_vocab
    tfidf = TFIDF(path_vocab, path_stopwords, path_output_vocab)
    tfidf.cal_distance(conf.distance_method)

if __name__ == "__main__":
    tfidf_run()
    cal_distance_tfidf()
        
        

