"""Frame renderer + video export."""
import argparse, math, os, subprocess, sys, time
import numpy as np
import skia
import gfx
from gfx import fill, stroke, alpha, shade, clamp, smooth, ease_io, ease_out, ease_in, ease_back, font, text_width, wrap_text, rad_grad
from engine import TL, M, SH, LN, FPS
import sets as S
import scenes as SC

HERE = os.path.dirname(os.path.abspath(__file__))
OUTW, OUTH = 720, 1280


class Film:
    def __init__(self, captions=True):
        self.captions = captions
        self.cls = SC.ClassScene()
        self.yard = SC.YardScene()
        self.bridge = SC.BridgeScene()
        self.porch = SC.PorchScene()
        self.fort = SC.FortScene()
        self.shots = TL["shots"]
        self.ctx = {}

    def scene_for(self, name):
        if name.startswith("class"):
            return self.cls
        if name.startswith("yard"):
            return self.yard
        if name.startswith("bridge"):
            return self.bridge
        if name.startswith("porch") or name in ("sky", "title_end"):
            return self.porch
        if name.startswith("fort"):
            return self.fort
        raise KeyError(name)

    def shot_at(self, t):
        for s in self.shots:
            if s["t0"] <= t < s["t1"]:
                return s["name"]
        return self.shots[-1]["name"]

    def yard_freeze(self):
        if "yard_freeze" not in self.ctx:
            surf = skia.Surface(540, 960)
            cv = surf.getCanvas()
            cv.scale(0.5, 0.5)
            t = M["silence"] + 1.2
            self.draw_world(cv, t, "yard_silence", 1.0)
            self.ctx["yard_freeze"] = surf.makeImageSnapshot()
        return self.ctx["yard_freeze"]

    def draw_world(self, cv, t, shot, out_scale):
        sc = self.scene_for(shot)
        cx, cy, z = sc.cam[shot](t)
        cv.save()
        cv.translate(540, 960)
        cv.scale(z, z)
        cv.translate(-cx, -cy)
        self.ctx["blur"] = max(0.0, (z - 1.6) * 2.2) / (z * out_scale) if z > 1.6 else 0.0
        sc.draw(cv, t, shot, self.ctx)
        cv.restore()
        return (cx, cy, z)

    # ------------------------------------------------------------------ overlays
    def overlays(self, cv, t, shot, cam):
        # vignette per set
        if shot.startswith("fort"):
            S.vignette(cv, 0.6)
        elif shot.startswith("porch") or shot in ("sky", "title_end"):
            S.vignette(cv, 0.4, "#050818")
        elif shot.startswith("bridge"):
            S.vignette(cv, 0.35, "#050818")
        else:
            S.vignette(cv, 0.18, "#3a2010")
        # keyhole mask for the cell (looking through the keyhole)
        if shot == "fort_cell":
            p = S.keyhole_path(540, 880, 820)
            cv.save()
            cv.clipPath(p, skia.ClipOp.kDifference, True)
            cv.drawRect(skia.Rect.MakeLTRB(0, 0, 1080, 1920), fill("#07060a"))
            cv.restore()
            cv.drawPath(p, stroke(alpha("#ffcc66", 0.35), 10))
            cv.drawPath(p, stroke(alpha("#ffcc66", 0.12), 30))
        # keyhole wipe out of the classroom, in to the yard
        kw = M["keyhole_wipe"]
        y0 = SH["yard_wide"][0]
        s = None
        if kw <= t < y0:
            u = ease_in(clamp((t - kw) / (y0 - kw)))
            s = 2600 * (1 - u) + 1
        elif y0 <= t < y0 + 0.8:
            u = ease_out(clamp((t - y0) / 0.8))
            s = 2600 * u + 1
        if s is not None:
            p = S.keyhole_path(540, 960, s)
            cv.save()
            cv.clipPath(p, skia.ClipOp.kDifference, True)
            cv.drawRect(skia.Rect.MakeLTRB(0, 0, 1080, 1920), fill("#120c08"))
            cv.restore()
        # location cards
        self.card(cv, t, SH["bridge_wide"][0] + 0.1, 2.6, "MEANWHILE, IN MY HEAD...")
        self.card(cv, t, SH["fort_hall"][0] + 0.1, 2.8, "MEANWHILE, IN DANNY'S HEAD...")
        self.card(cv, t, SH["yard_wide"][0] + 0.6, 2.4, "20 YEARS LATER")
        # name tags (world anchored)
        def w2s(x, y):
            cx, cy, z = cam
            return (x - cx) * z + 540, (y - cy) * z + 960
        def tag_window(t0, t1, wx, wy, txt, col):
            tt = t - t0
            a = clamp(tt / 0.3) * (1 - clamp((t - (t1 - 0.4)) / 0.4))
            if a > 0 and t0 <= t <= t1:
                self.tag(cv, *w2s(wx, wy), txt, a, col)
        if shot == "bridge_wide":
            o1 = LN("emb", "Oh my God")
            tag_window(o1[1] + 0.15, SH["bridge_wide"][1], 540, 1120, "EMBARRASSMENT", "#ff8fb5")
        if shot == "bridge_bored":
            tag_window(SH["bridge_bored"][0] + 0.1, SH["bridge_bored"][0] + 2.4, 850, 1335, "BOREDOM", "#7ff0e0")
        if shot == "fort_hall":
            tg = LN("narr", "But it was never", 1)
            tag_window(tg, tg + 3.0, 835, 1110, "DANNY'S ANGER", "#ff8a6a")
        if shot == "fort_cell":
            tg = LN("narr", "What he was guarding", 1)
            tag_window(tg + 0.2, SH["fort_cell"][1], 540, 1330, "GUILT", "#a9c0ff")
        # title
        self.title(cv, t)
        if self.captions:
            self.caption(cv, t)

    def card(self, cv, t, t0, dur, txt):
        tt = t - t0
        if tt < 0 or tt > dur:
            return
        a = clamp(tt / 0.35) * (1 - clamp((tt - (dur - 0.4)) / 0.4))
        f = font("Fredoka-SemiBold.ttf", 46)
        w = text_width(txt, f)
        y = 230 - 20 * (1 - ease_out(clamp(tt / 0.5)))
        cv.drawRoundRect(skia.Rect.MakeLTRB(540 - w / 2 - 34, y - 58, 540 + w / 2 + 34, y + 22), 40, 40, fill(alpha("#101326", 0.72 * a)))
        cv.drawString(txt, 540 - w / 2, y, f, fill(alpha("#fff3d6", a)))

    def tag(self, cv, x, y, txt, a, col):
        f = font("Fredoka-SemiBold.ttf", 40)
        w = text_width(txt, f)
        sc = 0.85 + 0.15 * ease_back(clamp(a))
        cv.save()
        cv.translate(x, y)
        cv.scale(sc, sc)
        cv.drawRoundRect(skia.Rect.MakeLTRB(-w / 2 - 24, -50, w / 2 + 24, 16), 33, 33, fill(alpha("#101326", 0.8 * a)))
        cv.drawRoundRect(skia.Rect.MakeLTRB(-w / 2 - 24, -50, w / 2 + 24, 16), 33, 33, stroke(alpha(col, a), 4))
        cv.drawString(txt, -w / 2, 0, f, fill(alpha(col, a)))
        p = gfx.path_poly([(-14, 16), (14, 16), (0, 36)])
        cv.drawPath(p, fill(alpha("#101326", 0.8 * a)))
        cv.restore()

    def title(self, cv, t):
        # opening title: fully visible on frame 0, fades after ~3.6 s
        if t < 4.4:
            a = 1.0 - clamp((t - 3.6) / 0.8)
            f1 = font("Fredoka-SemiBold.ttf", 132)
            f2 = font("Fredoka-Medium.ttf", 46)
            y = 250
            txt = "THE KEYHOLE"
            w = text_width(txt, f1)
            cv.drawRoundRect(skia.Rect.MakeLTRB(540 - w / 2 - 50, y - 140, 540 + w / 2 + 50, y + 105), 50, 50, fill(alpha("#1b1430", 0.78 * a)))
            cv.drawString(txt, 540 - w / 2 + 4, y + 6, f1, fill(alpha("#000000", 0.35 * a)))
            cv.drawString(txt, 540 - w / 2, y, f1, fill(alpha("#ffd36b", a)))
            sub = "why do we laugh when we're told not to?"
            w2 = text_width(sub, f2)
            cv.drawString(sub, 540 - w2 / 2, y + 70, f2, fill(alpha("#fff3e0", a)))
        # end title
        ts = M["title_start"]
        if t >= ts - 0.2:
            a = ease_out(clamp((t - ts + 0.2) / 1.0))
            f1 = font("Fredoka-SemiBold.ttf", 128)
            txt = "THE KEYHOLE"
            w = text_width(txt, f1)
            y = 1420
            for k, (g, al) in enumerate([(26, 0.12), (12, 0.25)]):
                cv.drawString(txt, 540 - w / 2, y, f1, stroke(alpha("#ffcf6b", al * a), g))
            cv.drawString(txt, 540 - w / 2, y, f1, fill(alpha("#fff3d0", a)))
            f2 = font("Fredoka-Medium.ttf", 44)
            sub = "laugh with the people you love."
            w2 = text_width(sub, f2)
            a2 = ease_out(clamp((t - ts - 0.8) / 1.0))
            cv.drawString(sub, 540 - w2 / 2, y + 90, f2, fill(alpha("#cfd8ff", a2)))

    def caption(self, cv, t):
        cur = None
        for c in TL["captions"]:
            if c["t0"] <= t < c["t1"]:
                cur = c
        if cur is None:
            return
        tt = t - cur["t0"]
        a = clamp(tt / 0.12) * clamp((cur["t1"] - t) / 0.12)
        f = font("Fredoka-SemiBold.ttf", 50)
        lines = wrap_text(cur["text"], f, 880)[-2:]
        narr = cur["who"] == "narr"
        col = "#ffe7a6" if narr else "#ffffff"
        y0 = 1430 - (len(lines) - 1) * 64
        for k, ln in enumerate(lines):
            w = text_width(ln, f)
            x = 540 - w / 2
            y = y0 + k * 64
            cv.drawString(ln, x, y, f, stroke(alpha("#120c18", 0.85 * a), 12))
            cv.drawString(ln, x, y, f, fill(alpha(col, a)))

    def frame(self, t, out_scale=OUTW / 1080, surf=None):
        shot = self.shot_at(t)
        if shot.startswith("bridge"):
            self.yard_freeze()
        if surf is None:
            surf = skia.Surface(int(1080 * out_scale), int(1920 * out_scale))
        cv = surf.getCanvas()
        cv.clear(skia.Color4f(0, 0, 0, 1))
        cv.save()
        cv.scale(out_scale, out_scale)
        cam = self.draw_world(cv, t, shot, out_scale)
        self.overlays(cv, t, shot, cam)
        cv.restore()
        return surf


