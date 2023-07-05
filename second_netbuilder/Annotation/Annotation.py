import requests
import json
import hashlib
import numpy                                              as np
from   NetworkManager.SpacyComponents import Section
from   Utility.Utility                import Utility      as UTS
from   ErrorMessage.Messages          import Messages
from   Logging.OntotagmePolling       import OntoPolling
from   TextSearch.PDFSearch import PDFSearch

# GLOBAL VARIABLE
MESSAGE_0     = "ONTOTAGME ERROR CODE: {error_code}"
MESSAGE_1     = "MISSING ANNOTATION"
SPT           = "spot"
WRD           = "Word"
CTS           = "categories"
SPS           = "start_pos"
EPS           = "end_pos"
SCT           = "section"
ANT           = "annotations"
ANTU          = "annotations_unfiltered"
CON           = "content"
FLD           = "failed"
RHO           = "rho"
QRY           = "query"


# CLASS 1: NODE OF THE NETWORK TEMPLATE
#   - spot      : REAL TERM EXTRACTED FROM THE TEXT
#   - word      : MAIN PAGE OF THE SPOT
#   - categories: CATEGORIES OF THE ANNOTATION
#   - freq      : RECURRENCE OF THE ANNOTATION
"""
class AnnotationGlobal:
    def __init__(self, annotation):
        self.spot       = annotation[SPT]
        self.word       = annotation[WRD]
        self.md5_code   = hashlib.md5(json.dumps(self.__dict__).encode("utf-8")).hexdigest()
        self.categories = [annotation.lower() for annotation in annotation[CTS] if annotation != ""]
        self.freq       = 1  # check

    def frequency_updating(self):
        self.freq += 1  # check     
"""


# CLASS 1: NODE OF THE NETWORK TEMPLATE
#   - word      : MAIN PAGE OF THE SPOT
#   - categories: CATEGORIES OF THE ANNOTATION
#   - md5_code  : HASH OF THE ANNOTATION CONSIDERING ONLY WORD AND CATEGORIES
#   - spots     : LIST OF SPOTS UNDER WORD PAGE
class AnnotationGlobal:
    def __init__(self, annotation):
        self.word       = annotation[WRD]
        self.categories = list(set([annotation.lower() for annotation in annotation[CTS] if annotation != ""]))
        self.md5_code   = hashlib.md5(json.dumps(self.__dict__).encode("utf-8")).hexdigest()
        self.spots      = [annotation[SPT]]

    def add_spot(self, spot):
        self.spots.append(spot)


# CLASS 2: NODES OF THE NETWORK
class AnnotationGlobalMap:
    def __init__(self):
        self.annotations_map = {}

    def add_annotation_if_not_exists(self, annotation):
        annotation_obj = AnnotationGlobal(annotation)
        if annotation_obj.md5_code not in self.annotations_map:
            self.annotations_map[annotation_obj.md5_code] = annotation_obj
        else:
            """
            act_cat  = self.annotations_map[annotation_obj.md5_code].categories
            act_cat += annotation_obj.categories
            act_cat  = list(set(act_cat))
            self.annotations_map[annotation_obj.md5_code].categories = act_cat
            """
            self.annotations_map[annotation_obj.md5_code].add_spot(annotation_obj.spots[0])
        return annotation_obj.md5_code

    def ger_annotation(self, md5_code):
        if md5_code in self.annotations_map:
            return self.annotations_map[md5_code]
        return None


# CLASS 3: SELECTED TEXT NODE TEMPLATE
#    - global_annotation: MD5 CODE OF THE GLOBAL NODE
#    - start_pos        : annotation start position within the section
#    - end_pos          : annotation end   position within the section
#    - rho              : tagme rho
#    - section          : section object
#    - section_offset   : offset of the section
class AnnotationSubtext:
    def __init__(self, annotation, global_annotations, sections, offsets):
        self.global_annotation = None
        self.start_pos         = None
        self.end_pos           = None
        self.rho               = 0.0
        self.section           = None
        self.section_offset    = None
        self._annotation_configuration(annotation, global_annotations, sections, offsets)

    def _annotation_configuration(self, annotation, global_annotations, sections, offsets):
        self.global_annotation = global_annotations.add_annotation_if_not_exists(annotation)
        self.start_pos         = annotation[SPS]
        self.end_pos           = annotation[EPS]
        self.rho               = annotation[RHO]
        self._section_configuration(sections, offsets)

    def _section_configuration(self, sections, offsets):
        sections_offset     = sections.offset_section_name
        selected_offset     = np.where(offsets <= self.start_pos)[0][-1]
        self.section        = sections_offset[offsets[selected_offset]]
        self.section_offset = offsets[selected_offset]


