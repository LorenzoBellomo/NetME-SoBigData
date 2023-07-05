import hashlib
from   NetworkManager.Network import Node
from   Annotation.Annotation  import AnnotationGlobal
from   NetworkManager.Network import Network


"""
def node_template(node: Node, global_node: AnnotationGlobal):
    return {
        "key"       : global_node.spot,          # SPOT  (GLOBAL_NODE)
        "edge"      : global_node.spot,          # SPOT  (GLOBAL_NODE)
        "Word"      : global_node.word,          # WORD  (GLOBAL_NODE)
        "spot"      : global_node.spot,          # SPOT  (GLOBAL_NODE)
        "categories": global_node.categories,    # CATS  (GLOBAL_NODE)
        "count"     : round(node.size * 200, 2), # NODE
        "pagerank"  : round(node.pagerank,   3)
    }
"""


def node_template(node: Node, global_node: AnnotationGlobal):
    return {
        "key"       : global_node.word,              # WORD  (GLOBAL_NODE)
        "edge"      : global_node.word,              # WORD  (GLOBAL_NODE)
        "word"      : global_node.word,              # WORD  (GLOBAL_NODE)
        "spot"      : list(set(global_node.spots)),  # SPOT  (GLOBAL_NODE)
        "categories": global_node.categories,        # CATS  (GLOBAL_NODE)
        "count"     : round(node.size * 200, 2),     # NODE
        "pagerank"  : round(node.pagerank,   3)
        # "wiki_url"
    }


def edge_template(edge_obj, action_obj, key, global_annot):
    return {
        "key"     : key,   # EDGE_ID
        # "source"  : global_annot[edge_obj.source].spot,  # SPOT SRC
        # "target"  : global_annot[edge_obj.target].spot,  # SPOT DST
        "source"  : global_annot[edge_obj.source].word,  # WORD SRC
        "target"  : global_annot[edge_obj.target].word,  # WORD DST
        "edge"    : "; ".join(action_obj.action_term),   # CONCATENATE EDGE LABEL
        "weight"  : round(edge_obj.weight      , 3),     # TF IDF
        "mrho"    : round(edge_obj.mrho        , 3),     # FINAL MRHO
        "bio"     : round(action_obj.bio_scores, 3),     # BIO VALUE
        "articles": edge_obj.aid,                        # ARTICLES ID
    }


def sentence_template(sentence):
    sent = sentence.sentence_obj
    return {
        "text"     : sent.spacy_sentence.text,
        "start_pos": sent.start_pos,
        "end_pos"  : sent.end_pos,
        "edges"    : [],
        "edges_new": {},
    }


def node_creation_dump(network: Network, annotations):
    glob_annot = annotations.global_annotations.annotations_map
    return [
        node_template(node, glob_annot[node_id])
        for node_id, node in network.nodes.items()
    ]


def sentence_edge_creation_dump(network: Network, annotations):
    graph_edges   = {}
    gui_sentences = {}
    glob_annot    = annotations.global_annotations.annotations_map

    for document_id, doc_obj in network.docs_sents.items():
        if document_id not in gui_sentences:
            gui_sentences[document_id] = {}
        doc = gui_sentences[document_id]
        for sentence_id, sentence_obj in doc_obj.sentences.items():
            if sentence_id not in doc:
                doc[sentence_id] = sentence_template(sentence_obj)
            sent = doc[sentence_id]
            for edge_id, actions_info in sentence_obj.edges_new.items():
                for i in range(len(actions_info["actions"])):
                    edge_obj   = network.edges[edge_id]
                    action_obj = network.actions.actions[actions_info["actions"][i][0]]
                    # SELF LOOP MANAGING
                    if edge_obj.source == edge_obj.target and len(action_obj.action_term) > 1: continue
                    key        = edge_id + "_" + actions_info["actions"][i][0]
                    key        = hashlib.md5(key.encode('utf-8')).hexdigest()
                    if key not in graph_edges:
                        graph_edges[key] = edge_template(edge_obj, action_obj, key, glob_annot)
                    sent["edges"].append(key)
                    sent["edges_new"][key] = {
                        "source"  : actions_info["sources"][i],
                        "target"  : actions_info["targets"][i],
                        "act_pos" : actions_info["act_pos"][i],
                    }
    for document_id, sentences in gui_sentences.items():
        gui_sentences[document_id] = list(sentences.values())
    return list(graph_edges.values()), gui_sentences


def dump_creation(network: Network, annotations, query_mode):
    # DUPLICATE DELETION
    for doc_sents in network.docs_sents.values():
        for sentence in doc_sents.sentences.values():
            sentence.data_cleaning()
    documents        = [
        network.type + "|" + doc + "|" +
        annotations.documents_sections[doc].title if
        annotations.documents_sections[doc].title else doc
        for doc in list(network.docs_sents.keys())
    ]
    nodes            = node_creation_dump(network, annotations)
    edges, sentences = sentence_edge_creation_dump(network, annotations)
    edges = sorted(edges, key=lambda d: d['bio'], reverse=True)
    return {
        "nodes"     : nodes,
        "edges"     : edges,
        "articles"  : documents,
        "sentences" : sentences
    }