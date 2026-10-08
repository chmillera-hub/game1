"""Act 2: the board meeting at Mammon Capital."""
import math, random
import skia
from common import *
from characters import *
from cast import CEO, CFO, TYLER, PAM, JESUS

FLOOR = 2350
TABLE_BACK, TABLE_FRONT, PANEL_BOT = 1862, 1968, 2290
TABLE_L, TABLE_R = 150, 1625
SHOULDER_Y = 1702
SEATS = {"PAM": 330, "CFO": 690, "CEO": 1040, "TYLER": 1390}
LOOKS = {"PAM": PAM, "CFO": CFO, "CEO": CEO, "TYLER": TYLER, "JESUS": JESUS}
JX, JY = 1850, 1828          # Jesus seated shoulder point
SCREEN_R = (420, 640, 1240, 700)
SEED_POS = (1566, 1905)
CLOCK = (1870, 905)

SHOTS = {
    "WIDE": (1040, 1990, 2120),
    "WIDE_HI": (1040, 1560, 1700),
    "SCREEN": (1040, 1130, 1420),
    "BOARD3": (1040, 1730, 1220),
    "CFO_TY": (1040, 1700, 1050),
    "RIGHT": (1600, 1930, 1180),
    "SEED": (1566, 1860, 420),
    "SEED_W": (1500, 1700, 1000),
}
for k, x in SEATS.items():
    SHOTS[k + "_M"] = (x, 1735, 700)
    SHOTS[k + "_C"] = (x, 1650, 440)
SHOTS["JESUS_M"] = (JX, 1930, 760)
SHOTS["JESUS_C"] = (JX, 1772, 450)
SHOTS["CLOCK"] = (CLOCK[0] - 60, CLOCK[1] + 120, 520)


