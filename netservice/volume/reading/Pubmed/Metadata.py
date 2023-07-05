# GLOBAL FUNCTION
def dict_field_population(selected_tag, sub_tag_name, selected_dict):
    sub_tags = selected_tag.findall(".//" + sub_tag_name)
    if not sub_tags or len(sub_tags) == 0: return
    for sub_tag in sub_tags:
        if not sub_tag.attrib: continue
        tag_attrib = next(iter(sub_tag.attrib.values()))
        selected_dict[tag_attrib] = sub_tag.text


# CLASS
class Metadata:
    def __init__(self, article_meta_tag):
        self.article_id_map = dict()
        dict_field_population(article_meta_tag, "article-id", self.article_id_map)
