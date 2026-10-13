"""Final encode for "Brindle Cross": PNG frames + mix + burned-in ASS -> one MP4 under a size cap.

Usage: python3 encode.py --frames DIR/f%05d.png --audio mix.wav --ass film.ass --out out.mp4
                         [--max-mb 14.5] [--codec h264|hevc] [--fps 24] [--quality-check]

* Frame 1 of the sequence is the first video frame; no fades are added. The ASS is
  burned in with libass (fonts from --fontsdir, default the Inter directory).
* The sequence must be gap-free (ffmpeg's image reader stops silently at a gap). A
  sequence shorter than the audio is padded with black (tpad) to the audio duration,
  so the end card still renders; shorter audio is padded with silence.
* Size: video bitrate = (max-mb x 10^6 bytes, less 1.5 % container overhead, less the
  audio) / duration, two-pass. H.264: libx264 High, preset slower, tune animation,
  aq-mode 3; HEVC: libx265 preset slow, tune animation, tagged hvc1. Keyframe at most every 4 s,
  BT.709 yuv420p, AAC 96 kb/s stereo 48 kHz, +faststart. If the file still comes out
  over the cap, pass 2 is redone at a lower bitrate.
* --quality-check: SSIM / PSNR against the subtitled lossless source (same filter
  chain, no encode), and the loudness / true peak of the encoded audio.

Heavy commands run under `nice -n 15` (the render shares the machine).
"""
import argparse
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

import soundfile as sf

FONTS = '/usr/share/fonts/opentype/inter'
OVERHEAD = 0.015
AUDIO_KBPS = 96


def run(cmd, nice=15, capture=False):
    cmd = (['nice', '-n', str(nice)] if nice else []) + cmd
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if r.returncode:
        sys.stderr.write(r.stderr[-4000:])
        raise SystemExit('command failed: %s' % ' '.join(cmd[:12]))
    return r.stderr if capture else None


def ffprobe(path, entries, stream=None):
    cmd = ['ffprobe', '-v', 'error', '-of', 'default=nw=1']
    if stream:
        cmd += ['-select_streams', stream]
    cmd += ['-show_entries', entries, path]
    out = subprocess.run(cmd, stdout=subprocess.PIPE, text=True).stdout
    return dict(ln.split('=', 1) for ln in out.split() if '=' in ln)


def scan_frames(pattern):
    """(start_number, count) of a printf-style image sequence; refuses gaps."""
    m = re.search(r'%0?(\d*)d', pattern)
    if not m:
        raise SystemExit('frame pattern needs a %%d / %%05d field: %s' % pattern)
    width = int(m.group(1) or 0)
    head, tail = pattern[:m.start()], pattern[m.end():]
    rx = re.compile(re.escape(os.path.basename(head)) + r'(\d+)' + re.escape(tail) + '$')
    nums = sorted(int(rx.match(os.path.basename(p)).group(1))
                  for p in glob.glob(glob.escape(head) + '*' + glob.escape(tail))
                  if rx.match(os.path.basename(p)))
    nums = [n for n in nums if not width or len(str(n)) <= width]
    if not nums:
        raise SystemExit('no frames match %s' % pattern)
    missing = sorted(set(range(nums[0], nums[-1] + 1)) - set(nums))
    if missing:
        raise SystemExit('frame sequence has %d gaps, first missing: %s' % (len(missing), pattern % missing[0]))
    return nums[0], len(nums)


def quote(path):
    """A path as a filtergraph option value."""
    return "'" + path.replace('\\', '\\\\').replace("'", "'\\''") + "'"


