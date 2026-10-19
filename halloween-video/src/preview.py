import pickle, sys, time
from PIL import Image
import render
states = pickle.load(open('states.pkl','rb'))
ts = [float(x) for x in sys.argv[2:]]
out = sys.argv[1]
ims=[]
for t in ts:
    st = states[min(int(t*24), len(states)-1)]
    t0=time.time(); s = render.render(st); dt=time.time()-t0
    s.write_to_png('/tmp/_p.png'); ims.append(Image.open('/tmp/_p.png').convert('RGB').resize((360,640)))
    print(t, f'{dt*1000:.0f}ms', st['scene'], st['cam'][2], st['sub'][1][:40] if st['sub'] else '')
cols=min(len(ims),5); rows=(len(ims)+cols-1)//cols
sheet=Image.new('RGB',(cols*360,rows*640))
for i,im in enumerate(ims): sheet.paste(im,((i%cols)*360,(i//cols)*640))
sheet.save(out)
