# -*- coding: utf-8 -*-
"""Merge a third-party language edit into the manuscript without letting it change the science.

The language edit (TNCC_Cellulose_Manuscript_v4, run through an editing service) is accepted paragraph by
paragraph. A paragraph of the edit is accepted only if, once spelling is made American and function words and
punctuation are ignored, it contains exactly the same content words, the same numbers and symbols, the same
equation text, the same count of sub/superscript runs and the same dash characters as the source paragraph
(build_manuscript.py output). Otherwise the source paragraph is kept, with American spelling. Reference
entries are never accepted from the edit, because their titles are verified Crossref records.

    python merge_language_edit.py <source_v3.docx> <edited_v4.docx> <out_v5.docx>

A report of every rejected paragraph and the reason is written next to the output.
"""
import copy
import io
import re
import sys

import docx
from docx.oxml.ns import qn

US = [
    (r"nanofibre", "nanofiber"), (r"microfibre", "microfiber"), (r"fibre", "fiber"), (r"moulded", "molded"),
    (r"moulding", "molding"), (r"mould", "mold"), (r"oxidised", "oxidized"), (r"organised", "organized"),
    (r"organise", "organize"), (r"recognised", "recognized"), (r"micrometre", "micrometer"), (r"nanometre", "nanometer"),
    (r"colour", "color"), (r"favourable", "favorable"), (r"centred", "centered"), (r"centre", "center"),
    (r"analogue", "analog"), (r"unpolarised", "unpolarized"), (r"polarisation", "polarization"),
    (r"microfluidisation", "microfluidization"), (r"microfluidised", "microfluidized"), (r"hydrophobisation", "hydrophobization"), (r"optimised", "optimized"),
    (r"summarised", "summarized"), (r"analysed", "analyzed"), (r"programme", "program"), (r"licence", "license"),
    (r"grey", "gray"), (r"characterised", "characterized"), (r"modelled", "modeled"), (r"modelling", "modeling"),
    (r"towards", "toward"), (r"multi-stage", "multistage"), (r"non-equivalent", "nonequivalent"), (r"non-financial", "nonfinancial"), (r"micro-sized", "microsized"), (r"bio-based", "biobased"), (r"sub-micron", "submicron"), (r"vapour", "vapor"), (r"behaviour", "behavior"),
    (r"normalised", "normalized"), (r"minimise", "minimize"), (r"visualise", "visualize"), (r"utilise", "utilize"),
    (r"emphasise", "emphasize"), (r"labelled", "labeled"), (r"catalogue", "catalog"), (r"whilst", "while"),
]
_US = [(re.compile(a, re.I), b) for a, b in US]


def americanize(s):
    def fix(pat, rep, text):
        def r(m):
            w = m.group(0)
            if w.isupper() and len(w) > 1:
                return rep.upper()
            if w[0].isupper():
                return rep[0].upper() + rep[1:]
            return rep
        return pat.sub(r, text)
    for pat, rep in _US:
        s = fix(pat, rep, s)
    return s


STOP = set("the a an of is are was were be been being in on at that which and respectively as to for by with from it its their this these "
           "those into has have had can could would will may also".split())
SYN = {"raises": "increase", "raise": "increase", "rises": "increase", "rise": "increase", "increases": "increase",
       "increased": "increase", "about": "approximately", "falls": "decrease", "fall": "decrease", "decreases": "decrease",
       "so": "thus", "gives": "give", "gave": "give", "sets": "set", "lowers": "decrease", "decide": "determine",
       "decides": "determine", "regardless": "whatever", "whatever": "whatever"}
DASHES = "‐‑‒–—―−"


# Paragraphs whose edit changes content words but was reviewed by hand and found to preserve the meaning.
ACCEPT_REVIEWED = [
    'Densifying nanofibrils removes that scatteri',
    'The feedstock evidence is mixed in a way tha',
    'A submicron natural wax layer is proposed. I',
    'Table 1 sets out the published evidence and ',
    'Negative / absent',
    'Light scattered by a dense nanofibril networ',
    'where Δε = nc2 − 1 is the permittivity contr',
    'Because strain is never perfectly uniform, t',
    'How well does the screen reproduce published',
    'The screen can be compared with the one publ',
    'Fig. 3 Wet-stiffness screen. a Water-saturat',
    'Among the unknowns, the wrinkling tolerance ',
    'Consequences for the optical budget. The coa',
    'Fig. 7 Robustness to the prior distributions',
    'Scope of the forming result. The cup result ',
    'P3 (bagasse threshold). A dense bagasse nano',
    'The forming screen bounds mean area strain a',
    'Data availability No experimental data were ',
]


# Paragraphs where the edit passes the automatic check but a hand review found the meaning or grammar changed
# (for example "changes the optical budget" became "changes in the optical budget"; "is unvalidated" became "was unvalidated").
REJECT_REVIEWED = [
    "What the combination adds.", "H2 (chitosan).", "The feedstock evidence is mixed", "The 19 parameters of the screens",
    "The constituents (cellulose, chitosan", "Food-contact regulatory status",
]


