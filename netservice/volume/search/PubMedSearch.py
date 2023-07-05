import json
import requests
import logging
from   xml.etree               import ElementTree
from   lxml                    import etree
from   reading.Pubmed.Document import Document
from   search.Search           import Search


# LOGGING CREATION
logging.basicConfig(filename="files/netme.log", level=logging.DEBUG)


class RequestParameter:
    def __init__(self, idlist, apikey, retmode="xml", dbtype="pmc"):
        self.db      = dbtype
        self.id      = idlist
        self.retmode = retmode
        self.apikey  = apikey


class PubMedHandler(Search):
    # STATIC VARIABLES
    URI_SEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?apikey="
    URL_FETCH  = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    @staticmethod
    def _sub_list(idlist, n, retmax, sup, len_id_list):
        return idlist[n * retmax: sup] if sup < len_id_list else idlist[n * retmax:]

    def _my_dict(self, element):
        if hasattr(element, "__dict__"):
            element = element.__dict__ if element is not None else None
        if isinstance(element, list):
            element = [self._my_dict(item) for item in element]
        elif isinstance(element, dict):
            element = {key: self._my_dict(val) for key, val in element.items()}
        return element

    # 1. XML TO PYTHON OBJECT (PUBMED)
    def _pubmed_parser(self, response):
        logging.info("PUBMED DOCUMENTS PARSING")
        for article_tag in response.findall('PubmedArticle'):
            article_id = article_tag.find(".//PMID")
            if not article_id.text: continue
            content = ''
            for abstract_tag in article_tag.findall('.//AbstractText'):
                if abstract_tag.text: content += abstract_tag.text
            if not (len(content) > 100 and article_id.text not in self.articles): continue
            self.articles[article_id.text] = {
                "pubmed_id" : article_id.text,
                "title"     : article_tag.find(".//ArticleTitle").text,
                "abstract"  : content.replace('\n', '')
            }
            self.articles_id.append("pubmed|" + article_id.text)
        logging.info("ENDED DOCUMENTS PARSING")

    # 2. XML TO PYTHON OBJECT (PUBMED CENTRAL)
    def _pubmedcentral_parser(self, response, etree_obj):
        logging.info("PUBMED CENTRAL DOCUMENTS PARSING")
        articles_records = response.findall(".//article")
        for article in articles_records:
            article_obj = Document(article, etree_obj)
            self.articles[article_obj.pmcid] = self._my_dict(article_obj)
            self.articles_id.append("pmc|" + article_obj.pmcid)
        logging.info("PUBMED CENTRAL DOCUMENTS ENDED")

    # 3. GET ARTICLES' ID FROM PUBMED OR PUBMED
    def get_document_id_by_query(self, terms, sort, apikey, retmax=20, dbtype = "pmc"):
        logging.info("DOCUMENTS' ID DOWNLOADING BASED ON TERMS")
        try:
            self.idlist = []
            terms = terms + "+AND+free+fulltext[filter]" if (dbtype == "pmc") else terms
            url_search = self.URI_SEARCH + apikey + "&db=" + dbtype + \
                "&term=" + terms + "&retmax=" + str(retmax) + "&sort=" + sort
            r = requests.get(url=url_search, params='')
            r = ElementTree.fromstring(r.content)
            for id_list_tag in r.findall('IdList'):
                for id_article_tag in id_list_tag.findall('Id'):
                    self.idlist.append(id_article_tag.text)
        except Exception as e:
            logging.error("ERROR: " + str(e))

    # 4. DOCUMENTS DOWNLOADING
    def articles_fetch(self, apikey, retmode="xml", retmax=20, dbtype="pmc"):
        logging.info("DOCUMENTS DOWNLOADING")
        try:
            len_id_list = len(self.idlist)
            for n in range((len_id_list // retmax) + 1):
                print("n: " + str(n))
                ids_str   = ','.join(self._sub_list(self.idlist, n, retmax, (n + 1) * retmax, len_id_list))
                parameter = RequestParameter(ids_str, apikey, retmode, dbtype).__dict__
                r         = requests.post(url=self.URL_FETCH, params=parameter)
                try:
                    if dbtype == "pmc":
                        r = etree.fromstring(r.content, parser=etree.XMLParser(huge_tree=True))
                        self._pubmedcentral_parser(r, etree)
                    else:
                        r = ElementTree.fromstring(r.content)
                        self._pubmed_parser(r)
                except Exception as e:
                    print(e)
        except Exception as e:
            logging.error("ERROR MESSAGE: " + str(e))

    # PUBMED OR PUBMED CENTRAL DOWNLOADING
    def search(self, post, api_key):
        logging.info("PARSING THE FOLLOWS POST: " + json.dumps(post))
        on       = "pmc" if post["searchType"] == "full-text" else "pubmed"
        query    = [term.strip() for term in post["input"].split(",")]
        retmax   = int(post["papersNumber"])
        retmax_2 = min(50, retmax)
        if   post["searchOn"] == "terms":
            for q in query:
                self.get_document_id_by_query(q, post["sortType"], api_key, retmax, on)
                self.articles_fetch(api_key, "xml", retmax_2, on)
        elif post["searchOn"] == "ids":
            self.idlist = query
            self.articles_fetch(api_key, "xml", retmax_2, on)
        logging.info("PARSING HAS BEEN COMPLETED")

    # GET ARTICLE TEXT
    def get_article(self, article_id):
        article = self.articles[article_id]
        if   "full_text" in article:
            if article["full_text"] is None: return ""
            text = []
            self.subsection_iter(article["full_text"]["sections"], text)
            return "\n".join(text)
        elif "abstract"  in article and article["abstract"] is not None: return article["abstract"]
        else: return ""

    #
    def subsection_iter(self, sections, text_vet):
        for section in sections:
            if section["text"] != "": text_vet.append(section["text"])
            self.subsection_iter(section["sections"], text_vet)