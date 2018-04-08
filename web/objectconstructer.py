class ObjectConstructor(object):

    def __init__(self, _query, _doc, _prefix_url_rawdetail, _prefix_url_simcase):
        self.query = _query
        self.doc = _doc
        self.prefix_url_rawdetail = _prefix_url_rawdetail
        self.prefix_url_simcase = _prefix_url_simcase

    def get_title(self):
        title = ''
        for char in self.doc['title']:
            if char in self.query:
                char = '<hltext> ' + char + ' </hltext>'
            title += char
        return title

    def get_text(self):
        string = self.doc['content']['text']
        if len(self.query)>0:
            cur = string.find(self.query[0])
        else:
            cur = 0
        i = max(0, cur - 40)
        j = cur + 90
        origin = string[i:j]
        returnString = ''
        for char in origin:
            if char in self.query:
                char = '<hltext>' + char + '</hltext>'
            returnString += char
        return returnString


    def get_url_ori(self):
        return self.doc['url']

    def get_url_rawdetail(self):
        url = self.prefix_url_rawdetail + '?_id=' + str(self.doc['_id'])
        return url

    def get_simcase_ori(self):
        url = self.prefix_url_simcase + "?_id=" + str(self.doc['_id'])
        return url

    def get_simcase_distance(self):
        return self.doc['dis']

        