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
SHOTS["JESUS_S"] = (JX - 10, 1790, 700)
SHOTS["JESUS_SC"] = (JX - 10, 1680, 470)
SHOTS["CLOCK"] = (CLOCK[0] - 60, CLOCK[1] + 120, 520)


class Board:
    def __init__(self, tl):
        self.tl = tl
        T, E, Wd = tl.s, tl.e, tl.wfind
        self.T, self.E, self.Wd = T, E, Wd
        self.blink = {k: Blinker(i * 13 + 3) for i, k in enumerate(LOOKS)}
        self.t_start = E("title") - 0.3
        self.lights_off = E("b36") + 0.55

        # ---------------- expressions
        F = FaceTrack
        aw = expr("awkward", sweat=0.0)
        self.face = {
            "CEO": F([(0, "tired"), (T("b1"), "stern"), (Wd("b2", "Thanks"), "smile"), (T("b3") + 0.4, "confused"),
                      (T("b4"), "deadpan"), (T("b5"), "annoyed"), (T("b7"), "smug"), (Wd("b7", "Where"), "skeptical"),
                      (T("b9"), "annoyed"), (T("b10"), "stern"), (Wd("b11", "birds"), "confused"),
                      (T("silence1"), "deadpan"), (T("b12"), "annoyed"), (T("b14"), "tired"), (T("b16"), "smug"),
                      (T("b18"), "neutral"), (Wd("b18", "advertisers") - 1.0, expr("neutral", lid=0.3)),
                      (T("spit"), "shocked", 0.1), (T("b19"), "furious"), (T("b20"), "angry"),
                      (Wd("b20", "God"), "nervous"), (T("b21"), "stern"), (Wd("b22", "attacking"), "confused"),
                      (T("b23"), "skeptical"), (T("b25"), "annoyed"), (T("b27") - 0.3, "furious", 0.15),
                      (T("b28"), "angry"), (Wd("b28", "soul"), "confused"), (T("silence2") + 0.5, "deadpan"),
                      (T("b30"), "stern"), (Wd("b30", "suppressed"), "smug"), (T("rise"), "skeptical"),
                      (Wd("b32", "Love"), expr("nervous", sweat=0.0)), (T("exit") + 1.0, "nervous"),
                      (T("b35"), "annoyed"), (T("b36"), "smug")]),
            "CFO": F([(0, "neutral"), (T("b4"), "smile"), (T("b5"), "stern"), (T("b6"), "skeptical"),
                      (T("b7"), "neutral"), (T("b8"), "deadpan"), (T("b11"), "skeptical"), (T("silence1"), "deadpan"),
                      (T("b14"), "stern"), (T("b15"), "skeptical"), (T("b16"), "annoyed"), (T("b18"), "stern"),
                      (T("spit"), "wince", 0.1), (T("b19"), "annoyed"), (T("b20"), "deadpan"), (T("b21"), "stern"),
                      (T("b22"), "confused"), (Wd("b22", "hope"), expr("sad", lid=0.2), 1.0), (T("b23"), "skeptical"),
                      (T("b24"), expr("sad", glisten=0.3)), (T("b25"), "neutral"), (T("b26"), "confused"),
                      (T("b27"), "neutral"), (T("b28"), "confused"), (T("silence2"), "deadpan"), (T("b30"), "smug"),
                      (Wd("b32", "Love"), "nervous"), (T("b34"), "deadpan"), (T("b35"), "annoyed")]),
            "TYLER": F([(0, "smug"), (T("b3"), "confused"), (T("b4"), "smug"), (T("b7"), "excited"),
                        (Wd("b7", "Where"), "annoyed"), (T("b8"), "confused"), (T("b10"), "smug"),
                        (T("b11") + 2, "confused"), (T("b14"), "smug"), (T("b16"), "excited"),
                        (Wd("b16", "bless"), "confused"), (Wd("b16", "Do"), "annoyed"), (T("b17"), "confused"),
                        (T("spit"), "wince", 0.1), (T("b19"), "shocked"), (T("b20"), "smug"), (T("b21"), "neutral"),
                        (T("b22"), "confused"), (T("b23"), "nervous"), (T("b25"), "smug"), (T("b26"), "confused"),
                        (T("b27"), "shocked"), (T("silence2"), "awkward"), (T("b30"), "smug"),
                        (Wd("b32", "Love"), expr("nervous", sweat=0.0)), (T("exit") + 1.0, "nervous"),
                        (T("b35"), "nervous")]),
            "PAM": F([(0, "neutral"), (T("b3"), "smile"), (T("b4"), "neutral"), (T("b6"), "smile"), (T("b7"), "neutral"),
                      (T("b8"), "kind"), (T("b9"), "neutral"), (T("b11") + 1.5, "hopeful", 1.0), (T("silence1") + 0.6, aw),
                      (T("b13"), "nervous"), (T("b15"), "kind"), (T("b16"), "neutral"), (T("b17"), "smile"),
                      (T("spit"), "shocked", 0.1), (T("b20"), "smile"), (T("b21"), "sad"),
                      (T("b22"), expr("hopeful", glisten=0.9), 0.8), (T("b23"), "neutral"), (T("b26"), "kind"),
                      (T("b27"), "nervous"), (T("b28"), expr("compassion", glisten=0.9), 0.8), (T("silence2"), "sad"),
                      (T("b30"), "sad"), (T("b32"), expr("hopeful", glisten=1.0), 0.8), (T("exit") + 1.5, "sad"),
                      (T("b35"), "hopeful"), (T("b36") + 1.0, "smile")]),
            "JESUS": F([(0, "serene"), (T("b1"), aw), (Wd("b2", "Thanks"), "kind"), (T("b4"), aw), (T("b5"), "serene"),
                        (T("b6"), "kind"), (T("b7"), "serene"), (Wd("b7", "Where"), "smile"), (T("b8"), "kind"),
                        (T("b9") + 0.4, "smile"), (T("b10"), "serene"), (T("b11"), "kind"),
                        (Wd("b11", "birds"), expr("hopeful", glisten=0.6)), (T("silence1") + 0.8, aw),
                        (T("b12") + 0.4, "smile"), (T("b14"), "compassion"), (T("b15"), "kind"), (T("b16"), "serene"),
                        (T("b17"), "kind"), (T("b18"), "serene"), (T("b20"), "stern"), (T("b21"), "compassion"),
                        (T("b22"), expr("hopeful", glisten=0.7)), (T("b23"), "smile"), (T("b25"), "compassion"),
                        (T("b26"), "kind"), (T("b27"), "serene"), (T("b28"), expr("compassion", glisten=0.8)),
                        (T("b29") + 0.3, "smile"), (T("b30"), "kind"), (Wd("b30", "suppressed"), "compassion"),
                        (T("b31"), "smile"), (T("rise"), "kind"), (T("b32"), expr("kind", glisten=0.6))]),
        }

        # ---------------- who each speaker addresses
        self.address = {"b1": "CAM", "b3": "CEO", "b4": "CFO", "b5": "CEO", "b6": "CFO", "b8": "TYLER",
                        "b12": "CFO", "b13": "TYLER", "b15": "CFO", "b17": "TYLER", "b20": "CEO", "b22": "CFO",
                        "b23": "CFO", "b24": "TYLER", "b26": "TYLER", "b28": "CEO", "b29": "JESUS", "b30": "JESUS",
                        "b31": "JESUS", "b32": "SWEEP", "b33": "CFO", "b34": "TYLER", "b35": "CEO", "b36": "PAM"}
        self.overrides = {
            "CEO": [(Wd("b18", "advertisers") - 1.0, T("spit"), "MUG"), (Wd("b30", "suppressed") - 0.5, Wd("b30", "suppressed") + 0.5, "MUG"),
                    (T("exit"), T("b33"), "JESUS"), (T("b36") - 0.2, E("b36") + 2, "SEED")],
            "CFO": [(T("b5") + 0.5, Wd("b5", "Engagement") + 0.8, "SCREEN"), (T("b14"), Wd("b14", "lonely"), "SCREEN"),
                    (T("b21"), Wd("b21", "Trolls"), "SCREEN"), (T("b34"), E("b34"), "TABLET"),
                    (T("exit"), T("b33"), "JESUS"), (T("silence1"), T("silence1") + 1.2, "CEO"),
                    (T("silence1") + 1.2, E("silence1"), "CAM")],
            "TYLER": [(Wd("b7", "paywall"), Wd("b7", "Where"), "SCREEN"), (T("exit"), T("b33"), "JESUS"),
                      (T("silence1"), T("silence1") + 1.0, "JESUS"), (T("silence1") + 1.0, E("silence1"), "CEO"),
                      (T("silence2"), E("silence2"), "CEO"), (T("b31"), E("b31") + 0.3, "DOOR")],
            "PAM": [(T("b35"), E("b35"), "CEO"), (E("b35"), E("b36") + 2, "SEED"), (T("exit"), T("b33"), "JESUS"),
                    (T("silence1"), T("silence1") + 1.4, "CFO"), (T("silence1") + 1.4, E("silence1"), "CAM")],
            "JESUS": [(T("b1"), T("b2"), "SCREEN"), (T("silence1"), T("silence1") + 1.0, "CEO"),
                      (T("silence1") + 1.0, E("silence1"), "CAM"), (T("silence2"), E("silence2"), "CEO"),
                      (T("rise") + 0.6, E("rise"), "ROBE"), (E("b32") + 0.2, E("exit"), "SEED")],
        }

        # ---------------- hands (body coords)
        rest = ((-62, 186), (66, 182))
        sup = Wd("b30", "suppressed")
        self.stamp_win = (Wd("b30", "decision") - 0.2, E("b30") + 0.6)
        self.hands = {
            "CEO": Keys([(0, rest), (T("b10"), ((-20, 112), (20, 112)), 0.4), (E("b10") + 0.3, rest, 0.4),
                         (Wd("b18", "advertisers") - 1.0, ((-62, 186), (22, -52)), 0.5), (T("spit") + 0.25, rest, 0.35),
                         (T("b27") - 0.45, ((-70, 30), (70, 30)), 0.25), (T("b27") - 0.08, ((-62, 186), (62, 186)), 0.08),
                         (E("b27") + 0.2, rest, 0.4),
                         (Wd("b30", "decision"), ((-62, 186), (60, 160)), 0.3),
                         (sup - 0.55, ((-62, 186), (66, -10)), 0.3), (sup - 0.06, ((-62, 186), (48, 176)), 0.07),
                         (E("b30") + 0.6, rest, 0.4)]),
            "CFO": Keys([(0, ((-50, 186), (58, 186)))]),
            "TYLER": Keys([(0, ((-62, 186), (64, 186))), (Wd("b7", "paywall") - 0.2, ((-112, 40), (112, 40)), 0.25),
                           (Wd("b7", "Where"), ((-62, 186), (64, 186)), 0.35),
                           (T("b14"), ((-55, -125), (55, -125)), 0.5), (T("b15"), ((-62, 186), (64, 186)), 0.4),
                           (T("b23") - 0.3, ((-62, 186), (42, -54)), 0.3), (E("b23") + 0.3, ((-62, 186), (64, 186)), 0.3),
                           (T("b31") - 0.1, ((-62, 186), (175, 10)), 0.3), (E("b31") + 0.4, ((-62, 186), (64, 186)), 0.4),
                           (T("b33") - 0.3, ((-62, 186), (42, -54)), 0.3), (E("b33") + 0.3, ((-62, 186), (64, 186)), 0.3)]),
            "PAM": Keys([(0, ((-46, 192), (44, 186))), (T("b35") - 0.2, ((-46, 192), (128, -150)), 0.35),
                         (E("b35") + 0.3, ((-46, 192), (44, 186)), 0.4)]),
        }
        self.hand_kind = {
            "CEO": lambda t: ("fist", "fist"),
            "TYLER": lambda t: ("open", "open") if (Wd("b7", "paywall") - 0.3 < t < Wd("b7", "Where")) else
            (("fist", "point") if T("b31") - 0.1 < t < E("b31") + 0.4 else
             (("fist", "open") if (T("b23") - 0.3 < t < E("b23") + 0.3 or T("b33") - 0.3 < t < E("b33") + 0.3) else ("fist", "fist"))),
            "PAM": lambda t: ("fist", "open") if T("b35") - 0.1 < t < E("b35") + 0.3 else ("fist", "fist"),
            "CFO": lambda t: ("fist", "fist"),
        }
        self.behind_head = {"TYLER": [(T("b14") + 0.25, T("b15") - 0.1)]}
        self.lean = {
            "TYLER": Keys([(0, 0.0), (T("b23") - 0.3, -38.0, 0.3), (E("b23") + 0.3, 0.0, 0.3),
                           (T("b33") - 0.3, -38.0, 0.3), (E("b33") + 0.3, 0.0, 0.3)]),
        }
        # Jesus hands (seated, relative to shoulder point)
        jr = ((-66, 250), (66, 250))
        one = ((-66, 250), (92, 150))
        both = ((-96, 150), (96, 150))
        heart = ((-66, 250), (22, 105))
        g = []
        for lid, pose, wd in (("b6", one, None), ("b8", both, None), ("b11", one, "mustard"), ("b15", one, "doctor"),
                              ("b17", both, None), ("b20", one, None), ("b22", heart, None), ("b26", both, None),
                              ("b28", one, "world")):
            t0 = (Wd(lid, wd) - 0.4) if wd else T(lid) + 0.1
            g += [(t0, pose, 0.5), (E(lid) + 0.4, jr, 0.6)]
        g.insert(4, (Wd("b11", "tree"), both, 0.6))
        self.jhands = Keys([(0, jr), (Wd("b2", "Thanks") + 0.2, ((-74, 262), (98, 40)), 0.3), (E("b2") + 0.7, jr, 0.4)] + g)
        self.jkind = lambda t: ("open", "open")
        # standing hands (after rising)
        st = ((-70, 250), (70, 250))
        self.pat = (T("rise") + 0.7, E("rise") - 0.05)
        self.jstand = Keys([(0, st), (Wd("b32", "Love") - 0.3, ((-112, 140), (112, 140)), 0.5),
                            (Wd("b32", "Goodbye") - 0.2, ((-70, 250), (98, 40)), 0.3), (E("b32") + 0.15, st, 0.3)])
        self.jwave = (Wd("b32", "Goodbye") - 0.05, E("b32") + 0.15)
        self.aura0 = Wd("b32", "Love")

        # ---------------- slides
        self.slides = [(0, "title"), (Wd("b1", "Next"), "agenda"), (T("b5") - 0.2, "metrics"),
                       (Wd("b7", "paywall") - 0.3, "funnel"), (Wd("b10", "What"), "strategy"),
                       (Wd("b11", "smallest") - 0.2, "seed"), (T("b14") - 0.2, "audience"),
                       (Wd("b16", "Do") - 0.3, "trolls"), (T("b18") - 0.2, "brandsafety"),
                       (T("b21") - 0.1, "sentiment"), (Wd("b25", "flagged") - 0.3, "flagged"),
                       (Wd("b27", "one") - 0.2, "kpi"), (T("b30"), "decision")]
        self.stamp_t = sup

        # ---------------- camera
        self.shots = [
            (self.t_start, "WIDE", 0), (Wd("b1", "Next") - 0.2, "SCREEN", 1.3),
            (T("b2"), "CEO_M", 0), (T("b3") - 0.15, "JESUS_M", 0), (T("b4") - 0.1, "CEO_M", 0),
            (T("b5") - 0.2, "SCREEN", 0), (Wd("b5", "Engagement") + 0.3, "CFO_C", 0), (T("b6") - 0.2, "JESUS_C", 0),
            (T("b7") - 0.1, "TYLER_M", 0), (Wd("b7", "paywall") - 0.1, "SCREEN", 0), (Wd("b7", "Where") - 0.1, "TYLER_C", 0),
            (T("b8") - 0.2, "JESUS_M", 0), (T("b9") - 0.1, "TYLER_M", 0), (T("b10") - 0.1, "CEO_C", 0),
            (T("b11") - 0.2, "JESUS_M", 0), (Wd("b11", "smallest") - 0.1, "SCREEN", 0),
            (Wd("b11", "But"), "JESUS_M", 0), (Wd("b11", "But") + 0.05, "JESUS_C", 5.0),
            (T("silence1"), "WIDE", 0), (T("silence1") + 1.0, "PAM_C", 0), (T("silence1") + 1.8, "BOARD3", 0),
            (T("b12") - 0.1, "TYLER_M", 0), (T("b13") - 0.1, "CFO_M", 0), (T("b14") + 0.1, "SCREEN", 0),
            (Wd("b14", "These") - 0.1, "CFO_C", 0), (T("b15") - 0.15, "JESUS_M", 0),
            (T("b16") - 0.1, "TYLER_M", 0), (Wd("b16", "Do") - 0.1, "SCREEN", 0), (T("b17") - 0.15, "JESUS_C", 0),
            (T("b18") - 0.1, "SCREEN", 0), (Wd("b18", "You") - 0.1, "CEO_M", 0), (T("spit"), "CEO_C", 0),
            (T("b20") - 0.1, "JESUS_M", 0), (T("b20") + 0.05, "JESUS_C", 4.5),
            (T("b21") - 0.1, "CFO_M", 0), (Wd("b21", "enemies") - 0.1, "SCREEN", 0), (Wd("b21", "What") - 0.1, "CFO_C", 0),
            (T("b22") - 0.2, "JESUS_M", 0), (T("b22") + 0.05, "JESUS_C", 9.0),
            (T("b23") - 0.2, "CFO_TY", 0), (T("b24") - 0.1, "CFO_C", 0),
            (T("b25") - 0.1, "TYLER_M", 0), (Wd("b25", "flagged") - 0.1, "SCREEN", 0), (T("b26") - 0.2, "JESUS_M", 0),
            (T("b27") - 0.5, "CEO_M", 0), (Wd("b27", "one") - 0.1, "CEO_C", 0),
            (T("b28") - 0.2, "JESUS_M", 0), (T("b28") + 0.05, "JESUS_C", 4.5),
            (T("silence2"), "CEO_C", 0), (T("silence2") + 1.1, "CLOCK", 0), (E("silence2") - 0.4, "CEO_C", 0),
            (T("b30") - 0.1, "CEO_M", 0), (sup - 0.1, "SCREEN", 0), (Wd("b30", "given") - 0.2, "CEO_M", 0),
            (T("b31") - 0.1, "TYLER_M", 0), (T("rise") - 0.05, "JESUS_M", 0), (T("b32") - 0.1, "JESUS_S", 0),
            (T("b32"), "JESUS_SC", 5.0), (E("b32") + 0.1, "RIGHT", 0),
            (T("b33") - 0.15, "CFO_TY", 0), (T("b34") - 0.1, "CFO_C", 0), (T("b35") - 0.15, "PAM_C", 0),
            (T("b36") - 0.1, "CEO_M", 0), (E("b36") + 0.2, "SEED_W", 0), (E("b36") + 0.3, "SEED", 2.2),
        ]

        # Jesus' exit choreography
        e0 = E("b32")
        self.j_rise = (T("rise") + 0.05, T("rise") + 0.65)
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
                "TABLET": (hx, hy + 330), "NOTE": (hx + 10, hy + 330), "DOOR": (2150, 1700), "ROBE": (hx, hy + 420)}.get(name)

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
        text(cv, "MAMMON MEDIA", cx - 196, 495, font("black", 74), paint("#1f2b47"))
        text(cv, "ENGAGEMENT  ·  RETENTION  ·  MORE", cx - 194, 548, font("bold", 30), paint("#46566e"))
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
        def rows(items, y0=270, dy=100, t0=None):
            for i, (a, b, c) in enumerate(items):
                rk = 1.0 if t0 is None else ease_out(prog(t, t0 + i * 0.35, t0 + i * 0.35 + 0.3))
                y = y0 + i * dy
                text(cv, a, 70, y, F("semi", 44), paint(grey, rk))
                text(cv, b, w - 70, y, F("black", 48), paint(c, rk), "right")

        def stamp(word, ts, col=red, size=150, box=(660, 190)):
            sk = prog(t, ts - 0.05, ts + 0.18)
            if sk > 0:
                s_ = lerp(2.4, 1.0, ease_in(sk))
                cv.save()
                cv.translate(w / 2, h / 2 + 40)
                cv.rotate(-12)
                cv.scale(s_, s_)
                a_ = clamp(sk * 2)
                rrect(cv, -box[0] / 2, -box[1] / 2, box[0], box[1], 22, paint(col, a_, stroke=16))
                text(cv, word, 0, size * 0.35, F("black", size), paint(col, a_), "center")
                cv.restore()

        if name == "title":
            rect(cv, 0, 0, w, h, paint("#1f2b47"))
            text(cv, "CREATOR ACCOUNT REVIEW", w / 2, h / 2 - 10, F("black", 80), paint("#ffffff"), "center")
            text(cv, "Mammon Media  ·  Confidential", w / 2, h / 2 + 60, F("semi", 36), paint("#c9a227"), "center")
        elif name == "agenda":
            title("AGENDA")
            items = ["5. Rage-bait rollout", "6. Ad load +40%", "7. Account review: Jesus"]
            for i, s_ in enumerate(items):
                y = 270 + i * 120
                if i == 2:
                    rrect(cv, 40, y - 75, w - 80, 105, 16, paint("#ffe9a8"))
                text(cv, s_, 70, y, F("bold" if i == 2 else "medium", 54), paint(navy if i == 2 else grey))
        elif name == "metrics":
            title("ACCOUNT: @Jesus", "Last 30 days")
            rows([("Followers", "12", red), ("Avg. watch time", "0:11", red), ("Engagement rate", "0.2%", red),
                  ("Hours spent replying to comments", "312", green)], 280, 105, self.T("b5"))
        elif name == "funnel":
            title("MONETIZATION FUNNEL")
            rows([("Paywall", "NONE", red), ("Merch", "NONE", red), ("Subscriptions", "NONE", red),
                  ("Content given away free", "100%", grey)], 270, 105, self.Wd("b7", "paywall") - 0.2)
        elif name == "strategy":
            title("GROWTH STRATEGY")
            text(cv, "???", w / 2, 470, F("black", 260), paint("#d6dbe1"), "center")
        elif name == "seed":
            title("GROWTH STRATEGY", "Proposed by: Jesus")
            circle(cv, w / 2, 420, 6, paint("#6b4e2e"))
            ak = ease_back(prog(t, self.Wd("b11", "smallest"), self.Wd("b11", "smallest") + 0.5))
            cv.save()
            cv.translate(w / 2 + 40, 400)
            cv.scale(ak, ak)
            cv.drawPath(quad_path((0, 0), (80, -40), (170, -60)), paint(red, stroke=5))
            text(cv, "(actual size)", 180, -50, F("bold", 40), paint(red))
            cv.restore()
        elif name == "audience":
            title("AUDIENCE QUALITY")
            parts = [("Lonely people", 0.32, "#3b6fb6"), ("Sick people", 0.22, "#8a9a5b"),
                     ("Broke people", 0.24, "#c9a227"), ("People nobody\nelse replies to", 0.22, "#b4564a")]
            cx, cy, r = 330, 420, 210
            a0 = -90
            gk = ease_out(prog(t, self.T("b14"), self.T("b14") + 1.2))
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
                for j, s_ in enumerate(lab.split("\n")):
                    text(cv, s_, 670, ly + j * 40, F("bold", 38), paint(navy))
            text(cv, "Ad value per user: $0.00", 70, 670, F("black", 34), paint(red))
        elif name == "trolls":
            title("TROLL RESPONSE")
            rows([("Industry best practice", "Dunk. Clip. Repost.", grey), ("@Jesus", "Blesses them", navy),
                  ("Rage-bait used", "0", red), ("Reach left on the table", "98%", red)], 270, 105, self.Wd("b16", "Do") - 0.2)
        elif name == "brandsafety":
            rect(cv, 0, 0, w, 120, paint("#fff1d6"))
            title("\u26a0 BRAND SAFETY ALERT")
            rows([("Video", "\u201cStop profiting off pain\u201d", navy), ("Advertisers named", "7", red),
                  ("Violence encouraged", "0", green), ("Status", "DEMONETIZED", red)], 270, 105, self.T("b18"))
        elif name == "sentiment":
            title("BRAND SENTIMENT")
            x0, y0 = 90, 600
            line(cv, x0, y0, x0 + 1060, y0, paint(grey, stroke=4))
            line(cv, x0, y0, x0, 200, paint(grey, stroke=4))
            gk = ease_io(prog(t, self.T("b21") + 0.2, self.Wd("b21", "followers") + 0.5))
            n = 40
            f_pts = [(x0 + 10 + i * 26, y0 - 60 - 4 * math.sin(i)) for i in range(n)]
            e_pts = [(x0 + 10 + i * 26, y0 - 60 - (i / n) ** 2.4 * 360) for i in range(n)]
            m = max(2, int(n * gk))
            cv.drawPath(poly(f_pts[:m], False), paint(green, stroke=8))
            cv.drawPath(poly(e_pts[:m], False), paint(red, stroke=8))
            text(cv, "Followers", f_pts[m - 1][0] - 10, f_pts[m - 1][1] + 50, F("bold", 34), paint(green), "right")
            text(cv, "Trolls & haters", e_pts[m - 1][0] - 10, e_pts[m - 1][1] - 20, F("bold", 34), paint(red), "right")
        elif name == "flagged":
            title("CONTENT FLAGGED")
            rows([("Video", "\u201cLove your enemies\u201d", navy), ("Label", "DIVISIVE", red),
                  ("Comment section", "War zone", red), ("Violence encouraged", "0", green)], 270, 105, self.Wd("b25", "flagged"))
        elif name == "kpi":
            title("KEY PERFORMANCE INDICATOR")
            text(cv, "???", w / 2, 500, F("black", 260), paint(red), "center")
        elif name == "decision":
            title("DECISION: @Jesus")
            rows([("Boost", "DENIED", red), ("Recommend to others", "DENIED", red), ("Reach", "LIMITED", red)],
                 270, 105, self.T("b30") + 0.3)
            stamp("SUPPRESSED", self.stamp_t, size=118, box=(900, 180))

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
        names = {"PAM": ("PAM", "Intern"), "CFO": ("M. LEDGER", "Monetization"), "CEO": ("R. GAINS", "CEO"),
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
        if who == "CEO" and self.stamp_win[0] < t < self.stamp_win[1]:
            # mug parked on the table, big red rubber stamp in hand
            rrect(cv, 100, 134, 48, 58, 8, paint("#fafafa"))
            text(cv, "#1 BOSS", 124, 168, font("black", 11), paint("#c0392b"), "center")
            sx, sy = hr
            if t > self.stamp_t - 0.02:
                rect(cv, -60, 168, 120, 30, paint("#ffffff"))
                cv.save()
                cv.translate(0, 183)
                cv.rotate(-6)
                text(cv, "SUPPRESSED", 0, 7, font("black", 19), paint("#d0392b"), "center")
                cv.restore()
            rrect(cv, sx - 34, sy + 4, 68, 22, 4, paint("#d0392b"))
            rect(cv, sx - 8, sy - 40, 16, 46, paint("#6b4423"))
            circle(cv, sx, sy - 46, 18, paint("#d0392b"))
            draw_hand(cv, L, sx, sy - 22, "fist", 1)
            wx, wy = hl
            rrect(cv, wx - 20, wy - 40, 40, 16, 5, paint("#d4af37"))
            circle(cv, wx, wy - 32, 11, paint("#f6e7a8"))
            circle(cv, wx, wy - 32, 11, paint("#b8941f", stroke=3))
        elif who == "CEO":
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
        # warm presence, swelling into a soft aura as he leaves
        aura = smooth(prog(t, self.aura0, self.aura0 + 2.5))
        fk = self.Wd("b22", "Father")
        aura = max(aura, 0.75 * pulse(t, fk - 0.2, 0.5, 2.2, 1.2))
        circle(cv, 0, 60, 330 + 120 * aura, paint("#ffd98a", 0.10 + 0.22 * aura, blur=60 + 30 * aura))
        if aura > 0:
            cv.save()
            cv.translate(0, -60)
            cv.rotate(t * 6)
            for k in range(12):
                cv.rotate(30)
                cv.drawPath(poly([(0, 0), (-40, -620), (40, -620)]), paint("#fff1c4", 0.07 * aura))
            cv.restore()
            r = random.Random(17)
            for i in range(16):
                ph = (t * 0.35 + r.random()) % 1.0
                px = r.uniform(-170, 170) + math.sin(t * 2 + i) * 10
                py = 300 - ph * 600
                circle(cv, px, py, r.uniform(3, 6), paint("#fff6d0", aura * math.sin(ph * math.pi)))
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
            standing = self.jstand(t)
            pat = prog(t, *self.pat)
            if 0 < pat < 1:
                # brushing the dust off his robe
                b = abs(math.sin(pat * math.pi * 5))
                standing = ((-86 + 6 * b, 300 - 34 * b), (86 - 6 * b, 300 - 34 * abs(math.sin(pat * math.pi * 5 + 1.2))))
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
        wave = self.Wd("b2", "Thanks") + 0.4 < t < self.E("b2") + 0.5 or self.jwave[0] < t < self.jwave[1]
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
        if self.pat[0] < t < self.pat[1] + 1.2:
            r = random.Random(23)
            for i in range(26):
                t0 = self.pat[0] + r.uniform(0, self.pat[1] - self.pat[0])
                d = t - t0
                if 0 < d < 1.1:
                    px = r.choice((-1, 1)) * r.uniform(60, 130) + r.uniform(-40, 40) * d
                    py = 290 - 60 * d + r.uniform(-20, 20)
                    circle(cv, px, py, 6 + 14 * d, paint("#d8c8a8", 0.45 * (1 - d / 1.1)))
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
