from PIL import Image,ImageDraw
from pathlib import Path
files=sorted(Path('qa_manual_render_v2').glob('page-*.png'),key=lambda p:int(p.stem.split('-')[1]))
thumbs=[]
for p in files:
 im=Image.open(p).convert('RGB'); im.thumbnail((260,340)); c=Image.new('RGB',(280,370),'white'); c.paste(im,((280-im.width)//2,5)); ImageDraw.Draw(c).text((8,348),p.name,fill='black'); thumbs.append(c)
cols=4; rows=(len(thumbs)+cols-1)//cols; out=Image.new('RGB',(cols*280,rows*370),(220,225,230))
for i,c in enumerate(thumbs):out.paste(c,((i%cols)*280,(i//cols)*370))
out.save('qa_manual_render_v2/contact.png'); print(len(files))
