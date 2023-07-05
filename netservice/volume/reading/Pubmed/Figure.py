from   itertools import chain
import sys
sys.path.append("../../")
from reading.Pubmed.Section import Section


# GLOBAL FUNCTION
def stringify_children(node):
    """
    Filters and removes possible Nones in texts and tails
    ref: http://stackoverflow.com/questions/4624062/get-all-text-inside-a-tag-in-lxml
    """
    if node is None: return
    parts = (
        [node.text]
        + list(chain(*([c.text, c.tail] for c in node.getchildren())))
        + [node.tail]
    )
    return "".join(filter(None, parts))


class Image:
    def __init__(self, element_tag, etree):
        self.fig_id      = element_tag.attrib["id"]
        self.label       = stringify_children(element_tag.find(".//label"))
        self.caption     = Section(element_tag.find(".//caption"), etree, "Caption")
        self.graphic_ref = self.graphic_ref_definition(element_tag)

    @staticmethod
    def graphic_ref_definition(parent_tag):
        graphic     = parent_tag.find("graphic")
        graphic_ref = graphic.attrib.values()[0] if graphic is not None else None
        return graphic_ref

