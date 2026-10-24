import sys
from PIL import Image
fs=sys.argv[2:]; out=sys.argv[1]
ims=[Image.open(f).resize((360,640)) for f in fs]
cols=min(5,len(ims)); rows=(len(ims)+cols-1)//cols
sh=Image.new('RGB',(cols*360,rows*640),'white')
for i,im in enumerate(ims): sh.paste(im,((i%cols)*360,(i//cols)*640))
sh.save(out)
