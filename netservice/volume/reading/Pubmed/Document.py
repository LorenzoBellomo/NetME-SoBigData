from   reading.Pubmed.Metadata import Metadata
from   reading.Pubmed.Section  import Section
from   reading.Pubmed.Figure   import Image


class Document:
    def __init__(self, article, etree):
        self.pmcid      = None
        self.title      = self.title_configuration(article.find(".//article-title"))
        self.metadata   = None
        self.abstract   = None
        self.full_text  = None
        self.images     = {}
        self.document_configuration(article, etree)

    @staticmethod
    def title_configuration(title_tag):
        if title_tag is None: return ""
        title = [t for t in title_tag.itertext()]
        sub_title = title_tag.findall(".//title-group/subtitle")
        if sub_title is not None:
            sub_title = [stitle.text for stitle in sub_title if sub_title is not None and sub_title.text is not None]
        title.extend(sub_title)
        title = [t.replace("\n", " ").replace("\t", " ") for t in title]
        return " ".join(title)

    @staticmethod
    def images_elaboration(images, etree):
        images_dict = {}
        if images is not None:
            count = 0
            for image in images:
                img = Image(image, etree)
                if not img.fig_id: img.fig_id = "Image_" + str(count)
                images_dict[img.fig_id] = img
                count += 1
        return images_dict

    # DOCUMENT CREATINON
    def document_configuration(self, article, etree):
        # XML NODE
        journal_metadata = article.find(".//journal-meta")
        article_metadata = article.find(".//article-meta")
        body             = article.find(".//body")
        images           = article.findall(".//fig")

        # METADATA CONFIGURTION
        print("-METADATA ELABORATION STARTING!")
        self.metadata = Metadata(article_metadata)
        self.pmcid = self.metadata.article_id_map["pmc"] if "pmc" in self.metadata.article_id_map else \
                     self.metadata.article_id_map["pmid"]
        # ABSTRACT
        print("-ABSTRACT ELABORATION STARTING!")
        abstract      = article_metadata.find(".//abstract")
        self.abstract = Section(abstract, etree, "abstract")

        # FULL TEXT
        print("-FULL TEXT ELABORATION STARTING!")
        if body is not None:
            self.full_text = Section(body, etree, "full_text")

        # IMAGE
        print("-IMAGES ELABORATION STARTING!")
        self.images = self.images_elaboration(images, etree)

