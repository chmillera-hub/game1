"""Frame compositor + encoder driver."""
import math
import os
import random
import subprocess
import sys
import numpy as np
import skia

from common import W, H, FPS, BUILD
from gfx import rgb, mix, fill, stroke, oval, rrect, poly, font, lin_grad, rad_grad, hash01, noise1
from rig import draw_character, DESIGNS, head_world
from robot import draw_robot
from sets import (build_audience_bg, build_stage_bg, AUD_BOUNDS, STAGE_BOUNDS, draw_spot_cone,
                  draw_back_silhouette, BACK_X, BACK_Y, ROW_X)
from screenplay import SPEAKER_COLORS

CHARS = ['doubt', 'boredom', 'me', 'anger', 'stranger']
SAMPLING = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)


class Renderer:
    def __init__(self, tl):
        self.tl = tl
        self.aud = build_audience_bg().withDefaultMipmaps()
        self.stage = build_stage_bg().withDefaultMipmaps()
        self.surface = skia.Surface(W, H)
        self.vignette = self._vignette()
        self._particles()
        self._captions()

    # ------------------------------------------------------------ helpers
    def _vignette(self):
        s = skia.Surface(W, H)
        c = s.getCanvas()
        c.clear(skia.Color(0, 0, 0, 0))
        p = skia.Paint()
        p.setShader(rad_grad((W / 2, H * 0.45), H * 0.75,
                             [((0, 0, 0), 0.0), ((0, 0, 0), 0.0), ((0, 0, 0), 0.55)], [0, 0.55, 1.0]))
        c.drawRect(skia.Rect.MakeWH(W, H), p)
        return s.makeImageSnapshot()

    def _particles(self):
        self.parts = []
        for b in self.tl.bursts:
            rnd = random.Random(b['seed'] * 7919 + 13)
            for i in range(b['n']):
                vx = rnd.uniform(-0.5, 0.5) * b['spread']
                vy = -rnd.uniform(0.45, 1.0) * b['up']
                floor = b['floor'] + rnd.uniform(-10, 45)
                self.parts.append(dict(t0=b['t'] + rnd.uniform(0, 0.08), x=b['x'] + rnd.uniform(-20, 20),
                                       y=b['y'] + rnd.uniform(-15, 15), vx=vx, vy=vy, floor=floor,
                                       spin=rnd.uniform(-8, 8), sz=b['size'] * rnd.uniform(0.8, 1.2),
                                       world=b['world'], seed=rnd.random()))

    def _captions(self):
        """Split each line into readable caption chunks timed by its audio fragments."""
        self.caps = []
        for ln in self.tl.lines:
            if not ln.get('caption') or not ln.get('frags'):
                continue
            chunks = []
            cur = None
            for (a, b, txt) in ln['frags']:
                if cur is None:
                    cur = [a, b, txt]
                else:
                    joined = cur[2] + ' ' + txt
                    if len(joined) <= 52 and not cur[2].rstrip().endswith(('.', '?', '!')) or len(joined) <= 26:
                        cur = [cur[0], b, joined]
                    else:
                        chunks.append(cur)
                        cur = [a, b, txt]
            if cur:
                chunks.append(cur)
            for i, (a, b, txt) in enumerate(chunks):
                t0 = ln['t0'] + a - 0.05
                t1 = ln['t0'] + (chunks[i + 1][0] - 0.05 if i + 1 < len(chunks) else b + 0.45)
                self.caps.append(dict(t0=t0, t1=t1, text=txt, speaker=ln['speaker'],
                                      shout='shout' in ln.get('fx', ())))
        self.caps.sort(key=lambda c: c['t0'])

    # ------------------------------------------------------------ world drawing
    def _draw_popcorn(self, cv, t, world, resting):
        for p in self.parts:
            if p['world'] != world or t < p['t0']:
                continue
            dt = t - p['t0']
            g = 1900.0
            x = p['x'] + p['vx'] * dt
            y = p['y'] + p['vy'] * dt + 0.5 * g * dt * dt
            landed = y >= p['floor'] and (p['vy'] + g * dt) > 0
            if landed:
                # time of landing
                a, b_, c = 0.5 * g, p['vy'], p['y'] - p['floor']
                disc = max(0.0, b_ * b_ - 4 * a * c)
                tl_ = (-b_ + math.sqrt(disc)) / (2 * a)
                x = p['x'] + p['vx'] * tl_
                y = p['floor']
            if landed != resting:
                continue
            ang = (p['spin'] * min(dt, 3.0)) * 57.3
            cv.save()
            cv.translate(x, y)
            cv.rotate(ang)
            s = 9 * p['sz']
            for (ox, oy, r) in ((-0.5, 0.1, 0.75), (0.45, -0.1, 0.8), (0.0, -0.55, 0.7), (0.05, 0.45, 0.65)):
                cv.drawPath(oval(ox * s, oy * s, r * s, r * s * 0.9), fill((255, 246, 220)))
            cv.drawPath(oval(-0.1 * s, -0.05 * s, 1.15 * s, 1.0 * s), stroke((150, 110, 50), 1.6, 0.8))
            cv.drawPath(oval(0.2 * s, 0.25 * s, 0.35 * s, 0.3 * s), fill((255, 205, 110)))
            cv.restore()

    def draw_world(self, cv, t, cam):
        world = cam['world']
        if world == 'aud':
            l, tp, r, b = AUD_BOUNDS
            cv.drawImage(self.aud, l, tp, SAMPLING)
            self._draw_popcorn(cv, t, 'aud', True)
            states = [(n, self.tl.state(n, t)) for n in CHARS]
            states.sort(key=lambda s: (s[1]['y'], s[1].get('lying', 0)))
            for n, st in states:
                draw_character(cv, n, st, t)
            self._draw_popcorn(cv, t, 'aud', False)
        else:
            l, tp, r, b = STAGE_BOUNDS
            cv.drawImage(self.stage, l, tp, SAMPLING)
            gst = self.tl.state('gemini', t)
            draw_robot(cv, gst, t)
            draw_spot_cone(cv, gst['x'] * 0.6, -1500, 0, 270, 1.0, t)
            # audience from behind
            order = sorted(CHARS, key=lambda n: -ROW_X[n])
            for n in order:
                st = self.tl.state(n, t)
                if st.get('lying', 0) > 0.5:
                    continue
                bx = -st['x'] * 1.1
                by = BACK_Y - (50 if st['y'] > 50 else 0)
                bs = {'stand': max(st['stand'], 0.0) * (1 - st.get('kneel', 0)), 'lean': st['lean'] * 0.5,
                      'head_tilt': st['head_tilt'],
                      'arms_up': 1.0 if (st['la1'] > 120 and st['ra1'] > 120) else 0.0,
                      'popcorn_up': 1.0 if (n == 'anger' and st.get('prop_r') == 'popcorn') else 0.0,
                      'sink': st.get('sink', 0) * 1.5}
                draw_back_silhouette(cv, n, bx, by, 1.25, bs, t)

    # ------------------------------------------------------------ overlays
    def draw_overlays(self, cv, t):
        for ov in self.tl.overlays:
            if not (ov['t0'] <= t <= ov['t1']):
                continue
            k = ov['kind']
            u_in = min(1.0, (t - ov['t0']) / 0.35)
            fo = ov.get('fade_out', 0.4)
            u_out = min(1.0, (ov['t1'] - t) / fo)
            a = min(u_in if k != 'title' else 1.0, u_out)
            if k == 'title':
                self._title(cv, a, t)
            elif k == 'tag':
                self._tag(cv, ov['text'], ov['who'], a, t - ov['t0'])
            elif k == 'end':
                self._end(cv, a, t - ov['t0'])

    def _outlined_text(self, cv, txt, x, y, f, col, a=1.0, ow=10, oc=(20, 8, 12)):
        cv.drawString(txt, x, y, f, stroke(oc, ow, a))
        cv.drawString(txt, x, y, f, fill(col, a))

    def _title(self, cv, a, t):
        f1 = font('InterDisplay-Black', 128)
        f2 = font('InterDisplay-ExtraBold', 44)
        f3 = font('InterDisplay-Black', 84)
        cy = 150
        bob = math.sin(t * 2.2) * 3
        txt = 'ANGER'
        w = f1.measureText(txt)
        cv.drawString(txt, (W - w) / 2, cy + 115 + bob, f1, fill((255, 90, 50), 0.6 * a, blur=18))
        self._outlined_text(cv, txt, (W - w) / 2, cy + 115 + bob, f1, (255, 96, 64), a, 14)
        txt = 'GOES TO A'
        w = f2.measureText(txt)
        self._outlined_text(cv, txt, (W - w) / 2, cy + 175, f2, (255, 244, 230), a, 9)
        txt = 'COMEDY SHOW'
        w = f3.measureText(txt)
        self._outlined_text(cv, txt, (W - w) / 2, cy + 262 - bob, f3, (255, 214, 80), a, 12)

    def _tag(self, cv, txt, who, a, dt):
        col = SPEAKER_COLORS.get(who, (255, 255, 255))
        f = font('InterDisplay-Black', 64)
        w = f.measureText(txt)
        slide = (1 - min(1, dt / 0.35)) ** 3 * 40
        x = (W - w) / 2
        y = 205 - slide
        cv.drawPath(rrect(x - 28, y - 62, x + w + 28, y + 20, 18), fill((10, 6, 10), 0.55 * a))
        self._outlined_text(cv, txt, x, y, f, col, a, 9)

    def _end(self, cv, a, dt):
        cv.drawRect(skia.Rect.MakeWH(W, H), fill((8, 4, 8), 0.55 * a))
        f1 = font('InterDisplay-Black', 92)
        f2 = font('InterDisplay-SemiBoldItalic', 46)
        txt = 'ANGER'
        w = f1.measureText(txt)
        self._outlined_text(cv, txt, (W - w) / 2, 560, f1, (255, 96, 64), a, 12)
        for i, txt in enumerate(('still the boss', 'of comedy.')):
            w = f2.measureText(txt)
            self._outlined_text(cv, txt, (W - w) / 2, 640 + i * 60, f2, (255, 244, 230), a * min(1, max(0, (dt - 0.5) / 0.5)), 8)

    def draw_captions(self, cv, t):
        for c in self.caps:
            if c['t0'] <= t < c['t1']:
                self._caption(cv, c, t)

    def _caption(self, cv, c, t):
        narr = c['speaker'] == 'narr'
        f = font('Inter-SemiBoldItalic' if narr else 'Inter-Bold', 37 if not c['shout'] else 40)
        col = SPEAKER_COLORS.get(c['speaker'], (255, 255, 255))
        words = c['text'].split()
        lines, cur = [], ''
        for wd in words:
            test = (cur + ' ' + wd).strip()
            if f.measureText(test) > 610 and cur:
                lines.append(cur)
                cur = wd
            else:
                cur = test
        if cur:
            lines.append(cur)
        lh = 50
        base = 1175
        u = min(1.0, (t - c['t0']) / 0.12)
        top = base - lh * len(lines) - 6
        wmax = max(f.measureText(l) for l in lines)
        cv.drawPath(rrect(W / 2 - wmax / 2 - 22, top - 10 + (1 - u) * 6, W / 2 + wmax / 2 + 22,
                          base + 16 + (1 - u) * 6, 18), fill((6, 4, 8), 0.58 * u))
        for i, l in enumerate(lines):
            w = f.measureText(l)
            y = top + lh * (i + 1) - 10 + (1 - u) * 6
            cv.drawString(l, (W - w) / 2, y, f, stroke((10, 6, 10), 6, u))
            cv.drawString(l, (W - w) / 2, y, f, fill(col, u))

    # ------------------------------------------------------------ frame
    def cam_state(self, t):
        cam = self.tl.state('cam', t)
        fol = cam.get('follow', '')
        fw = cam.get('fw', 0.0)
        if fol and fw > 0.001:
            xs, ys = [], []
            for dt in (-0.3, -0.15, 0.0, 0.15, 0.3):
                hx_, hy = head_world(fol, self.tl.state(fol, t + dt))
                xs.append(hx_)
                ys.append(hy)
            hx_, hy = sum(xs) / len(xs), sum(ys) / len(ys)
            cam['cx'] = cam['cx'] * (1 - fw) + (hx_ + cam.get('fdx', 0)) * fw
            cam['cy'] = cam['cy'] * (1 - fw) + (hy + cam.get('fdy', 0)) * fw
        return cam

    def frame(self, t):
        cam = self.cam_state(t)
        cv = self.surface.getCanvas()
        cv.clear(skia.Color(0, 0, 0))
        grade = cam.get('desat', 0) > 0.01 or cam.get('dark', 0) > 0.01
        if grade:
            ds = cam['desat']
            lum = [0.299, 0.587, 0.114]
            m = []
            for row in range(3):
                for col in range(3):
                    m.append((1 - ds) * (1.0 if row == col else 0.0) + ds * lum[col])
                m += [0, 0]
                # insert alpha column placeholders below
            mat = [m[0], m[1], m[2], 0, 0,
                   m[5], m[6], m[7], 0, 0,
                   m[10], m[11], m[12], 0, 0,
                   0, 0, 0, 1, 0]
            # warm/sepia tint while desaturated
            mat[4] = 0.04 * ds
            mat[9] = 0.02 * ds
            mat[14] = -0.02 * ds
            p = skia.Paint()
            p.setColorFilter(skia.ColorFilters.Matrix(mat))
            cv.saveLayer(None, p)
        cv.save()
        sh = cam.get('shake', 0)
        jx = noise1(t * 40, 2.2) * 14 * sh
        jy = noise1(t * 40, 5.9) * 14 * sh
        cv.translate(W / 2 + jx, H / 2 + jy)
        cv.scale(cam['z'], cam['z'])
        cv.translate(-cam['cx'], -cam['cy'])
        self.draw_world(cv, t, cam)
        cv.restore()
        if grade:
            cv.restore()
        cv.drawImage(self.vignette, 0, 0)
        dk = cam.get('dark', 0)
        if dk > 0.01:
            p = skia.Paint()
            p.setShader(rad_grad((W / 2, H * 0.42), H * 0.62,
                                 [((0, 0, 0), 0.0), ((0, 0, 0), 0.9 * dk)], [0.35, 1.0]))
            cv.drawRect(skia.Rect.MakeWH(W, H), p)
        fl = cam.get('flash', 0)
        if fl > 0.01:
            cv.drawRect(skia.Rect.MakeWH(W, H), fill((255, 255, 255), fl))
        self.draw_overlays(cv, t)
        self.draw_captions(cv, t)
        return self.surface

    def frame_rgb(self, t):
        s = self.frame(t)
        img = s.makeImageSnapshot()
        arr = img.toarray(colorType=skia.kRGBA_8888_ColorType)
        return arr


def render_range(f0, f1, out_path, tl):
    r = Renderer(tl)
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W}x{H}',
           '-r', str(FPS), '-i', 'pipe:0', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '6',
           '-pix_fmt', 'yuv420p', out_path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for fi in range(f0, f1):
        arr = r.frame_rgb(fi / FPS)
        p.stdin.write(arr.tobytes())
    p.stdin.close()
    p.wait()


if __name__ == '__main__':
    from screenplay import build
    tl = build()
    mode = sys.argv[1]
    if mode == 'stills':
        out = sys.argv[2]
        os.makedirs(out, exist_ok=True)
        r = Renderer(tl)
        times = [float(x) for x in sys.argv[3:]]
        for t in times:
            r.frame(t).makeImageSnapshot().save(os.path.join(out, f'f_{t:07.2f}.png'), skia.kPNG)
    elif mode == 'chunk':
        f0, f1, outp = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        render_range(f0, f1, outp, tl)
