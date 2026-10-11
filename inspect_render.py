from PIL import Image
from pathlib import Path
for p in sorted(Path('qa_manual_render_v1').glob('page-*.png')):
 im=Image.open(p); print(p.name, im.size)
