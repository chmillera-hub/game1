"""Join the rendered segments with the mix into the final phone-portrait MP4,
and write the subtitles as an .srt too (handy for platforms with caption upload).

    python encode.py [target_mb]     # default 14.2 MB, two-pass H.264 sized to fit
    python encode.py --check         # SSIM / PSNR of alice.mp4 against the lossless render
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, 'build')
OUT = os.path.join(HERE, 'alice.mp4')
FPS = 24      # the segments' mkv timestamps are rounded to ms; re-clock them exactly


def srt_time(t):
    ms = int(round(t * 1000))
    return f'{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}'


def write_srt():
    tl = json.load(open(os.path.join(BUILD, 'timeline.json')))
    names = {'N': '', 'A': 'ALICE: ', 'S': 'SIMMER: '}
    with open(os.path.join(HERE, 'alice.srt'), 'w') as fh:
        for i, (s0, s1, spk, text) in enumerate(tl['subs'], 1):
            fh.write(f'{i}\n{srt_time(s0)} --> {srt_time(s1)}\n{names[spk]}{text}\n\n')


def loudnorm():
    """Two-pass, linear EBU R128 normalization to -15 LUFS / -1.5 dBTP."""
    src = os.path.join(BUILD, 'mix.wav')
    dst = os.path.join(BUILD, 'mix_norm.wav')
    target = 'I=-15:TP=-1.5:LRA=11'
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', src, '-af',
                        f'loudnorm={target}:print_format=json', '-f', 'null', '-'],
                       capture_output=True, text=True, check=True)
    m = json.loads(r.stderr[r.stderr.rindex('{'):r.stderr.rindex('}') + 1])
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', src, '-af',
                    f"loudnorm={target}:linear=true:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
                    f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']},"
                    "aresample=48000", '-c:a', 'pcm_f32le', dst], check=True)
    return dst


AUDIO_KBPS = 96


def video_args(kbps, pass_no):
    return ['-c:v', 'libx264', '-preset', 'veryslow', '-tune', 'animation', '-b:v', f'{kbps}k',
            '-maxrate', f'{kbps * 3}k', '-bufsize', f'{kbps * 6}k', '-pass', str(pass_no),
            '-passlogfile', os.path.join(BUILD, 'x264pass'),
            '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-level', '4.1',
            '-x264-params', 'keyint=240:min-keyint=24:aq-mode=3',
            '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
            '-vf', 'scale=out_color_matrix=bt709:flags=lanczos']


def check():
    src = ['-r', str(FPS), '-f', 'concat', '-safe', '0', '-i', os.path.join(BUILD, 'segments', 'list.txt')]
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', OUT] + src + [
        '-lavfi', '[0:v]format=yuv420p[a];[1:v]scale=out_color_matrix=bt709:flags=lanczos,format=yuv420p[b];'
                  '[a][b]ssim;[0:v]format=yuv420p[c];[1:v]scale=out_color_matrix=bt709:flags=lanczos,format=yuv420p[d];[c][d]psnr',
        '-f', 'null', '-'], capture_output=True, text=True)
    for line in r.stderr.splitlines():
        if 'SSIM Y' in line or 'PSNR y' in line:
            print(line.split(']')[-1].strip())


def main():
    if '--check' in sys.argv:
        check()
        return
    target_mb = float(sys.argv[1]) if len(sys.argv) > 1 else 14.2
    write_srt()
    audio = loudnorm()
    tl = json.load(open(os.path.join(BUILD, 'timeline.json')))
    total_kbps = target_mb * 8e3 / tl['duration'] * 0.985          # leave room for the container
    kbps = int(total_kbps - AUDIO_KBPS)
    src = ['-r', str(FPS), '-f', 'concat', '-safe', '0', '-i', os.path.join(BUILD, 'segments', 'list.txt')]
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error'] + src + video_args(kbps, 1) +
                   ['-an', '-f', 'mp4', os.devnull], check=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error'] + src + ['-i', audio, '-map', '0:v', '-map', '1:a'] +
                   video_args(kbps, 2) +
                   ['-c:a', 'aac', '-b:a', f'{AUDIO_KBPS}k', '-ar', '48000',
                    '-shortest', '-movflags', '+faststart', OUT], check=True)
    size = os.path.getsize(OUT) / 1e6
    print(f'{OUT}: {size:.2f} MB (video {kbps} kbps, audio {AUDIO_KBPS} kbps)')


if __name__ == '__main__':
    main()
