"""Character designs."""
from anim import hashf, mixc
from rig import Style

MOSES = Style(skin=(184, 128, 88), beard=(70, 50, 38), beard_kind="full", beard_len=1.1,
              hair=(58, 42, 32), brow=(48, 34, 26), iris=(80, 52, 30),
              robe=(176, 150, 112), sash=(124, 70, 44), cloak=(118, 84, 56),
              head="keffiyeh", head_c1=(214, 198, 166), head_c2=(140, 92, 60), seed=1)

ELDER = Style(skin=(196, 152, 118), beard=(196, 192, 186), beard_kind="long", beard_len=1.0,
              brow=(170, 166, 160), iris=(60, 66, 70), face_w=0.9, jaw=0.82, wrinkles=1.0,
              robe=(72, 70, 96), robe2=(178, 150, 82), sash=(178, 150, 82),
              head="tall_hat", head_c1=(56, 54, 78), head_c2=(184, 156, 86), seed=2)

GUARD = Style(skin=(170, 118, 84), beard=(40, 32, 28), beard_kind="short", brow=(36, 28, 24),
              robe=(96, 88, 78), sash=(80, 40, 34), armor=(150, 110, 60), sleeve=(120, 106, 90),
              head="helmet", head_c1=(176, 132, 70), head_c2=(120, 40, 36), seed=3)
GUARD2 = Style(**{**GUARD.__dict__, "skin": (150, 102, 72), "seed": 4, "beard": (30, 26, 24)})

WEAVER = Style(skin=(200, 150, 112), female=True, mustache=False, brow=(54, 38, 30),
               hair=(40, 28, 22), iris=(66, 44, 26), robe=(150, 90, 70), sash=(70, 80, 120),
               head="veil", head_c1=(64, 78, 128), head_c2=(196, 168, 92), face_w=0.94, jaw=0.85, seed=5,
               girth=0.9)

POTTER = Style(skin=(176, 124, 86), beard=(52, 38, 30), beard_kind="short", beard_len=1.0,
               hair=(46, 34, 28), brow=(42, 30, 24), robe=(130, 110, 86), sleeve=(130, 110, 86),
               sash=(90, 70, 50), apron=(150, 96, 66), head="cap", head_c1=(160, 140, 104),
               head_c2=(110, 80, 56), ears=True, seed=6, girth=1.08)

SKINS = [(196, 146, 106), (172, 120, 84), (206, 160, 120), (160, 108, 76), (188, 136, 98)]
ROBES = [(160, 150, 130), (140, 132, 118), (170, 160, 140), (150, 142, 128), (132, 128, 120)]
HEADC = [(180, 172, 156), (120, 116, 108), (160, 150, 130), (96, 100, 120), (150, 130, 110)]


def villager(i):
    """Plain, uniform villagers: muted greys -- order over individuality."""
    f = hashf(i, 77) > 0.5
    return Style(skin=SKINS[i % 5], female=f, mustache=not f,
                 beard=None if f or hashf(i, 3) < 0.4 else mixc((50, 40, 32), (150, 146, 140), hashf(i, 5)),
                 beard_kind="short", robe=ROBES[(i * 3) % 5], sash=(110, 104, 96),
                 head="veil" if f else ("wrap" if hashf(i, 9) < 0.6 else "cap"),
                 head_c1=HEADC[(i * 7) % 5], head_c2=(120, 110, 96), ears=not f,
                 face_w=0.9 + 0.15 * hashf(i, 8), jaw=0.85 + 0.2 * hashf(i, 10), seed=10 + i,
                 girth=0.92 + 0.16 * hashf(i, 12))
