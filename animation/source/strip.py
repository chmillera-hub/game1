import sys,subprocess
from PIL import Image
starts=[int(x) for x in open('strips.txt').read().split()]
rows=[]
for st in starts:
    fr=[st+2*i for i in range(8)]
    subprocess.run(['node','render.js','0','0','test/s.png',*map(str,fr)],check=True)
    rows.append([Image.open(f'test/s_{f}.png').convert('RGB') for f in fr])
out=Image.new('RGB',(8*180,len(rows)*320))
for r,row in enumerate(rows):
    for c,im in enumerate(row): out.paste(im.resize((180,320)),(c*180,r*320))
out.save('test/strips.png')
