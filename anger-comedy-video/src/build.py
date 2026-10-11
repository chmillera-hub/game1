"""Build the whole video: voices -> mix -> frames -> compressed portrait MP4.

usage: python3 build.py [out.mp4] [--target-mb 13.5]
"""
import json
import os
import subprocess
import sys
import time

from common import BUILD, FPS, W, H, ROOT

HERE = os.path.dirname(os.path.abspath(__file__))


def run(cmd, **kw):
    print('+', ' '.join(cmd) if isinstance(cmd, list) else cmd, flush=True)
    return subprocess.run(cmd, check=True, **kw)


def probe_duration(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', path],
                         capture_output=True, text=True, check=True).stdout
    return float(json.loads(out)['format']['duration'])


def main():
    args = sys.argv[1:]
    out = os.path.join(ROOT, 'anger_goes_to_a_comedy_show.mp4')
    target_mb = 13.5
    workers = os.cpu_count() or 4
    i = 0
    while i < len(args):
        if args[i] == '--target-mb':
            target_mb = float(args[i + 1]); i += 2
        elif args[i] == '--workers':
            workers = int(args[i + 1]); i += 2
        else:
            out = args[i]; i += 1

    t_start = time.time()
    from screenplay import build
    import music
    tl = build()
    total = tl.end
    nframes = int(round(total * FPS))
    print(f'timeline {total:.2f}s, {nframes} frames, {len(tl.lines)} lines', flush=True)

    # ---- audio
    mix_wav = os.path.join(BUILD, 'mix.wav')
    music.mix(tl, mix_wav)
    print('mixed audio', flush=True)

    # ---- frames (parallel chunks, near-lossless intermediates)
    chunk_dir = os.path.join(BUILD, 'chunks')
    os.makedirs(chunk_dir, exist_ok=True)
    per = (nframes + workers - 1) // workers
    procs = []
    parts = []
    for k in range(workers):
        f0, f1 = k * per, min(nframes, (k + 1) * per)
        if f0 >= f1:
            continue
        p = os.path.join(chunk_dir, f'part{k:02d}.mp4')
        parts.append(p)
        procs.append(subprocess.Popen([sys.executable, os.path.join(HERE, 'render.py'), 'chunk', str(f0), str(f1), p],
                                      cwd=HERE))
    for pr in procs:
        if pr.wait() != 0:
            raise SystemExit('render worker failed')
    print(f'rendered frames in {time.time() - t_start:.0f}s', flush=True)
    lst = os.path.join(chunk_dir, 'list.txt')
    with open(lst, 'w') as f:
        for p in parts:
            f.write(f"file '{p}'\n")
    hq = os.path.join(BUILD, 'video_hq.mp4')
    run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', hq])

    # ---- audio: loudness normalise (two-pass) -> AAC mono
    meas = subprocess.run(['ffmpeg', '-hide_banner', '-i', mix_wav, '-af',
                           'loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'],
                          capture_output=True, text=True).stderr
    js = json.loads(meas[meas.rindex('{'):meas.rindex('}') + 1])
    ln = (f"loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
          f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    a_kbps = 64
    aac = os.path.join(BUILD, 'audio.m4a')
    run(['ffmpeg', '-v', 'error', '-y', '-i', mix_wav, '-af', ln + ',aresample=48000', '-ac', '1',
         '-c:a', 'aac', '-b:a', f'{a_kbps}k', aac])

    # ---- video: two-pass x264 sized to the budget
    dur = total
    budget_kbits = target_mb * 8 * 1000 * 0.985          # MB -> kbit, minus container overhead
    v_kbps = int(budget_kbits / dur - a_kbps)
    print(f'video bitrate target {v_kbps} kbps', flush=True)
    x264 = ['-c:v', 'libx264', '-preset', 'veryslow', '-tune', 'animation', '-profile:v', 'high',
            '-pix_fmt', 'yuv420p', '-b:v', f'{v_kbps}k', '-maxrate', f'{int(v_kbps * 2.2)}k',
            '-bufsize', f'{int(v_kbps * 4)}k', '-g', str(FPS * 6), '-x264-params', 'aq-mode=3:aq-strength=0.9']
    log = os.path.join(BUILD, 'x264pass')
    run(['ffmpeg', '-v', 'error', '-y', '-i', hq] + x264 + ['-pass', '1', '-passlogfile', log, '-an', '-f', 'mp4', os.devnull])
    vid = os.path.join(BUILD, 'video_final.mp4')
    run(['ffmpeg', '-v', 'error', '-y', '-i', hq] + x264 + ['-pass', '2', '-passlogfile', log, '-an', vid])
    run(['ffmpeg', '-v', 'error', '-y', '-i', vid, '-i', aac, '-c', 'copy', '-map', '0:v:0', '-map', '1:a:0',
         '-movflags', '+faststart', '-shortest', out])
    size = os.path.getsize(out) / 1e6
    print(f'DONE {out}: {size:.2f} MB, {probe_duration(out):.2f}s, total build {time.time() - t_start:.0f}s')


if __name__ == '__main__':
    main()
