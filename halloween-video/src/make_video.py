import os, pickle, subprocess, sys
from multiprocessing import Process
HERE = os.path.dirname(os.path.abspath(__file__))
NW = 4

def work(i, states):
    import render
    lo = len(states) * i // NW; hi = len(states) * (i + 1) // NW
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr0', '-s', '1080x1920',
                          '-r', '24', '-i', 'pipe:0', '-c:v', 'libx264', '-preset', 'fast', '-crf', '8',
                          '-pix_fmt', 'yuv420p', os.path.join(HERE, f'seg{i}.mp4')], stdin=subprocess.PIPE)
    # stop-motion: animate "on twos" (each pose held for two frames)
    data = None
    for k in range(lo, hi):
        if data is None or k % 2 == 0:
            surf = render.render(states[k - k % 2], None)
            surf.flush()
            data = bytes(surf.get_data())
        p.stdin.write(data)
        if (k - lo) % 200 == 0:
            print(f'w{i} {k - lo}/{hi - lo}', flush=True)
    p.stdin.close(); p.wait()

if __name__ == '__main__':
    states = pickle.load(open(os.path.join(HERE, 'states.pkl'), 'rb'))
    ps = [Process(target=work, args=(i, states)) for i in range(NW)]
    [p.start() for p in ps]; [p.join() for p in ps]
    with open(os.path.join(HERE, 'segs.txt'), 'w') as f:
        for i in range(NW):
            f.write(f"file 'seg{i}.mp4'\n")
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', os.path.join(HERE, 'segs.txt'),
                    '-c', 'copy', os.path.join(HERE, 'master.mp4')], check=True)
    print('master done')
