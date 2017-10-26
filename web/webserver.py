import tornado.ioloop
import tornado.web

import os
import sys
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__),'../'))
import webconf
import conf
from datamanager.dataprepare import MemoryIndexer
from datamanager.dataprepare import RawDataPrepare
from datamanager.dataprepare import Segmenter
from searcher.searcher import Searcher
from objectconstructer import ObjectConstructor

# global object
print('loading data..')
indexer = MemoryIndexer(_data_path = conf.data_index_json_file)
segementer = Segmenter(_path_vocab = conf.data_vocab_vocab_file,_path_stopwords = conf.data_vocab_stopwords_file)
dataprepare = RawDataPrepare(conf.mongo_collection_rawdata)
searcher = Searcher(_indexer = indexer,_segmenter = segementer,_data_prepare = dataprepare)
print('searcher construct complete..')


# Handler

class HomeHandler(tornado.web.RequestHandler):
    def get(self):
        self.render(webconf.path_template_homehandler)

class SearchHandler(tornado.web.RequestHandler):
    def get(self):
        query_phrase = self.get_arguments('query')
        query_phrase = ' '.join(query_phrase)
        res_docs = searcher.query(query_phrase)
        res_objs = []
        for doc in res_docs:
            res_objs.append(ObjectConstructor(query_phrase,doc,'/rawdetail'))
        return self.render(webconf.path_template_searchhandler,objs = res_objs)

class SearchHandler_test(tornado.web.RequestHandler):
    def get(self):
        query_phrase = self.get_arguments('query')
        query_phrase = ' '.join(query_phrase)
        res_docs = searcher.query(query_phrase)
        res_objs = []
        for doc in res_docs:
            res_objs.append(ObjectConstructor(query_phrase,doc,'/rawdetail'))
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
    




# settings and URL Mapping

settings = {
"static_path": os.path.join(os.path.dirname(__file__), "static") 
}

application = tornado.web.Application([
        (r"/", HomeHandler),
        (r"/search_test",SearchHandler_test),
        (r"/search",SearchHandler),
        (r"/formdetail",FormDetailHandler),
        (r"/rawdetail",RawDetailHanlder)
    ],**settings)



 # run...
if __name__ == "__main__":
    
    application.listen(8080)
    tornado.ioloop.IOLoop.current().start()

