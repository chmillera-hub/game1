"""Final encode for "Brindle Cross": PNG frames + mix + burned-in ASS -> one MP4 under a size cap.

Usage: python3 encode.py --frames DIR/f%05d.png --audio mix.wav --ass film.ass --out out.mp4
                         [--timeline timeline.json] [--zero-frame 0] [--max-mb 14.5]
                         [--codec h264|hevc] [--fps 24] [--audio-kbps 96] [--quality-check]

* Time: image number N shows t = (N - zero_frame) / fps, as Blender renders it (film.py
  bakes frame N at N / fps, so --zero-frame defaults to 0). A sequence that starts after
  the zero frame (e.g. a render of frames 1..) has its first image held back to t = 0, so
  picture, mix and subtitles stay frame-locked and the first frame is real animation. No
  fades are added. The ASS is burned in with libass (fonts from --fontsdir).
* --timeline: fps and duration come from it, and everything after the last shot is the
  black tail the end card sits on (rendered frames there are ignored). The frames up to
  the tail must all exist. Without it, the duration is the audio's and a short sequence
  is padded with black.
* The sequence must be gap-free and without empty files (ffmpeg's image reader stops
  silently at a gap; Blender leaves 0-byte placeholders for frames in progress). Audio
  is padded with silence or trimmed to the duration.
* Size: video bitrate = (max-mb x 10^6 bytes, less 1.5 % container overhead, less the
  audio) / duration, two-pass. H.264: libx264 High, preset slower, tune animation,
  aq-mode 3; HEVC: libx265 preset slow, tune animation, tagged hvc1. Keyframe at most every 4 s,
  BT.709 yuv420p, AAC (--audio-kbps, 96) stereo 48 kHz, +faststart (checked). If the file still comes
  out over the cap, pass 2 is redone at a lower bitrate. MB means 10^6 bytes.
* --quality-check: SSIM / PSNR against the subtitled lossless source (same filter
  chain, no encode), and the loudness / true peak of the encoded audio.

Heavy commands run under `nice -n 15` (the render shares the machine).
"""
import argparse
import glob
import json
import math
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


def scan_frames(pattern, first=0, last=None):
    """(start_number, count) of a printf-style image sequence within [first, last].

    Refuses gaps and empty files (Blender's placeholders for frames still rendering)."""
    m = re.search(r'%0?(\d*)d', pattern)
    if not m:
        raise SystemExit('frame pattern needs a %%d / %%05d field: %s' % pattern)
    width = int(m.group(1) or 0)
    head, tail = pattern[:m.start()], pattern[m.end():]
    rx = re.compile(re.escape(os.path.basename(head)) + r'(\d+)' + re.escape(tail) + '$')
    nums = sorted(int(rx.match(os.path.basename(p)).group(1))
                  for p in glob.glob(glob.escape(head) + '*' + glob.escape(tail))
                  if rx.match(os.path.basename(p)))
    nums = [n for n in nums if (not width or len(str(n)) <= width) and n >= first and (last is None or n <= last)]
    if not nums:
        raise SystemExit('no frames match %s' % pattern)
    missing = sorted(set(range(nums[0], nums[-1] + 1)) - set(nums))
    if missing:
        raise SystemExit('frame sequence has %d gaps, first missing: %s' % (len(missing), pattern % missing[0]))
    empty = [n for n in nums if os.path.getsize(pattern % n) == 0]
    if empty:
        raise SystemExit('%d empty frame files (render placeholders?), first: %s' % (len(empty), pattern % empty[0]))
    return nums[0], len(nums)


def read_timeline(path):
    """(fps, duration, start of the black tail or None) from timeline.json."""
    tl = json.load(open(path))
    fps, dur = tl['fps'], tl['duration']
    shots = tl.get('shots') or []
    end = max(s['t1'] for s in shots) if shots else dur
    return fps, dur, (end if dur - end > 0.5 / fps else None)


def quote(path):
    """A path as a filtergraph option value."""
    return "'" + path.replace('\\', '\\\\').replace("'", "'\\''") + "'"


