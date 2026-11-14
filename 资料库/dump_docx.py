# -*- coding: utf-8 -*-
import sys
from docx import Document
for fp in sys.argv[1:]:
    print('\n\n========== FILE:', fp, '==========')
    d = Document(fp)
    for p in d.paragraphs:
        t = p.text.strip()
        if t:
            print('['+ (p.style.name or '') +'] ' + t)
