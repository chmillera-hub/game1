"""Render frames [a, b) to a lossless intermediate:  python3 render.py a b out.mkv"""
import subprocess
import sys
import numpy as np
import skia
import scenes
from timeline import FPS

a, b, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', '720x1280',
                       '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'ultrafast', '-qp', '0',
                       '-pix_fmt', 'yuv444p', out], stdin=subprocess.PIPE)
for i in range(a, b):
    img = scenes.render_frame(i / FPS)
    arr = img.toarray(colorType=skia.kBGRA_8888_ColorType)
    ff.stdin.write(arr.tobytes())
    if (i - a) % 240 == 0:
        print(f'[{a}-{b}] frame {i}', flush=True)
ff.stdin.close()
ff.wait()
