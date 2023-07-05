class Connection:
    def __init__(self, sel_token, offset, connection_idx):
        self.text             = None
        self.is_root          = False
        self.verb_lem         = []
        self.bioterms_score   = []
        self.offset           = offset
        # SPACY CONNECTION POS
        self.spacy_spos       = None
        self.spacy_epos       = None
        self.pos              = []
        # TEXT CONNECTION POS
        self.start_pos        = None
        self.end_pos          = None
        # ENTITIES
        self.left_entity      = set()
        self.right_entity     = set()
        # CONNECTIONS
        self.left_connection  = set()
        self.right_connection = set()
        # HOPS
        self.verb_hop_left    = []
        self.verb_hop_right   = []
        self._verb_configuration(sel_token, connection_idx)

    # VERB BASE CONFIGURATION
    def _verb_configuration(self, sel_token, connection_idx):
        self.text       = sel_token.text
        self.is_root    = sel_token.dep_ == "ROOT"
        self.spacy_spos = sel_token.i
        self.spacy_epos = self.spacy_spos + 1
        self.start_pos  = sel_token.idx
        self.end_pos    = self.start_pos  + len(self.text)
        self.pos.append(sel_token.pos_)
        connection_idx[self.spacy_spos] = self.spacy_spos
        if sel_token.pos_ == "VERB": self.verb_lem.append(sel_token.lemma_)

    # CONNECTION JOINING
    def connection_merging(self, connection, doc_, connection_idx):
        self.text        = doc_.text[self.start_pos: connection.end_pos]
        self.is_root     = self.is_root or connection.is_root
        if connection.verb_lem: self.verb_lem += connection.verb_lem
        self.spacy_epos  = connection.spacy_epos
        self.end_pos     = connection.end_pos
        self.pos        += connection.pos
        connection_idx[connection.spacy_spos] = self.spacy_spos

    # ADD ENTITIES
    def add_entity(self, entity_pos):
        if entity_pos < self.spacy_spos:
            self.left_entity.add(entity_pos)
            return
        self.right_entity.add(entity_pos)

    # ADD CONNECTIONS
    def add_connection(self, connection_pos):
        if connection_pos == self.spacy_spos: return
        if connection_pos < self.spacy_spos:
            self.left_connection.add(connection_pos)
            return
        self.right_connection.add(connection_pos)