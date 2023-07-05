import requests
import time
from   lxml     import etree


# GLOBAL VARIABLE
URI_SEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?apikey={ak}&db={db}&term={tm}&retmax={rm}&sort={st}"
MESSAGE_0  = "SOME PROBLEM WITH PUBMED CONNECTION"
MESSAGE_1  = "ID LIST IS NONE"
INP        = "input"
STP        = "searchType"
SRT        = "sortType"
PNM        = "papersNumber"
SON        = "searchOn"


class PubmedSearch:
    def __init__(self, apikey):
        self.ids     = None
        self.apikey  = apikey
        self.err_msg = None

    # THIS FUNCTION IS USED TO OBTAIN DOCUMENTS' ID BY QUERY TEXT
    async def get_document_id_by_query(self, user_request, utility, req_id, pub):
        terms = user_request[INP]
        if user_request[SON] == "ids":
            terms    = terms.replace(" ", "")
            self.ids = terms.split(",")
            return
        dbtype     = "pmc" if user_request[STP] == "full-text" else "pubmed"
        retmax     = user_request[PNM]
        sort       = user_request[SRT]
        terms      = terms + "+AND+free+fulltext[filter]" if (dbtype == "pmc") else terms
        url_search = URI_SEARCH.format(ak=self.apikey, db=dbtype, tm=terms, rm=retmax, st=sort)
        iteration  = 0
        timer      = 5.0 / 2.5
        while iteration < 5:
            try:
                self.err_msg = []
                request      = requests.get(url=url_search, params='')
                if request.status_code != 200:
                    self.err_msg.append(MESSAGE_0)
                else:
                    data      = etree.fromstring(request.content, parser=etree.XMLParser(huge_tree=True))
                    id_list   = data.find(".//IdList")
                    if id_list is None:
                        self.err_msg.append(MESSAGE_1)
                    else:
                        id_list   = id_list.findall(".//Id")
                        self.ids  = [id_.text for id_ in id_list]
                        if dbtype == "pmc": self.ids = ["PMC" + id_ for id_ in self.ids]
                        iteration = 4
            except Exception as e:
                print(str(e))
                self.err_msg.append(str(e))
            if iteration != 4:
                timer = timer * 2.5
                await utility.task_status_updating(
                    "There was a problem with pubmed/pubmed central connection creation. Netme will try to get documents list"
                    " after {time} seconds".format(time=timer), 0.0, req_id, pub
                )
                time.sleep(timer)
            iteration += 1
        if not self.ids:
            await utility.task_status_updating("Pubmed/pubmed central is unavailable now. Try late", 1.0, req_id, pub)