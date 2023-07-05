import asyncio
import json
import logging
import aioredis
import en_core_web_sm
import nltk
from   utils                   import Utils
from   search.PubMedSearch     import PubMedHandler
from   search.FreetextSearch   import FreeTextSearch
from   search.PDFSearch        import PDFSearch
from   network.Network         import Network
from   celery                  import Celery
from   celery.utils.log        import get_task_logger
from   celery.signals          import after_setup_logger


# LOGGING CREATION
logging.basicConfig(filename="files/netme.log", level=logging.DEBUG)


# CLASS DEFINITION
class NetBuilderWrapper:
    def __init__(self):
        logging.info("START WRAPPER CONFIGURATION")
        logging.info("\tBUILDING OF SPACY SERVICE")
        self.nlp = en_core_web_sm.load()
        self.nlp.add_pipe("merge_entities")
        self.nlp.add_pipe("merge_noun_chunks")
        logging.info("\tMONGODB AND RABBITMQ CHANNEL CREATION")
        self.mongo_db   = Utils.mongo_db()
        self.bioterms   = self.get_bioterms()
        self.pub        = None
        logging.info("\tENDED WRAPPER CONFIGURATION")

    async def create_message_producer(self, req_id: str):
        pub = aioredis.Redis.from_url("redis://" + Utils.rabbit_url + ":6379/0", decode_responses=True)
        self.pub = pub

    # BIOTERMS EXTRACTION FROM MONGODB
    def get_bioterms(self):
        try:
            r = self.mongo_db["terms"].find_one({"_id": "bioterms"})
            if r: return r["data"]
        except Exception as e:
            logging.error("WORKER get_bioterms: " + str(e))
            return []

    # BIOTERMS EDITING DISTANCE
    def check_bio_edge(self, edge):
        score = len(edge)
        for e in self.bioterms:
            if nltk.edit_distance(e, edge) < score:
                score = nltk.edit_distance(e, edge)
        try   : normalized_score = score / len(edge)
        except: normalized_score = 999
        return round(normalized_score, 3)


class NetBuilder:
    def __init__(self, task):
        self.wrapper      = NetBuilderWrapper()
        self.task         = task
        self.req_id       = "-1"
        self.post_data    = None
        self.network      = None
        self.searcher     = None

    # METHODS
    async def update_status(self, msg: str, progress, status: str = "PROGRESS"):
        try:
            logging.info(f"UPDATE STATUS OF req_id: {self.req_id}".format(req_id=self.req_id))
            logging.info("\tBODY CONFIGURATION")
            body = json.dumps({"time": Utils.get_time(), "progress": progress, "status": status, "msg": msg, "routing_key": self.req_id})
            await self.wrapper.pub.publish(self.req_id, body)
            logging.info("ENDED UPDATING PHASE")
        except Exception as e:
            logging.error("WORKER update_status: " + str(e))

    async def error_status(self, msg: str, progress = 0.0, ui_msg: str = ''):
        logging.error(msg)
        if ui_msg == '':
            ui_msg = f'ERROR - During network construction: {msg}'
        await self.update_status(f"{ui_msg}", progress, status="ERROR")
        await self.wrapper.pub.close()

    # MAIN ELABORATION FUNCTION
    async def elaborate(self, req: dict):
        logging.info("START ELABORATION PROCEDURES")
        self.req_id    = req["id"]
        await self.wrapper.create_message_producer(self.req_id)
        logging.info("\t- REQ_ID: " + self.req_id)
        await self.update_status("Initialize elaboration", 0.0)

        if req is None: return None
        # DOCUMENTS CREATION
        logging.info("DOCUMENTS CREATION")
        self.post_data = req
        if   req["queryMode"] == "pubmed": self.searcher = PubMedHandler()
        elif req["queryMode"] == "text"  : self.searcher = FreeTextSearch()
        else                             : self.searcher = PDFSearch()
        self.searcher.search(req, Utils.apikey)
        if self.searcher.articles is None or len(self.searcher.articles) == 0: 
            await self.error_status("No articles")
            return None
        self.network = Network(self.wrapper)
        try:
            data = await self.make_net()
            await self.update_status(f"network construction ending...", 1.0)
            await self.wrapper.pub.close()
            return json.loads(data)
        except Exception as e:
            await self.error_status("WORKER elaborate: " + str(e))
            return None

    # NETWORK CREATION
    async def make_net(self):
        logging.info("NETWORK CONSTRUCTION")
        dim = len(self.searcher.articles)
        # ANNOTATIONS CONFIGURATION
        for idx, id_article in enumerate(self.searcher.articles):
            await self.update_status(f"ANNOTATING {str(idx + 1)} of {str(dim)} articles", 0.3 * (idx/dim))
            self.network.request_data(id_article, self.searcher.get_article(id_article))
        # EDGE CONSTRUCTION
        size = len(self.network.annotations["article"])
        for index_article, id_article in enumerate(self.network.annotations["article"]):
            await self.update_status(f"finding edges in article: {id_article}", 0.6 * (index_article/size) + 0.3)
            try:
                total_word    = 1
                sentence_map  = self.network.sentences[id_article]
                doc_edges_num = {"edges_num": 0}
                for sentence_id in list(sentence_map.keys()):
                    if len(sentence_map[sentence_id][2]) > 1:
                        await self.network.edges_finding(id_article, total_word, sentence_id, doc_edges_num)
                    else: sentence_map.pop(sentence_id)
                for edge_id, edge in self.network.network["edges"].items():
                    if id_article not in edge["tf"]: continue
                    edge["tf"][id_article]["total_words"] = doc_edges_num["edges_num"]
            except Exception as e:
                logger.error(str(e))

        # FINAL COMPUTING
        self.network.edge_elaboration(dim)
        await self.update_status(f"sorting...", 0.9)
        self.network.element_sorting()
        dump = {
            "annotations": self.network.annotations,
            "nodes"      : self.network.network["nodes"],
            "edges"      : self.network.network["edges"],
            "articles"   : self.searcher.articles_id,
            "sentences"  : self.network.sentences_gui
        }
        await self.update_status(f"END ELABORATION", 1.0)
        return json.dumps(dump, default = self.set_default)

    @staticmethod
    def set_default(obj):
        if isinstance(obj, set):
            return list(obj)
        raise TypeError


# SCRIPT
BROKER_URI  = "redis://" + Utils.rabbit_url + ":6379/0"
BACKEND_URI = "redis://" + Utils.rabbit_url + ":6379/0"
celery_app  = Celery("tasks", backend=BACKEND_URI, broker=BROKER_URI)

celery_app.conf.task_track_started = True
logger      = get_task_logger(__name__)


@after_setup_logger.connect
def setup_loggers(logger, *args, **kwargs):
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    fh = logging.FileHandler("files/worker_logs.log")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)


async def elaborate(task, req: dict):
    netbuilder = NetBuilder(task)
    result     = await netbuilder.elaborate(req)
    del netbuilder
    return result


@celery_app.task(bind=True)
def make_net(self, req: dict):
    logging.info("MAKE NETWORK CREATION")
    print("MAKE NETWORK GENERATION")
    res = asyncio.run(elaborate(self, req))
    return res
