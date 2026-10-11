# -*- coding: utf-8 -*-
from docx import Document

p = r'C:\Users\HP\Desktop\重复使用运载器健康管理原型系统测试大纲.docx'
d = Document(p)
ids = ['FF-FTA-01','FF-DIAG-01','FF-DIAG-02','FF-DIAG-03','FF-DIAG-04','FF-LIFE-01','FF-HEALTH-01','FF-HEALTH-02','FF-HEALTH-03','FF-SIM-01','FF-EXT-01','FF-EXT-02','FF-EXT-03','FF-EDGE-01','JKGLYXXT-GN-08-01','JKGLYXXT-XN-01','JKGLYXXT-XN-02','ZL-05','JKGLYXXT-QT-03','JKGLYXXT-QT-04']
for t in d.tables:
    flat = ' '.join(c.text for row in t.rows for c in row.cells)
    hit = next((x for x in ids if x in flat), None)
    if not hit:
        continue
    print('\n###', hit)
    for row in t.rows:
        vals = []
        for c in row.cells:
            tx = ' '.join(c.text.split())
            if not vals or tx != vals[-1]:
                vals.append(tx)
        if vals:
            print(' | '.join(vals))
