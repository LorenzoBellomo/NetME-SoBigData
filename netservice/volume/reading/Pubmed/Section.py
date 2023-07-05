import re


# GLOBAL FUNCTIONS
def text_cleaning(tag_text, element_to_remove):
    multiple_space           = re.compile(r'(\s){2,}')
    isnt_last_element_string = True
    number_of_elements       = len(element_to_remove)
    cleaner_text             = tag_text[:element_to_remove[0][0]]
    for i in range(number_of_elements):
        if i + 1 >= number_of_elements:
            isnt_last_element_string = False
            text = tag_text[element_to_remove[i][1]:]
        else:
            text = tag_text[element_to_remove[i][1]: element_to_remove[i + 1][0]]
        cleaner_text += text
    if isnt_last_element_string:
        cleaner_text += tag_text[element_to_remove[-1][1]:]
    return re.sub(multiple_space, " ", cleaner_text)


def add_element(sel_dict, tag_name, tag):
    if tag_name not in sel_dict: sel_dict[tag_name] = [tag]
    else: sel_dict[tag_name].append(tag)


class Section:
    # ATTRIBUTES
    def __init__(self, sec_tag, etree, title):
        self.title    = title
        self.text     = ""
        self.sections = []
        self.section_configuration_init(sec_tag, etree)

    @staticmethod
    # REPLACEMENT ARE RELATED TO:
    #   1. MULTIPLE COMMAS              -->  SINGLE COMMA
    #   2. COMMA POINT AND SPACE        -->  SINGLE POINT
    #   3. SQUARE AND MULTIPLE COMMA    -->  NOTHING
    def make_replacement(text):
        multiple_comma = re.compile(r'(,){2,}')
        comma_point    = re.compile(r'[,]*\s*\.')
        square_commas  = re.compile(r'\s\[(,)*\s*]')
        round_commas   = re.compile(r'\s\((,)*\s*\)')
        text           = re.sub(multiple_comma, ",", text)
        text           = re.sub(comma_point, "..", text)
        text           = re.sub(square_commas ,  "", text)
        text           = re.sub(round_commas  ,  "", text)
        return text

    @staticmethod
    # REMOVE REFERENCE FROM THE TEXT
    def remove_references_section(p_tag_txt):
        pos_to_remove        = []
        # text <xref ...>citation or reference</xref>
        ref_tag_pos_regex    = re.compile(r"<xref[^>]*>([^<]+)</xref[^>]*>")
        # [text and number] | numbers
        ref_validation_regex = re.compile(r"\[[^]]+]|\d+")
        # rid="code" -> it will be selected
        rid_refer            = re.compile(r'rid="([^"]+)"')
        for ref in ref_tag_pos_regex.finditer(p_tag_txt):
            term             = ref.group(1)
            validation_term  = ref_validation_regex.match(term)
            if not validation_term: continue
            if rid_refer.search(ref.group(0)) is None: continue
            pos_to_remove.append([ref.start(), ref.end()])
        if len(pos_to_remove) == 0: return  p_tag_txt
        return text_cleaning(p_tag_txt, pos_to_remove)

    # REMOVE XML TAG FROM THE TEXT
    def paragraph_elaboration(self, p_tags, etree):
        paragraphs  = []
        tag_regex   = re.compile(r"<[/]*[^>]+>")
        final_text  = ""
        for p in p_tags:
            if p.tag == "p" and final_text != "":
                paragraphs.append(self.make_replacement(final_text))
                final_text = ""
            p_string  = etree.tostring(p, encoding="utf8").decode("utf8")
            p_cleaned = self.remove_references_section(p_string)
            tag_list  = [[stag.start(), stag.end()] for stag in tag_regex.finditer(p_cleaned)]
            if len(tag_list) == 0: final_text = p_cleaned
            else: final_text += text_cleaning(p_cleaned, tag_list)
        # add last record
        if final_text != "": paragraphs.append(self.make_replacement(final_text))
        self.text = "\n".join(paragraphs)

    def section_configuration_init(self, sec_tag, etree):
        children_map = {}
        if  sec_tag is None: return
        for sub_tag in sec_tag:
            add_element(children_map, sub_tag.tag, sub_tag)
        if "title"  in children_map: self.title    = children_map["title"][0].text
        if "p"      in children_map: self.paragraph_elaboration(children_map["p"], etree)
        if "sec"    in children_map: self.sections = [Section(sec, etree, "") for sec in children_map["sec"]]