class Job:
    """Everything both passes (and the quality check) need to agree on."""

    def __init__(self, a):
        self.a = a
        self.audio_dur = sf.info(a.audio).duration
        black = None
        if a.timeline:
            fps, self.dur, black = read_timeline(a.timeline)
            self.fps = a.fps or fps
            if abs(self.audio_dur - self.dur) > 1.0 / self.fps:
                print('warning: audio is %.3f s, timeline %.3f s' % (self.audio_dur, self.dur))
        else:
            self.fps = a.fps or 24
            self.dur = self.audio_dur
        if a.black_from is not None:
            black = a.black_from
        self.black_from = black
        # frames of picture before the black tail (or the end)
        picture = min(self.dur, black) if black is not None else self.dur
        want = int(math.ceil(picture * self.fps - 1e-3))
        self.lead = 0
        if a.test_source:
            self.video_in = ['-f', 'lavfi', '-i', a.test_source]
            avail = round((a.test_duration or self.dur) * self.fps)
            self.n_frames = min(avail, want)
        else:
            z = a.zero_frame
            start, n = scan_frames(a.frames, z, z + want - 1)
            self.lead = start - z
            if self.lead > self.fps:
                raise SystemExit('sequence starts at %d, %.1f s after the zero frame %d' % (start, self.lead / self.fps, z))
            self.video_in = ['-framerate', str(self.fps), '-start_number', str(start), '-i', a.frames]
            self.n_frames = n
            if a.timeline and self.lead + n < want:
                raise SystemExit('render incomplete: picture needs frames up to %d, last on disk is %d' % (
                    z + want - 1, start + n - 1))
        self.video_dur = (self.lead + self.n_frames) / float(self.fps)
        self.pad = max(0.0, self.dur - self.video_dur)

    def vfilter(self):
        chain = ['trim=end_frame=%d,setpts=PTS-STARTPTS' % self.n_frames]
        pad = []
        if self.lead:
            pad.append('start=%d:start_mode=clone' % self.lead)
        if self.pad > 0.5 / self.fps:
            pad.append('stop_mode=add:stop_duration=%.6f:color=black' % self.pad)
        if pad:
            chain.append('tpad=' + ':'.join(pad))
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
            '-c:a', 'aac', '-b:a', '%dk' % self.a.audio_kbps, '-ac', '2', '-ar', '48000',
            '-movflags', '+faststart', '-metadata', 'title=Brindle Cross - A Sunday in November', out]
        run(cmd, self.a.nice)


def video_kbps(max_bytes, dur, audio_kbps=AUDIO_KBPS):
    usable = max_bytes * 8 * (1 - OVERHEAD) - audio_kbps * 1000 * dur
    return int(usable / dur / 1000)


def moov_first(path):
    """True when the 'moov' atom precedes 'mdat' (faststart)."""
    with open(path, 'rb') as f:
        while True:
            hdr = f.read(8)
            if len(hdr) < 8:
                return False
            size, kind = int.from_bytes(hdr[:4], 'big'), hdr[4:]
            if kind in (b'moov', b'mdat'):
                return kind == b'moov'
            if size == 1:
                size = int.from_bytes(f.read(8), 'big') - 8
            f.seek(size - 8, 1)


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
    ap.add_argument('--fps', type=int, help='default: the timeline\'s, else 24')
    ap.add_argument('--timeline', help='timeline.json: fps, duration and the black tail after the last shot')
    ap.add_argument('--zero-frame', type=int, default=0, help='image number shown at t = 0 (Blender: 0)')
    ap.add_argument('--black-from', type=float, help='seconds; black from here to the end')
    ap.add_argument('--audio-kbps', type=int, default=AUDIO_KBPS)
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
    kbps = video_kbps(max_bytes, job.dur, a.audio_kbps)
    print('%s: %d frames + %d held at the start (%.3f s) + %.3f s black, audio %.3f s -> %.3f s; '
          'target %.2f MB, video %d kb/s %s' % (
              'test source' if a.test_source else a.frames, job.n_frames, job.lead, job.video_dur, job.pad,
              job.audio_dur, job.dur, a.max_mb, kbps, a.codec))
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
    print('wrote %s: %.3f MB (%d bytes) <= %.2f MB: %s, faststart: %s' % (
        a.out, size / 1e6, size, a.max_mb, size <= max_bytes, moov_first(a.out)))
    if a.quality_check:
        quality_check(job, a.out)


if __name__ == '__main__':
    main()
