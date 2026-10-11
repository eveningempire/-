from pathlib import Path
p=Path('build_manual.py')
s=p.read_text(encoding='utf-8')
s=s.replace(')\\nfigure', ')\nfigure').replace(')\\nh(', ')\nh(')
p.write_text(s,encoding='utf-8')
