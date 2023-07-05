from   Utility.Utility           import Utility as Ut
from   ErrorMessage.Messages     import Messages


# LEFT ENTITIES EXPANSION
def left_population(sel_verb, edges):
    left_conn = [(connection, []) for connection in sel_verb.left_connection]
    left_conn.sort(key=lambda tup: tup[0], reverse=True)
    update_conn = []
    while len(left_conn) != 0:
        for connection in left_conn:
            conn_obj = edges[connection[0]]
            if len(conn_obj.left_entity) != 0:
                sel_verb.verb_hop_left += connection[1]
                sel_verb.verb_hop_left.append(connection[0])
                update_conn = []
                break
            sub_left_conn = conn_obj.left_connection
            if len(sub_left_conn) == 0: continue
            if len(conn_obj.verb_hop_left) != 0:
                sel_verb.verb_hop_left += connection[1]
                sel_verb.verb_hop_left.append(connection[0])
                sel_verb.verb_hop_left += conn_obj.verb_hop_left.copy()
                update_conn = []
                break
            for sub_conn in sub_left_conn:
                update_conn.append((sub_conn, connection[1].copy() + [connection[0]]))
        left_conn   = update_conn
        update_conn = []
        left_conn.sort(key=lambda tup: tup[0], reverse=True)


# RIGHT ENTITIES EXPANSION
def right_population(sel_verb, edges):
    right_conn = [(connection, []) for connection in sel_verb.right_connection]
    right_conn.sort(key=lambda tup: tup[0], reverse=False)
    update_conn = []
    while len(right_conn) != 0:
        for connection in right_conn:
            conn_obj = edges[connection[0]]
            if len(conn_obj.right_entity) != 0:
                sel_verb.verb_hop_right += connection[1]
                sel_verb.verb_hop_right.append(connection[0])
                update_conn = []
                break
            else:
                sub_right_conn = conn_obj.right_connection
                if len(sub_right_conn) == 0: continue
                if len(conn_obj.verb_hop_right) != 0:
                    sel_verb.verb_hop_right += connection[1]
                    sel_verb.verb_hop_right.append(connection[0])
                    sel_verb.verb_hop_right += conn_obj.verb_hop_right.copy()
                    update_conn = []
                    break
                for sub_conn in sub_right_conn:
                    update_conn.append((sub_conn, connection[1].copy() + [connection[0]]))
        right_conn  = update_conn
        update_conn = []
        right_conn.sort(key=lambda tup: tup[0], reverse=False)


# CONFIGURED FOR LEFT ENTITY EXPANSION
def action_construction_reverse(edge, edges):
    hops       = list(reversed(edge.verb_hop_left))
    actions    = [edges[hop].text for hop in hops]
    actions.append(edge.text)
    bio_scores = [edges[hop].bioterms_score for hop in hops]
    bio_scores.append(edge.bioterms_score)
    actions_ps = [(edges[hop].start_pos, edges[hop].end_pos) for hop in hops]
    actions_ps.append((edge.start_pos, edge.end_pos))
    return actions, bio_scores, actions_ps


# CONFIGURED FOR RIGHT ENTITY EXPANSION
def action_construction_directed(edge, edges):
    hops       = edge.verb_hop_right
    actions    = [edges[hop].text for hop in hops]
    actions    = [edge.text] + actions
    bio_scores = [edges[hop].bioterms_score for hop in hops]
    bio_scores = [edge.bioterms_score] + bio_scores
    actions_ps = [(edges[hop].start_pos, edges[hop].end_pos) for hop in hops]
    actions_ps = [(edge.start_pos, edge.end_pos)] + actions_ps
    return  actions, bio_scores, actions_ps


# ADD NODES AND EDGES INTO NETWORK
def add_nodes_edges(doc_id, sentence_obj, left, right, actions, bio_scores, network, actions_ps):
    for left_id in left:
        src = sentence_obj.nodes[sentence_obj.nodes_idx[left_id][1]]
        for right_id in right:
            dst    = sentence_obj.nodes[sentence_obj.nodes_idx[right_id][1]]
            tuple_ = (src, (doc_id, sentence_obj, actions, bio_scores, actions_ps), dst)
            network.add_edge(tuple_)


def section_elaboration(doc_id, section, network):
    for sentence_id, sentence in section.sentences.items():
        for edge in sentence.edges.values():
            if len(edge.left_entity)  != 0 and len(edge.right_entity) != 0:
                actions_ps = [(edge.start_pos, edge.end_pos)]
                add_nodes_edges(doc_id, sentence, edge.left_entity, edge.right_entity, [edge.text], [edge.bioterms_score], network, actions_ps)
                continue
            if len(edge.left_entity)  == 0 and len(edge.right_entity) == 0:
                continue
            if len(edge.left_entity)  == 0:
                left_population(edge, sentence.edges)
                if len(edge.verb_hop_left) == 0: continue
                actions, bioscores, actions_ps = action_construction_reverse(edge, sentence.edges)
                left = sentence.edges[edge.verb_hop_left[-1]].left_entity
                add_nodes_edges(doc_id, sentence, left, edge.right_entity, actions, bioscores, network, actions_ps)
            else:
                right_population(edge, sentence.edges)
                if len(edge.verb_hop_right) == 0: continue
                actions, bioscores, actions_ps = action_construction_directed(edge, sentence.edges)
                right = sentence.edges[edge.verb_hop_right[-1]].right_entity
                add_nodes_edges(doc_id, sentence, edge.left_entity, right, actions, bioscores, network, actions_ps)


async def edge_creation_main(annotation_data, network, req_id, pub):
    utility = Ut()
    doc_num = len(annotation_data.documents_sections)
    count   = 0.0
    for doc_id, document in annotation_data.documents_sections.items():
        score = 0.6 + count/doc_num * 0.3
        await utility.task_status_updating(Messages.EDGE_DOC.format(id=doc_id), score, req_id, pub)
        combinations = {}
        for section_name, offset_section in document.spacy_sections.items():
            combinations[section_name] = []
            for section in offset_section.values():
                section_elaboration(doc_id, section, network)
