from dataclasses import dataclass

import pymupdf


@dataclass
class PdfPage:
    number: int
    text: str


def extract_pages(pdf_bytes: bytes) -> list[PdfPage]:
    document = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    pages: list[PdfPage] = []
    try:
        for index, page in enumerate(document, start=1):
            text = page.get_text("text") or ""
            cleaned = "\n".join(line.strip() for line in text.splitlines()).strip()
            if cleaned:
                pages.append(PdfPage(number=index, text=cleaned))
    finally:
        document.close()
    return pages
