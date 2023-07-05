# IMPORT
import hashlib
import json
import math
from   NetworkManager.ActionsStructure import ActionsMap


# SOURCE AND TARGET ARE THE SPOT
# KEY IS THE MD5 VALUE BETWEEN:
#    - GLOBAL ANNOTATION SOURCE MD5
#    - GLOBAL ANNOTATION TARGET MD5
# RELATIONS IS A DICT:
#    - ACTION LENGTH
#         - ACTION MD5 CODE: SCORE * FREQ
# WEIGHT IS THE TF-IDF
class Edge:
    def __init__(self):
        self.key         = None
        self.source      = None
        self.target      = None
        self.relations   = {}
        self.mrho        = []
        self.tf          = {}
        self.weight      = 0.0
        self.aid         = []

    def edge_configuration(self, code, source_node, dest_node, edge_info, actions):
        self.key         = code
        self.source      = source_node.global_annotation
        self.target      = dest_node.global_annotation
        self.mrho        = [(float(source_node.rho) + float(dest_node.rho)) / 2.0]
        act_cod, act_scr = self._relation_setting(edge_info[2], actions, edge_info[3])
        self.tf          = {edge_info[0]: {"tf": act_scr}}
        return act_cod, act_scr

    def edge_updating(self, source_node, dest_node, edge_info, actions):
        self.mrho.append((float(source_node.rho) + float(dest_node.rho)) / 2.0)
        act_cod, act_scr = self._relation_setting(edge_info[2], actions, edge_info[3])
        if edge_info[0] not in self.tf: self.tf[edge_info[0]] = {"tf": act_scr}
        else: self.tf[edge_info[0]]["tf"] += act_scr
        return act_cod, act_scr

    def _relation_setting(self, action, actions, bio_scores):
        action_obj   = actions.add_action_in_map(action, bio_scores)
        if action_obj.action_size not in self.relations:
            self.relations[action_obj.action_size] = {}
        size_struct  = self.relations[action_obj.action_size]
        if action_obj.code not in size_struct:
            size_struct[action_obj.code] = 0.0
        size_struct[action_obj.code] += action_obj.action_score
        return action_obj.code, action_obj.action_score

    def tf_computing(self, doc_num, docs_sents):
        idf = math.log10(doc_num / len(self.tf))
        tf  = sum([
            doc["tf"] / docs_sents[doc_id].document_edges
            for doc_id, doc in self.tf.items()
        ])
        self.weight = (tf * idf) if idf != 0 else tf


#
# ---> CLASS INFORMATION
# GRAPH NODE:
#   - KEY  IS THE GLOBAL ANNOTATION MD5.
#   - SIZE IS THE NODE FREQUENCY
#   - EDGE PART CONTAINS THE SCORE OF EACH IN COMING AND
#     OUT COMING EDGE
class Node:
    def __init__(self, node_info):
        self.key         = None
        self.size        = 0
        self.pagerank    = None
        self._node_configuration(node_info)

    def _node_configuration(self, node_info):
        self.key         = node_info.global_annotation
        self.size        = 1

    def node_updating(self):
        self.size       += 1


#
# --->CLASS INFO
# DOCUMENT SENTENCE STRUCTURE
#   - sentence_obj CONTAINS THE SPACY SENTENCE OBJECT
#   - edges IS A TUPLE CONTAINS THE SENTENCE'S EDGE INFORMATION
#     --> (edge_code, action_code)
# WHERE:
#     edge_code   IS THE md5 OF (src.md5, dst.md5)
#     action_code IS THE md5 OF THE ACTION (VERBS) OBJECT
class SentenceEdges:
    def __init__(self, sentence):
        self.sentence_obj = sentence
        self.edges_new    = {}

    def add_edge_info(self, edge_code, action_code, snode, tnode, action_pos):
        if edge_code not in self.edges_new:
            self.edges_new[edge_code] = {
                "sources": [],
                "targets": [],
                "actions": [],
                "act_pos": [],
            }
        action_pos = [(tuple_[0] - self.sentence_obj.spacy_offset, tuple_[1] - self.sentence_obj.spacy_offset) for tuple_ in action_pos]
        self.edges_new[edge_code]["sources"].append((snode.start_pos - self.sentence_obj.start_pos, snode.end_pos - self.sentence_obj.start_pos))
        self.edges_new[edge_code]["targets"].append((tnode.start_pos - self.sentence_obj.start_pos, tnode.end_pos - self.sentence_obj.start_pos))
        self.edges_new[edge_code]["actions"].append(action_code)
        self.edges_new[edge_code]["act_pos"].append(action_pos)

    def data_cleaning(self):
        edge_new_elab = {}
        for edge_code, edge_data in self.edges_new.items():
            if len(edge_data["sources"]) == 1:
                edge_new_elab[edge_code] = edge_data
                continue
            edge_new_elab[edge_code] = {
                "sources": [],
                "targets": [],
                "actions": [],
                "act_pos": [],
            }
            hash_vals  = []
            for i in range(len(edge_data["sources"])):
                hash_v = hashlib.md5(json.dumps(
                    (edge_data["sources"][i], edge_data["targets"][i], edge_data["actions"][i], edge_data["act_pos"][i]),
                    sort_keys=True).encode('utf-8')
                ).hexdigest()
                if hash_v in hash_vals: continue
                hash_vals.append(hash_v)
                edge_new_elab[edge_code]["sources"].append(edge_data["sources"][i])
                edge_new_elab[edge_code]["targets"].append(edge_data["targets"][i])
                edge_new_elab[edge_code]["actions"].append(edge_data["actions"][i])
                edge_new_elab[edge_code]["act_pos"].append(edge_data["act_pos"][i])
        self.edges_new = edge_new_elab