# CLASS 4: DOCUMENT ANNOTATIONS
# STRUCTURE:
#     --> SECTION_NAME
#           OFFSET
#             ANNOTATION_START_POS: ANNOTATION_OBJECT
class DocumentAnnotations:
    def __init__(self):
        self.document_annotations = {}

    def add_document_annotations(self, annotations, global_annotation, sections):
        offsets = np.array(list(sorted(sections.offset_section_name.keys())))
        for annotation in annotations:
            annotation_obj = AnnotationSubtext(annotation, global_annotation, sections, offsets)
            section        = annotation_obj.section
            spos           = annotation_obj.start_pos
            if section not in self.document_annotations:
                self.document_annotations[section]   = {}
            if annotation_obj.section_offset not in self.document_annotations[section]:
                self.document_annotations[section][annotation_obj.section_offset] = {}
            self.document_annotations[section][annotation_obj.section_offset][spos] = annotation_obj


# CLASS 5: DOCUMENT SECTION
# STRUCTURE
#    --> SECTION_NAME
#           OFFSET: SECTION TXT
class DocumentSections:
    def __init__(self, sections, nlp):
        self.title               = None
        self.document_sections   = {}
        self.offset_section_name = {}
        self.spacy_sections      = {}
        self._add_document_sections(sections)
        self._spacy_sections_configuration(nlp)

    def _add_document_sections(self, sections):
        if type(sections) is str:
            self.document_sections["UNKNOWN"] = {0: sections}
            self.offset_section_name[0] = "UNKNOWN"
            return
        for section_name, section_info in sections.items():
            if section_name not in self.document_sections:
                self.document_sections[section_name]  = {}
            self.document_sections[section_name][section_info[1]] = section_info[0]
            self.offset_section_name[section_info[1]] = section_name
        elem_title = []
        for key in self.document_sections.keys():
            if "TITLE" not in key: continue
            elem_title = list(self.document_sections[key].values())
        self.title = "\n".join(elem_title)

    def _spacy_sections_configuration(self, nlp):
        for section_name, offset_subsection in self.document_sections.items():
            self.spacy_sections[section_name] = {
                offset: Section(offset, subsection, section_name, nlp)
                for offset, subsection in offset_subsection.items()
            }

    def add_annotation(self, annotations, global_annotations):
        sections_name = list(self.spacy_sections.keys())
        for section_name in sections_name:
            offset_section      = self.spacy_sections[section_name]
            offset_section_keys = list(offset_section.keys())
            for offset in offset_section_keys:
                section = offset_section[offset]
                section.add_annotation(annotations, global_annotations)
                if len(section.sentences) != 0: continue
                offset_section.pop(offset)
            if len(offset_section) != 0: continue
            self.spacy_sections.pop(section_name)

    def add_connections(self):
        for offset_section in self.spacy_sections.values():
            for section in offset_section.values():
                section.add_connection()


