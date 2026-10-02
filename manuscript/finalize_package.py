# -*- coding: utf-8 -*-
"""Produce the submission files after build_manuscript.py, build_si.py and build_cover_letter.py.

  1. TNCC_Cellulose_Manuscript_v5.docx = v3 build + the accepted parts of the third-party language edit
     (merge_language_edit.py; the edited file is kept in language_edit/ as provenance).
  2. American spelling in the Supporting Information and the cover letter, so the three documents agree.
     Reference titles (the 'Reference' table of the SI) are left exactly as in the verified records.

    python finalize_package.py
"""
import os
import sys

import docx
from docx.oxml.ns import qn

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import merge_language_edit as M  # noqa: E402


def us_file(path, protect_tables=("Reference",)):
    d = docx.Document(path)
    protected = set()
    for t in d.tables:
        if t.rows and t.rows[0].cells and t.rows[0].cells[0].text.strip() in protect_tables:
            protected.update(t._tbl.iter(qn("w:p")))
    n = 0
    for p in d.element.body.iter(qn("w:p")):
        if p in protected:
            continue
        before = M.ptext(p)
        M.us_paragraph(p)
        n += before != M.ptext(p)
    d.save(path)
    return n


if __name__ == "__main__":
    M.main(os.path.join(HERE, "TNCC_Cellulose_Manuscript_v3.docx"),
           os.path.join(HERE, "language_edit", "TNCC_Cellulose_Manuscript_v4_language_edit.docx"),
           os.path.join(HERE, "TNCC_Cellulose_Manuscript_v5.docx"))
    for f in ("TNCC_Supplementary_Information.docx", "TNCC_Cover_Letter_Cellulose.docx"):
        print(f, "paragraphs respelled:", us_file(os.path.join(HERE, f)))
