# -*- coding: utf-8 -*-
from docx import Document
import re

p = r'C:\Users\HP\Desktop\重复使用运载器健康管理原型系统测试大纲.docx'
d = Document(p)
for i, t in enumerate(d.tables):
    s = ' '.join(c.text for row in t.rows for c in row.cells)
    m = re.search(r'(JKGLYXXT-[A-Z0-9-]+|FF-[A-Z0-9-]+|JCYJ-[A-Z0-9-]+|ZL-[0-9]+)', s)
    if m:
        print(i, m.group(1), len(t.rows), s[:120])
        if 7 <= i <= 59:
            for row in t.rows:
                vals = [c.text.replace('\n', ' ') for c in row.cells]
                if vals and any(k in vals[0] for k in ('测试目的','前提和约束','测试用例通过准则','输入及操作步骤','预期测试结果','备')):
                    print('  ', repr(vals))