# ANNOTATOR CLASS
class Annotator:
    def __init__(self, pub, req_id):
        self.errors                = None
        self.global_annotations    = AnnotationGlobalMap()
        self.documents_annotations = {}
        self.documents_sections    = {}
        self.pub                   = pub
        self.req_id                = req_id
        self.utility               = UTS()

    async def document_creation(self, document, pmc_id, nlp, score):
        await self.utility.task_status_updating(Messages.DOC_SECT.format(id=pmc_id), score, self.req_id, self.pub)
        document_sect = DocumentSections(document[CON], nlp)
        self.documents_sections[pmc_id] = document_sect
        document_annot = DocumentAnnotations()
        await self.utility.task_status_updating(Messages.DIST_ANN.format(id=pmc_id), score, self.req_id, self.pub)
        document_annot.add_document_annotations(document[ANT], self.global_annotations, document_sect)
        self.documents_annotations[pmc_id] = document_annot
        document_sect.add_annotation(document_annot, self.global_annotations)
        await self.utility.task_status_updating(Messages.ACT_EXTR.format(id=pmc_id), score, self.req_id, self.pub)
        document_sect.add_connections()

    # SINGLE DOCUMENT ANNOTATION BY ID
    async def get_pmc_document_by_id(self, pmc_id, nlp):
        self.errors    = []
        print("SEND REQUEST TO ONTOTAGME")
        req = requests.post(UTS.URL_BY_ID_PMC, json={'a_id': pmc_id})
        if req.status_code != 200:
            self.errors.append(MESSAGE_0.format(error_code=str(req.status_code)))
            return None
        returned_json  = json.loads(req.content.decode('utf-8'))
        print("DOCUMENTS ANNOTATIONS ELABORATION")
        if ANT not in returned_json: self.errors.append(MESSAGE_1)
        await self.document_creation(returned_json, pmc_id, nlp, 0.0)

    async def documents_elaboration(self, returned_json, nlp):
        await self.utility.task_status_updating(Messages.DOC_ANNT, 0.3, self.req_id, self.pub)
        doc_size = len(returned_json)
        count = 0.0
        for document in returned_json:
            score = 0.3 * count / doc_size + 0.3
            await self.utility.task_status_updating(Messages.DOC_PROC.format(id=document['a_id']), score, self.req_id, self.pub)
            if not (FLD in document or ANT not in document):
                await self.document_creation(document, document['a_id'], nlp, score)
                count += 1
                continue
            await self.utility.task_status_updating(Messages.NO_ANNOT.format(id=document['a_id']), score, self.req_id, self.pub)
            count += 1

    # MULTIPLE DOCUMENTS ANNOTATIONS BY IDS
    async def get_pmc_documents_by_ids(self, pmc_list, nlp, req_id, mode):
        self.req_id = req_id
        self.errors = []
        await self.utility.task_status_updating(Messages.DOC_BYID, 0.0, self.req_id, self.pub)
        # POLLING
        OntoPolling(self.req_id)
        req     = requests.post(UTS.URL_BY_IDS, json={'idlist': ",".join(pmc_list), 'mode': mode, 'token': self.req_id})
        if req.status_code != 200:
            await self.utility.task_status_updating(Messages.PUB_ERRS.format(code=req.status_code), 1.0, self.req_id, self.pub)
            self.errors.append(MESSAGE_0.format(error_code=str(req.status_code)))
            return None
        returned_json = json.loads(req.content.decode('utf-8'))
        await self.documents_elaboration(returned_json, nlp)

    # FREE TEXT
    async def get_annotation_by_text(self, text, nlp):
        self.errors = []
        await self.utility.task_status_updating(Messages.CUST_TXT, 0.0, self.req_id, self.pub)
        await self.utility.task_status_updating(Messages.ONTO_REQ, 0.0, self.req_id, self.pub)
        req = requests.post(UTS.URL_BY_TEXT, json={'text': text})
        if req.status_code != 200:
            await self.utility.task_status_updating(Messages.ANN_ERRS, 1.0, self.req_id, self.pub)
            self.errors.append(MESSAGE_0.format(error_code=str(req.status_code)))
            return None
        returned_json = json.loads(req.content.decode('utf-8'))
        returned_json[CON] = returned_json.pop(QRY)
        returned_json[ANT] = returned_json[ANTU]
        await self.document_creation(returned_json, "freetext", nlp, 0.6)

    async def get_annotation_by_sections(self, req, nlp):
        if "fn_list" not in req or len(req["fn_list"]) <= 0: return None
        await self.utility.task_status_updating(Messages.DOC_PDF, 0.0, self.req_id, self.pub)
        documents        = []
        for file_name in req["fn_list"]:
            file_        = file_name.split("/")[-1]
            await self.utility.task_status_updating("Article parser: " + file_, 0.0, self.req_id, self.pub)
            document_pdf = PDFSearch(file_name)
            pages_comp   = {key: val[0] for key, val in document_pdf.pages_component['content'].items()}
            req          = requests.post(UTS.URL_BY_PDF, json={'article': pages_comp})
            if req.status_code != 200:
                await self.utility.task_status_updating(str(req.content), 0.0, self.req_id, self.pub)
                continue
            document    = json.loads(req.content)
            annotations = []
            for section_name, values in document["annotations"].items():
                for value in values:
                    value["section"  ]  = section_name
                    value["start_pos"] += document_pdf.pages_component['content'][section_name][1]
                    value["end_pos"  ] += document_pdf.pages_component['content'][section_name][1]
                    annotations.append(value)
            document_pdf.pages_component["annotations"] = annotations
            document_pdf.pages_component["mode"       ] = document["mode"]
            document_pdf.pages_component["a_id"       ] = file_
            documents.append(document_pdf.pages_component)
        await self.documents_elaboration(documents, nlp)
