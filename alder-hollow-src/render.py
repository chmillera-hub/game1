import sys, subprocess, os
from scenes import *
N = int(TOTAL * FPS)
def work(a, b, out):
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-crf', '17', '-preset', 'medium', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for n in range(a, b):
        im, _ = frame(n)
        p.stdin.write(im.tobytes())
    p.stdin.close(); p.wait()
if __name__ == '__main__':
    a, b, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    work(a, b, out)
