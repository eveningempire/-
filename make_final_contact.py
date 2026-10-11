from PIL import Image,ImageDraw
from pathlib import Path
files=sorted(Path('qa_manual_render_final').glob('page-*.png'),key=lambda p:int(p.stem.split('-')[1])); print('pages',len(files))
thumbs=[]
for p in files:
 im=Image.open(p).convert('RGB'); im.thumbnail((240,320)); c=Image.new('RGB',(260,350),'white'); c.paste(im,((260-im.width)//2,4)); ImageDraw.Draw(c).text((7,329),p.name,fill='black'); thumbs.append(c)
cols=5; rows=(len(thumbs)+cols-1)//cols; out=Image.new('RGB',(cols*260,rows*350),(220,225,230))
for i,c in enumerate(thumbs):out.paste(c,((i%cols)*260,(i//cols)*350))
out.save('qa_manual_render_final/contact.png')
