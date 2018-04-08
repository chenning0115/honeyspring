import tornado.ioloop
import tornado.web

import os
import sys
import math
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__),'../'))
import webconf
import conf
from datamanager.dataprepare import MemoryIndexer
from datamanager.dataprepare import RawDataPrepare
from datamanager.dataprepare import Segmenter
from searcher.searcher import Searcher
from objectconstructer import ObjectConstructor
from datamanager.dataprepare import SimCaseSearch

# global object
print('loading data..')
indexer = MemoryIndexer(_data_path = conf.data_index_json_file)
segementer = Segmenter(_path_vocab = conf.data_vocab_vocab_file,_path_stopwords = conf.data_vocab_stopwords_file)
dataprepare = RawDataPrepare(conf.mongo_collection_rawdata)
searcher = Searcher(_indexer = indexer,_segmenter = segementer,_data_prepare = dataprepare)
simcasesearch = SimCaseSearch(conf.distance_method)
print('searcher construct complete..')


# Handler

class HomeHandler(tornado.web.RequestHandler):
    def get(self):
        self.render(webconf.path_template_homehandler)

class SearchHandler(tornado.web.RequestHandler):
    def get(self):
        query_phrases = self.get_arguments('query')
        query_phrase = ''
        if len(query_phrases)!=0:
            query_phrase = ' '.join(query_phrases)
        page_number_list = self.get_arguments('page')
        page_number = 0
        if len(page_number_list) != 0:
            page_number = int(page_number_list[0])
        start = page_number * webconf.searcher_num_per_page
        end = start + webconf.searcher_num_per_page
        # print(start,end)
        if query_phrase == '':
            res_docs,searchcount = searcher.query_all(start,end)
        else:
            res_docs,searchcount = searcher.query(query_phrase,start,end)
        res_objs = []
        for doc in res_docs:
            res_objs.append(ObjectConstructor(query_phrase,doc,'/rawdetail','/simcase'))
        page_pre = max(0,page_number - 1)
        page_next = page_number + 1
        response_objs = {
            "objs":res_objs,
            "query":query_phrase,
            "pagepre":page_pre,
            "pagenext":page_next,
            "searchcount":searchcount,
            "pagecount": math.ceil(searchcount / webconf.searcher_num_per_page),
            "pagenumber":page_number 
        }
        return self.render(webconf.path_template_searchhandler,**response_objs)

class SearchHandler_test(tornado.web.RequestHandler):
    def get(self):
        query_phrase = self.get_arguments('query')
        page_number = self.get_arguments('page')
        print(page_number)
        query_phrase = ' '.join(query_phrase)
        res_docs = searcher.query(query_phrase)
        res_objs = []
        for doc in res_docs:
            res_objs.append(ObjectConstructor(query_phrase,doc,'/rawdetail','/simcase'))
        return self.render(webconf.path_template_queryhandler,objs = res_objs)

class FormDetailHandler(tornado.web.RequestHandler):
    def get(self):
        return self.render(webconf.path_template_formdetail)

class RawDetailHanlder(tornado.web.RequestHandler):
    def get(self):
        doc_id = self.get_arguments('_id')[0].strip()
        if doc_id== '':
            return 
        docs = dataprepare.getdocsbyids([doc_id])
        if len(docs)==1:
            mydoc = docs[0]
            mydoc['content']['text'] = mydoc['content']['text'].replace('\r\n','</p><p>')
            mydoc['content']['text'] = '<p>' + mydoc['content']['text']+'</p>'
            return self.render(webconf.path_template_rawdetail,mydoc = mydoc)
    
class SimCaseHandler(tornado.web.RequestHandler):
    def get(self):
        doc_id = self.get_arguments('_id')[0].strip()
        if doc_id== '':
            return 
        ids_dis = simcasesearch.get_sim_case(doc_id)
        ids = []
        dis = []
        for dd in ids_dis:
            ids.append(dd['_id'])
            dis.append(dd['dis'])
        docs = dataprepare.getdocsbyids(ids)
        res_objs = []
        for i in range(len(docs)):
            doc = docs[i]
            doc['dis'] = dis[i]
            res_objs.append(ObjectConstructor("",doc,'/rawdetail','/simcase'))

        return self.render(webconf.path_template_simdocs, objs = res_objs)
        
        




# settings and URL Mapping

settings = {
"static_path": os.path.join(os.path.dirname(__file__), "static") 
}

application = tornado.web.Application([
        (r"/", HomeHandler),
        (r"/search_test",SearchHandler_test),
        (r"/search",SearchHandler),
        (r"/formdetail",FormDetailHandler),
        (r"/rawdetail",RawDetailHanlder),
        (r"/simcase",SimCaseHandler)
    ],**settings)



 # run...
if __name__ == "__main__":
    
    application.listen(8080)
    tornado.ioloop.IOLoop.current().start()

