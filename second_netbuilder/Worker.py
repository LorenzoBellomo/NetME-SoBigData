import asyncio
import aioredis
import en_core_web_sm
from   Annotation.Annotation             import Annotator
from   NetworkManager.Network            import Network
from   Utility.Utility                   import Utility as Ut, configuration_extraction
from   TextSearch.PubmedSearch           import PubmedSearch
from   Netbuilder.NetbuilderTree         import edge_creation_main
from   ErrorMessage.Messages             import Messages
from   celery                            import Celery
from   GuiModels.GuiModels               import dump_creation
from   NetworkManager.PagerankAproximate import PageRankApproximate


class Worker:
    # NOTE:
    #   - pub: is the
    def __init__(self, task):
        self.task        = task
        self.mongo_conn  = Ut.mongo_db()
        self.req_id      = "-1"
        self.post_data   = None
        self.pub         = None
        self.create_message_producer()
        self.nlp         = en_core_web_sm.load()
        self.utility     = Ut()
        self.annotations = Annotator(self.pub, self.req_id)
        self.network     = Network()

    # COMMUNICATION MECHANISM BY REDIS
    def create_message_producer(self):
        pub      = aioredis.Redis.from_url("redis://" + Ut.redis + ":6379/0", decode_responses=True)
        self.pub = pub

    # HANDLER OF NO ARTICLES MESSAGE
    async def error_status(self, msg: str, progress = 0.0, ui_msg: str = ''):
        if ui_msg == '': ui_msg = f'ERROR - During network construction: {msg}'
        await self.utility.task_status_updating(f"{ui_msg}", progress, self.req_id, self.pub, "ERROR")
        await self.pub.close()

    @staticmethod
    def set_default(obj):
        if isinstance(obj, set): return list(obj)
        raise TypeError

    # WORKER MAIN FUNCTION: REQUEST ELABORATION
    async def elaboration(self, req: dict):
        # bfs_managing   = BFsDJK(self.network)
        pagerk_manag   = PageRankApproximate()
        self.req_id    = req["id"]
        self.post_data = req
        onto_config    = configuration_extraction("ontotagme.json")
        await self.utility.task_status_updating(Messages.INI_ELAB, 0.0, self.req_id, self.pub)
        if   req["queryMode"] == "pubmed":
            self.network.type = "pmc" if "full-text" in req["searchType"] else "pubmed"
            mode     = "pm" if self.network.type == "pubmed" else "pmc"
            searcher = PubmedSearch(onto_config["apikey"])
            await searcher.get_document_id_by_query(req, self.utility, self.req_id, self.pub)
            await self.annotations.get_pmc_documents_by_ids(searcher.ids, self.nlp, self.req_id, mode)
        elif req["queryMode"] == "text":
            self.network.type = "text"
            await self.annotations.get_annotation_by_text(req['input'], self.nlp)
        else:
            self.network.type = "pdf"
            await self.annotations.get_annotation_by_sections(req, self.nlp)
        # NETWORK ELABORATION
        await self.utility.task_status_updating(Messages.EDGE_CRT, 0.6, self.req_id, self.pub)
        await edge_creation_main(self.annotations, self.network, self.req_id, self.pub)
        await self.utility.task_status_updating(Messages.EDGE_SCR, 0.9, self.req_id, self.pub)
        self.network.edge_score_computing()
        self.network.node_score_normalization()
        await self.utility.task_status_updating(Messages.NODE_SOR, 0.9, self.req_id, self.pub)
        # bfs_managing.node_bfs()
        pagerk_manag.approximate_pagerank_computing(self.network)
        await self.utility.task_status_updating(f"END ELABORATION", 1.0, self.req_id, self.pub)
        dumps = dump_creation(self.network, self.annotations, req["queryMode"])
        return dumps


# ENTRYPOINT CELERY
celery_app  = Celery("tasks", backend=Ut.BACKEND_URI, broker=Ut.BROKER_URI)
celery_app.conf.task_track_started = True


# ELABORATE FUNCTION
async def elaborate(task, req: dict):
    netbuilder = Worker(task)
    result     = await netbuilder.elaboration(req)
    del netbuilder
    return result


# TASK IMPLEMENTATION
@celery_app.task(bind=True)
def make_net(self, req: dict):
    print("MAKE NETWORK GENERATION")
    res = asyncio.run(elaborate(self, req))
    return res
