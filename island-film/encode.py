"""Final encodes.
Usage: python3 encode.py [--test [FRAMES]] [--render] [--skip-master]
  --test N : render frames 0..N (default 240) via render_all.sh, use build/dialogue.wav if build/mix.wav missing,
             write out/test_* files instead of the real outputs.
  --render : (full mode) run render_all.sh first.
Outputs: out/film_master.mp4 (subs burned, x264 crf16 slow, AAC 192k; SSIM reference),
         out/film_small_h264.mp4 (x264 2-pass veryslow tune animation), out/film_small_hevc.mp4 (x265 2-pass slow, hvc1),
         both sized for 14.3 MB total with AAC-LC 80k stereo; out/encode_report.txt (size + SSIM All vs master).
No fades: first output frame = first rendered frame."""
import json, os, subprocess, sys, time, re
ROOT = os.path.dirname(os.path.abspath(__file__)); os.chdir(ROOT)
args = sys.argv[1:]
TEST = '--test' in args
NFR = int(args[args.index('--test') + 1]) if TEST and len(args) > args.index('--test') + 1 and args[args.index('--test') + 1].isdigit() else 240
TL = json.load(open('build/timeline.json'))
pre = 'out/test_' if TEST else 'out/film_'
os.makedirs('out', exist_ok=True)
TARGET_MB, AUDIO_K = 14.3, 80

def run(cmd):
    print('$', ' '.join(cmd)[:200], flush=True); subprocess.run(cmd, check=True)

def dur(f):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f]))

t0 = time.time()
run(['python3', 'audio/subs.py'])
if TEST:
    run(['./render_all.sh', '0', str(NFR)])
elif '--render' in args:
    run(['./render_all.sh'])
audio = 'build/mix.wav' if os.path.exists('build/mix.wav') else 'build/dialogue.wav'
if not TEST and audio != 'build/mix.wav': print('WARNING: build/mix.wav missing, using dialogue.wav')
D = dur('build/video_raw.mkv')
master = pre + 'master.mp4'
if '--skip-master' not in args or not os.path.exists(master):
    run(['ffmpeg', '-y', '-loglevel', 'error', '-i', 'build/video_raw.mkv', '-i', audio, '-map', '0:v', '-map', '1:a',
         '-vf', 'ass=build/subs.ass', '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p',
         '-c:a', 'aac', '-b:a', '192k', '-t', f'{D:.3f}', '-movflags', '+faststart', master])

# video bitrate budget: total bits minus audio, minus ~1.5% container overhead
vk = int((TARGET_MB * 1e6 * 8 * 0.985 / D - AUDIO_K * 1000) / 1000)
print(f'duration {D:.2f}s -> video {vk} kb/s')
common_in = ['-i', master]
A = ['-c:a', 'aac', '-profile:a', 'aac_low', '-ac', '2', '-b:a', f'{AUDIO_K}k']
log = 'build/passlog'
cands = {
  'h264': (['-c:v', 'libx264', '-preset', 'veryslow', '-tune', 'animation', '-profile:v', 'high', '-pix_fmt', 'yuv420p',
            '-b:v', f'{vk}k', '-maxrate', f'{int(vk*2.5)}k', '-bufsize', f'{vk*5}k', '-passlogfile', log],
           lambda p: ['-pass', str(p)]),
  'hevc': (['-c:v', 'libx265', '-preset', 'slow', '-pix_fmt', 'yuv420p', '-tag:v', 'hvc1', '-b:v', f'{vk}k'],
           lambda p: ['-x265-params', f'pass={p}:stats={log}_x265.log:log-level=error']),
}
rep = [f'duration {D:.3f}s  frames {round(D*TL["fps"])}  audio {audio}  video target {vk} kb/s  audio {AUDIO_K} kb/s']
for name, (vopts, passopt) in cands.items():
    out = f'{pre}small_{name}.mp4'
    run(['ffmpeg', '-y', '-loglevel', 'error'] + common_in + ['-map', '0:v'] + vopts + passopt(1) + ['-an', '-f', 'mp4', '/dev/null'])
    run(['ffmpeg', '-y', '-loglevel', 'error'] + common_in + ['-map', '0:v', '-map', '0:a'] + vopts + passopt(2) + A +
        ['-movflags', '+faststart', out])
    r = subprocess.run(['ffmpeg', '-i', out, '-i', master, '-lavfi', '[0:v][1:v]ssim', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    m = re.search(r'All:([\d.]+) \(([\d.inf]+)\)', r)
    sz = os.path.getsize(out)
    line = f'{name}: {out}  {sz/1e6:.3f} MB  SSIM All {m.group(1) if m else "?"} ({m.group(2) if m else "?"} dB)  {"OK" if sz < 15e6 else "OVER 15MB"}'
    print(line); rep.append(line)
rep.append(f'master: {master} {os.path.getsize(master)/1e6:.2f} MB; total time {time.time()-t0:.0f}s')
open(pre + 'encode_report.txt' if TEST else 'out/encode_report.txt', 'w').write('\n'.join(rep) + '\n')
print('\n'.join(rep))