class Job:
    """Everything both passes (and the quality check) need to agree on."""

    def __init__(self, a):
        self.a = a
        self.fps = a.fps
        self.audio_dur = sf.info(a.audio).duration
        if a.test_source:
            self.video_in = ['-f', 'lavfi', '-i', a.test_source]
            self.video_dur = a.test_duration or self.audio_dur
            self.n_frames = round(self.video_dur * self.fps)
        else:
            start, self.n_frames = scan_frames(a.frames)
            self.video_in = ['-framerate', str(self.fps), '-start_number', str(start), '-i', a.frames]
            self.video_dur = self.n_frames / float(self.fps)
        self.dur = max(self.video_dur, self.audio_dur)
        self.pad = self.dur - self.video_dur

    def vfilter(self):
        chain = []
        if self.a.test_source:
            chain.append('trim=duration=%.6f,setpts=PTS-STARTPTS' % self.video_dur)
        if self.pad > 0.5 / self.fps:
            chain.append('tpad=stop_mode=add:stop_duration=%.6f:color=black' % self.pad)
        chain.append('setsar=1')
        if self.a.ass:
            chain.append('ass=filename=%s:fontsdir=%s' % (quote(self.a.ass), quote(self.a.fontsdir)))
        chain.append('scale=out_color_matrix=bt709:out_range=tv:flags=bicubic+accurate_rnd+full_chroma_int')
        chain.append('format=yuv420p')
        return ','.join(chain)

    def video_codec(self, kbps, pass_no, log):
        a, fps = self.a, self.fps
        vbv = ['-maxrate', '%dk' % (kbps * 3), '-bufsize', '%dk' % (kbps * 6)]
        if a.codec == 'hevc':
            params = 'pass=%d:stats=%s:keyint=%d:min-keyint=%d:aq-mode=3:log-level=error' % (
                pass_no, log + '.x265', 4 * fps, fps)
            return ['-c:v', 'libx265', '-preset', a.preset or 'slow', '-tune', 'animation', '-profile:v', 'main',
                    '-b:v', '%dk' % kbps, '-tag:v', 'hvc1', '-x265-params', params] + vbv
        return ['-c:v', 'libx264', '-preset', a.preset or 'slower', '-tune', 'animation', '-profile:v', 'high',
                '-b:v', '%dk' % kbps, '-g', str(4 * fps), '-keyint_min', str(fps), '-x264-params', 'aq-mode=3',
                '-pass', str(pass_no), '-passlogfile', log] + vbv

    def colour_tags(self):
        return ['-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries', 'bt709',
                '-color_trc', 'bt709', '-color_range', 'tv']

    def first_pass(self, kbps, log):
        cmd = ['ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'error', '-y'] + self.video_in + [
            '-vf', self.vfilter(), '-t', '%.6f' % self.dur, '-an'] + self.video_codec(kbps, 1, log) + \
            self.colour_tags() + ['-f', 'null', os.devnull]
        run(cmd, self.a.nice)

    def second_pass(self, kbps, log, out):
        afilter = 'aresample=48000,apad=whole_dur=%.6f' % self.dur
        cmd = ['ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'error', '-y'] + self.video_in + [
            '-i', self.a.audio, '-map', '0:v:0', '-map', '1:a:0',
            '-vf', self.vfilter(), '-af', afilter, '-t', '%.6f' % self.dur] + \
            self.video_codec(kbps, 2, log) + self.colour_tags() + [
            '-c:a', 'aac', '-b:a', '%dk' % AUDIO_KBPS, '-ac', '2', '-ar', '48000',
            '-movflags', '+faststart', '-metadata', 'title=Brindle Cross - A Sunday in November', out]
        run(cmd, self.a.nice)


def video_kbps(max_bytes, dur):
    usable = max_bytes * 8 * (1 - OVERHEAD) - AUDIO_KBPS * 1000 * dur
    return int(usable / dur / 1000)


def report(path, dur):
    size = os.path.getsize(path)
    v = ffprobe(path, 'stream=bit_rate,nb_frames,width,height', 'v:0')
    au = ffprobe(path, 'stream=bit_rate', 'a:0')
    d = float(ffprobe(path, 'format=duration').get('duration', dur))
    print('  %s: %.3f MB (%d bytes), %.2f s, %sx%s, %s frames, video %.0f kb/s, audio %.0f kb/s' % (
        os.path.basename(path), size / 1e6, size, d, v.get('width'), v.get('height'), v.get('nb_frames'),
        float(v.get('bit_rate', 0)) / 1000, float(au.get('bit_rate', 0)) / 1000))
    return size