def render_range(f0, f1, path, captions=True, w=OUTW, h=OUTH):
    film = Film(captions=captions)
    surf = skia.Surface(w, h)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{w}x{h}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "8", "-pix_fmt", "yuv420p", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    info = skia.ImageInfo.Make(w, h, skia.ColorType.kRGBA_8888_ColorType, skia.AlphaType.kPremul_AlphaType)
    buf = np.empty((h, w, 4), dtype=np.uint8)
    t_start = time.time()
    for fi in range(f0, f1):
        t = fi / FPS
        film.frame(t, w / 1080, surf)
        surf.readPixels(info, buf, w * 4, 0, 0)
        p.stdin.write(buf.tobytes())
        if (fi - f0) % 240 == 0:
            el = time.time() - t_start
            print(f"[{f0}-{f1}] frame {fi} t={t:.1f}s  ({(fi - f0 + 1) / max(el, 1e-3):.1f} fps)", flush=True)
    p.stdin.close()
    p.wait()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stills", type=str, default=None)
    ap.add_argument("--out", type=str, default="qa")
    ap.add_argument("--range", type=str, default=None)
    ap.add_argument("--seg", type=str, default=None)
    ap.add_argument("--nocap", action="store_true")
    a = ap.parse_args()
    if a.stills:
        film = Film(captions=not a.nocap)
        os.makedirs(a.out, exist_ok=True)
        for ts in a.stills.split(","):
            t = float(ts)
            surf = film.frame(t, 0.5)
            surf.makeImageSnapshot().save(os.path.join(a.out, f"still_{t:07.2f}.png"), skia.kPNG)
        return
    if a.range:
        f0, f1 = [int(x) for x in a.range.split(":")]
        render_range(f0, f1, a.seg, captions=not a.nocap)


if __name__ == "__main__":
    main()
