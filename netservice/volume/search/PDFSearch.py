import logging
import fitz
from   search.Search import Search


# LOGGING CREATION
logging.basicConfig(filename="files/netme.log", level=logging.DEBUG)


class PDFSearch(Search):
    def search(self, post, api_key):
        if "fn_list" not in post or len(post["fn_list"]) <= 0: return
        for fn in post["fn_list"]:
            rfn = f'pdf|{"_".join(fn.split("_")[1:])}'
            self.articles[rfn] = self.parse_pdf(fn)
            self.articles_id.append(rfn)

    def get_article(self, article_id):
        return self.articles[article_id]

    @staticmethod
    def parse_pdf(fn):
        try:
            article = ""
            doc = fitz.open(fn)
            page_count = doc.pageCount

            # PAGE CREATIONS
            pages_blocks = dict()
            duplicate_blk = dict()
            logging.info("PDF READING IS RUNNING")
            for page in range(0, page_count):
                page_i = doc.loadPage(page)
                for block in page_i.getText("blocks"):
                    block_coords = block[0:4]
                    if block_coords not in pages_blocks:
                        pages_blocks[block_coords] = dict()
                        pages_blocks[block_coords][page] = block[4:6]
                    else:
                        if block_coords not in duplicate_blk:
                            duplicate_blk[block_coords] = {
                                "count": 0,
                                "testo": block[4:6],
                            }
                        duplicate_blk[block_coords]["count"] += 1

            logging.info("\t REMOVE DUPLICATE BLOCK")
            for key in duplicate_blk:
                if duplicate_blk[key]["count"] <= 2: continue
                pages_blocks.pop(key)

            logging.info("\t CREATE PDF FINAL TEXT")
            for block in pages_blocks:
                for text in pages_blocks[block]:
                    article += (
                            pages_blocks[block][text][0].replace("\n", " ").strip().replace("  ", " ") + ". "
                    )
            return article
        except Exception as e:
            logging.error("QUEUE" + "Error in parse_pdf: " + str(e))
            return ""
