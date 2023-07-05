from abc import abstractmethod


class Search:
    def __init__(self):
        self.idlist      = []
        self.articles    = {}
        self.articles_id = []

    @abstractmethod
    def search(self, post, api_key)  : pass

    @abstractmethod
    def get_article(self, article_id): pass
