import hashlib
import json
import logging
import math
import requests
import numpy
from   utils         import Utils
from   spacy.symbols import VERB


# LOGGING CREATION
logging.basicConfig(filename="files/netme.log", level=logging.DEBUG)
spot_key = 'spot'


class Network:
    def __init__(self, wrapper):
        self.wrapper        = wrapper
        self.network        = {"edges"  : {}, "nodes": {}}
        self.annotations    = {"article": {}, "word_list": {}, "spot_list": {}}
        self.sentences      = {}
        self.sentences_gui  = {}
        self.sentences_map  = {}
        self.max_count      = 0
        self.max_connection = 0

    def request_data(self, article_id, article_text):
        data = self.get_annotations(article_id)
        try:
            # ANNOTATIONS BUILDING
            if data is None:
                par  = {"name": article_text}
                r    = requests.post(url=Utils.webserver_url, data=par, timeout=1800)
                data = r.json()
                if data["response"]:
                    self.save_annotations_db(article_id, json.dumps(data["response"]))
                data = data["response"]
            if data is None: return
            doc = self.wrapper.nlp(article_text)

            # ARTICLE_ID -> SENTENCEs' TEXT
            for sentence_id, sentence in enumerate(doc.sents):
                if article_id in self.sentences_map:
                    self.sentences_map[article_id].append(sentence.text)
                else:
                    self.sentences_map[article_id] = [sentence.text]

            # ARTICLE_ID -> SENTENCE_END_POS -> [SENTENCE_ID, SPACY_SENTENCE_OBJECT, SENTENCE_ANNOTATIONS_START_POS]
            self.sentences[article_id]     = {}
            self.sentences_gui[article_id] = {}
            for sentence_id, sentence in enumerate(doc.sents):
                start_pos = doc[sentence.start].idx
                end_pos   = start_pos + (len(sentence.text) - 1)
                self.sentences[article_id][end_pos] = [sentence_id, sentence, []]
                self.sentences_gui[article_id][end_pos] = self.sentence_model(sentence, start_pos, end_pos)
            self.annotations_configuration(article_id, data, self.sentences[article_id])
        except Exception as e:
            print(e)
            logging.error("ERROR: " + str(e))

    # GET ANNOTATIONS FROM MONGODB
    def get_annotations(self, article_id, searchid=None):
        logging.info("GET ANNOTATION FROM MONGODB")
        try:
            if "pmc|" in article_id or "pubmed|" in article_id:
                annotations = self.wrapper.mongo_db["annotations"].find({"id_article": article_id})
            else:
                annotations = self.wrapper.mongo_db["annotations"].find({"search_id": searchid, "id_article": article_id})
            return json.loads(annotations["data"]) if annotations is not None else None
        except Exception as e:
            logging.error("WORKER get_annotations: " + str(e))
            return None

    # SAVING DOCUMENT'S ANNOTATION INTO MONGODB
    def save_annotations_db(self, id_article, text, searchid=None):
        logging.info("SAVE ANNOTATION WITHIN MONGODB")
        try:
            self.wrapper.mongo_db["annotations"].update_one(
                {"search_id": searchid},
                {"$set": {"data": text, "id_article": id_article}},
                upsert=True,
            )
        except Exception as e:
            logging.error("WORKER save_annotations_db: " + str(e))

    # CONFIGURE ANNOTATION STRUCTURE
    def annotations_configuration(self, id_article, data, sentence_map):
        logging.info("ANNOTATIONS CONFIGURATION")
        sen_pos = sentence_map.keys()
        self.annotations["article"][id_article] = {}
        for key, annotation in enumerate(data):
            try:
                # ADD SENTENCE TO ANNOTATION TERM
                for pos in sen_pos:
                    if pos < annotation["start_pos"]: continue
                    annotation["setence_id"] = sentence_map[pos][0]
                    sentence_map[pos][2].append(annotation["start_pos"])
                    break
                # ADD OTHER TO EMPTY CATEGORY LIST
                if len(annotation["categories"]) == 0 or annotation["categories"][0] == "":
                    annotation["categories"] = ["other"]
                # WORDS
                words = self.annotations["word_list"]
                if annotation["Word"] not in words: words[annotation["Word"]] = {**annotation, "count": 0}
                words[annotation["Word"]]["count"] += 1
                # SPOT
                spots = self.annotations["spot_list"]
                if annotation["spot"] not in spots: spots[annotation["spot"]] = {**annotation, "count": 0}
                spots[annotation["spot"]]["count"] += 1
                # DOCUMENT ANNOTATIONS
                self.annotations["article"][id_article][annotation["start_pos"]] = annotation
            except Exception as e:
                logging.error("Error: " + str(e))

    # EDGE FINDING
    async def edges_finding(self,  article_id, total_words, sentence_id, doc_edges_num):
        sentence_obj = self.sentences[article_id][sentence_id]
        verbs = [(verb.idx, verb.text) for verb in sentence_obj[1] if verb.pos == VERB]
        sentence_obj.append(verbs)
        if len(sentence_obj[3]) == 0: return
        # ENTITY INFORMATION
        words = sentence_obj[2]
        len_w = len(words)
        # VERBS INFORMATION
        last_verb_pos = 0
        verbs   = sentence_obj[3]
        len_v   = len(verbs)
        # DOC ANNOTATIONS
        doc_ann = self.annotations["article"][article_id]
        for i in range(len_w - 1):
            if last_verb_pos == len_v: break
            word_1 = words[i]
            word_2 = words[i + 1]
            while last_verb_pos != len_v:
                if verbs[last_verb_pos][0] >= word_2: break
                if verbs[last_verb_pos][0] <= word_1:
                    last_verb_pos += 1
                else:
                    spot_1 = doc_ann[word_1]
                    spot_2 = doc_ann[word_2]
                    lbls   = verbs[last_verb_pos][1]
                    self.save_edge(article_id, spot_1, spot_2, lbls, total_words, sentence_id, doc_edges_num)
                    last_verb_pos += 1

    #
    def save_edge(self, id_article, spot1, spot2, edge_label, total_words, sentence_id, doc_edges_num):
        edges   = self.network["edges"]
        # EDGE ID CREATION
        edge_id = hashlib.md5((spot1[spot_key] + spot2[spot_key] + edge_label).encode("utf-8")).hexdigest()
        doc_edges_num["edges_num"] += 1
        # CREATE OR UPDATE EDGE DATE
        if edge_id not in edges: 
            edges[edge_id] = self.new_edge_generation(spot1, spot2, edge_label, id_article, total_words, sentence_id, edge_id)
        else:
            new_edge = edges[edge_id]
            new_edge["aid" ].add(id_article)
            new_edge["mrho"].append((float(spot1["rho"]) + float(spot2["rho"])) / 2.0)
            self.sentences_gui[id_article][sentence_id]["edges"].append(edge_id)
            new_edge["articles"] = list(set([id_article] + new_edge["articles"]))
            if id_article not in new_edge["tf"]: new_edge["tf"][id_article] = {"tf": 0, "total_words": total_words}
            new_edge["tf"][id_article]["tf"] += 1

        # NODE CONFIGURATION
        nodes   = self.network["nodes"]
        n1_hash = hashlib.md5((spot1[spot_key]).encode("utf-8")).hexdigest()  # Word --> spot
        n2_hash = hashlib.md5((spot2[spot_key]).encode("utf-8")).hexdigest()  # Word --> spot
        self.node_configuration_completion(nodes, spot1, n1_hash)
        self.node_configuration_completion(nodes, spot2, n2_hash)

    # NODE ELABORATION
    def node_configuration_completion(self, nodes, spot, n_hash):
        # NODE INIT CONFIGURATION
        if n_hash not in nodes:
            nodes[n_hash] = spot
            nodes[n_hash]['key'       ] = spot[spot_key]  # Word --> spot
            nodes[n_hash]['edge'      ] = spot[spot_key]  # Word --> spot
            nodes[n_hash]['size'      ] = 0
            nodes[n_hash]['count'     ] = 0
            nodes[n_hash]['connection'] = 0
        # OTHER CONFIGURATIONS
        nodes[n_hash]['size'      ] += 1
        nodes[n_hash]['count'     ] += 1
        nodes[n_hash]['connection'] += 1
        # GLOBAL CONFIGURATION
        if nodes[n_hash]["count"]      > self.max_count     : self.max_count      = nodes[n_hash]["count"]
        if nodes[n_hash]["connection"] > self.max_connection: self.max_connection = nodes[n_hash]["connection"]

    # EDGE GENERATION TEMPLATE
    def new_edge_generation(self, spot1, spot2, edge_label, id_article, total_words, sentence, edge_id):
        self.sentences_gui[id_article][sentence]["edges"].append(edge_id)
        return {
            "key"       : edge_id,
            "source"    : spot1[spot_key],  # Word  --> spot
            "target"    : spot2[spot_key],  # Word  --> spot
            "edge"      : edge_label,       # label --> edge
            "weight"    : 0,
            "mrho"      : [(float(spot1["rho"]) + float(spot2["rho"])) / 2.0],
            "bio"       : 0,
            "aid"       : {id_article},
            "tf"        : {id_article: {"tf": 1, "total_words": total_words}},
            "articles"  : [id_article]
        }

    @staticmethod
    def sentence_model(sentence, s_pos, e_pos):
        return {
            "text"     : sentence.text,
            "start_pos": s_pos,
            "end_pos"  : e_pos,
            "edges"    : []
        }

    def edge_elaboration(self, articles_num):
        for edge_id, edge in self.network["edges"].items():
            edge["bio" ] = self.wrapper.check_bio_edge(edge["edge"].replace("not ", ""))
            edge["aid" ] = list(edge["aid"])
            edge["mrho"] = numpy.average(edge["mrho"])
            tf_medio     = 0
            for _, tf in edge["tf"].items(): tf_medio += tf["tf"] / tf["total_words"]
            tf_medio = tf_medio / len(edge["tf"])
            idf = math.log(articles_num / len(edge["tf"]))
            edge["weight"] = tf_medio * idf if idf > 0 else tf_medio

    def element_sorting(self):
        w_connection = self.max_connection / 0.7
        w_count      = self.max_count      / 0.3
        # NODE SORTING
        self.network["nodes"] = list(self.network["nodes"].values())
        self.network["nodes"] = sorted(
            self.network["nodes"],
            key     = lambda x: x["connection"] / w_connection + x["count"] / w_count,
            reverse = True
        )
        self.network["edges"] = list(self.network["edges"].values())
        for article_id, sentences_ids in self.sentences_gui.items():
            self.sentences_gui[article_id] = list(sentences_ids.values())