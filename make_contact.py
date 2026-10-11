from PIL import Image,ImageOps,ImageDraw
from pathlib import Path
files=sorted(Path('docs/manual_20261010/screenshots').glob('*.png'))
thumbs=[]
for p in files:
 im=Image.open(p).convert('RGB'); im.thumbnail((320,210)); canvas=Image.new('RGB',(340,250),'white'); canvas.paste(im,((340-im.width)//2,10)); ImageDraw.Draw(canvas).text((8,225),p.stem,fill='black'); thumbs.append(canvas)
cols=3; rows=(len(thumbs)+cols-1)//cols
out=Image.new('RGB',(cols*340,rows*250),(230,235,240))
for i,im in enumerate(thumbs):out.paste(im,((i%cols)*340,(i//cols)*250))
out.save('docs/manual_20261010/screenshots/contact.png')
print(len(files))
