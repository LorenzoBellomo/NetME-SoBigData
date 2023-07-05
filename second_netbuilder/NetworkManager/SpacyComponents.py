# SENTENCE MODEL
import numpy as np
from   NetworkManager.SpacyConnection import Connection
from   Utility.Utility                import Utility     as UT


# GLOBAL VARIABLE
ACTIONS  = ["VERB", "AUX", "PART"]
BIOTERMS = UT.get_bio_terms()


class Sentence:
    def __init__(self, sentence, offset, section):
        self.spacy_sentence  = sentence
        self.section_ref     = section
        self.offset          = offset
        self.spacy_offset    = section[self.spacy_sentence.start].idx
        self.start_pos       = None
        self.end_pos         = None
        self.nodes           = []
        self.edges           = {}
        self.nodes_idx       = {}
        self.edges_idx       = {}
        self.other_elem_spos = {}
        self.other_elem_epos = {}
        self._position_configuration(section)

    def _position_configuration(self, section):
        self.start_pos = self.offset    + self.spacy_offset
        self.end_pos   = self.start_pos + len(self.spacy_sentence.text)

    def add_annotations(self, annotations, annotations_key, global_annotations):
        # tokens_idx_i: {token_real_start_pos: (token_spacy_index, token_real_end_pos)}
        tokens_idx_i = {}
        for token in self.spacy_sentence:
            token_real_pos = token.idx + self.offset
            tokens_idx_i[token_real_pos] = (token.i, token_real_pos + len(token.text))
        # ANNOTATIONS WITHIN SENTENCE
        positions    = (annotations_key >= self.start_pos) & (annotations_key < self.end_pos)
        selected_annotations_spos = annotations_key[positions]
        annotations_global = global_annotations.annotations_map
        # PROCESSING
        for spos in selected_annotations_spos:
            annotation = annotations[spos]
            self.nodes.append(annotation)
            annotation_vect_pos = len(self.nodes) - 1
            # selected_tokens: [token_spacy_index]
            selected_tokens = []
            for token_spos, token_info in tokens_idx_i.items():
                if token_info[1] <= spos or token_spos >= annotation.end_pos: continue
                selected_tokens.append(token_info[0])
            for element in selected_tokens:
                self.nodes_idx[element] = (selected_tokens[0], annotation_vect_pos)

    def add_edges(self):
        # EDGE SELECTION
        for token in self.spacy_sentence:
            # IF TOKEN IS NOT A VERB OR HAS BEEN ANNOTATED BY ONTOTAGME
            if token.pos_ not in ACTIONS or token.i in self.nodes_idx: continue
            # PART OF SPEACH IS A VERB, BUT IT IS AN ERROR
            if "obj"  in token.dep_: continue
            # CONJUNCTION OF THE VERB, BUT THE HEAD IS NOT A VERB
            if "conj" in token.dep_ and "obj" in token.head.dep_: continue
            connection = Connection(token, self.offset, self.edges_idx)
            self.edges[connection.spacy_spos] = connection
        if len(self.edges) == 0: return
        # EDGE MERGING
        verbs_pos = list(self.edges.keys())
        last_pos  = verbs_pos[0]
        for verb_pos in verbs_pos[1:]:
            verb  = self.edges[verb_pos]
            if self.edges[last_pos].spacy_epos != verb_pos:
                last_pos = verb_pos
                continue
            self.edges[last_pos].connection_merging(verb, self.section_ref, self.edges_idx)
            self.edges.pop(verb_pos)
        # ADD BIOTERM SCORE
        for edge in self.edges.values():
            UT.bioterms_score_computing(BIOTERMS, edge)
        # ADD LEFT AND RIGHT CONNECTION
        for i, j in self.edges_idx.items():
            token = self.section_ref[i]
            while True:
                if token.head.i not in self.edges_idx and token.head.dep_ != "ROOT":
                    token = token.head
                    continue
                if token.head.dep_ == "ROOT": break
                if self.edges_idx[token.head.i] == j:
                    token = token.head
                    continue
                break
            if token.head.i not in self.edges_idx: continue
            self.edges[j].add_connection(self.edges_idx[token.head.i])
            self.edges[self.edges_idx[token.head.i]].add_connection(j)

    def add_entities_to_edges(self):
        for i, node_info in self.nodes_idx.items():
            token = self.section_ref[i]
            while token.head.i not in self.edges_idx and token.head.dep_ != "ROOT":
                token = token.head
            if token.head.i not in self.edges_idx: continue
            edge = self.edges[self.edges_idx[token.head.i]]
            edge.add_entity(node_info[0])


# SECTION MODEL
class Section:
    def __init__(self, offset, section, section_name, nlp):
        self.spacy_doc       = nlp(section)
        self.offset          = offset
        self.section_name    = section_name
        self.start_pos       = offset
        self.end_pos         = offset + len(section)
        self.sentences       = {}
        self._sentences_configuration()

    def _sentences_configuration(self):
        for sentence in self.spacy_doc.sents:
            sentence_obj = Sentence(sentence, self.offset, self.spacy_doc)
            self.sentences[sentence_obj.start_pos] = sentence_obj

    def add_annotation(self, document_annotations, global_annotations):
        if self.section_name not in document_annotations.document_annotations:
            self.sentences = {}
            return
        annotations        = document_annotations.document_annotations[self.section_name]
        if self.offset not in annotations:
            self.sentences = {}
            return
        annotations        = annotations[self.offset]
        annotations_keys   = np.array(list(sorted(annotations.keys())))
        sentences_keys     = list(self.sentences.keys())
        for sentence_id in sentences_keys:
            sentence       = self.sentences[sentence_id]
            sentence.add_annotations(annotations, annotations_keys, global_annotations)
            if len(sentence.nodes) > 1: continue
            self.sentences.pop(sentence_id)

    def add_connection(self):
        for sentence in self.sentences.values():
            sentence.add_edges()
            sentence.add_entities_to_edges()