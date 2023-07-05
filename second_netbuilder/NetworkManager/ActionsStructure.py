import hashlib


# ACTION IS A CLASS THAT CONTAINS:
#   - action_term: VECTOR CONTAINING VERBS
#   - action_size: NUMBER OF VERBS
#   - score      : 1 / NUMBER OF VERB
class Action:
    def __init__(self, action_data):
        self.action_term  = None
        self.bio_scores   = None
        self.action_size  = 0
        self.action_score = 0
        self.code         = None
        self.action_configuration(action_data)

    def action_configuration(self, action_data):
        self.action_term  = action_data
        self.action_size  = len(action_data)
        self.action_score = 1.0 / len(self.action_term)
        self.code         = hashlib.md5((",".join(action_data)).encode("utf-8")).hexdigest()


class ActionsMap:
    def __init__(self):
        self.actions = {}

    def add_action_in_map(self, action_data, bio_scores):
        action = Action(action_data)
        if action.code not in self.actions:
            action.bio_scores         = round(sum(bio_scores) / len(bio_scores), 3)
            self.actions[action.code] = action
        return self.actions[action.code]
