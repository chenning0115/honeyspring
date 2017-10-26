

import os
import sys

# data info
data_prefix_path = os.path.join(os.path.dirname(__file__),'data')



#mongodb info
mongo_url = "mongodb://localhost:27017"
mongo_db_name = "test"
mongo_collection_rawdata = "coal_accident_case_check"
mongo_collection_seg_rawdata = "seg_coal_accident_case"
#redis info


# vocabulary info
data_vocab_path = os.path.join(data_prefix_path,'vocab')
data_vocab_vocab_file = os.path.join(data_vocab_path,'vocab_0.txt')
data_vocab_stopwords_file = os.path.join(data_vocab_path,'stopwords_0.txt')


# indexes of json file info
data_index_json_file = os.path.join(data_prefix_path,'index.txt')