#
# --> CLASS DOCUMENTATION
# THIS CLASS IS USED TO STORE THE WHOLE SET OF SELECTED DOCUMENT
# SENTENCES WITHIN sentences ATTRIBUTE. THE SECOND ATTRIBUTE,
# INSTEAD, CONTAINS THE TOTAL NUMBER OF DOCUMENT'S EDGE
class DocumentSentences:
    def __init__(self):
        self.sentences      = {}
        self.document_edges = 0

    def add_edge_data(self, sentence, edge_code, action_code, snode, tnode, action_pos):
        if sentence.end_pos not in self.sentences:
            self.sentences[sentence.end_pos] = SentenceEdges(sentence)
        sent_obj = self.sentences[sentence.end_pos]
        sent_obj.add_edge_info(edge_code, action_code, snode, tnode, action_pos)
        self.document_edges += 1


class Network:
    def __init__(self):
        self.type         = None
        self.actions      = ActionsMap()
        self.docs_sents   = {}
        self.nodes        = {}
        self.edges        = {}
        self.adj_list     = {}
        self.max_prn_node = 300

    # edge: (
    #     -> source_annotation,
    #           0          1                  2                       3                           4
    #     -> (doc_id, sentence_obj, [verb_1, ..., verb_n], [bio_s_1, ..., bio_s_n], [verb_1_pos, ..., verb_n_pos])
    #     -> dest_annotation
    # )
    def add_edge(self, edge):
        sannot, edge_info, dannot = edge
        snode_id = self._add_node(sannot)
        dnode_id = self._add_node(dannot)
        edge_id  = hashlib.md5((snode_id + "_" + dnode_id).encode("utf-8")).hexdigest()
        if edge_id not in self.edges:
            edge      = Edge()
            action_id = edge.edge_configuration(edge_id, sannot, dannot, edge_info, self.actions)
            self.edges[edge_id] = edge
        else:
            edge      = self.edges[edge_id]
            action_id = edge.edge_updating(sannot, dannot, edge_info, self.actions)
        if edge_info[0] not in self.docs_sents:
            self.docs_sents[edge_info[0]] = DocumentSentences()
        self.docs_sents[edge_info[0]].add_edge_data(edge_info[1], edge_id, action_id, sannot, dannot, edge_info[-1])

    def _add_node(self, annotation_obj):
        if annotation_obj.global_annotation not in self.nodes:
            node_obj = Node(annotation_obj)
            self.nodes[node_obj.key] = node_obj
            return node_obj.key
        self.nodes[annotation_obj.global_annotation].node_updating()
        return annotation_obj.global_annotation

    def edge_score_computing(self):
        doc_num = len(self.docs_sents)
        max_edge_score = -1
        for edge in self.edges.values():
            edge.tf_computing(doc_num, self.docs_sents)
            max_edge_score = max(edge.weight, max_edge_score)
        for edge_id, edge in self.edges.items():
            edge.weight      = edge.weight/max_edge_score
            edge.mrho        = sum(edge.mrho) / len(edge.mrho)
            edge.aid         = list(edge.tf.keys())
            src, dst         = edge.source, edge.target
            if src not in self.adj_list: self.adj_list[src] = []
            self.adj_list[src].append((dst, edge_id))

    def node_score_normalization(self):
        max_score     = -1
        for node in self.nodes.values():
            max_score = max(max_score, node.size)
        for node in self.nodes.values():
            node.size = node.size / max_score
        self.nodes = dict(sorted(self.nodes.items(), key=lambda x: x[1].size, reverse=True))