def quality_check(job, out):
    """SSIM/PSNR of the encode against the same filter chain left unencoded; audio loudness."""
    ref = job.vfilter() + ',setpts=PTS-STARTPTS'
    graph = ('[1:v]%s,split[r1][r2];[0:v]setpts=PTS-STARTPTS,split[d1][d2];'
             '[d1][r1]ssim;[d2][r2]psnr' % ref)
    cmd = ['ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'info', '-i', out] + job.video_in + [
        '-filter_complex', graph, '-t', '%.6f' % job.dur, '-f', 'null', '-']
    log = run(cmd, job.a.nice, capture=True)
    ssim = re.search(r'SSIM Y:([\d.]+).*All:([\d.]+) \(([\d.]+|inf)\)', log)
    psnr = re.search(r'PSNR y:([\d.inf]+).*average:([\d.inf]+) min:([\d.inf]+)', log)
    if ssim:
        print('  SSIM  Y %s  All %s (%s dB)' % ssim.groups())
    if psnr:
        print('  PSNR  Y %s dB  average %s dB  worst frame %s dB' % psnr.groups())
    log = run(['ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'info', '-i', out, '-map', '0:a:0',
               '-af', 'ebur128=peak=true', '-f', 'null', '-'], job.a.nice, capture=True)
    i = re.findall(r'I:\s+(-?[\d.]+) LUFS', log)
    tp = re.findall(r'Peak:\s+(-?[\d.inf]+) dBFS', log)
    if i:
        print('  audio %s LUFS integrated, true peak %s dBFS' % (i[-1], tp[-1] if tp else '?'))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--frames', help="printf pattern, e.g. render/f%%05d.png")
    ap.add_argument('--audio', required=True)
    ap.add_argument('--ass')
    ap.add_argument('--out', required=True)
    ap.add_argument('--max-mb', type=float, default=14.5)
    ap.add_argument('--codec', choices=('h264', 'hevc'), default='h264')
    ap.add_argument('--fps', type=int, default=24)
    ap.add_argument('--preset', help='override the x264/x265 preset')
    ap.add_argument('--fontsdir', default=FONTS)
    ap.add_argument('--nice', type=int, default=15)
    ap.add_argument('--quality-check', action='store_true')
    # testing without rendered frames: a lavfi source instead of the PNG sequence
    ap.add_argument('--test-source', help=argparse.SUPPRESS)
    ap.add_argument('--test-duration', type=float, help=argparse.SUPPRESS)
    a = ap.parse_args()
    if not a.frames and not a.test_source:
        ap.error('--frames is required')
    if a.ass and not os.path.exists(a.ass):
        ap.error('no such ASS file: %s' % a.ass)

    job = Job(a)
    max_bytes = a.max_mb * 1e6
    kbps = video_kbps(max_bytes, job.dur)
    print('%s: %d frames (%.2f s) + %.2f s black pad, audio %.2f s -> %.2f s; target %.2f MB, video %d kb/s %s' % (
        'test source' if a.test_source else a.frames, job.n_frames, job.video_dur, job.pad, job.audio_dur,
        job.dur, a.max_mb, kbps, a.codec))
    if kbps < 150:
        raise SystemExit('size budget leaves only %d kb/s for video' % kbps)

    work = tempfile.mkdtemp(prefix='encode_', dir=os.path.dirname(os.path.abspath(a.out)))
    log = os.path.join(work, 'pass')
    tmp_out = os.path.join(work, 'out' + os.path.splitext(a.out)[1])
    try:
        t = time.time()
        job.first_pass(kbps, log)
        print('  pass 1: %.0f s' % (time.time() - t))
        for attempt in range(4):
            t = time.time()
            job.second_pass(kbps, log, tmp_out)
            print('  pass 2 at %d kb/s: %.0f s' % (kbps, time.time() - t))
            size = report(tmp_out, job.dur)
            if size <= max_bytes:
                break
            over_kbps = (size - max_bytes * 0.99) * 8 / job.dur / 1000
            kbps = int(kbps - over_kbps - 4)
            print('  over %.2f MB by %.3f MB; retrying at %d kb/s' % (a.max_mb, (size - max_bytes) / 1e6, kbps))
        else:
            raise SystemExit('could not get under %.2f MB' % a.max_mb)
        shutil.move(tmp_out, a.out)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    size = os.path.getsize(a.out)
    print('wrote %s: %.3f MB (%d bytes) <= %.2f MB: %s' % (a.out, size / 1e6, size, a.max_mb, size <= max_bytes))
    if a.quality_check:
        quality_check(job, a.out)


if __name__ == '__main__':
    main()
