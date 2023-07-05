from pdfminer.converter   import PDFPageAggregator
from pdfminer.layout      import LAParams, LTTextBox, LTTextLine
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp   import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage     import PDFPage
from pdfminer.pdfparser   import PDFParser


# CLASS FOR PDF ELABORATION
class PDFSearch:
    def __init__(self, file):
        self.document        = None
        self.interpreter     = None
        self.device          = None
        self.pages_component = {}
        self.pdfParsing(file)

    @staticmethod
    def createPDFDoc(fpath):
        fp           = open(fpath, 'rb')
        parser       = PDFParser(fp)
        document_pdf = PDFDocument(parser, password='')
        if not document_pdf.is_extractable: raise "Not extractable"
        else: return document_pdf

    @staticmethod
    def createDeviceInterpreter():
        rsrcmgr    = PDFResourceManager()
        laparams   = LAParams()
        device_prs = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpr    = PDFPageInterpreter(rsrcmgr, device_prs)
        return device_prs, interpr

    @staticmethod
    def sposWidthFontsize(sel_bloc, bloc_i):
        return (
            sel_bloc[0] <= bloc_i[0] and
            -10  + sel_bloc[1] <= bloc_i[1] <=  10 + sel_bloc[1] and
            -0.9 + sel_bloc[2] <= bloc_i[2] <= 0.9 + sel_bloc[2]
        )

    @staticmethod
    def widthFontsize(sel_bloc, bloc_i):
        return (
            -10  + sel_bloc[1] <= bloc_i[1] <=  10 + sel_bloc[1] and
            -0.9 + sel_bloc[2] <= bloc_i[2] <= 0.9 + sel_bloc[2]
        )

    @staticmethod
    def mergeTextParts(sel_blocs, sel_bloc, operator):
        for bloc_i in sel_blocs:
            if not operator(sel_bloc, bloc_i): continue
            if   sel_bloc[3][-1] == "-": bloc_i[3] = sel_bloc[3][:-1]  + bloc_i[3]
            elif sel_bloc[3][-1] == " ": bloc_i[3] = sel_bloc[3]       + bloc_i[3]
            else:                        bloc_i[3] = sel_bloc[3] + " " + bloc_i[3]
            return True
        return False

    # ============================================================================
    # THIS FUNCTION CONSIDER EACH BLOC ROW. THE ROWS ARE PUT INTO DIFFERENT      #
    # LINES IF THE LAST ELEMENT OF FIRST ROW IS A POINT;                         #
    # OTHERWISE THE TWO ROWS ARE CONCATENATE BY A SPACE, OR NOTHING IF THE       #
    # LAST ELEMENT IS -                                                          #
    # ============================================================================
    @staticmethod
    def blocElaboration(bloc, width_thr, width_page, page_struct):
        # IF BLOC NOT A LTTEXTBOX, RETURN
        if not isinstance(bloc, LTTextBox):           return False
        # IF REFERENCES IS THE CONSIDERED ELEMENT, RETURN
        if "references\n" == bloc.get_text().lower(): return True
        # IF BLOC HAVING WIDTH LESS THAN THR, RETURN
        if bloc.width < width_thr:                    return False
        finale_text = []
        text_font_size   = 0
        for line in bloc:
            if not isinstance(line, LTTextLine): continue
            text_font_size = round(line.height, 2)
            text           = line.get_text().replace("\n", "").replace("- ", "-")
            if text[-2:] == ". ": text = text[:-1]
            if len(finale_text) == 0: finale_text.append(text)
            else:
                last_text = finale_text[-1]
                if   "." in last_text[-1:] and text[0].isupper(): finale_text.append(text)
                elif "-" in last_text[-1] : finale_text[-1] = last_text[:-1]       + text
                elif last_text[-1]  == " ": finale_text[-1] = last_text            + text
                else:                       finale_text[-1] = last_text      + " " + text
        page_element_conf = [round(bloc.x0, 2), round(bloc.width, 2), text_font_size, "\n".join(finale_text), bloc.index]
        page_struct["left" if page_element_conf[0] < width_page else "right"].append(page_element_conf)
        return False

    # =====================================================================================
    # SEVERAL PAPERS ARE COMPOSED OF TWO COLUMNS, SO WE NEED TO CONCATENATE THE LAST BLOC #
    # OF THE LEFT COLUMN WITH THE FIRST BLOC OF THE SECOND ONE WHEN THE LAST CHARACTER OF #
    # THE LEFT COLUMN IS NOT A POINT.                                                     #
    # =====================================================================================
    def pageBlocsJoining(self, page_struct, pages_components, page_id):
        components = ["left", "right"]
        for id_v, component in enumerate(components):
            blocs = page_struct[component]
            while len(blocs) != 0:
                bloc_0 = blocs.pop(0)
                if bloc_0[3][-1] == ".":
                    pages_components[page_id].append(bloc_0)
                    continue
                is_matched = self.mergeTextParts(blocs, bloc_0, self.sposWidthFontsize)
                if is_matched: continue
                if id_v < 1:
                    other_blocs = page_struct[components[id_v + 1]]
                    is_matched  = self.mergeTextParts(other_blocs, bloc_0, self.sposWidthFontsize)
                    if is_matched: continue
                pages_components[page_id].append(bloc_0)

    # PAGE ELABORATION MAIN FUNCTION
    def pageElaboration(self, page, pages_components, page_id):
        self.interpreter.process_page(page)
        width_page  = page.attrs["CropBox"][2] / 2
        width_thr   = page.attrs["CropBox"][2] / 3
        page_struct = {"left": [], "right": []}
        isReference = False
        for bloc in self.device.get_result()._objs:
            isReference = self.blocElaboration(bloc, width_thr, width_page, page_struct)
        if isReference: return isReference
        # WE TRY TO MERGE THE SECTIONS THAT ARE SPLIT INTO TWO COLUMN
        # page_struct["left" ].sort(key=lambda x: x[3])
        # page_struct["right"].sort(key=lambda x: x[3])
        self.pageBlocsJoining(page_struct, pages_components, page_id)
        return isReference

    # MAIN PARSING FUNCTION
    def pdfParsing(self, file):
        document                      = self.createPDFDoc(file)
        self.device, self.interpreter = self.createDeviceInterpreter()
        pages                         = PDFPage.create_pages(document)
        for page_id, page in enumerate(pages):
            self.pages_component[page_id] = []
            isReference = self.pageElaboration(page, self.pages_component, page_id)
            if isReference: break
        len_pg = len(self.pages_component) - 1
        for page_id, page in self.pages_component.items():
            if page_id == len_pg: continue
            sel_tuple = page[-1]
            if "fig" in sel_tuple[3][:3].lower() or "." in sel_tuple[3][-2:]: continue
            pone      = page_id + 1
            page_pone = self.pages_component[pone]
            result    = self.mergeTextParts(page_pone, sel_tuple, self.widthFontsize)
            if result: del page[-1]
        counter = 0
        offset  = 0
        page_component_final = {}
        for page_id, page in self.pages_component.items():
            for tuple_ in page:
                page_component_final["SECTION_{i}".format(i = counter)] = [tuple_[3], offset]
                offset      += len(tuple_[3]) - 1
                counter     += 1
        self.pages_component = {"content": page_component_final}
