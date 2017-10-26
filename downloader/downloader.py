import urllib.request as request
import bs4
import logging
import datetime as dt
import json
import random
import time
from pymongo import MongoClient



class Downloader(object):
    def __init__(self):
        self.proxy_list = [
            ('218.75.101.66',	3128),
            ('221.214.110.130',	8080),
            ('222.85.127.130',	9999),
            ('60.191.134.165',	9999),
            ('222.85.127.130',	9797),
            ('111.40.84.73',	9797),
            ('120.84.239.50',	8080),
            ('220.249.185.178',	9999),
            ('220.249.185.178',	9999),
            ('120.204.85.29',	3128),
            ('120.204.85.29',	3128),
            ('120.204.85.29',	3128),
            ('124.206.22.120',	3128),
            ('121.35.243.157',	8080),
            ('222.85.127.130',	9797),
            ('118.190.14.150',	3128),
            ('220.249.185.178',	9999),
            ('218.75.116.58',	9999),
            ('218.56.132.158',	8080),
            ('220.249.185.178',	9999),
            ('123.138.216.91',	9999),
            ('218.200.52.206',	8080),
            ('218.6.145.11',	9797),
            ('218.56.132.156',	8080),
            ('183.57.82.71',	8081),
            ('183.57.82.71',	8081),
            ('123.139.56.238',	9999),
            ('211.101.153.126',	8080),
            ('114.215.150.13',	3128),
            ('112.91.218.21',	9000),
            ('222.85.127.130',	9797),
            ('120.204.85.29',	3128)]
        self.openner_list = []
        for ip,port in self.proxy_list:
            handler = request.ProxyBasicAuthHandler()
            openner = request.build_opener(request.HTTPHandler, handler)
            self.openner_list.append(openner)

        
    def _get_random_openner(self):
        r = random.randint(0,len(self.openner_list)-1)
        return self.openner_list[r]

    def test(self):
        openner = self._get_random_openner()
        f = openner.open("http://www.baidu.com")
        print(f.read())

    def get_page_list(self,page_num = 1):
        openner = self._get_random_openner()
        url = "http://www.mkaq.org/sggl/shigual/List_%d.shtml" % (page_num)
        with openner.open(url) as f:
            doc = f.read()
            soup = bs4.BeautifulSoup(doc,'html.parser')
            li_title_list = soup.select("div[class='article_list1']")[0].select("li")
            # print(li_title_list)
            res_dict = {}
            if len(li_title_list) > 0:
                for item in li_title_list:
                    tmp = item.select('a')[0]
                    tmp_title = tmp.text
                    tmp_href = tmp['href']
                    res_dict[tmp_title] = "http://www.mkaq.org" + tmp_href
                logging.info('page of %d download success!' % page_num)
            else:
                logging.info('page of %d download failed!' % page_num)
            return res_dict
    def get_one_case(self,url_case):
        openner = self._get_random_openner()
        with openner.open(url_case) as f:
            doc = f.read()
            soup = bs4.BeautifulSoup(doc,'html.parser')
            div_article = soup.select("div[class='newsShow_cont']")[0]
            p_line_list = div_article.select("p")
            img_list = div_article.select("img")
            # print(p_line_list)
            article = ""
            imgurl_list = []
            src_time_str = p_line_list[0].text
            src = src_time_str[src_time_str.index('来源：')+3:src_time_str.index('发布时间：')].strip()
            publish_time = src_time_str[src_time_str.index('发布时间：')+5: ].strip()
            for i in range(1,len(p_line_list)):
                item = p_line_list[i]
                line = item.text
                article = article + line + "\r\n"
            for img in img_list:
                imgurl_list.append("http://www.mkaq.org"+img['src'])
            return src,publish_time,article.strip(),imgurl_list


def start_download(page_num_list):
    count =  0
    failed_url_list = []
    failed_page_num_list = []
    for page_num in page_num_list:
        with open('data/coal_accident_case_%d.txt' % page_num,'w') as fout:
            data_list = []
            downloader = Downloader()
            try:
                res = downloader.get_page_list(page_num)
                for title,url_case in res.items():
                    try:
                        src,publishtime,article,imgurl_list = downloader.get_one_case(url_case)
                        data = {
                            "id":count,
                            "title":title,
                            "url":url_case,
                            "source":src,
                            "publish_time":publishtime,
                            "insert_time":dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            "insert_author":"chenning",
                            "content":{
                                "text":article,
                                "img":imgurl_list
                            }
                        }
                        data_list.append(data)
                        count += 1
                        print(count)
                    except Exception as e:
                        failed_url_list.append({"title":title,"url":url_case})
                        print("failed download page %d but we will continue!" % url_case)
                        print(str(e))
            except Exception as pe:
                failed_page_num_list.append(page_num)
                print("failed download page %d but we will continue!" % page_num)
                print(str(pe))
            
            data_json = json.dumps(data_list)
            fout.write(data_json)
            fout.flush()
            fout.close()
            # print("start to sleep for 10 seconds..")
            # time.sleep(10)
        print("success download page %d " % page_num)
    with open('failed_url.txt','w') as failed_fout:
        failed_fout.write(json.dumps(failed_url_list))
        failed_fout.flush()
        failed_fout.close()
    print(failed_page_num_list)







class DBHandler(object):
    def __init__(self,collection_name = "coal_accident_case"):
        self.client = MongoClient('mongodb://localhost:27017')['test']
        self.collection_name = collection_name
        self.count = 0
    def _dumps2mongo(self,path):
        with open(path,'r') as f:
            db = self.client[self.collection_name]
            data_json = f.readline()
            data = json.loads(data_json)
            for case in data:
                case['id'] = self.count
                case['title'] = case['title'].strip()
                self.count += 1
                mid = db.insert(case)
                print(mid)
    def dumpsall(self):
        for page in range(1,56):
            self._dumps2mongo('data/coal_accident_case_%d.txt' % page)
            print('success dumps page %d' % page)





if __name__ == "__main__":
    # downloader = Downloader()
    # downloader.test()
    # page_num_list = [55]
    # start_download(page_num_list)
    dbhandler = DBHandler()
    dbhandler.dumpsall()


        