def tokens(text):
    t = americanize(text).lower()
    t = re.sub("[%s]" % DASHES, "-", t).replace("’", "'")
    words = re.findall(r"[a-z0-9µμα-ωΔΦ°%≤≥<>=±+]+(?:[.\-/'][a-z0-9µμα-ω]+)*|[≤≥<>=±]", t)
    out = []
    flat = []
    for w in words:
        flat += [x for x in w.split("-") if x]
    words = flat
    for i, w in enumerate(words):
        if w == "a":
            nxt = words[i + 1] if i + 1 < len(words) else ""
            if re.fullmatch(r"[a-z]{3,}", nxt) and nxt != "nm":
                continue                     # article
            out.append("VAR_a")             # the symbol a (correlation length)
            continue
        if w in STOP:
            continue
        w = SYN.get(w, w)
        if len(w) > 4 and w.endswith("s") and not w.endswith("ss") and not any(c.isdigit() for c in w):
            w = w[:-1]
        out.append(w)
    return out


def dash_count(text):
    return sum(text.count(c) for c in DASHES), text.count("?")


def sig(p):
    """(subscript runs, superscript runs, bold runs, italic runs, math text)"""
    sub = sup = b = i = 0
    for r in p.iterfind(".//" + qn("w:r")):
        rpr = r.find(qn("w:rPr"))
        if rpr is None or r.find(qn("w:t")) is None:
            continue
        va = rpr.find(qn("w:vertAlign"))
        if va is not None:
            sub += va.get(qn("w:val")) == "subscript"
            sup += va.get(qn("w:val")) == "superscript"
        bb, ii = rpr.find(qn("w:b")), rpr.find(qn("w:i"))
        b += bb is not None and bb.get(qn("w:val")) not in ("0", "false")
        i += ii is not None and ii.get(qn("w:val")) not in ("0", "false")
    math = "".join(t.text or "" for t in p.iter("{http://schemas.openxmlformats.org/officeDocument/2006/math}t"))
    return sub, sup, b > 0, i > 0, math


def ptext(p):
    return "".join(t.text or "" for t in p.iter(qn("w:t")))


def us_paragraph(p):
    for t in p.iter(qn("w:t")):
        if t.text:
            t.text = americanize(t.text)


def main(src_path, edit_path, out_path):
    src = docx.Document(src_path)
    edit = docx.Document(edit_path)
    sp = list(src.element.body.iter(qn("w:p")))
    ep = list(edit.element.body.iter(qn("w:p")))
    assert len(sp) == len(ep), "paragraph counts differ: %d vs %d" % (len(sp), len(ep))
    in_refs = False
    report, accepted, rejected, same = [], 0, 0, 0
    for i, (a, b) in enumerate(zip(sp, ep)):
        ta, tb = ptext(a), ptext(b)
        if ta.strip() == "References":
            in_refs = True
        if ta == tb:
            same += 1
            continue
        reason = None
        if in_refs and ta != "References":
            reason = "reference entry (verified record)"
        elif any(ta.startswith(p) or americanize(ta).startswith(p) for p in REJECT_REVIEWED):
            reason = "hand review: edit changes tense or meaning"
        elif tokens(ta) != tokens(tb) and not any(americanize(ta).startswith(p) for p in ACCEPT_REVIEWED):
            ca, cb = tokens(ta), tokens(tb)
            diff = [x for x in ca if x not in cb] + ["+" + x for x in cb if x not in ca]
            reason = "content words differ: %s" % " ".join(diff[:10])
        elif dash_count(americanize(ta)) != dash_count(tb):
            reason = "dash or question-mark change"
        elif sig(a)[:2] != sig(b)[:2] or sig(a)[4] != sig(b)[4]:
            reason = "sub/superscript or equation text differs"
        if reason:
            new = copy.deepcopy(a)
            if not in_refs:
                us_paragraph(new)               # reference titles stay exactly as in the verified records
            b.getparent().replace(b, new)
            rejected += 1
            report.append("#%d REJECT (%s)\n    kept : %s\n    edit : %s" % (i, reason, americanize(ta)[:230], tb[:230]))
        else:
            accepted += 1
    edit.core_properties.author = src.core_properties.author
    edit.core_properties.last_modified_by = ""
    edit.save(out_path)
    with io.open(out_path.replace(".docx", "_merge_report.txt"), "w", encoding="utf-8") as f:
        f.write("identical paragraphs: %d\naccepted from the language edit: %d\nrejected (source kept, American spelling): %d\n\n"
                % (same, accepted, rejected))
        f.write("\n\n".join(report))
    print("identical %d | accepted %d | rejected %d" % (same, accepted, rejected))


if __name__ == "__main__":
    main(*sys.argv[1:4])
