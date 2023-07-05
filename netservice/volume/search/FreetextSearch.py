import json
from   search.Search import Search


class FreeTextSearch(Search):
    def search(self, post, api_key):
        self.articles = json.loads('{"freetext": "' + self.json_string(post["input"]) + '"}')
        self.articles_id.append("freetext")

    def get_article(self, article_id):
        return self.articles[article_id]

    @staticmethod
    def json_string(string):
        string = string.replace("\r\n", " ")
        string = string.replace("\r"  , "")
        string = string.replace("\n"  , "")
        string = string.replace('"'   , "")
        return string