class Board:
    def __init__(self, tl):
        self.tl = tl
        T, E, Wd = tl.s, tl.e, tl.wfind
        self.T, self.E, self.Wd = T, E, Wd
        self.blink = {k: Blinker(i * 13 + 3) for i, k in enumerate(LOOKS)}
        self.t_start = E("title") - 0.3
        self.lights_off = E("b34") + 0.55

        # ---------------- expressions
        F = FaceTrack
        aw = expr("awkward", sweat=0.0)
        self.face = {
            "CEO": F([(0, "tired"), (T("b1"), "stern"), (Wd("b2", "Thanks"), "smile"), (T("b3") + 0.4, "confused"),
                      (T("b4"), "deadpan"), (T("b5"), "annoyed"), (Wd("b8", "Five"), "excited"),
                      (Wd("b8", "free"), "shocked"), (Wd("b8", "Where"), "angry"), (T("b9"), "skeptical"),
                      (T("b11"), "stern"), (Wd("b12", "birds"), "confused"), (T("silence1"), "deadpan"),
                      (T("b13"), "annoyed"), (T("b17"), "neutral"), (Wd("b17", "sell"), expr("neutral", lid=0.3)),
                      (T("spit"), "shocked", 0.1), (T("b18"), "furious"), (T("b19"), "angry"),
                      (Wd("b19", "rich"), "nervous"), (T("b20"), "stern"), (Wd("b21", "den"), "nervous"),
                      (T("b22"), "annoyed"), (T("b26") - 0.3, "furious", 0.15), (T("b27"), "angry"),
                      (Wd("b27", "soul"), "confused"), (T("silence2") + 0.5, "deadpan"), (T("b29"), "tired"),
                      (T("b30"), "annoyed"), (T("exit") + 1.0, "skeptical"), (T("b31"), "smug"),
                      (T("b33"), "annoyed"), (T("b34"), "smug")]),
            "CFO": F([(0, "neutral"), (T("b4"), "smile"), (T("b5"), "stern"), (T("b6"), "shocked", 0.15),
                      (T("b7"), "skeptical"), (T("b8"), "annoyed"), (T("b9"), "deadpan"), (T("b12"), "skeptical"),
                      (T("silence1"), "deadpan"), (T("b15"), "stern"), (T("b16"), "skeptical"),
                      (T("b17"), "annoyed"), (T("spit"), "wince", 0.1), (T("b18"), "annoyed"),
                      (T("b19"), "deadpan"), (Wd("b21", "den"), "nervous"), (T("b23"), "stern"),
                      (T("b24"), "confused"), (T("b25"), "skeptical"), (T("b26"), "neutral"),
                      (T("b27"), "confused"), (T("silence2"), "deadpan"), (T("b30"), "neutral"),
                      (T("b32"), "smug"), (T("b33"), "annoyed")]),
            "TYLER": F([(0, "smug"), (T("b3"), "confused"), (T("b4"), "smug"), (T("b8"), "excited"),
                        (Wd("b8", "But"), "confused"), (Wd("b8", "Where"), "annoyed"), (T("b9"), "confused"),
                        (T("b11"), "smug"), (T("b12") + 2, "confused"), (T("b15"), "smug"),
                        (T("b17"), "excited"), (Wd("b17", "told"), "smug"), (T("spit"), "wince", 0.1),
                        (T("b19"), "shocked"), (T("b20"), "smug"), (Wd("b21", "den"), "nervous"),
                        (T("b23"), "neutral"), (T("b24"), "confused"), (T("b26"), "shocked"),
                        (T("silence2"), "awkward"), (T("b30"), "smug"), (T("b33"), "neutral"), (T("b34"), "smug")]),
            "PAM": F([(0, "neutral"), (T("b3"), "smile"), (T("b4"), "neutral"), (T("b6"), "shocked"),
                      (T("b7"), "neutral"), (T("b9"), "smile"), (T("b10"), "neutral"), (T("b12") + 1.5, "hopeful", 1.0),
                      (T("silence1") + 0.6, aw), (T("b14"), "nervous"), (T("b16"), "kind"), (T("spit"), "shocked", 0.1),
                      (T("b19"), "smile"), (Wd("b21", "den"), "nervous"), (T("b24"), "kind"),
                      (T("b26"), "nervous"), (T("b27"), expr("compassion", glisten=0.9, tears=0.0), 0.8),
                      (T("silence2"), "sad"), (T("b30"), "hopeful"), (T("exit") + 1.5, "sad"),
                      (T("b33"), "hopeful"), (T("b34") + 1.0, "smile")]),
            "JESUS": F([(0, "serene"), (T("b1"), aw), (Wd("b2", "Thanks"), "kind"), (T("b4"), aw),
                        (T("b5"), "serene"), (T("b6") - 0.6, "compassion", 0.6), (T("b7") + 0.4, "serene"),
                        (Wd("b8", "viral"), "smile"), (T("b9"), "kind"), (T("b10") + 0.6, "smile"),
                        (T("b11"), "serene"), (T("b12"), "kind"), (Wd("b12", "birds"), expr("hopeful", glisten=0.6)),
                        (T("silence1") + 0.8, aw), (T("b13") + 0.4, "smile"), (T("b15"), "kind"),
                        (T("b16"), "compassion"), (T("b17"), "serene"), (T("b19"), "kind"),
                        (T("b20"), "serene"), (T("b21"), "stern"), (T("b22") + 0.4, "serene"), (T("b24"), "kind"),
                        (T("b25"), "smile"), (T("b26"), "serene"), (T("b27"), expr("compassion", glisten=0.8)),
                        (T("b28") + 0.3, "smile"), (T("b29"), "kind"), (T("b30"), expr("kind", glisten=0.5))]),
        }

        # ---------------- who each speaker addresses
        self.address = {"b1": "CAM", "b4": "CFO", "b5": "CEO", "b7": "JESUS", "b13": "CFO", "b14": "TYLER",
                        "b22": "CFO", "b25": "CFO", "b31": "CFO", "b32": "SCREEN", "b33": "CEO", "b34": "PAM",
                        "b3": "CEO", "b6": "CFO", "b9": "TYLER", "b16": "CFO", "b19": "CEO", "b24": "CFO",
                        "b27": "CEO", "b30": "CEO", "b28": "JESUS", "b29": "JESUS", "b21": "SWEEP"}
        self.overrides = {
            "CEO": [(Wd("b17", "sell"), T("spit"), "MUG"), (Wd("b19", "rich"), E("b19") + 1.2, "WATCH"),
                    (T("exit"), T("b31"), "JESUS"), (T("b34") - 0.2, E("b34") + 2, "SEED")],
            "CFO": [(T("b5") + 0.5, Wd("b5", "And"), "SCREEN"), (T("b15"), Wd("b15", "These"), "SCREEN"),
                    (T("b23"), Wd("b23", "Your"), "SCREEN"), (T("b32"), E("b32"), "TABLET"),
                    (T("exit"), T("b31"), "JESUS"), (T("silence1"), T("silence1") + 1.2, "CEO"),
                    (T("silence1") + 1.2, E("silence1"), "CAM")],
            "TYLER": [(Wd("b8", "Five"), Wd("b8", "That's"), "SCREEN"), (T("exit"), T("b31"), "JESUS"),
                      (T("silence1"), T("silence1") + 1.0, "JESUS"), (T("silence1") + 1.0, E("silence1"), "CEO"),
                      (T("silence2"), E("silence2"), "CEO")],
            "PAM": [(T("b33"), E("b33"), "CEO"), (E("b33"), E("b34") + 2, "SEED"), (T("exit"), T("b31"), "JESUS"),
                    (T("silence1"), T("silence1") + 1.4, "CFO"), (T("silence1") + 1.4, E("silence1"), "CAM")],
            "JESUS": [(T("b1"), T("b2"), "SCREEN"), (T("silence1"), T("silence1") + 1.0, "CEO"),
                      (T("silence1") + 1.0, E("silence1"), "CAM"), (T("silence2"), E("silence2"), "CEO"),
                      (E("b30") + 0.2, E("exit"), "SEED"), (T("b33") - 2, E("b34") + 5, "CAM")],
        }

        # ---------------- hands (body coords)
        rest = ((-62, 186), (66, 182))
        self.hands = {
            "CEO": Keys([(0, rest), (T("b11"), ((-20, 112), (20, 112)), 0.4), (E("b11") + 0.3, rest, 0.4),
                         (Wd("b17", "sell"), ((-62, 186), (22, -52)), 0.5), (T("spit") + 0.25, rest, 0.35),
                         (Wd("b19", "rich"), ((-62, 186), (-10, 110)), 0.4), (E("b19") + 1.1, rest, 0.4),
                         (T("b26") - 0.45, ((-70, 30), (70, 30)), 0.25), (T("b26") - 0.08, ((-62, 186), (62, 186)), 0.08),
                         (E("b26") + 0.2, rest, 0.4),
                         (T("b29") - 0.1, ((-76, -105), (76, -105)), 0.45), (E("b29") + 0.2, rest, 0.5)]),
            "CFO": Keys([(0, ((-50, 186), (58, 186)))]),
            "TYLER": Keys([(0, ((-62, 186), (64, 186))), (Wd("b8", "viral"), ((-112, 40), (112, 40)), 0.25),
                           (Wd("b8", "But"), ((-62, 186), (64, 186)), 0.35),
                           (T("b15"), ((-55, -125), (55, -125)), 0.5), (T("b16"), ((-62, 186), (64, 186)), 0.4),
                           (T("b22") - 0.3, ((-50, 186), (-30, -50)), 0.3), (E("b22") + 0.3, ((-62, 186), (64, 186)), 0.3),
                           (T("b25") - 0.3, ((-50, 186), (-30, -50)), 0.3), (E("b25") + 0.3, ((-62, 186), (64, 186)), 0.3),
                           (T("b31"), ((-55, -125), (55, -125)), 0.5), (E("b34") - 1, ((-62, 186), (64, 186)), 0.4)]),
            "PAM": Keys([(0, ((-46, 192), (44, 186))), (T("b33") - 0.2, ((-46, 192), (128, -150)), 0.35),
                         (E("b33") + 0.3, ((-46, 192), (44, 186)), 0.4)]),
        }
        self.hand_kind = {
            "CEO": lambda t: ("fist", "fist") if not (T("b29") - 0.2 < t < E("b29") + 0.3) else ("open", "open"),
            "TYLER": lambda t: ("open", "open") if (Wd("b8", "viral") - 0.1 < t < Wd("b8", "But")) else
            (("fist", "open") if (T("b22") - 0.3 < t < E("b22") + 0.3 or T("b25") - 0.3 < t < E("b25") + 0.3) else ("fist", "fist")),
            "PAM": lambda t: ("fist", "open") if T("b33") - 0.1 < t < E("b33") + 0.3 else ("fist", "fist"),
            "CFO": lambda t: ("fist", "fist"),
        }
        self.behind_head = {"TYLER": [(T("b15") + 0.25, T("b16") - 0.1), (T("b31") + 0.25, E("b34") - 1.1)]}
        self.lean = {
            "TYLER": Keys([(0, 0.0), (T("b22") - 0.3, -38.0, 0.3), (E("b22") + 0.3, 0.0, 0.3),
                           (T("b25") - 0.3, -38.0, 0.3), (E("b25") + 0.3, 0.0, 0.3)]),
            "CEO": Keys([(0, 0.0), (T("b11"), 0.0), (T("spit"), 0.0)]),
        }
        # Jesus hands (seated, relative to shoulder point)
        jr = ((-66, 250), (66, 250))
        self.jhands = Keys([(0, jr), (Wd("b2", "Thanks") + 0.2, ((-74, 262), (98, 40)), 0.3), (E("b2") + 0.7, jr, 0.4),
                            (Wd("b12", "mustard") - 0.2, ((-74, 262), (92, 150)), 0.6),
                            (Wd("b12", "tree"), ((-96, 140), (96, 140)), 0.6), (E("b12") + 0.6, jr, 0.8),
                            (Wd("b16", "doctor") - 0.4, ((-74, 262), (92, 150)), 0.5), (E("b16") + 0.4, jr, 0.6),
                            (Wd("b19", "camel") - 0.3, ((-74, 262), (92, 150)), 0.5), (E("b19") + 0.3, jr, 0.6),
                            (T("b24"), ((-96, 150), (96, 150)), 0.6), (E("b24") + 0.3, jr, 0.6),
                            (Wd("b27", "world") - 0.6, ((-74, 262), (88, 110)), 0.6), (E("b27") + 0.6, jr, 0.8)])
        self.jkind = lambda t: ("open", "open")

        # ---------------- slides
        self.slides = [(0, "title"), (Wd("b1", "Next"), "agenda"), (Wd("b5", "Twelve") - 0.3, "followers"),
                       (Wd("b8", "Five") - 0.3, "event"), (Wd("b11", "What"), "strategy"),
                       (Wd("b12", "smallest") - 0.2, "seed"), (T("b15") - 0.2, "demo"),
                       (Wd("b17", "whale") - 0.2, "whale"), (Wd("b20", "temple") - 0.2, "temple"),
                       (T("b23") - 0.1, "sentiment"), (Wd("b26", "one") - 0.2, "kpi"),
                       (Wd("b32", "Projected") - 0.2, "doomed")]

        # ---------------- camera
        S = SHOTS
        self.shots = [
            (self.t_start, "WIDE", 0), (Wd("b1", "Next") - 0.2, "SCREEN", 1.3),
            (T("b2"), "CEO_M", 0), (T("b3") - 0.15, "JESUS_M", 0), (T("b4") - 0.1, "CEO_M", 0),
            (T("b5") - 0.2, "CFO_M", 0), (Wd("b5", "Twelve") - 0.1, "SCREEN", 0), (Wd("b5", "And") - 0.1, "CFO_C", 0),
            (T("b6") - 0.25, "JESUS_C", 0), (T("b7") - 0.1, "CFO_C", 0),
            (T("b8") - 0.15, "TYLER_M", 0), (Wd("b8", "Five") - 0.1, "SCREEN", 0), (Wd("b8", "viral") - 0.1, "TYLER_M", 0),
            (Wd("b8", "But"), "TYLER_C", 0.8),
            (T("b9") - 0.2, "JESUS_M", 0), (T("b10") - 0.1, "TYLER_M", 0), (T("b11") - 0.1, "CEO_C", 0),
            (T("b12") - 0.2, "JESUS_M", 0), (Wd("b12", "smallest") - 0.1, "SCREEN", 0),
            (Wd("b12", "But"), "JESUS_M", 0), (Wd("b12", "But") + 0.05, "JESUS_C", 5.0),
            (T("silence1"), "WIDE", 0), (T("silence1") + 1.0, "PAM_C", 0), (T("silence1") + 1.8, "BOARD3", 0),
            (T("b13") - 0.1, "TYLER_M", 0), (T("b14") - 0.1, "CFO_M", 0), (T("b15") + 0.1, "SCREEN", 0),
            (Wd("b15", "These") - 0.1, "CFO_C", 0), (T("b16") - 0.15, "JESUS_M", 0),
            (T("b17") - 0.1, "TYLER_M", 0), (Wd("b17", "And", 1) - 0.1, "CEO_M", 0), (T("spit"), "CEO_C", 0),
            (T("b19") - 0.1, "JESUS_M", 0), (T("b19") + 0.05, "JESUS_C", 6.5), (E("b19") + 0.1, "CEO_C", 0),
            (T("b20") + 0.2, "CEO_M", 0), (Wd("b20", "temple") - 0.1, "SCREEN", 0),
            (T("b21") - 0.15, "JESUS_C", 0), (Wd("b21", "den") - 0.1, "BOARD3", 0),
            (T("b22") - 0.15, "CFO_TY", 0), (T("b23") - 0.1, "CFO_M", 0), (Wd("b23", "Your") - 0.1, "SCREEN", 0),
            (T("b24") - 0.15, "JESUS_M", 0), (T("b25") - 0.3, "CFO_TY", 0),
            (T("b26") - 0.5, "CEO_M", 0), (Wd("b26", "one") - 0.1, "CEO_C", 0),
            (T("b27") - 0.2, "JESUS_M", 0), (T("b27") + 0.05, "JESUS_C", 4.5),
            (T("silence2"), "CEO_C", 0), (T("silence2") + 1.2, "CLOCK", 0), (E("silence2") - 0.4, "CEO_C", 0),
            (T("b29") - 0.1, "CEO_M", 0), (T("b30") - 0.2, "JESUS_M", 0), (E("b30") + 0.1, "RIGHT", 0),
            (T("b31") - 0.1, "TYLER_M", 0), (T("b32") - 0.1, "CFO_M", 0),
            (Wd("b32", "Projected") - 0.1, "SCREEN", 0), (T("b33") - 0.15, "PAM_C", 0), (T("b34") - 0.1, "CEO_M", 0),
            (E("b34") + 0.2, "SEED_W", 0), (E("b34") + 0.3, "SEED", 2.2),
        ]

        # Jesus' exit choreography
        e0 = E("b30")
        self.j_rise = (T("b30") + 0.1, T("b30") + 0.8)
        self.j_step = (e0 + 0.15, e0 + 0.75)       # move left to the table
        self.j_reach = (e0 + 0.75, e0 + 1.25)
        self.j_seed = e0 + 1.15
        self.j_back = (e0 + 1.25, e0 + 1.6)
        self.j_walk = (e0 + 1.6, e0 + 3.6)

    # ------------------------------------------------------------ camera
    def camera(self, t):
        sh = self.shots
        cur = SHOTS[sh[0][1]]
        for (t0, name, dur) in sh:
            if t < t0:
                break
            tgt = SHOTS[name]
            if dur > 0:
                u = ease_io(prog(t, t0, t0 + dur))
                cur = tuple(lerp(a, b, u) for a, b in zip(cur, tgt))
            else:
                cur = tgt
        # find start time of current shot for drift
        last = max([s for s in sh if s[0] <= t] or [sh[0]], key=lambda s: s[0])
        age = t - last[0]
        cx, cy, w = cur
        w *= 1 - 0.035 * smooth(age / 6.0)
        cx += noise1(t * 0.25, 41) * w * 0.006
        cy += noise1(t * 0.25, 42) * w * 0.006
        if self.T("b26") - 0.12 < t < self.T("b26") + 0.35:    # slam shake
            k = 1 - prog(t, self.T("b26") - 0.12, self.T("b26") + 0.35)
            cx += math.sin(t * 90) * 12 * k
            cy += math.cos(t * 77) * 12 * k
        return cx, cy, w

    # ------------------------------------------------------------ attention
    def head_pos(self, who, t):
        if who == "JESUS":
            x, y = self.jesus_xy(t)
            return x, y - 115
        return SEATS[who] + self.lean_x(who, t), SHOULDER_Y - 114

    def lean_x(self, who, t):
        return self.lean[who](t) if who in self.lean else 0.0

    def target_xy(self, who, name, t):
        if name in LOOKS:
            return self.head_pos(name, t)
        hx, hy = self.head_pos(who, t)
        return {"SCREEN": (1040, 980), "SEED": SEED_POS, "MUG": (hx + 10, hy + 160), "WATCH": (hx - 30, hy + 260),
                "TABLET": (hx, hy + 330), "NOTE": (hx + 10, hy + 330), "DOOR": (2150, 1700)}.get(name)

    def attention(self, who, t):
        for (a, b, name) in self.overrides.get(who, []):
            if a <= t < b:
                return name
        L = self.tl.current(t)
        if L is None:
            L = self.tl.last_speaker(t)
        if L is None or not L["id"].startswith("b"):
            return "SCREEN" if who != "JESUS" else "CEO"
        if L["who"] == who:
            a = self.address.get(L["id"], "JESUS" if who != "JESUS" else "CEO")
            if a == "SWEEP":
                u = prog(t, L["start"], L["end"])
                order = ["TYLER", "CEO", "CFO", "PAM"]
                return order[min(3, int(u * 4))]
            return a
        if L["who"] in LOOKS:
            if who == "PAM" and self.tl.current(t) is None:
                return "NOTE"
            return L["who"]
        return "CAM"

    def gaze(self, who, t):
        hx, hy = self.head_pos(who, t)

        def g(tt):
            name = self.attention(who, tt)
            if name == "CAM":
                return 0.0, 0.0
            p = self.target_xy(who, name, tt)
            if p is None:
                return 0.0, 0.0
            return p[0] - hx, p[1] - hy
        eye = [g(t - k * 0.04) for k in range(3)]
        head = [g(t - k * 0.07) for k in range(8)]
        ex = sum(e[0] for e in eye) / 3
        ey = sum(e[1] for e in eye) / 3
        hxv = sum(e[0] for e in head) / 8
        gx = clamp(ex / 320, -1, 1) + noise1(t * 1.7, hash(who) % 50) * 0.08
        gy = clamp(ey / 420, -1, 1) + noise1(t * 1.3, hash(who) % 50 + 7) * 0.06
        turn = clamp(hxv / 1300, -0.42, 0.42)
        return gx, gy, turn

    # ------------------------------------------------------------ jesus
    def jesus_xy(self, t):
        """Shoulder point of Jesus (moves when he stands/walks)."""
        x, y = JX, JY
        r = ease_io(prog(t, *self.j_rise))
        y -= 93 * r
        s = ease_io(prog(t, *self.j_step))
        x -= 150 * s
        w = prog(t, *self.j_walk)
        x += 760 * w ** 1.25
        if t < self.j_rise[0]:
            # awkward shuffling on the tiny stool at the start
            x += noise1(t * 0.9, 77) * 6 * (1 - prog(t, self.T("b5"), self.T("b5") + 1))
        return x, y

    # ------------------------------------------------------------ draw
    def face_for(self, who, t):
        f = self.face[who](t)
        gx, gy, turn = self.gaze(who, t)
        f["gx"], f["gy"] = gx, gy
        f["turn"] = clamp(f["turn"] + turn, -0.6, 0.6)
        f["blink"] = self.blink[who](t)
        sp = self.tl.mouth(who, t)
        L = self.tl.speaking(who, t)
        tilt = noise1(t * 0.35, len(who)) * 2.5
        if L:
            tilt += noise1(t * 2.2, len(who) + 3) * 4 * sp
        f["tilt"] += tilt
        return f, sp * 0.9

    def head_bob(self, who, t):
        sp = self.tl.mouth(who, t)
        return -sp * 4 + noise1(t * 0.5, len(who) + 9) * 3

    def draw(self, cv, t):
        self.draw_room(cv, t)
        present = t < self.lights_off
        if present:
            for who in ("PAM", "CFO", "CEO", "TYLER"):
                self.draw_chair(cv, SEATS[who], who == "CEO")
            for who in ("PAM", "CFO", "CEO", "TYLER"):
                self.draw_upper(cv, who, t)
        else:
            for who in ("PAM", "CFO", "CEO", "TYLER"):
                self.draw_chair(cv, SEATS[who], who == "CEO", empty=True)
        self.draw_table(cv, t)
        if present:
            for who in ("PAM", "CFO", "CEO", "TYLER"):
                self.draw_arms_props(cv, who, t)
        self.draw_table_front(cv, t)
        self.draw_seed(cv, t)
        self.draw_stool(cv, t)
        if t < self.j_walk[1] + 0.2:
            self.draw_jesus(cv, t)
        self.draw_door(cv, t)
        if present:
            self.draw_spit(cv, t)
        self.draw_lighting(cv, t)

    # ---- room
    def draw_room(self, cv, t):
        rect(cv, -800, -2000, 3700, 2400, paint("#dfe4e8"))
        rect(cv, -800, 300, 3700, FLOOR - 300,
             paint("#000", shader=lin_grad((0, 300), (0, FLOOR), [("#c3ccd6", 1), ("#9eabb9", 1)])))
        # ceiling band & lights
        rect(cv, -800, 230, 3700, 70, paint("#cfd6dc"))
        for x in (300, 1040, 1780):
            ellipse(cv, x, 300, 150, 14, paint("#fffbe8"))
            cv.drawPath(poly([(x - 150, 300), (x + 150, 300), (x + 420, 1100), (x - 420, 1100)]),
                        paint("#fffbe8", 0.06))
        # wall panels
        for x in range(-700, 2900, 240):
            line(cv, x, 300, x, FLOOR - 200, paint("#8f9cab", 0.35, stroke=3))
        rect(cv, -800, FLOOR - 200, 3700, 200, paint("#7d8a99"))
        rect(cv, -800, FLOOR - 206, 3700, 8, paint("#6b7887"))
        # window with skyline (left)
        self.draw_window(cv, t)
        # logo
        cx = 1040
        cv.save()
        cv.translate(cx - 260, 470)
        cv.rotate(45)
        rrect(cv, -38, -38, 76, 76, 10, paint("#c9a227"))
        cv.restore()
        text(cv, "$", cx - 260, 497, font("black", 70), paint("#1f2b47"), "center")
        text(cv, "MAMMON CAPITAL", cx - 196, 495, font("black", 74), paint("#1f2b47"))
        text(cv, "GROWTH  ·  SYNERGY  ·  MORE", cx - 194, 548, font("bold", 30), paint("#46566e"))
        # clock
        self.draw_clock(cv, t)
        # plant
        self.draw_plant(cv, 70, FLOOR)
        # screen
        x, y, w, h = SCREEN_R
        rrect(cv, x - 24, y - 24, w + 48, h + 48, 18, paint("#1b1f27"))
        rrect(cv, x - 24, y - 24, w + 48, h + 48, 18, paint("#000000", 0.25, blur=20))
        cv.save()
        cv.translate(x, y)
        cv.clipRect(skia.Rect.MakeWH(w, h))
        self.draw_slides(cv, t, w, h)
        cv.restore()
        rect(cv, x + w / 2 - 40, y + h + 24, 80, 40, paint("#2a2f39"))
        # floor
        rect(cv, -800, FLOOR, 3700, 2400,
             paint("#000", shader=lin_grad((0, FLOOR), (0, FLOOR + 1400), [("#56606e", 1), ("#3a414c", 1)])))
        for k in range(1, 12):
            y = FLOOR + k * k * 12
            line(cv, -800, y, 2900, y, paint("#2f353f", 0.35, stroke=2))

    def draw_window(self, cv, t):
        x0, y0, w, h = -560, 620, 520, 900
        dark = clamp((t - self.lights_off) / 0.3)
        rrect(cv, x0 - 16, y0 - 16, w + 32, h + 32, 8, paint("#e8ecef"))
        sky = lin_grad((0, y0), (0, y0 + h), [("#9ccbe8", 1), ("#e7f0f5", 1)])
        cv.save()
        cv.clipRect(skia.Rect.MakeXYWH(x0, y0, w, h))
        rect(cv, x0, y0, w, h, paint("#000", shader=sky))
        r = random.Random(3)
        bx = x0
        while bx < x0 + w:
            bw = r.uniform(50, 110)
            bh = r.uniform(250, 700)
            rect(cv, bx, y0 + h - bh, bw - 6, bh, paint("#7f93a8"))
            for wy in range(int(y0 + h - bh + 20), int(y0 + h), 40):
                for wx in range(int(bx + 10), int(bx + bw - 16), 22):
                    rect(cv, wx, wy, 10, 18, paint("#c9dbe8", 0.6))
            bx += bw
        cv.restore()
        line(cv, x0 + w / 2, y0, x0 + w / 2, y0 + h, paint("#e8ecef", stroke=10))

    def draw_clock(self, cv, t):
        x, y = CLOCK
        circle(cv, x, y + 6, 92, paint("#000", 0.2, blur=8))
        circle(cv, x, y, 90, paint("#2b2f36"))
        circle(cv, x, y, 80, paint("#fbfbf8"))
        for k in range(12):
            a = k / 12 * 2 * math.pi
            line(cv, x + 66 * math.sin(a), y - 66 * math.cos(a), x + 74 * math.sin(a), y - 74 * math.cos(a),
                 paint("#2b2f36", stroke=5 if k % 3 == 0 else 3))
        sec = math.floor(t) + ease_elastic(clamp((t % 1) / 0.25)) if True else t
        mins = 47 + t / 60
        hrs = 4 + mins / 60
        for ang, ln, wd, col in ((hrs / 12, 40, 7, "#2b2f36"), (mins / 60, 60, 5, "#2b2f36"), (sec / 60, 66, 2.5, "#c0392b")):
            a = ang * 2 * math.pi
            line(cv, x, y, x + ln * math.sin(a), y - ln * math.cos(a), paint(col, stroke=wd))
        circle(cv, x, y, 6, paint("#c0392b"))

    def draw_plant(self, cv, x, y):
        rrect(cv, x - 70, y - 160, 140, 160, 14, paint("#e9e4da"))
        rrect(cv, x - 70, y - 160, 140, 24, 8, paint("#d8d2c4"))
        r = random.Random(11)
        for k in range(9):
            a = -math.pi / 2 + r.uniform(-1.0, 1.0)
            ln = r.uniform(180, 330)
            px, py = x + ln * math.cos(a), y - 150 + ln * math.sin(a)
            cv.drawPath(quad_path((x, y - 150), (x + (px - x) * 0.3, py), (px, py)), paint("#2f6b3f", stroke=26))
            cv.drawPath(quad_path((x, y - 150), (x + (px - x) * 0.3, py), (px, py)), paint("#3f8a52", stroke=12))

    def draw_door(self, cv, t):
        x0, x1, y0 = 2090, 2330, 1520
        rect(cv, x0 - 16, y0 - 16, x1 - x0 + 32, FLOOR - y0 + 16, paint("#6b7887"))
        open_ = pulse(t, self.j_walk[0] + 0.9, 0.35, 0.9, 0.4)
        rect(cv, x0, y0, x1 - x0, FLOOR - y0, paint("#2a2f39"))
        dw = (x1 - x0) * (1 - 0.8 * open_)
        rect(cv, x0, y0, dw, FLOOR - y0, paint("#a07a55"))
        rect(cv, x0 + 20, y0 + 30, dw - 40, 300, paint("#8e6a47"))
        circle(cv, x0 + dw - 30, y0 + 470, 10, paint("#d9c27a"))

    # ---- slides
    def draw_slides(self, cv, t, w, h):
        cur, prev, t0 = None, None, 0
        for (ts, name) in self.slides:
            if t >= ts:
                prev, cur, t0 = cur, name, ts
        k = ease_out(prog(t, t0, t0 + 0.35))
        if prev and k < 1:
            self.slide(cv, prev, t, w, h, 1.0)
        cv.save()
        cv.clipRect(skia.Rect.MakeXYWH(0, 0, w * k, h))
        self.slide(cv, cur, t, w, h, k)
        cv.restore()
        dark = clamp((t - self.lights_off) / 0.3)
        if dark > 0:
            rect(cv, 0, 0, w, h, paint("#000000", 0.35 * dark))

    def slide(self, cv, name, t, w, h, k):
        rect(cv, 0, 0, w, h, paint("#f7f9fb"))
        rect(cv, 0, 0, w, 14, paint("#c9a227"))
        F = font
        navy, red, green, grey = "#1f2b47", "#d0392b", "#2e9e5b", "#7a8696"

        def title(s, sub=None):
            text(cv, s, 60, 110, F("black", 64), paint(navy))
            if sub:
                text(cv, sub, 62, 160, F("semi", 32), paint(grey))
        if name == "title":
            rect(cv, 0, 0, w, h, paint("#1f2b47"))
            text(cv, "Q3 GROWTH REVIEW", w / 2, h / 2 - 10, F("black", 92), paint("#ffffff"), "center")
            text(cv, "Mammon Capital  ·  Confidential", w / 2, h / 2 + 60, F("semi", 36), paint("#c9a227"), "center")
        elif name == "agenda":
            title("AGENDA")
            items = ["5. Synergy alignment", "6. Q4 layoffs (celebration)", "7. Kingdom of Heaven division"]
            for i, s in enumerate(items):
                y = 270 + i * 120
                if i == 2:
                    rrect(cv, 40, y - 75, w - 80, 105, 16, paint("#ffe9a8"))
                text(cv, s, 70, y, F("bold" if i == 2 else "medium", 54), paint(navy if i == 2 else grey))
        elif name == "followers":
            title("CORE FOLLOWERS", "Year 3")
            text(cv, "12", 110, 470, F("black", 260), paint(navy))
            x0, y0 = 520, 560
            line(cv, x0, y0, x0 + 640, y0, paint(grey, stroke=4))
            line(cv, x0, y0, x0, 230, paint(grey, stroke=4))
            pts = [(x0 + 20 + i * 60, y0 - 260 + (3 if i % 2 else 0)) for i in range(10)]
            gk = clamp(prog(t, self.Wd("b5", "Twelve") - 0.3, self.Wd("b5", "Twelve") + 1.2))
            n = max(2, int(len(pts) * gk))
            cv.drawPath(poly(pts[:n], False), paint(navy, stroke=8))
            ak = ease_back(prog(t, self.Wd("b5", "one"), self.Wd("b5", "one") + 0.5))
            if ak > 0:
                cv.save()
                cv.translate(x0 + 470, y0 - 330)
                cv.scale(ak, ak)
                rrect(cv, -170, -60, 340, 110, 16, paint(red))
                text(cv, "1 PENDING CHURN", 0, -12, F("black", 36), paint("#fff"), "center")
                text(cv, "(30 pieces of silver)", 0, 30, F("semi", 28), paint("#ffe0dc"), "center")
                cv.restore()
        elif name == "event":
            title("EVENT: LUNCH ON A HILLSIDE")
            rows = [("Attendees", "5,000+", green), ("Ticket price", "FREE", red), ("Revenue", "$0.00", red),
                    ("Cost", "5 loaves, 2 fish", grey), ("Leftovers", "12 baskets", grey)]
            for i, (a, b, c) in enumerate(rows):
                y = 250 + i * 95
                rk = ease_out(prog(t, self.Wd("b8", "Five") + i * 0.35, self.Wd("b8", "Five") + i * 0.35 + 0.3))
                text(cv, a, 80, y, F("semi", 48), paint(grey, rk))
                text(cv, b, w - 80, y, F("black", 52), paint(c, rk), "right")
        elif name == "strategy":
            title("GROWTH STRATEGY")
            text(cv, "???", w / 2, 470, F("black", 260), paint("#d6dbe1"), "center")
        elif name == "seed":
            title("GROWTH STRATEGY", "Proposed by: Jesus")
            circle(cv, w / 2, 420, 6, paint("#6b4e2e"))
            ak = ease_back(prog(t, self.Wd("b12", "smallest"), self.Wd("b12", "smallest") + 0.5))
            cv.save()
            cv.translate(w / 2 + 40, 400)
            cv.scale(ak, ak)
            cv.drawPath(quad_path((0, 0), (80, -40), (170, -60)), paint(red, stroke=5))
            text(cv, "(actual size)", 180, -50, F("bold", 40), paint(red))
            cv.restore()
        elif name == "demo":
            title("TARGET DEMOGRAPHICS")
            parts = [("Fishermen", 0.32, "#3b6fb6"), ("Tax collectors", 0.24, "#c9a227"),
                     ("Lepers", 0.22, "#8a9a5b"), ("Literally everyone else\nnobody wanted", 0.22, "#b4564a")]
            cx, cy, r = 330, 420, 210
            a0 = -90
            gk = ease_out(prog(t, self.T("b15"), self.T("b15") + 1.2))
            for i, (lab, frac, col) in enumerate(parts):
                sweep = frac * 360 * gk
                p = skia.Path()
                p.moveTo(cx, cy)
                p.arcTo(skia.Rect.MakeLTRB(cx - r, cy - r, cx + r, cy + r), a0, sweep, False)
                p.close()
                cv.drawPath(p, paint(col))
                cv.drawPath(p, paint("#ffffff", stroke=4))
                a0 += sweep
                ly = 250 + i * 95
                rect(cv, 620, ly - 30, 34, 34, paint(col))
                for j, s in enumerate(lab.split("\n")):
                    text(cv, s, 670, ly + j * 40, F("bold", 38), paint(navy))
        elif name == "whale":
            title("LOST ACCOUNT: \"RICH YOUNG GUY\"")
            rows = [("Lifetime value", "$$$$$$", green), ("Pitch received", "Sell everything", grey),
                    ("", "Give it to the poor", grey), ("Status", "Walked away sad", red)]
            for i, (a, b, c) in enumerate(rows):
                y = 270 + i * 100
                text(cv, a, 80, y, F("semi", 46), paint(grey))
                text(cv, b, w - 80, y, F("black", 50), paint(c), "right")
        elif name == "temple":
            title("LEGAL: TEMPLE INCIDENT")
            rows = [("Tables flipped", "ALL OF THEM", red), ("Doves released", "40+", grey),
                    ("Vendor complaints", "Pending", grey), ("Whip", "Handmade", grey)]
            for i, (a, b, c) in enumerate(rows):
                y = 270 + i * 100
                text(cv, a, 80, y, F("semi", 46), paint(grey))
                text(cv, b, w - 80, y, F("black", 50), paint(c), "right")
        elif name == "sentiment":
            title("BRAND SENTIMENT")
            x0, y0 = 90, 600
            line(cv, x0, y0, x0 + 1060, y0, paint(grey, stroke=4))
            line(cv, x0, y0, x0, 200, paint(grey, stroke=4))
            gk = ease_io(prog(t, self.T("b23") + 0.2, self.Wd("b23", "followers") + 0.5))
            n = 40
            f_pts = [(x0 + 10 + i * 26, y0 - 60 - 4 * math.sin(i)) for i in range(n)]
            e_pts = [(x0 + 10 + i * 26, y0 - 60 - (i / n) ** 2.4 * 360) for i in range(n)]
            m = max(2, int(n * gk))
            cv.drawPath(poly(f_pts[:m], False), paint(green, stroke=8))
            cv.drawPath(poly(e_pts[:m], False), paint(red, stroke=8))
            text(cv, "Followers", f_pts[m - 1][0] - 10, f_pts[m - 1][1] + 50, F("bold", 34), paint(green), "right")
            text(cv, "Enemies", e_pts[m - 1][0] - 10, e_pts[m - 1][1] - 20, F("bold", 34), paint(red), "right")
        elif name == "kpi":
            title("KEY PERFORMANCE INDICATOR")
            text(cv, "???", w / 2, 500, F("black", 260), paint(red), "center")
        elif name == "doomed":
            title("5-YEAR PROJECTION: KINGDOM OF HEAVEN")
            x0, y0 = 90, 620
            line(cv, x0, y0, x0 + 1060, y0, paint(grey, stroke=4))
            pts = [(x0 + 10 + i * 50, 260 + (i / 20) ** 1.5 * 320 + 10 * math.sin(i * 1.7)) for i in range(21)]
            cv.drawPath(poly(pts, False), paint(red, stroke=8))
            st = self.Wd("b32", "doomed")
            sk = prog(t, st - 0.05, st + 0.18)
            if sk > 0:
                s = lerp(2.4, 1.0, ease_in(sk))
                cv.save()
                cv.translate(w / 2, h / 2 + 30)
                cv.rotate(-12)
                cv.scale(s, s)
                a = clamp(sk * 2)
                rrect(cv, -330, -95, 660, 190, 22, paint(red, a, stroke=16))
                text(cv, "DOOMED", 0, 52, F("black", 150), paint(red, a), "center")
                cv.restore()

    # ---- furniture
    def draw_chair(self, cv, x, big=False, empty=False):
        top = 1430 if big else 1480
        rrect(cv, x - 128, top, 256, TABLE_BACK - top + 40, 60, paint("#1c1d22"))
        rrect(cv, x - 112, top + 18, 224, TABLE_BACK - top, 50, paint("#2a2c33"))
        for k in range(3):
            line(cv, x - 60 + k * 60, top + 60, x - 60 + k * 60, TABLE_BACK - 20, paint("#1c1d22", 0.6, stroke=4))
        if empty:
            rrect(cv, x - 140, 1760, 280, 90, 30, paint("#1c1d22"))

    def draw_table(self, cv, t):
        p = poly([(TABLE_L + 40, TABLE_BACK), (TABLE_R - 40, TABLE_BACK), (TABLE_R, TABLE_FRONT), (TABLE_L, TABLE_FRONT)])
        cv.drawPath(p, paint("#000", shader=lin_grad((0, TABLE_BACK), (0, TABLE_FRONT),
                                                      [("#6b4a35", 1), ("#835c42", 1)])))
        cv.drawPath(poly([(TABLE_L + 60, TABLE_BACK + 30), (TABLE_R - 300, TABLE_BACK + 30),
                          (TABLE_R - 340, TABLE_BACK + 50), (TABLE_L + 50, TABLE_BACK + 50)]), paint("#ffffff", 0.08))

    def draw_table_front(self, cv, t):
        rect(cv, TABLE_L, TABLE_FRONT, TABLE_R - TABLE_L, 22, paint("#5a3d2b"))
        rect(cv, TABLE_L + 30, TABLE_FRONT + 22, TABLE_R - TABLE_L - 60, PANEL_BOT - TABLE_FRONT - 22,
             paint("#000", shader=lin_grad((0, TABLE_FRONT), (0, PANEL_BOT), [("#4a3324", 1), ("#3a281c", 1)])))
        ellipse(cv, (TABLE_L + TABLE_R) / 2, FLOOR + 20, (TABLE_R - TABLE_L) / 2 + 40, 40, paint("#000", 0.25, blur=14))
        for x in (TABLE_L + 30, TABLE_R - 70):
            rect(cv, x, PANEL_BOT, 40, FLOOR - PANEL_BOT, paint("#3a281c"))
        # nameplates
        names = {"PAM": ("PAM", "Intern"), "CFO": ("M. LEDGER", "CFO"), "CEO": ("R. GAINS", "CEO"),
                 "TYLER": ("TYLER", "Head of Growth")}
        for who, x in SEATS.items():
            rrect(cv, x - 110, TABLE_FRONT - 52, 220, 62, 8, paint("#1b1f27"))
            rrect(cv, x - 104, TABLE_FRONT - 46, 208, 50, 6, paint("#c9a227"))
            text(cv, names[who][0], x, TABLE_FRONT - 22, font("black", 24), paint("#1b1f27"), "center")
            text(cv, names[who][1], x, TABLE_FRONT - 0, font("semi", 18), paint("#1b1f27"), "center")

    def draw_stool(self, cv, t):
        x, y = JX, JY + 250
        cv.drawPath(poly([(x - 100, y + 20), (x - 125, FLOOR)], False), paint("#7a5432", stroke=16))
        cv.drawPath(poly([(x + 100, y + 20), (x + 125, FLOOR)], False), paint("#7a5432", stroke=16))
        line(cv, x - 112, y + 160, x + 112, y + 160, paint("#6a4528", stroke=10))
        rrect(cv, x - 115, y - 10, 230, 34, 10, paint("#9a6b40"))
        rrect(cv, x - 115, y - 10, 230, 12, 6, paint("#b5814f"))
        ellipse(cv, x, FLOOR + 10, 170, 22, paint("#000", 0.25, blur=10))

    # ---- board members
    def draw_upper(self, cv, who, t):
        L = LOOKS[who]
        x = SEATS[who] + self.lean_x(who, t)
        y = SHOULDER_Y + noise1(t * 0.3, len(who)) * 2
        f, sp = self.face_for(who, t)
        cv.save()
        cv.translate(x, y)
        cv.rotate(self.lean_x(who, t) * -0.12)
        draw_torso(cv, L, t, math.sin(t * 1.6 + len(who)))
        draw_neck(cv, L)
        behind = any(a <= t < b for a, b in self.behind_head.get(who, []))
        if behind:
            self._arms(cv, who, t, L)
        cv.save()
        cv.translate(f["turn"] * 6, -112 + self.head_bob(who, t))
        draw_head(cv, L, f, t, sp)
        cv.restore()
        cv.restore()

    def _arms(self, cv, who, t, L):
        hl, hr = self.hands[who](t)
        kl, kr = self.hand_kind[who](t)
        if who == "PAM" and self._writing(t):
            hr = (hr[0] + math.sin(t * 19) * 5 + noise1(t * 3, 5) * 6, hr[1] + math.cos(t * 23) * 3)
        if who == "CFO":
            hr = (hr[0] + (math.sin(t * 31) * 3 if self._typing(t) else 0), hr[1])
            hl = (hl[0] + (math.cos(t * 27) * 3 if self._typing(t) else 0), hl[1])
        if who == "CEO" and self.T("b29") - 0.1 < t < self.E("b29") + 0.2:
            hl = (hl[0] + math.sin(t * 9) * 4, hl[1] + math.cos(t * 9) * 4)
            hr = (hr[0] - math.sin(t * 9) * 4, hr[1] + math.cos(t * 9) * 4)
        col = arm_color(L)
        draw_arm(cv, L, -1, hl, kl, 0, col)
        draw_arm(cv, L, 1, hr, kr, 0, col)
        return hl, hr

    def _writing(self, t):
        busy = self.tl.current(t)
        return busy is not None and busy["who"] in ("CEO", "CFO", "TYLER") and not (self.T("b33") - 0.5 < t)

    def _typing(self, t):
        return self.T("b32") < t < self.E("b32") + 0.3

    def draw_arms_props(self, cv, who, t):
        L = LOOKS[who]
        x = SEATS[who] + self.lean_x(who, t)
        y = SHOULDER_Y
        cv.save()
        cv.translate(x, y)
        # props under hands
        if who == "CFO":
            rrect(cv, -95, 160, 190, 40, 6, paint("#2a2f39"))
            rrect(cv, -88, 164, 176, 30, 4, paint("#7fb2e5", 0.9))
        if who == "PAM":
            cv.save()
            cv.rotate(-6)
            rect(cv, -60, 158, 130, 52, paint("#fff7c2"))
            for k in range(4):
                line(cv, -50, 170 + k * 10, 50 + (k * 7) % 15, 170 + k * 10, paint("#7a8696", 0.6, stroke=2))
            cv.restore()
        if who == "TYLER":
            rrect(cv, 85, 120, 34, 66, 8, paint("#121212"))
            rrect(cv, 85, 132, 34, 30, 2, paint("#9cff57"))
            text(cv, "GRIND", 102, 152, font("black", 10), paint("#121212"), "center")
            rrect(cv, -110, 172, 46, 24, 5, paint("#111111"))
        behind = any(a <= t < b for a, b in self.behind_head.get(who, []))
        hl = hr = None
        if not behind:
            hl, hr = self._arms(cv, who, t, L)
        if who == "CEO":
            # coffee mug follows the right hand
            mx, my = hr
            rrect(cv, mx - 6, my - 48, 48, 58, 8, paint("#fafafa"))
            cv.drawPath(quad_path((mx + 42, my - 38), (mx + 64, my - 20), (mx + 42, my - 2)), paint("#fafafa", stroke=8))
            text(cv, "#1 BOSS", mx + 18, my - 15, font("black", 11), paint("#c0392b"), "center")
            draw_hand(cv, L, mx - 2, my - 14, "fist", 1)
            # gold watch
            wx, wy = hl
            rrect(cv, wx - 20, wy - 40, 40, 16, 5, paint("#d4af37"))
            circle(cv, wx, wy - 32, 11, paint("#f6e7a8"))
            circle(cv, wx, wy - 32, 11, paint("#b8941f", stroke=3))
        cv.restore()

    def draw_spit(self, cv, t):
        t0 = self.T("spit")
        if not (t0 < t < t0 + 1.4):
            return
        hx, hy = self.head_pos("CEO", t)
        r = random.Random(5)
        dt = t - t0
        for i in range(70):
            a = r.uniform(-0.9, 0.9) - 1.57
            v = r.uniform(300, 1100)
            delay = r.uniform(0, 0.15)
            d = dt - delay
            if d < 0:
                continue
            x = hx + 12 + math.cos(a) * v * d * 0.7 + r.uniform(-1, 1) * v * d * 0.5
            y = hy + 45 + math.sin(a) * v * d * 0.35 + 1200 * d * d
            s = r.uniform(3, 9)
            circle(cv, x, y, s, paint("#6b4423", clamp(1.4 - dt)))

    def draw_seed(self, cv, t):
        if t < self.j_seed:
            return
        x, y = SEED_POS
        glow = 0.0
        if t > self.lights_off:
            glow = 0.5 + 0.2 * math.sin(t * 3)
        if glow:
            circle(cv, x, y - 4, 60, paint("#ffe9a0", 0.35 * glow, blur=20))
        ellipse(cv, x, y + 4, 12, 4, paint("#000", 0.3, blur=2))
        ellipse(cv, x, y - 3, 8, 6.5, paint("#7a5530"))
        ellipse(cv, x - 2, y - 5, 3, 2, paint("#c9a070"))
        k = pulse(t, self.j_seed, 0.1, 0.1, 0.6)
        if k > 0:
            for a in range(4):
                ang = a * math.pi / 2 + 0.4
                line(cv, x + math.cos(ang) * 16, y - 4 + math.sin(ang) * 16, x + math.cos(ang) * 30,
                     y - 4 + math.sin(ang) * 30, paint("#fff3b0", k, stroke=4))

    # ---- Jesus
    def draw_jesus(self, cv, t):
        L = JESUS
        x, y = self.jesus_xy(t)
        f, sp = self.face_for("JESUS", t)
        stand = ease_io(prog(t, *self.j_rise))
        walking = prog(t, *self.j_walk)
        stepping = prog(t, *self.j_step)
        moving = (0 < walking < 1) or (0 < stepping < 1)
        phase = (t - self.j_walk[0]) * 7 if walking > 0 else (t - self.j_step[0]) * 7
        bob = abs(math.sin(phase)) * 8 if moving else 0
        if walking > 0:
            f["turn"] = 0.45
            f["gx"] = 0.8
        cv.save()
        cv.translate(x, y - bob)
        # warm presence
        circle(cv, 0, 60, 330, paint("#ffd98a", 0.10, blur=60))
        # legs / robe below the waist
        robe = L.c1
        if stand < 0.5:
            # seated: lap toward the viewer, shins down to the floor
            fl = FLOOR - y
            cv.drawPath(poly([(-104, 222), (104, 222), (120, 285), (96, fl - 30), (-96, fl - 30), (-120, 285)]),
                        paint(shade(robe, -0.08)))
            for s_ in (-1, 1):
                ellipse(cv, s_ * 58, 262, 64, 40, paint(shade(robe, 0.04)))
                line(cv, s_ * 58, 300, s_ * 62, fl - 36, paint(shade(robe, -0.2), 0.5, stroke=3))
            line(cv, 0, 290, 0, fl - 34, paint(shade(robe, -0.25), 0.7, stroke=4))
            for s in (-1, 1):
                self._sandal(cv, s * 46, fl - 12, s)
        else:
            fl = FLOOR - y + bob
            sw = math.sin(phase) * 22 if moving else 0
            cv.drawPath(poly([(-100, 230), (100, 230), (118, fl - 40), (-118, fl - 40)]), paint(shade(robe, -0.06)))
            for k in (-40, 30):
                line(cv, k, 300, k * 1.2, fl - 50, paint(shade(robe, -0.15), 0.5, stroke=3))
            self._sandal(cv, -44 + sw, fl - 14, -1)
            self._sandal(cv, 44 - sw, fl - 14, 1)
        draw_torso(cv, L, t, math.sin(t * 1.4))
        draw_neck(cv, L)
        cv.save()
        cv.translate(f["turn"] * 6, -112 + self.head_bob("JESUS", t) * 0.7)
        draw_head(cv, L, f, t, sp)
        cv.restore()
        # arms
        hl, hr = self.jhands(t)
        if stand > 0:
            standing = ((-70, 250), (70, 250))
            hl = lerp2(hl, standing[0], stand)
            hr = lerp2(hr, standing[1], stand)
            reach = pulse(t, self.j_reach[0], 0.35, 0.15, 0.35)
            sx, sy = SEED_POS[0] - x, SEED_POS[1] - (y - bob) - 14
            hr_reach = (sx, sy)
            hl = lerp2(hl, (sx, sy), reach)
            if moving:
                hl = (hl[0] - math.sin(phase) * 16, hl[1])
                hr = (hr[0] + math.sin(phase) * 16, hr[1])
        kl, kr = self.jkind(t)
        wave = self.Wd("b2", "Thanks") + 0.4 < t < self.E("b2") + 0.5
        draw_arm(cv, L, -1, hl, kl, 0, L.c1, width=46)
        draw_arm(cv, L, 1, hr, kr, math.sin(t * 12) * 18 if wave else 0, L.c1, width=46)
        # name sticker
        cv.save()
        cv.translate(42, 118)
        cv.rotate(-6)
        rrect(cv, -40, -28, 80, 56, 6, paint("#ffffff"))
        rect(cv, -40, -28, 80, 19, paint("#d0392b"))
        text(cv, "HELLO my name is", 0, -14, font("black", 8.5), paint("#ffffff"), "center")
        text(cv, "Jesus", 0, 18, font("hand", 24), paint("#1b2a4a"), "center")
        cv.restore()
        cv.restore()

    def _sandal(self, cv, x, y, s):
        ellipse(cv, x, y + 4, 34, 13, paint("#6b4423"))
        ellipse(cv, x, y - 2, 26, 12, paint(JESUS.skin))
        line(cv, x - 22, y - 2, x + 22, y - 2, paint("#6b4423", stroke=6))

    # ---- lighting
    def draw_lighting(self, cv, t):
        d = clamp((t - self.lights_off) / 0.12)
        if d > 0:
            rect(cv, -2000, -3000, 6000, 8000, paint("#0a1022", 0.82 * d))
            x, y = SEED_POS
            circle(cv, x, y - 10, 220, paint("#ffe7a0", 0.12 * d, blur=60))
            # moonbeam from the window side
            cv.drawPath(poly([(-500, 600), (-100, 600), (x + 120, y + 30), (x - 120, y + 30)]),
                        paint("#9fb8ff", 0.06 * d))
