# -*- coding: utf-8 -*-
"""Escape bare '%' inside strings used with the % operator (one-off helper).

AST column offsets count UTF-8 BYTES, not characters, so all offset arithmetic is done on the
encoded source. (An earlier version mixed the two and corrupted files containing non-ASCII text.)
The file is parsed BEFORE it is overwritten, so a failed fix leaves the original untouched.
"""
import ast
import io
import re
import sys

path = sys.argv[1]
src = io.open(path, encoding="utf-8").read()
raw = src.encode("utf-8")
tree = ast.parse(src)
line_start = [0]
for ln in raw.split(b"\n"):
    line_start.append(line_start[-1] + len(ln) + 1)

spans = []
for node in ast.walk(tree):
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
        L = node.left
        if isinstance(L, ast.Constant) and isinstance(L.value, str):
            spans.append((line_start[L.lineno - 1] + L.col_offset, line_start[L.end_lineno - 1] + L.end_col_offset))

SPEC = re.compile(rb"%%|%[+\-0 #]*\d*(?:\.\d+)?[sdfgrxXeEc]")
fixed = 0
for a, b in sorted(spans, reverse=True):
    seg, out, i = raw[a:b], [], 0
    while i < len(seg):
        if seg[i:i + 1] == b"%":
            mo = SPEC.match(seg, i)
            if mo:
                out.append(mo.group(0))
                i = mo.end()
            else:
                out.append(b"%%")
                i += 1
                fixed += 1
        else:
            out.append(seg[i:i + 1])
            i += 1
    raw = raw[:a] + b"".join(out) + raw[b:]

new_src = raw.decode("utf-8")
ast.parse(new_src)                                  # verify before writing
io.open(path, "w", encoding="utf-8").write(new_src)
print("escaped %d bare percent signs in %d %%-formatted strings; file parses" % (fixed, len(spans)))
