from datetime import datetime, time
import json
from pymongo import MongoClient


class Utils:

    apikey        = "9fa42ec62c582485fb7e6c69148eaf940308"
    webserver_url = "http://131.114.50.197/tagme_string"
    rabbit_url    = "172.39.0.10"

    @staticmethod
    def get_time():
        return datetime.fromtimestamp(datetime.now().timestamp()).strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def get_timestamp_id():
        return str(int(datetime.now().timestamp()))

    @staticmethod
    def mongo_db():
        with open("files/config.json", "r") as conf_file:
            conf = json.load(conf_file)["mongo_config"]

        mongo_client = MongoClient(
            host       = conf["host"],
            username   = conf["username"],
            password   = conf["password"],
            authSource = conf["db"],
        )

        return mongo_client[conf["db"]]

    @staticmethod
    def create_search_data(req: dict):
        search_data = dict()
        search_data["id"] = req["id"]
        search_data["description"] = req["networkName"]

        if req["queryMode"] == "pubmed":
            on = "pmc" if req["searchType"] == "full-text" else "pubmed"
            search_data[on + "_retmax"] = req["papersNumber"]
            search_data[on + "_sort"] = req["sortType"]
            if req["searchOn"] == "terms":
                search_data[on + "_terms"] = req["input"]
            elif req["searchOn"] == "ids":
                search_data[on + "_id"] = req["input"]
        elif req["queryMode"] == "text":
            search_data["freetext"] = req["input"]
        elif req["queryMode"] == "pdf":
            search_data["pdf"] = req["fn_list"]

        search_data["created_on"] = Utils.get_time()

        return search_data
