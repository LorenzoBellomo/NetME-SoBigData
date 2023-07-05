from   datetime import datetime
from   pathlib  import Path
from   pymongo  import MongoClient
import os
import json
import nltk
import redis


#  GLOBAL VARIABLE
CON = "Configuration"
QMD = "queryMode"
STP = "searchType"
# - USED FOR ONTOTAGME REQUEST
PMD = "onto_pmd"
PMC = "onto_pmc"
LST = "onto_lst"
TXT = "onto_text"
PDF = "onto_pdf"
LOG = "onto_log"


def configuration_extraction(file_name, sub_dir = CON):
    root_path  = Path(os.path.abspath(__file__)).parents[1]
    config_dir = os.path.join(root_path, sub_dir, file_name)
    return json.load(open(config_dir))


class Utility:
    open_conf     = configuration_extraction("ontotagme.json")
    apikey        = open_conf["apikey"   ]
    redis         = open_conf["redis_ip" ]

    # REDIS URL
    BROKER_URI    = "redis://" + redis + ":6379/0"
    BACKEND_URI   = "redis://" + redis + ":6379/0"

    # ONTOTAGME URL CONFIGURATION
    URL_BY_ID_PMD = open_conf[PMD]
    URL_BY_ID_PMC = open_conf[PMC]
    URL_BY_IDS    = open_conf[LST]
    URL_BY_TEXT   = open_conf[TXT]
    URL_BY_PDF    = open_conf[PDF]
    URL_FOR_LOG   = open_conf[LOG]

    @staticmethod
    def get_time():
        return datetime.fromtimestamp(
               datetime.now().timestamp()
        ).strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def get_timestamp_id():
        return str(int(datetime.now().timestamp()))

    @staticmethod
    def mongo_db(connection=False):
        conf     = configuration_extraction("mongo.json")
        mongo_client   = MongoClient(
             host       = conf["host"    ],
             username   = conf["username"],
             password   = conf["password"],
             authSource = conf["db"      ],
        )
        if connection: return mongo_client
        return mongo_client[conf["db"]]

    def create_search_data(self, req: dict):
        search_data = dict()
        search_data["id"] = req["id"]
        search_data["description"] = req["networkName"]

        if req[QMD] == "pubmed":
            on = "pmc" if req[STP] == "full-text" else "pubmed"
            search_data[on + "_retmax"]    = req["papersNumber"]
            search_data[on + "_sort"]      = req["sortType"]
            if req["searchOn"] == "terms":
                search_data[on + "_terms"] = req["input"]
            elif req["searchOn"] == "ids":
                search_data[on + "_id"]    = req["input"]
        elif req["queryMode"] == "text": search_data["freetext"] = req["input"]
        elif req["queryMode"] == "pdf" : search_data["pdf"] = req["fn_list"]

        search_data["created_on"] = self.get_time()
        return search_data

    # GET BIOLOGICAL VERBS FROM A JSON FILE
    @staticmethod
    def get_bio_terms():
        subdir   = os.path.join("Files", "Bioterms")
        bioterms = configuration_extraction("bioterms.json", subdir)
        return bioterms["bioterms_list"]

    # BIOTERMS SCORE COMPUTING
    @staticmethod
    def bioterms_score_computing(bioterms, edge_obj):
        verb_components = edge_obj.verb_lem
        if len(verb_components) == 0:
            edge_obj.bioterms_score = 1/100
            return
        for component in verb_components:
            score = nltk.edit_distance(component, bioterms[0]) + 1
            for bioterm in bioterms[1:]:
                other_score = nltk.edit_distance(component, bioterm) + 1
                score = min(score, other_score)
            score = 1 / score
            edge_obj.bioterms_score.append(score)
        edge_obj.bioterms_score = round(
            sum(edge_obj.bioterms_score) / len(edge_obj.bioterms_score), 3
        )

    # WEBSOCKET MESSAGE EXCHANGE BY REDIS
    async def task_status_updating(self, msg: str, progress, req_id, pub, status: str = "PROGRESS"):
        try:
            body = json.dumps({
                "time"       : self.get_time(),
                "progress"   : progress,
                "status"     : status,
                "msg"        : msg,
                "routing_key": req_id
            })
            await pub.publish(req_id, body)
        except Exception as e:
            print(str(e))

    def task_status_updating_onto(self, msg: str, progress, req_id, pub, status: str = "PROGRESS"):
        try:
            body = json.dumps({
                "time"       : self.get_time(),
                "progress"   : progress,
                "status"     : status,
                "msg"        : msg,
                "routing_key": req_id
            })
            pub.publish(req_id, body)
        except Exception as e:
            print(str(e))