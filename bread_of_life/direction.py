"""Shot list and acting direction.

Screen geography (kept consistent for eyelines):
  Jesus faces screen-RIGHT (yaw > 0). The crowd (Eli, Miriam, listeners) is
  to his right and faces screen-LEFT (yaw < 0). Peter stands at Jesus' side
  (screen-left of him) and faces RIGHT toward Jesus/the crowd.
"""
from anim import Perf
from config import H, W
from timeline import Timeline

T = Timeline()

import chars  # noqa: E402

NECK = {k: c.st.get("neck_len", 1.72) for k, c in chars.CHARS.items()}
NECK["man2"] = NECK["jesus"]
EYE_Y = {k: c.st.get("eye_y", 0.03) for k, c in chars.CHARS.items()}
EYE_Y["man2"] = EYE_Y["jesus"]
BODY_K = {"miriam": 0.95}
SOLE = 16.95


def place(who, x, eye_y, S, **kw):
    """Character placement with the eyes at screen height eye_y (pixels)."""
    y = eye_y + (NECK[who] - EYE_Y[who]) * S
    d = dict(who=who, x=x, y=y, S=S)
    d.update(kw)
    return d


def stand(who, x, feet_y, S, **kw):
    """Full-body placement with the soles at screen height feet_y."""
    d = dict(who=who, x=x, y=feet_y - SOLE * S * BODY_K.get(who, 1.0), S=S)
    d.update(kw)
    return d


SHOTS = []

# ---------------------------------------------------------------------------
# Gesture vocabulary: wrist targets (x, y, z) in body units from the neck base,
# z toward the camera. Hands follow the forearm with a natural wrist bend.
# ---------------------------------------------------------------------------
G_REACH_R = dict(target=(4.6, 2.5, 0.8), hand="open", palm=(0.25, -0.85, 0.45), wrist=8)  # full shots: arm out toward the crowd
G_REACH_M = dict(target=(3.3, 1.9, 1.8), hand="open", palm=(0.35, -0.15, 1.0), wrist=8)  # medium shots: forearm out, palm to them
G_TEACH_M = dict(target=(2.65, 1.6, 1.8), hand="open", palm=(-0.45, -0.5, 0.75), wrist=-10)  # medium shots: explaining, hand raised with the fingers up, palm to them
G_OFFER_R = dict(target=(2.7, 2.9, 1.6), hand="open", palm=(0.15, -1.0, 0.2), wrist=10)  # open palm offered in front of him
G_TEACH_R = dict(target=(3.7, 3.4, 1.0), hand="open", palm=(0.1, -1.0, 0.1), wrist=12)  # full shots: explaining, palm up
G_UP_R = dict(target=(3.5, -1.3, 0.8), hand="open", palm=(0.15, -0.6, 0.8), wrist=5)  # full shots: toward heaven
G_UP_M = dict(target=(3.4, 0.3, 1.3), hand="open", palm=(0.2, -0.3, 1.0), wrist=5)
G_HEART_L = dict(target=(0.1, 2.5, 1.1), hand="flat", palm=(0.0, 0.0, -1.0), wrist=12, still=True)
G_SELF_R = dict(target=(0.85, 2.45, 1.15), hand="soft", palm=(-0.1, 0.05, -1.0), wrist=8, still=True)  # "my flesh": hand laid on his chest
G_BREAD_R = dict(target=(0.95, 3.7, 1.6), hand="hold", palm=(-0.8, -0.5, 0.15), wrist=20, still=True)  # the loaf held up in front of him
G_BREAD_L = dict(target=(-0.75, 3.8, 1.6), hand="hold", palm=(-0.8, -0.5, 0.15), wrist=20, still=True)
G_GIVE_R = dict(target=(2.7, 3.5, 1.6), hand="cup", palm=(0.0, -1.0, 0.2), hand_dir=(0.9, 0.0, 0.4), still=True)  # offers the half on his open palm
G_PRAY_L = dict(target=(-0.2, 3.0, 1.4), hand="hold", palm=(0.0, -1.0, 0.0), hand_dir=(0.95, -0.2, 0.25), still=True)  # bread cradled in the hand, which comes straight out of the sleeve
P_CHIN_R = dict(target=(0.5, 0.3, 1.5), hand="relaxed", palm=(-0.4, 0.0, -1.0), wrist=-10, layer="front", still=True)
P_SCRATCH_R = dict(target=(1.5, -1.5, 0.3), hand="relaxed", still=True, palm=(-1.0, 0.3, -0.4))
P_SCRATCH_MID = dict(target=(2.7, 0.7, 1.5), hand="relaxed", still=True, palm=(-0.6, 0.3, -0.7))  # on the way up, in front of the shoulder
P_ASK_R = dict(target=(3.1, 2.4, 1.5), hand="open", palm=(0.2, -1.0, 0.3), wrist=10)
P_RECEIVE_L = dict(target=(-3.4, 3.5, 1.2), hand="cup", palm=(0.0, -1.0, 0.3), wrist=10, still=True)
P_TAKE_L = dict(target=(-3.02, 2.5, 2.1), hand="hold", palm=(0.0, 1.0, 0.3), wrist=10, still=True)  # takes it from his palm, from above
P_KEEP_L = dict(target=(-1.1, 3.6, 1.6), hand="hold", palm=(0.25, -1.0, 0.35), wrist=12, still=True)  # draws the bread close
E_CROSS_R = dict(target=(-1.2, 3.0, 1.15), hand="relaxed", palm=(0.0, 0.2, -1.0), wrist=10, still=True, pole=(0.6, 1.0, -0.15))
E_CROSS_L = dict(target=(1.15, 3.2, 0.95), hand="relaxed", palm=(0.0, 0.2, -1.0), wrist=10, still=True, pole=(0.6, 1.0, -0.15))
E_POINT_R = dict(target=(1.5, 1.0, 1.6), hand="point", palm=(-0.6, 0.1, -0.6), wrist=0, layer="front")  # index finger raised, palm toward his face, in front of his head cloth
E_TOWARD_L = dict(target=(-2.4, 1.9, 1.8), hand="open", palm=(0.5, -0.1, 0.85), wrist=8)
E_OUTBURST_L = dict(target=(-2.6, 1.6, 1.6), hand="open", palm=(0.5, -0.1, 0.85), wrist=6)
E_BOATS_L0 = dict(target=(-1.5, 1.8, 2.0), hand="open", palm=(0.1, 1.0, 0.25), wrist=8)  # "every boat..." sweep start
E_BOATS_L = dict(target=(-2.5, 1.9, 1.6), hand="open", palm=(0.1, 1.0, 0.25), wrist=6)  # ...sweeping out toward the shore
E_PALMS_R = dict(target=(2.0, 2.6, 1.8), hand="open", palm=(0.3, -1.0, 0.45), wrist=10)  # "how is that possible?"
E_PALMS_L = dict(target=(-2.0, 2.6, 1.8), hand="open", palm=(0.3, -1.0, 0.45), wrist=10)
M_CLUTCH_L = dict(target=(-0.15, 2.3, 1.05), hand="soft", palm=(0.0, 0.0, -1.0), wrist=10, still=True)  # hand pressed over her heart
CU_OPEN_R = dict(target=(1.7, 2.2, 1.9), hand="open", palm=(0.2, -0.9, 0.4), wrist=8)      # close-ups: a small open palm toward them
CU_OPEN_L = dict(target=(-1.6, 2.15, 1.9), hand="open", palm=(0.2, -0.9, 0.4), wrist=8)
CU_NOT_R = dict(target=(1.6, 2.6, 1.9), hand="open", palm=(0.0, 1.0, 0.2), wrist=4)        # a small palm-down "not this"
CU_RAISE_R = dict(target=(1.7, 2.2, 1.9), hand="open", palm=(0.15, -1.0, 0.35), wrist=8)   # an open palm lifting
P_HEART_R = dict(target=(0.15, 2.4, 1.1), hand="soft", palm=(-0.1, 0.05, -1.0), wrist=8, still=True)  # Peter's hand on his chest
M_MOUTH_L = dict(target=(-0.25, 0.45, 1.4), hand="cup", layer="front", still=True, palm=(0.0, 0.0, -1.0))

def shot(t0, name, plate, pcam, chars, blur=0.0, cam=None, light=None, fx=(), grade="morning",
         trans=None, crowd=None, title=None, handoff=None):
    SHOTS.append(dict(t0=t0, name=name, plate=plate, pcam=pcam, chars=chars, blur=blur,
                      cam=cam or {}, light=light or {}, fx=list(fx), grade=grade, trans=trans,
                      crowd=crowd or [], title=title, handoff=handoff))


# Lighting presets ------------------------------------------------------------
L_J_MORN = dict(light_x=-0.75, light_y=-0.5, rim=0.55, rim_x=-1.0)      # Jesus, sun behind-left
L_C_MORN = dict(light_x=0.7, light_y=-0.55, rim=0.25, rim_x=1.0)        # crowd, sun from right
L_SYN_J = dict(light_x=-0.55, light_y=-0.85, rim=0.45, rim_x=-1.0)
L_SYN_C = dict(light_x=-0.6, light_y=-0.8, rim=0.2, rim_x=-1.0)
L_DUSK_J = dict(light_x=0.8, light_y=-0.2, rim=0.7, rim_x=1.0)
L_DUSK_C = dict(light_x=-0.35, light_y=-0.3, rim=0.65, rim_x=-1.0)


def crowd(members, mood="listen", focus=-1.0, blur=2.5, z=0.0, light=None, t0=0.0):
    return dict(members=members, mood=mood, focus=focus, blur=blur, z=z, light=light or {}, t0=t0)


# Crowd layouts: (seed, x, feet_y, S, yaw_bias)
SHORE_BACK = [(201, 70, 815, 15, 0), (202, 205, 800, 13, 0), (203, 610, 830, 16, 0), (204, 470, 805, 13.5, 0),
              (205, 700, 812, 14.5, 0), (206, 330, 792, 12, 0), (207, 560, 790, 11.5, 0), (208, 130, 788, 11, 0)]
SYN_BACK = [(301, 60, 1090, 24, 0), (302, 205, 1075, 22, 0), (303, 560, 1095, 25, 0), (304, 690, 1080, 23, 0),
            (305, 130, 1040, 19, 0), (306, 640, 1035, 19, 0)]
# the synagogue crowd stands to Jesus' right (screen-right), turned toward him
SYN_WIDE = [(401, 400, 925, 26, -24), (402, 505, 920, 25.8, -26), (403, 615, 928, 26.2, -28), (413, 455, 880, 24, -25),
            (404, 360, 1015, 29.8, -22), (405, 470, 1010, 29.6, -27), (406, 585, 1018, 30, -28), (407, 700, 1012, 29.7, -30),
            (408, 420, 1150, 35.4, -24), (409, 545, 1145, 35.2, -26), (410, 675, 1152, 35.5, -30)]
SYN_UPROAR = [(501, 90, 1000, 25, 0), (502, 250, 990, 24, 0), (503, 410, 1005, 25, 0), (504, 570, 995, 24, 0),
              (505, 700, 1000, 25, 0), (506, 160, 1120, 31, 0), (507, 340, 1130, 32, 0), (508, 520, 1115, 31, 0),
              (509, 680, 1125, 32, 0), (510, 70, 1270, 39, 0), (511, 280, 1285, 40, 0), (512, 470, 1275, 39, 0),
              (513, 660, 1290, 40, 0)]
BEACH_FAR = [(601, 520, 905, 6.5, 0), (602, 560, 910, 6.8, 0), (603, 610, 902, 6.2, 0), (604, 650, 912, 7.0, 0),
             (605, 690, 906, 6.4, 0)]

# =============================================================================
# SCENE 1 - SHORE, MORNING
# =============================================================================
s1_end = T.scene_end["shore"]

# Cold open: the first frame is already a full image (no fade from black).
shot(0.0, "open_cu_jesus", "lake_morning", (0.42, 0.40, 1.0),
     [place("jesus", 300, 520, 124)], blur=6, cam=dict(z0=1.0, z1=1.07, fx=300, fy=520),
     light=L_J_MORN, fx=["sun_glow", "god_rays", "bokeh_water"], title="The Bread of Life")
shot(6.0, "wide_boats", "wide_morning", (0.50, 0.47, 0.82),
     [], blur=0, cam=dict(z0=1.0, z1=1.04, fx=360, fy=560), light=L_J_MORN,
     fx=["boats_moving", "water_sparkle", "god_rays"])
# a full figure on the sand: Jesus alone as the boats come in - no one saw how he came
shot(11.4, "fs_jesus_alone", "beach_morning", (0.46, 0.55, 1.0),
     [stand("jesus", 330, 1190, 46)], blur=1.0,
     cam=dict(z0=1.0, z1=1.05, fx=340, fy=760), light=L_J_MORN, fx=["sun_glow", "water_sparkle"],
     crowd=[crowd(BEACH_FAR, mood="listen", focus=-1, blur=0.8, z=1)])
shot(T("L03") - 1.15, "mcu_eli_arrives", "land_morning", (0.5, 0.42, 1.0),
     [place("miriam", 185, 480, 74, blur=3.0), place("eli", 440, 455, 118)], blur=6,
     cam=dict(z0=1.0, z1=1.04, fx=440, fy=455), light=L_C_MORN, fx=["bokeh_land"],
     crowd=[crowd(SHORE_BACK, mood="awe", focus=-1, blur=2.5, z=1)])
shot(T("L03", seg=3) - 0.2, "cu_eli_possible", "land_morning", (0.52, 0.42, 1.05),
     [place("eli", 400, 440, 152)], blur=8, light=L_C_MORN, fx=["bokeh_land"],
     cam=dict(z0=1.0, z1=1.04, fx=400, fy=440), crowd=[crowd(SHORE_BACK[:4], mood="awe", focus=-1, blur=3.5, z=1)])
shot(T("L03", "end") + 0.25, "cu_peter_knowing", "lake_morning", (0.35, 0.40, 1.1),
     [place("peter", 360, 440, 150)], blur=8, light=L_J_MORN, fx=["bokeh_water"],
     cam=dict(z0=1.0, z1=1.03, fx=360, fy=440))
shot(T("L03b") - 0.3, "cu_jesus_l03b", "lake_morning", (0.40, 0.40, 1.0),
     [place("jesus", 330, 430, 158)], blur=8, cam=dict(z0=1.0, z1=1.07, fx=330, fy=430),
     light=dict(L_J_MORN, rim=0.7), fx=["sun_glow", "bokeh_water", "god_rays"])
shot(T("L03b", "end") + 0.2, "cu_eli_puzzled", "land_morning", (0.52, 0.42, 1.05),
     [place("eli", 385, 440, 150)], blur=8, light=L_C_MORN, fx=["bokeh_land"],
     cam=dict(z0=1.0, z1=1.02, fx=385, fy=440), crowd=[crowd(SHORE_BACK[:4], mood="worried", focus=-1, blur=3.5, z=1)])
shot(T("L04") - 0.3, "cu_jesus_l04", "lake_morning", (0.40, 0.40, 1.0),
     [place("jesus", 330, 430, 158)], blur=8, cam=dict(z0=1.0, z1=1.05, fx=330, fy=430),
     light=L_J_MORN, fx=["sun_glow", "bokeh_water"])
shot(T("L04", word="ate") - 0.35, "cu_eli_caught", "land_morning", (0.52, 0.42, 1.05),
     [place("eli", 390, 440, 150)], blur=8, light=L_C_MORN, fx=["bokeh_land"],
     cam=dict(z0=1.0, z1=1.02, fx=390, fy=440), crowd=[crowd(SHORE_BACK[:4], mood="worried", focus=-1, blur=3.5, z=1)])
shot(T("L04", "end") - 0.6, "cu_miriam_listen", "land_morning", (0.46, 0.42, 1.05),
     [place("miriam", 380, 450, 150)], blur=8, light=L_C_MORN, fx=["bokeh_land"],
     cam=dict(z0=1.0, z1=1.02, fx=380, fy=450), crowd=[crowd(SHORE_BACK[3:], mood="listen", focus=-1, blur=3.5, z=1)])
shot(T("L05") - 0.35, "mcu_jesus_l05", "lake_morning", (0.40, 0.41, 1.0),
     [place("jesus", 230, 455, 112)], blur=6, cam=dict(z0=1.0, z1=1.05, fx=230, fy=455),
     light=L_J_MORN, fx=["sun_glow", "bokeh_water"])
shot(T("L05", seg=2) - 0.15, "cu_miriam_l05", "land_morning", (0.46, 0.42, 1.05),
     [place("miriam", 380, 450, 155)], blur=8, light=L_C_MORN, fx=["bokeh_land"],
     crowd=[crowd(SHORE_BACK[3:], mood="awe", focus=-1, blur=3.5, z=1)])
shot(T("L06") - 0.25, "cu_jesus_l06", "lake_morning", (0.38, 0.40, 1.0),
     [place("jesus", 340, 430, 160)], blur=8, cam=dict(z0=1.02, z1=1.06, fx=340, fy=430),
     light=L_J_MORN, fx=["sun_glow", "bokeh_water", "god_rays"])
shot(T("L07") - 0.6, "mcu_peter_l07", "lake_morning", (0.36, 0.42, 1.0),
     [place("jesus", 700, 470, 120, blur=3.5, z=60), place("peter", 250, 455, 118)], blur=6,
     light=L_J_MORN, fx=["bokeh_water"], cam=dict(z0=1.0, z1=1.03, fx=250, fy=455))
shot(T("L08") - 0.4, "cu_jesus_l08", "lake_morning", (0.48, 0.40, 1.0),
     [place("jesus", 380, 430, 158)], blur=8, light=L_J_MORN, fx=["sun_glow", "bokeh_water"],
     cam=dict(z0=1.0, z1=1.05, fx=380, fy=430))
shot(T("L09") - 0.45, "mcu_eli_l09", "land_morning", (0.52, 0.42, 1.0),
     [place("miriam", 570, 480, 80, blur=3.0), place("eli", 330, 455, 118)], blur=6, light=L_C_MORN,
     fx=["bokeh_land"], cam=dict(z0=1.0, z1=1.04, fx=330, fy=455),
     crowd=[crowd(SHORE_BACK, mood="skeptical", focus=-1, blur=2.5, z=1)])
shot(T("L09", seg=1) + 0.4, "cu_jesus_listens_l09", "lake_morning", (0.40, 0.40, 1.0),
     [place("jesus", 330, 430, 158)], blur=8, light=L_J_MORN, fx=["sun_glow", "bokeh_water"])
shot(T("L09", seg=2) - 0.2, "mcu_eli_l09b", "land_morning", (0.52, 0.42, 1.0),
     [place("eli", 400, 450, 128)], blur=7, light=L_C_MORN, fx=["bokeh_land"],
     cam=dict(z0=1.0, z1=1.03, fx=400, fy=450), crowd=[crowd(SHORE_BACK[:5], mood="skeptical", focus=-1, blur=3.0, z=1)])
shot(T("L10") - 0.5, "cu_jesus_l10", "lake_morning", (0.40, 0.40, 1.0),
     [place("jesus", 330, 430, 160)], blur=8, cam=dict(z0=1.0, z1=1.07, fx=330, fy=430),
     light=L_J_MORN, fx=["sun_glow", "bokeh_water", "god_rays"])
shot(T("L10", seg=1) + 0.9, "cu_eli_l10", "land_morning", (0.52, 0.42, 1.05),
     [place("eli", 385, 440, 152)], blur=8, light=L_C_MORN, fx=["bokeh_land"],
     cam=dict(z0=1.0, z1=1.02, fx=385, fy=440), crowd=[crowd(SHORE_BACK[:4], mood="worried", focus=-1, blur=3.5, z=1)])
shot(T("L10", seg=2) - 0.35, "cu_jesus_l10b", "lake_morning", (0.40, 0.40, 1.0),
     [place("jesus", 330, 430, 162)], blur=8, cam=dict(z0=1.02, z1=1.08, fx=330, fy=430),
     light=L_J_MORN, fx=["sun_glow", "bokeh_water", "god_rays"])
shot(T("L11", word="bread#1") - 0.12, "cu_eli_l11", "land_morning", (0.52, 0.42, 1.05),
     [place("eli", 385, 440, 152)], blur=8, light=L_C_MORN, fx=["bokeh_land"],
     cam=dict(z0=1.0, z1=1.03, fx=385, fy=440), crowd=[crowd(SHORE_BACK[:4], mood="awe", focus=-1, blur=3.5, z=1)])
shot(T("L11", seg=1) - 0.2, "cu_miriam_hope", "land_morning", (0.46, 0.42, 1.05),
     [place("miriam", 380, 450, 158)], blur=8, light=L_C_MORN, fx=["bokeh_land"],
     cam=dict(z0=1.0, z1=1.03, fx=380, fy=450), crowd=[crowd(SHORE_BACK[3:], mood="awe", focus=-1, blur=3.5, z=1)])
shot(T("L12") - 0.9, "cu_miriam_l12", "land_morning", (0.46, 0.42, 1.08),
     [place("miriam", 370, 455, 165)], blur=9, light=L_C_MORN, fx=["bokeh_land"],
     cam=dict(z0=1.0, z1=1.06, fx=370, fy=455), crowd=[crowd(SHORE_BACK[3:], mood="awe", focus=-1, blur=3.5, z=1)])
shot(T("L13") - 1.2, "cu_jesus_l13", "lake_morning", (0.38, 0.40, 1.0),
     [place("jesus", 340, 440, 162)], blur=9, cam=dict(z0=1.0, z1=1.08, fx=340, fy=440),
     light=dict(L_J_MORN, rim=0.85), fx=["sun_glow_strong", "bokeh_water", "god_rays"])
shot(T("L14", seg=1) - 0.25, "cu_miriam_tear", "land_morning", (0.46, 0.42, 1.08),
     [place("miriam", 370, 455, 165)], blur=9, light=L_C_MORN, fx=["bokeh_land"],
     cam=dict(z0=1.02, z1=1.05, fx=370, fy=455), crowd=[crowd(SHORE_BACK[3:], mood="awe", focus=-1, blur=3.5, z=1)])
shot(T("L14", "end") - 1.2, "ms_two_shot_end1", "lake_morning", (0.45, 0.43, 0.95),
     [place("miriam", 640, 430, 80), place("jesus", 165, 390, 90)], blur=4,
     light=L_J_MORN, fx=["sun_glow", "bokeh_water", "god_rays"], cam=dict(z0=1.0, z1=1.04, fx=360, fy=440))

# =============================================================================
# SCENE 2 - SYNAGOGUE
# =============================================================================
shot(s1_end + 1.1, "syn_wide", "syn_side", (0.5, 0.48, 0.80),
     [stand("jesus", 150, 900, 25)], blur=0.8, cam=dict(z0=1.0, z1=1.06, fx=260, fy=600),
     light=L_SYN_J, fx=["beams", "dust"], grade="synagogue", trans=("dissolve", 1.6),
     crowd=[crowd(SYN_WIDE, mood=[(s1_end, "listen"), (T("L15", word="murmur") - 0.2, "murmur")],
                  focus=-1.5, blur=0.0, z=40, light=L_SYN_C)])
shot(T("L16") - 0.6, "syn_eli_grumble", "syn_side", (0.62, 0.45, 1.05),
     [place("man2", 655, 520, 100, blur=2.0), place("eli", 390, 470, 128)], blur=6,
     light=L_SYN_C, fx=["beams", "dust"], grade="synagogue", cam=dict(z0=1.0, z1=1.03, fx=390, fy=470),
     crowd=[crowd(SYN_BACK, mood="murmur", focus=-1, blur=3.0, z=1, light=L_SYN_C)])
shot(T("L19") - 0.9, "syn_mcu_jesus_l19", "syn_front", (0.5, 0.42, 1.0),
     [place("jesus", 250, 460, 116)], blur=6, light=L_SYN_J, fx=["beams", "dust"], grade="synagogue",
     cam=dict(z0=1.0, z1=1.03, fx=250, fy=460))
shot(T("L20") - 0.6, "syn_cu_jesus_l20", "syn_front", (0.48, 0.40, 1.05),
     [place("jesus", 340, 435, 158)], blur=8, light=L_SYN_J, fx=["beams", "dust"], grade="synagogue",
     cam=dict(z0=1.0, z1=1.05, fx=340, fy=435))
shot(T("L20", seg=1) - 0.1, "syn_cu_eli_conflict", "syn_side", (0.6, 0.45, 1.05),
     [place("eli", 380, 440, 150)], blur=8, light=L_SYN_C, fx=["beams", "dust"], grade="synagogue",
     crowd=[crowd(SYN_BACK, mood="worried", focus=-1, blur=3.5, z=1, light=L_SYN_C)])
shot(T("L20", "end") - 0.4, "syn_mcu_jesus_l21", "syn_front", (0.5, 0.42, 1.0),
     [place("jesus", 225, 460, 116)], blur=6, light=L_SYN_J, fx=["beams", "dust"], grade="synagogue",
     cam=dict(z0=1.0, z1=1.04, fx=225, fy=460))
shot(T("L21", seg=2) - 0.25, "syn_cu_miriam_l21", "syn_side", (0.4, 0.45, 1.05),
     [place("miriam", 370, 450, 152)], blur=8, light=L_SYN_C, fx=["beams", "dust"], grade="synagogue",
     crowd=[crowd(SYN_BACK, mood="awe", focus=-1, blur=3.5, z=1, light=L_SYN_C)])
shot(T("L21", seg=2) + 2.6, "syn_mcu_jesus_l21b", "syn_front", (0.5, 0.42, 1.0),
     [place("jesus", 225, 460, 116)], blur=6, light=L_SYN_J, fx=["beams", "dust"], grade="synagogue")
shot(T("L22") - 1.0, "syn_cu_jesus_l22", "syn_front", (0.46, 0.40, 1.05),
     [place("jesus", 340, 440, 162)], blur=9, light=dict(L_SYN_J, rim=0.8), fx=["beams_strong", "dust"],
     grade="synagogue", cam=dict(z0=1.0, z1=1.08, fx=340, fy=440))
shot(T("L22", seg=1) + 0.2, "syn_cu_eli_l22", "syn_side", (0.6, 0.45, 1.05),
     [place("eli", 380, 440, 150)], blur=8, light=L_SYN_C, fx=["beams", "dust"], grade="synagogue",
     crowd=[crowd(SYN_BACK, mood="skeptical", focus=-1, blur=3.5, z=1, light=L_SYN_C)])
shot(T("L22", "end") - 0.3, "syn_cu_jesus_l23", "syn_front", (0.46, 0.40, 1.05),
     [place("jesus", 340, 440, 164)], blur=9, light=dict(L_SYN_J, rim=0.8), fx=["beams_strong", "dust"],
     grade="synagogue", cam=dict(z0=1.02, z1=1.09, fx=340, fy=440))
shot(T("L23", "end") - 0.25, "syn_cu_peter_notices", "syn_side", (0.3, 0.45, 1.05),
     [place("peter", 380, 445, 150)], blur=8, light=L_SYN_C, fx=["beams", "dust"], grade="synagogue",
     crowd=[crowd(SYN_BACK, mood="worried", focus=-1, blur=3.5, z=1, light=L_SYN_C)])
shot(T("L24") - 0.35, "syn_mcu_eli_l24", "syn_side", (0.62, 0.45, 1.0),
     [place("man2", 665, 540, 98, blur=2.5), place("eli", 420, 455, 126)], blur=6, light=L_SYN_C,
     fx=["beams", "dust"], grade="synagogue", cam=dict(z0=1.0, z1=1.05, fx=420, fy=455),
     crowd=[crowd(SYN_BACK, mood="agitated", focus=-1, blur=3.0, z=1, light=L_SYN_C)])
shot(T("L24", "end") + 0.15, "syn_uproar", "syn_side", (0.5, 0.48, 0.85),
     [], blur=2.5, light=L_SYN_C, fx=["beams", "dust"], grade="synagogue",
     cam=dict(z0=1.0, z1=1.06, fx=360, fy=640),
     crowd=[crowd(SYN_UPROAR, mood="agitated", focus=-1, blur=0.0, z=1, light=L_SYN_C, t0=T("L24", "end"))])
shot(T("L25") - 1.0, "syn_cu_jesus_l25", "syn_front", (0.46, 0.40, 1.05),
     [place("jesus", 345, 440, 160)], blur=9, light=dict(L_SYN_J, rim=0.6), fx=["beams", "dust"],
     grade="synagogue_dark", cam=dict(z0=1.0, z1=1.12, fx=345, fy=430))
shot(T("L25", "end") + 0.15, "syn_miriam_gasp", "syn_side", (0.4, 0.45, 1.05),
     [place("miriam", 370, 450, 155)], blur=8, light=L_SYN_C, fx=["beams", "dust"], grade="synagogue",
     crowd=[crowd(SYN_BACK, mood="worried", focus=-1, blur=3.5, z=1, light=L_SYN_C)])
shot(T("L25", "end") + 1.45, "syn_peter_steady", "syn_side", (0.3, 0.45, 1.05),
     [place("peter", 380, 445, 152)], blur=8, light=L_SYN_C, fx=["beams", "dust"], grade="synagogue",
     crowd=[crowd(SYN_BACK, mood="worried", focus=-1, blur=3.5, z=1, light=L_SYN_C)])
shot(T("L26") + 0.3, "syn_mcu_jesus_l26", "syn_front", (0.5, 0.42, 1.0),
     [place("jesus", 225, 460, 118)], blur=6, light=L_SYN_J, fx=["beams", "dust"], grade="synagogue",
     cam=dict(z0=1.0, z1=1.05, fx=225, fy=460))
shot(T("L27") - 0.25, "syn_cu_jesus_l27", "syn_front", (0.47, 0.40, 1.05),
     [place("jesus", 345, 440, 158)], blur=9, light=dict(L_SYN_J, rim=0.6), fx=["beams", "dust"], grade="synagogue",
     cam=dict(z0=1.0, z1=1.04, fx=345, fy=440))
shot(T("L28") - 0.8, "syn_cu_jesus_l28", "syn_front", (0.46, 0.40, 1.05),
     [place("jesus", 340, 440, 165)], blur=9, light=dict(L_SYN_J, rim=0.7), fx=["beams_strong", "dust"],
     grade="synagogue", cam=dict(z0=1.0, z1=1.06, fx=340, fy=440))
shot(T("L29") - 0.45, "syn_mcu_jesus_l29", "syn_front", (0.5, 0.42, 1.0),
     [place("jesus", 240, 460, 118)], blur=6, light=dict(L_SYN_J, rim=0.7), fx=["beams_strong", "dust"], grade="synagogue",
     cam=dict(z0=1.0, z1=1.04, fx=240, fy=440))
shot(T("L29", seg=1) - 0.1, "syn_cu_eli_unsettled", "syn_side", (0.6, 0.45, 1.05),
     [place("eli", 380, 440, 150)], blur=8, light=L_SYN_C, fx=["beams", "dust"], grade="synagogue",
     crowd=[crowd(SYN_BACK, mood="worried", focus=-1, blur=3.5, z=1, light=L_SYN_C)])
shot(T("L29", seg=1) + 1.8, "syn_mcu_jesus_l29b", "syn_front", (0.5, 0.42, 1.0),
     [place("jesus", 240, 460, 118)], blur=6, light=L_SYN_J, fx=["beams", "dust"], grade="synagogue")
shot(T("L30") - 0.6, "syn_cu_jesus_l30", "syn_front", (0.46, 0.40, 1.05),
     [place("jesus", 340, 440, 165)], blur=9, light=dict(L_SYN_J, rim=0.8), fx=["beams_strong", "dust"],
     grade="synagogue", cam=dict(z0=1.0, z1=1.1, fx=340, fy=440))
shot(T("L30", seg=1) - 0.15, "syn_cu_eli_l30", "syn_side", (0.6, 0.45, 1.05),
     [place("eli", 380, 440, 150)], blur=8, light=L_SYN_C, fx=["beams", "dust"], grade="synagogue",
     cam=dict(z0=1.0, z1=1.03, fx=380, fy=440), crowd=[crowd(SYN_BACK, mood="worried", focus=-1, blur=3.5, z=1, light=L_SYN_C)])
shot(T("L30", seg=2) - 0.45, "syn_mcu_jesus_l30b", "syn_front", (0.5, 0.42, 1.0),
     [place("jesus", 225, 450, 124)], blur=7, light=dict(L_SYN_J, rim=0.85), fx=["beams_strong", "dust"],
     grade="synagogue", cam=dict(z0=1.0, z1=1.07, fx=250, fy=470))

# =============================================================================
# SCENE 3 - SHORE AT SUNSET
# =============================================================================
s2_end = T.scene_end["synagogue"]
shot(s2_end + 0.6, "dusk_wide", "wide_dusk", (0.5, 0.47, 0.82), [], blur=0,
     cam=dict(z0=1.04, z1=1.0, fx=360, fy=560), light=L_DUSK_J, fx=["water_sparkle", "dusk_figures"],
     grade="dusk", trans=("dissolve", 1.4))
shot(T("L32") - 0.5, "dusk_mcu_eli", "land_dusk", (0.5, 0.42, 1.0),
     [place("eli", 360, 455, 125)], blur=6, light=L_DUSK_C, fx=["bokeh_land"], grade="dusk",
     cam=dict(z0=1.0, z1=1.04, fx=360, fy=455))
shot(T("L33") - 0.4, "dusk_leaving", "wide_dusk", (0.62, 0.5, 0.95), [], blur=0.0,
     light=L_DUSK_C, fx=["water_sparkle", "leaving"], grade="dusk", cam=dict(z0=1.0, z1=1.03, fx=520, fy=700))
shot(T("L34") - 3.2, "dusk_cu_jesus", "lake_dusk", (0.62, 0.40, 1.05),
     [place("jesus", 330, 440, 160)], blur=9, light=L_DUSK_J, fx=["sun_glow_dusk", "bokeh_dusk"], grade="dusk",
     cam=dict(z0=1.0, z1=1.06, fx=330, fy=440))
shot(T("L35") - 0.7, "dusk_cu_peter", "land_dusk", (0.4, 0.42, 1.05),
     [place("peter", 380, 445, 158)], blur=9, light=L_DUSK_C, fx=["bokeh_dusk"], grade="dusk",
     cam=dict(z0=1.0, z1=1.06, fx=380, fy=445))
shot(T("L36") - 0.2, "dusk_cu_miriam", "land_dusk", (0.45, 0.42, 1.05),
     [place("miriam", 380, 455, 155)], blur=9, light=L_DUSK_C, fx=["bokeh_dusk"], grade="dusk")
shot(T("L36") + 1.6, "dusk_cu_peter2", "land_dusk", (0.4, 0.42, 1.05),
     [place("peter", 380, 445, 160)], blur=9, light=L_DUSK_C, fx=["bokeh_dusk"], grade="dusk",
     cam=dict(z0=1.02, z1=1.06, fx=380, fy=445))
# the bread is broken and shared on the beach
TF = T("L36", "end") + 0.5   # Jesus breaks the bread and places half in Peter's hand
shot(TF, "dusk_bread", "beach_dusk", (0.55, 0.5, 1.0),
     [stand("miriam", 640, 1185, 40, blur=1.0), stand("peter", 520, 1205, 43, bread=[(TF + 3.05, [("l", 1)])], z=45),
      stand("jesus", 230, 1215, 44, bread=[(0.0, "both"), (TF + 3.05, [("l", -1)])])],
     blur=2.0, light=L_DUSK_J, fx=["sun_glow_dusk"], grade="dusk",
     cam=dict(z0=1.0, z1=1.05, fx=380, fy=760),
     handoff=dict(t0=TF + 2.85, t1=TF + 3.25, giver=("jesus", "r"), taker=("peter", "l")))
# Jesus prays over his half of the bread
shot(T("L37") - 0.45, "dusk_prayer", "lake_dusk", (0.62, 0.40, 1.05),
     [place("jesus", 330, 460, 132, bread=[("l", -1)])], blur=8, light=dict(L_DUSK_J, rim=0.85), fx=["sun_glow_dusk", "bokeh_dusk"],
     grade="dusk", cam=dict(z0=1.0, z1=1.06, fx=330, fy=460))
# final wide on the beach while the title rises
shot(T("L37", seg=3) - 0.3, "dusk_final", "beach_dusk", (0.55, 0.5, 1.0),
     [stand("miriam", 640, 1185, 40, blur=1.0), stand("peter", 520, 1205, 43, bread=[("l", 1)]),
      stand("jesus", 250, 1215, 44, bread=[("l", -1)])],
     blur=2.0, light=L_DUSK_J, fx=["sun_glow_dusk"], grade="dusk",
     cam=dict(z0=1.0, z1=0.97, fx=380, fy=760), title="John 6")

SHOTS.sort(key=lambda s: s["t0"])


# =============================================================================
# PERFORMANCES
# =============================================================================
def build_perfs():
    J = Perf("jesus", seed=1)
    P = Perf("peter", seed=2)
    M = Perf("miriam", seed=3)
    E = Perf("eli", seed=4)
    X = Perf("man2", seed=5)
    for pf in (J, P, M, E, X):
        pf.speaking_lines = [l for l in T.order if T.lines[l]["speaker"] == pf.name.upper()]
        pf.wind = [(0.0, 0.5), (T.scene_end["shore"], 0.05), (T.scene_end["synagogue"], 0.6)]

    # ---------------- SCENE 1 ----------------
    # Jesus: opening - looking out over the water, peaceful
    J.pose(0.0, 0.01, yaw=22, pitch=-2, roll=-2).look(0.0, 0.3, -0.08).expr(0.0, "gentle", 0.01, eo_l=1.0, eo_r=1.0, lo_l=0.1, lo_r=0.1)
    J.hold_eyes(0.0, 1.4)
    J.blink(2.2)
    J.look(3.6, 0.15, 0.05, 0.3).expr(3.4, "peace", 1.4, eo_l=0.9, eo_r=0.9)
    # alone on the sand as the boats come in: calm, watching them arrive, a faint knowing smile
    J.pose(11.4, 0.01, yaw=18, pitch=0, roll=0).look(11.4, 0.36, 0.02).expr(11.4, "peace", 0.01)
    P.pose(0.0, 0.01, yaw=14, pitch=0).look(0.0, 0.4, 0.0).expr(0.0, "neutral", 0.01)
    J.expr(13.2, "knowing", 1.2, m_smile=0.2)
    J.nod(13.9, 1.8, 0.8)
    J.look(15.0, 0.22, 0.08, 0.4).pose(14.9, 1.2, yaw=12, pitch=2)
    # Eli arrives: out of breath, astonished, specific
    t3 = T("L03") - 1.15
    E.pose(0.0, 0.01, yaw=-20, pitch=-2).look(0.0, -0.3, 0.0).expr(0.0, "anxious", 0.01)
    E.pose(T("L03") - 0.3, 0.4, yaw=-22, pitch=-4, roll=3)
    E.expr(T("L03") - 0.2, "surprised", 0.3, m_open=0.0)
    E.expr(T("L03", seg=1), "confused", 0.5)
    E.pose(T("L03", seg=1), 0.6, yaw=-18, pitch=0, roll=-4)
    E.arm(T("L03", seg=2) - 0.25, "l", E_BOATS_L0, 0.5)                    # "every boat..."
    E.arm(T("L03", seg=2) + 0.45, "l", E_BOATS_L, 1.4)                     # ...a slow sweep out toward the shore
    E.look(T("L03", seg=2), -0.15, -0.1, 0.25).pose(T("L03", seg=2), 0.7, yaw=-28)
    E.expr(T("L03", seg=2) + 1.2, "confused", 0.6, br_l=0.5, br_r=0.5)
    E.look(T("L03", seg=2) + 1.6, -0.4, 0.0, 0.25).pose(T("L03", seg=2) + 1.5, 0.7, yaw=-20)
    E.arm(T("L03", seg=3) - 0.35, "l", E_PALMS_L, 0.6)
    E.arm(T("L03", seg=3) - 0.3, "r", E_PALMS_R, 0.6)                      # "how is that possible?" - palms up
    E.expr(T("L03", seg=3) - 0.1, "shocked", 0.4, m_open=0.0, shrug=0.45)
    E.pose(T("L03", seg=3), 0.6, yaw=-20, pitch=-3, roll=4)
    E.arm(T("L03", "end") + 1.6, "r", None, 0.8)
    E.arm(T("L03", "end") + 1.5, "l", None, 0.8)
    M.pose(0.0, 0.01, yaw=-16, pitch=2).look(0.0, -0.35, 0.05).expr(0.0, "anxious", 0.01, bi_l=0.3, bi_r=0.3)
    # Peter's knowing beat: he knows Jesus walked on the water last night
    tp = T("L03", "end") + 0.25
    P.pose(tp - 0.2, 0.01, yaw=16, pitch=0, roll=0).look(tp - 0.2, 0.45, 0.0).expr(tp - 0.2, "neutral", 0.01)
    P.look(tp + 0.5, 0.65, -0.05, 0.15).pose(tp + 0.45, 0.4, yaw=26)
    P.expr(tp + 0.75, "knowing", 0.5, m_smile=0.4).look(tp + 1.5, 0.1, 0.35, 0.25).pose(tp + 1.4, 0.6, yaw=10, pitch=8)
    P.arm(tp + 0.6, "r", P_CHIN_R, 0.6)                                     # rubs his beard
    P.arm(tp + 2.6, "r", None, 0.7)
    P.nod(tp + 1.9, 2.5, 0.5)
    # L03b Jesus: mysterious, serene - "my Father has willed it"
    t3b = T("L03b") - 0.55
    J.pose(t3b, 0.01, yaw=17, pitch=0, roll=0).look(t3b, 0.35, 0.05).expr(t3b, "knowing", 0.01, m_smile=0.25, m_smirk=0.12)
    J.look(T("L03b", seg=1) + 0.2, 0.15, -0.55, 0.3).pose(T("L03b", seg=1) + 0.1, 0.9, pitch=-8, roll=-2)
    J.expr(T("L03b", seg=1) + 0.2, "peace", 0.8, m_smile=0.28)
    J.look(T("L03b", seg=2) - 0.1, 0.36, 0.05, 0.3).pose(T("L03b", seg=2) - 0.2, 0.9, pitch=1, roll=0, hx=0.04)
    J.expr(T("L03b", seg=2), "resolute", 0.8, m_smile=0.12)
    J.nod(T("L03b", seg=3) + 0.5, 2.5, 0.7)
    J.arm(T("L03b", seg=2) - 0.25, "l", G_HEART_L, 0.9)                      # "He has sent me..." - a hand to his chest
    J.arm(T("L03b", "end") + 0.3, "l", None, 1.0)
    J.blinks(T("L03b"), 0.5)
    J.blinks(T("L03b", "end"), 1.0)
    # Eli puzzled by the answer
    te = T("L03b", "end") + 0.2
    E.pose(te, 0.01, yaw=-20, pitch=0, roll=0).look(te, -0.35, 0.0).expr(te, "confused", 0.01, bfur=0.35)
    E.pose(te + 0.5, 0.8, roll=5, pitch=-2)
    # L04 Jesus: gentle, perceptive
    J.pose(T("L04") - 0.3, 0.01, yaw=17, pitch=1, roll=1).look(T("L04") - 0.3, 0.35, 0.05).expr(T("L04") - 0.3, "gentle", 0.01)
    J.expr(T("L04", seg=1), "compassion", 0.8)
    J.expr(T("L04", seg=2), "sad_smile", 1.0)
    J.pose(T("L04", seg=2), 1.0, yaw=19, pitch=3, roll=3)
    J.arm(T("L04", seg=1) - 0.2, "r", CU_OPEN_R, 0.9)                        # a small open palm toward them
    J.arm(T("L04", "end") + 0.3, "r", None, 1.0)
    # Eli caught - glances away
    tca = T("L04", word="ate") - 0.35
    E.pose(tca, 0.01, yaw=-20, pitch=0, roll=0).look(tca, -0.35, 0.0).expr(tca, "suspicious", 0.01)
    E.expr(T("L04", word="fill") - 0.2, "guilty", 0.6).look(T("L04", word="fill"), 0.15, 0.45, 0.25).pose(T("L04", word="fill"), 0.8, yaw=-8, pitch=7)
    # Miriam: looks down at her empty hands, then up
    tm = T("L04", "end") - 0.6
    M.pose(tm, 0.01, yaw=-18, pitch=6).look(tm, -0.1, 0.5).expr(tm, "ashamed", 0.01)
    M.look(tm + 1.2, -0.35, 0.0, 0.3).pose(tm + 1.1, 0.8, yaw=-20, pitch=0).expr(tm + 1.1, "hopeful", 0.8, wet=0.3)
    # L05 Jesus earnest, reaching out with an open hand
    J.pose(T("L05") - 0.35, 0.01, yaw=15, pitch=0, roll=0).look(T("L05") - 0.35, 0.35, 0.05).expr(T("L05") - 0.35, "compassion", 0.01)
    J.arm(T("L05", seg=1) - 0.3, "r", G_TEACH_M, 0.8)
    J.expr(T("L05", seg=1), "warm", 0.8)
    J.pose(T("L05", seg=1), 0.8, yaw=18, pitch=-2, hx=0.05)
    J.arm(T("L05", seg=2) + 1.4, "r", None, 0.9)
    M.pose(T("L05", seg=2) - 0.15, 0.01, yaw=-18, pitch=0).look(T("L05", seg=2) - 0.15, -0.35, -0.05).expr(T("L05", seg=2) - 0.15, "hopeful", 0.01, wet=0.35)
    M.expr(T("L05", seg=2) + 0.8, "longing", 1.0, wet=0.5).pose(T("L05", seg=2) + 0.8, 1.0, roll=-4)
    # L06 'God the Father' - glance upward
    J.pose(T("L06") - 0.25, 0.01, yaw=16, pitch=0).look(T("L06") - 0.25, 0.3, 0.0).expr(T("L06") - 0.25, "gentle", 0.01)
    J.look(T("L06", word="god") - 0.15, 0.15, -0.65, 0.3).pose(T("L06", word="god") - 0.2, 0.7, pitch=-8)
    J.expr(T("L06", word="god"), "peace", 0.6, m_smile=0.25)
    J.look(T("L06", word="seal") - 0.2, 0.32, 0.05, 0.3).pose(T("L06", word="seal") - 0.2, 0.7, pitch=1)
    # L07 Peter: practical, sincere
    t7 = T("L07") - 0.6
    P.pose(t7, 0.01, yaw=20, pitch=0, roll=0).look(t7, 0.45, 0.0).expr(t7, "confused", 0.01, bfur=0.15)
    P.arm(T("L07") - 0.55, "r", P_SCRATCH_MID, 0.45)                          # hand comes up in front...
    P.arm(T("L07") - 0.15, "r", P_SCRATCH_R, 0.55)                            # ...and scratches the back of his head
    P.arm(T("L07", seg=1) - 0.2, "r", P_SCRATCH_MID, 0.5)
    P.arm(T("L07", seg=1) + 0.3, "r", P_ASK_R, 0.85)
    P.expr(T("L07", seg=1), "anxious", 0.6, bi_l=0.35, bi_r=0.35)
    P.arm(T("L07", "end") + 0.8, "r", None, 0.8)
    J.pose(t7, 0.01, yaw=-8).look(t7, -0.3, 0.0).expr(t7, "gentle", 0.01)
    # L08 Jesus to Peter: warm; "so that we may glorify Him, and the Son"
    J.pose(T("L08") - 0.4, 0.01, yaw=-14, pitch=0, roll=-2).look(T("L08") - 0.4, -0.35, 0.0).expr(T("L08") - 0.4, "warm", 0.01)
    J.expr(T("L08", seg=1), "warm", 0.5, m_smile=0.5)
    J.nod(T("L08", seg=1) + 0.4, 4, 0.6)
    J.look(T("L08", seg=2), -0.1, -0.5, 0.3).pose(T("L08", seg=2) - 0.1, 0.8, pitch=-7, yaw=-6)
    J.expr(T("L08", seg=2), "peace", 0.6, m_smile=0.35)
    J.look(T("L08", "end") + 0.2, -0.35, 0.0, 0.3).pose(T("L08", "end"), 0.8, pitch=0, yaw=-12)
    J.arm(T("L08", seg=1) - 0.2, "l", CU_OPEN_L, 0.9)
    J.arm(T("L08", "end") + 0.2, "l", None, 1.0)
    P.nod(T("L08", seg=1) + 1.4, 3, 0.6)
    # L09 Eli: arms crossed, challenging, then lecturing with a raised finger
    t9 = T("L09") - 0.45
    E.pose(t9, 0.01, yaw=-20, pitch=2, roll=0).look(t9, -0.35, 0.0).expr(t9, "skeptical", 0.01)
    E.arm(t9, "r", E_CROSS_R, 0.01)
    E.arm(t9, "l", E_CROSS_L, 0.01)
    E.pose(T("L09", seg=1), 0.8, pitch=-4, roll=-3)
    E.expr(T("L09", seg=1), "indignant", 0.6, bfur=0.3)
    E.arm(T("L09", seg=2) - 0.5, "l", None, 0.6)
    E.arm(T("L09", seg=2) - 0.3, "r", E_POINT_R, 0.6)                        # index finger raised: making a point
    E.expr(T("L09", seg=2), "skeptical", 0.6, br_l=0.7)
    E.pose(T("L09", seg=2), 0.6, pitch=-6, yaw=-24)
    E.look(T("L09", word="as") - 0.05, -0.15, 0.4, 0.25)                     # "As it is written..." - recalling the words
    E.look(T("L09", word="he") - 0.1, -0.38, 0.0, 0.3)                       # ...and back to Jesus as he quotes them
    E.arm(T("L09", "end") + 0.5, "r", None, 0.8)
    M.pose(t9, 0.01, yaw=-14, pitch=2).look(t9, 0.25, 0.0).expr(t9, "anxious", 0.01)
    M.look(T("L09", seg=1), -0.3, 0.0, 0.3)
    # Jesus listening to Eli
    tj9 = T("L09", seg=1) + 0.4
    J.pose(tj9, 0.01, yaw=17, pitch=1, roll=0).look(tj9, 0.35, 0.05).expr(tj9, "gentle", 0.01)
    J.expr(tj9 + 1.0, "compassion", 1.2).nod(tj9 + 2.2, 2.0, 0.7)
    # L10 Jesus: steady, then lifts eyes at "my Father"
    J.pose(T("L10") - 0.5, 0.01, yaw=17, pitch=0, roll=0).look(T("L10") - 0.5, 0.35, 0.05).expr(T("L10") - 0.5, "firm", 0.01, m_press=0.1)
    J.expr(T("L10", seg=1), "resolute", 0.8)
    J.arm(T("L10", seg=1) - 0.15, "r", CU_NOT_R, 0.8)
    J.arm(T("L10", seg=2) + 0.2, "r", None, 1.0)
    J.look(T("L10", seg=2) + 0.6, 0.15, -0.6, 0.3).pose(T("L10", seg=2) + 0.5, 0.9, pitch=-9, roll=-2)
    J.expr(T("L10", seg=2) + 0.6, "peace", 0.8, m_smile=0.3)
    J.look(T("L10", "end") - 1.0, 0.33, 0.05, 0.3).pose(T("L10", "end") - 1.0, 0.8, pitch=0, roll=1)
    J.expr(T("L11"), "warm", 0.8)
    J.arm(T("L11") + 0.3, "l", G_HEART_L, 0.9)
    J.arm(T("L11", "end") - 0.6, "l", None, 0.9)
    # Eli bristles at "it is not society who has given you the bread from heaven"
    te10 = T("L10", seg=1) + 0.9
    E.arm(te10, "r", None, 0.01).arm(te10, "l", None, 0.01)
    E.pose(te10, 0.01, yaw=-20, pitch=0, roll=0).look(te10, -0.35, 0.0).expr(te10, "skeptical", 0.01)
    E.expr(te10 + 0.5, "suspicious", 0.6, bfur=0.4).pose(te10 + 0.4, 0.8, roll=3, pitch=-2)   # bristles at "not society"
    # ...and is struck when the bread of God "comes down from heaven"
    te11 = T("L11", word="bread#1") - 0.12
    E.pose(te11, 0.01, yaw=-20, pitch=-1, roll=2).look(te11, -0.35, 0.0).expr(te11, "suspicious", 0.01, bfur=0.3)
    E.expr(T("L11", word="comes") + 0.05, "surprised", 0.3, m_open=0.12, br_l=0.85, br_r=0.85, eo_l=1.2, eo_r=1.2)
    E.pose(T("L11", word="comes"), 0.35, pitch=-5, roll=0)
    E.expr(T("L11", word="heaven") + 0.1, "surprised", 0.5, m_open=0.04, br_l=0.7, br_r=0.7, eo_l=1.12, eo_r=1.12)
    # Miriam: hope rising
    th = T("L11", seg=1) - 0.2
    M.pose(th, 0.01, yaw=-17, pitch=-1, roll=0).look(th, -0.38, -0.05).expr(th, "hopeful", 0.01, wet=0.6)
    M.expr(th + 1.2, "longing", 1.0, wet=0.9).pose(th + 1.0, 1.2, roll=-3, pitch=-3)
    # L12 Miriam's plea
    t12 = T("L12") - 0.9
    M.pose(t12, 0.01, yaw=-18, pitch=-2, roll=-2).look(t12, -0.4, -0.05).expr(t12, "longing", 0.01, wet=0.9)
    M.arm(t12 + 0.2, "l", M_CLUTCH_L, 0.9)
    M.expr(T("L12"), "pleading", 0.6)
    # (eyes wet with longing, no tear yet)
    M.hold_eyes(T("L12"), T("L12", "end"))
    # L13/L14 Jesus: "I am the bread of life"
    t13 = T("L13") - 1.2
    J.pose(t13, 0.01, yaw=20, pitch=2, roll=2).look(t13, 0.38, 0.12).expr(t13, "compassion", 0.01, wet=0.25)
    J.expr(t13 + 0.6, "moved", 1.0, wet=0.35, m_smile=0.25)
    J.arm(T("L13") - 0.3, "l", G_HEART_L, 0.9)
    J.hold_eyes(T("L13") - 0.5, T("L13", "end"))
    J.pose(T("L13", "end"), 1.2, pitch=4, roll=3)
    J.expr(T("L14"), "warm", 1.0, wet=0.3)
    J.arm(T("L14", seg=1), "l", None, 0.9)
    J.arm(T("L14", seg=1) - 0.3, "r", G_OFFER_R, 1.0)                       # reaches out to them, palm open
    J.arm(T("L14", "end") + 0.9, "r", None, 1.0)
    # Miriam: tear falls, smile breaks through
    tt = T("L14", seg=1) - 0.25
    M.pose(tt, 0.01, yaw=-18, pitch=-1, roll=-2).look(tt, -0.4, -0.05).expr(tt, "moved", 0.01, wet=1.0, m_smile=0.1)
    M.tear("r", tt + 1.0, tt + 2.9)                                         # one tear, partway into the beat
    M.expr(tt + 1.4, "moved", 1.2, m_smile=0.55)
    M.arm(tt, "l", M_CLUTCH_L, 0.01)
    M.arm(tt + 2.5, "l", None, 1.0)
    # two-shot end of scene 1
    te1 = T("L14", "end") - 1.2
    J.pose(te1, 0.01, yaw=20, pitch=2, roll=0).look(te1, 0.4, 0.1).expr(te1, "warm", 0.01, wet=0.25)
    M.pose(te1, 0.01, yaw=-22, pitch=-1).look(te1, -0.45, -0.1).expr(te1, "moved", 0.01, m_smile=0.5, wet=0.8)

    # ---------------- SCENE 2 ----------------
    ts2 = T.scene_end["shore"] + 1.1
    J.pose(ts2, 0.01, yaw=20, pitch=0, roll=0).look(ts2, 0.3, 0.05).expr(ts2, "gentle", 0.01)
    J.arm(ts2 + 0.8, "r", dict(G_REACH_R, beat=0.9), 1.1)                    # teaching, arm out toward the crowd
    J.arm(T("L15", word="murmur") - 0.8, "r", dict(G_TEACH_R, beat=0.7), 1.0)
    J.arm(T("L16") - 1.0, "r", None, 0.9)
    J.mime(ts2 + 0.6, T("L16") - 1.2)                                          # we see him teach under the narration
    J.look(ts2 + 2.5, 0.42, 0.08, 0.3).look(ts2 + 4.2, 0.3, -0.02, 0.3).look(ts2 + 6.0, 0.45, 0.1, 0.3)
    # Eli grumbles to the man beside him
    tg = T("L16") - 0.6
    E.pose(tg, 0.01, yaw=14, pitch=3, roll=4).look(tg, 0.45, 0.05).expr(tg, "grumble", 0.01)
    X.pose(tg, 0.01, yaw=-26, pitch=2).look(tg, -0.4, 0.0).expr(tg, "suspicious", 0.01)
    E.look(T("L16", word="joseph") - 0.2, -0.4, 0.0, 0.2).pose(T("L16", word="joseph") - 0.45, 0.9, yaw=-18)
    E.look(T("L16", "end") + 0.1, 0.45, 0.05, 0.2).pose(T("L16", "end"), 0.8, yaw=14)
    X.expr(T("L17") - 0.1, "indignant", 0.3).nod(T("L17") + 0.3, 3.0, 0.5)
    E.nod(T("L17") + 0.5, 3.0, 0.6)
    E.expr(T("L18"), "indignant", 0.4)
    E.arm(T("L18") + 0.1, "l", E_TOWARD_L, 0.6)
    E.pose(T("L18"), 0.5, yaw=-10, roll=-3)
    E.look(T("L18"), -0.2, 0.0, 0.2)
    E.arm(T("L18", "end") + 0.6, "l", None, 0.7)
    # Jesus hears it
    t19 = T("L19") - 0.9
    J.pose(t19, 0.01, yaw=8, pitch=0, roll=0).look(t19, 0.1, 0.0).expr(t19, "gentle", 0.01)
    J.pose(t19 + 0.3, 0.7, yaw=22).look(t19 + 0.3, 0.4, 0.05, 0.2)
    J.expr(T("L19") - 0.15, "intense", 0.35, bi_l=-0.5, bi_r=-0.5, bfur=0.75, eo_l=0.86, eo_r=0.86, lo_l=0.12, lo_r=0.12,
           m_smile=-0.3, m_press=0.2)                                      # irritated: brows down, eyes narrowed
    J.pose(T("L19") - 0.1, 0.35, pitch=3, roll=-1).nod(T("L19", word="among") - 0.05, 2.5, 0.35)
    J.expr(T("L19", "end") + 0.15, "firm", 0.5)
    J.pose(T("L19", "end") + 0.2, 0.8, pitch=0, roll=0)
    J.expr(T("L19", "end") + 0.75, "compassion", 0.9)
    # L20
    t20 = T("L20") - 0.6
    J.pose(t20, 0.01, yaw=17, pitch=0, roll=0).look(t20, 0.35, 0.05).expr(t20, "compassion", 0.01)
    J.expr(T("L20", seg=1), "warm", 1.0)
    J.arm(T("L20", seg=1) - 0.2, "r", CU_RAISE_R, 0.9)
    te20 = T("L20", seg=1) - 0.1
    E.pose(te20, 0.01, yaw=-18, pitch=2, roll=0).look(te20, -0.35, 0.0).expr(te20, "suspicious", 0.01)
    E.expr(te20 + 1.3, "hurt", 1.2).look(te20 + 1.7, 0.2, 0.35, 0.3).pose(te20 + 1.6, 0.9, yaw=-8, pitch=6)
    # L21 - "It is written in the Prophets" - reaches out to them
    t21 = T("L20", "end") - 0.4
    J.pose(t21, 0.01, yaw=16, pitch=0).look(t21, 0.33, 0.05).expr(t21, "gentle", 0.01)
    J.arm(T("L21") - 0.2, "r", G_TEACH_M, 0.8)
    J.arm(T("L21", seg=1) - 0.3, "r", G_UP_M, 0.8)                           # "taught by God"
    J.look(T("L21", seg=1), 0.2, -0.45, 0.3).pose(T("L21", seg=1), 0.8, pitch=-7)
    J.arm(T("L21", seg=2) - 0.1, "r", G_REACH_M, 0.9)
    J.look(T("L21", seg=2) + 0.1, 0.35, 0.05, 0.3).pose(T("L21", seg=2), 0.8, pitch=0)
    J.expr(T("L21", seg=2), "warm", 0.8)
    J.arm(T("L21", "end") + 0.4, "r", None, 0.9)
    tm21 = T("L21", seg=2) - 0.25
    M.pose(tm21, 0.01, yaw=-18, pitch=0, roll=-2).look(tm21, -0.4, 0.0).expr(tm21, "moved", 0.01, m_smile=0.2, wet=0.5)
    M.nod(tm21 + 1.0, 2.5, 0.7)
    # L22 "I am the living bread" (strong beam)
    t22 = T("L22") - 1.0
    J.pose(t22, 0.01, yaw=18, pitch=0, roll=0).look(t22, 0.32, 0.05).expr(t22, "peace", 0.01)
    J.arm(T("L22") - 0.2, "l", G_HEART_L, 0.9)
    J.expr(T("L22"), "resolute", 0.6, m_smile=0.15)
    J.arm(T("L22", seg=1) + 0.4, "l", None, 0.9)
    J.expr(T("L22", seg=1), "warm", 0.8)
    te22 = T("L22", seg=1) + 0.2
    E.pose(te22, 0.01, yaw=-18, pitch=2, roll=0).look(te22, -0.35, 0.0).expr(te22, "suspicious", 0.01)
    E.expr(te22 + 0.6, "grumble", 0.6).pose(te22 + 0.6, 0.7, roll=-4, pitch=-2)
    E.mime(te22 + 0.75, te22 + 2.1, 0.32)                                  # mutters something under his breath
    J.pose(T("L22", "end") - 0.3, 0.01, yaw=18, pitch=0, roll=0).look(T("L22", "end") - 0.3, 0.33, 0.05)
    # L23 "This bread is my flesh" - grave, knowing
    J.expr(T("L23") - 0.3, "compassion", 0.8)
    J.expr(T("L23", seg=1) - 0.2, "sorrow", 1.2, wet=0.8, m_smile=0.0)
    J.tear("l", T("L23", seg=1) + 0.35, T("L23", seg=1) + 2.6, dry=T("L23", "end") + 0.6)
    J.look(T("L23", seg=1) - 0.1, 0.2, 0.3, 0.4).pose(T("L23", seg=1) - 0.2, 1.0, pitch=6, roll=2)
    tp23 = T("L23", "end") - 0.25
    P.pose(tp23, 0.01, yaw=-18, pitch=0, roll=-3).look(tp23, -0.42, 0.0).expr(tp23, "anxious", 0.01, bi_l=0.6, bi_r=0.6, wet=0.4)
    P.look(tp23 + 0.5, -0.3, 0.3, 0.3).pose(tp23 + 0.45, 0.8, pitch=6)
    J.look(T("L23", "end") - 0.4, 0.35, 0.05, 0.4).pose(T("L23", "end") - 0.6, 1.0, pitch=1)
    # L24 Eli's outburst
    t24 = T("L24") - 0.35
    E.pose(t24, 0.01, yaw=-20, pitch=-2, roll=0).look(t24, -0.35, 0.0).expr(t24, "shocked", 0.01)
    E.expr(T("L24", seg=1), "indignant", 0.4, bfur=0.8)
    E.arm(T("L24", seg=1) - 0.2, "l", E_OUTBURST_L, 0.5)
    E.pose(T("L24", seg=1), 0.5, pitch=-6, roll=-4)
    E.arm(T("L24", "end") + 0.4, "l", None, 0.7)
    X.pose(t24, 0.01, yaw=-22).look(t24, -0.45, 0.0).expr(t24, "shocked", 0.01)
    X.pose(T("L24", seg=1) + 0.5, 0.8, yaw=18).look(T("L24", seg=1) + 0.5, 0.5, 0.0).expr(T("L24", seg=1) + 0.5, "confused", 0.4)
    # L25 Jesus intense; a slight shake of the head on "you have no life in you"
    t25 = T("L25") - 1.6
    J.pose(t25, 0.01, yaw=17, pitch=2, roll=0).look(t25, 0.35, 0.05).expr(t25, "compassion", 0.01)
    J.expr(T("L25") - 0.4, "intense", 0.8)
    J.hold_eyes(T("L25"), T("L25", "end"))
    J.pose(T("L25", seg=1), 1.2, pitch=-1, hx=0.06)
    J.expr(T("L25", seg=2), "intense", 0.6, bi_l=-0.2, bi_r=-0.2)
    J.shake(T("L25", seg=2) + 0.05, amp=4.5, dur=1.5, cycles=2)
    # reactions
    tmg = T("L25", "end") + 0.15
    M.pose(tmg, 0.01, yaw=-18, pitch=0, roll=0).look(tmg, -0.4, 0.0).expr(tmg, "shocked", 0.01)
    M.arm(tmg, "l", M_MOUTH_L, 0.35)                                        # hand to mouth
    M.expr(tmg + 0.4, "anxious", 0.6, eo_l=1.15, eo_r=1.15)
    tps = T("L25", "end") + 1.45
    P.pose(tps, 0.01, yaw=-18, pitch=1, roll=0).look(tps, -0.42, 0.0).expr(tps, "confused", 0.01, bfur=0.2, br_l=0.2, br_r=0.0, bi_l=0.1, eo_l=1.0, eo_r=0.95)
    P.expr(tps + 0.25, "confused", 0.45, bfur=0.45, br_l=1.65, br_r=-0.45, bi_l=0.3, bi_r=-0.35, eo_l=1.16, eo_r=0.8, m_smirk=-0.3)
    P.pose(tps + 0.2, 1.0, roll=5, pitch=-1)
    P.expr(tps + 1.9, "resolute", 0.7, bfur=0.3)
    P.nod(tps + 2.15, 1.5, 0.8)
    M.arm(T("L26"), "l", None, 1.0)
    # L26/L27 strong, steady
    t26 = T("L26") + 0.3
    J.pose(t26, 0.01, yaw=16, pitch=0, roll=0, hx=0.0).look(t26, 0.35, 0.05).expr(t26, "resolute", 0.01)
    J.arm(T("L26", seg=1) - 0.2, "r", G_REACH_M, 0.9)
    J.arm(T("L27") - 0.3, "r", G_SELF_R, 0.8)
    J.expr(T("L27"), "firm", 0.6, m_press=0.0)
    J.arm(T("L27", "end") + 0.4, "r", None, 0.9)
    # L28 intimate
    t28 = T("L28") - 0.8
    J.pose(t28, 0.01, yaw=19, pitch=3, roll=2).look(t28, 0.38, 0.1).expr(t28, "compassion", 0.01, wet=0.25)
    J.arm(T("L28", seg=1) - 0.5, "l", G_HEART_L, 0.9)
    J.expr(T("L28", seg=1), "moved", 0.8, m_smile=0.35, wet=0.3)
    J.arm(T("L28", "end") + 0.15, "l", None, 0.9)
    # L29 - "Just as the living Father sent me": eyes lifted toward heaven
    t29 = T("L29") - 0.45
    J.pose(t29, 0.01, yaw=16, pitch=0, roll=0).look(t29, 0.33, 0.05).expr(t29, "warm", 0.01)
    J.look(T("L29") - 0.05, 0.12, -0.7, 0.35).pose(T("L29") - 0.1, 1.0, pitch=-14, roll=-2)
    J.expr(T("L29"), "peace", 0.8, m_smile=0.3, bi_l=0.2, bi_r=0.2, br_l=0.25, br_r=0.25, glint=1.0)
    J.look(T("L29", word="and") - 0.15, 0.35, 0.05, 0.35).pose(T("L29", word="and") - 0.3, 1.1, pitch=0, roll=0)
    J.expr(T("L29", word="and"), "warm", 0.9)
    te29 = T("L29", seg=1) - 0.1
    E.pose(te29, 0.01, yaw=-18, pitch=1, roll=0).look(te29, -0.35, 0.0).expr(te29, "suspicious", 0.01)
    E.expr(te29 + 0.3, "anxious", 0.7, eo_l=1.12, eo_r=1.12, bfur=0.35, m_press=0.45, m_smile=-0.25)  # unsettled, staring
    E.shake(te29 + 0.9, amp=2.2, dur=1.3, cycles=1.5)                      # a small "no" to himself
    E.pose(te29 + 1.0, 0.8, pitch=-2, roll=2)
    # Eli at "Your ancestors ate manna, and died..."
    te30 = T("L30", seg=1) - 0.15
    E.pose(te30, 0.01, yaw=-18, pitch=2, roll=0).look(te30, -0.35, 0.0).expr(te30, "suspicious", 0.01)
    E.expr(te30 + 0.35, "indignant", 0.35, m_open=0.16, br_l=0.35, br_r=0.35, bfur=0.4)   # draws breath to object
    E.pose(te30 + 0.3, 0.4, pitch=-4)
    E.expr(te30 + 1.25, "hurt", 0.8, m_open=0.0, m_press=0.5, wet=0.55, bi_l=0.55, bi_r=0.55, lo_l=0.2, lo_r=0.2)  # ...and says nothing
    E.pose(te30 + 1.2, 1.0, yaw=-12, pitch=3).look(te30 + 1.3, -0.45, 0.05, 0.3)
    # L30 final, warm and certain
    t30 = T("L30") - 0.6
    J.pose(t30, 0.01, yaw=18, pitch=1, roll=1).look(t30, 0.35, 0.05).expr(t30, "compassion", 0.01, wet=0.2)
    J.expr(T("L30", seg=1), "compassion", 0.8, wet=0.25)
    J.expr(T("L30", seg=2), "moved", 1.0, m_smile=0.4, wet=0.3)
    J.arm(T("L30", seg=2) - 0.2, "r", G_REACH_M, 1.0)
    J.arm(T("L30", "end") + 0.6, "r", None, 1.0)
    J.hold_eyes(T("L30", seg=2), T("L30", "end"))

    # ---------------- SCENE 3 ----------------
    tel = T("L32") - 0.5
    E.pose(tel, 0.01, yaw=-22, pitch=4, roll=0).look(tel, -0.3, 0.1).expr(tel, "hurt", 0.01)
    E.expr(T("L32"), "hurt", 0.4, bfur=0.5, wet=0.3)
    E.look(T("L32", seg=1) - 0.1, 0.3, 0.4, 0.3).pose(T("L32", seg=1) - 0.2, 0.8, yaw=-8, pitch=8)
    E.expr(T("L32", seg=1), "sorrow", 0.6, wet=0.4)
    # Jesus watches them go - serene trust: "Father, even if they leave me..."
    tj = T("L34") - 3.2
    J.pose(tj, 0.01, yaw=24, pitch=1, roll=0).look(tj, 0.45, 0.0).expr(tj, "peace", 0.01, m_smile=0.12, wet=0.0)
    J.look(tj + 0.9, 0.2, -0.55, 0.4).pose(tj + 0.8, 1.2, pitch=-9, roll=-2)    # a silent glance to heaven
    J.expr(tj + 1.0, "peace", 0.8, m_smile=0.3, bi_l=0.15, bi_r=0.15)
    J.look(tj + 2.2, 0.15, 0.05, 0.35).pose(tj + 2.1, 1.1, yaw=12, pitch=2)   # turns to Peter, who stands to his right
    J.expr(T("L34") - 0.3, "compassion", 0.6, m_smile=0.12, wet=0.0, bi_l=0.25, bi_r=0.25)
    J.look(T("L34"), 0.35, 0.05, 0.3)
    J.hold_eyes(T("L34"), T("L34", "end"))
    # Peter's answer: he does not fully understand, but he will not leave
    tp = T("L35") - 0.7
    P.pose(tp, 0.01, yaw=-18, pitch=2, roll=0).look(tp, -0.4, 0.05).expr(tp, "tearful", 0.01, m_smile=-0.2)
    P.expr(T("L35"), "pleading", 0.5, wet=0.9)
    P.pose(T("L35", seg=1), 0.8, pitch=-2, roll=3)
    P.expr(T("L35", seg=2), "moved", 0.8, m_smile=0.25, wet=1.0)
    P.tear("l", T("L35", seg=1) + 0.4, T("L35", seg=1) + 3.6)
    P.arm(T("L35", seg=1) - 0.2, "l", CU_OPEN_L, 0.8)
    P.arm(T("L35", seg=2) + 0.8, "l", None, 1.0)
    tpm = T("L36") - 0.2
    M.pose(tpm, 0.01, yaw=-20, pitch=0, roll=-2).look(tpm, -0.35, 0.0).expr(tpm, "moved", 0.01, m_smile=0.35, wet=1.0)
    M.nod(tpm + 0.5, 3, 0.7).nod(tpm + 1.3, 2.5, 0.7)
    tp2 = T("L36") + 1.6
    P.pose(tp2, 0.01, yaw=-18, pitch=0, roll=0).look(tp2, -0.4, 0.05).expr(tp2, "resolute", 0.01, wet=0.8, bi_l=0.4, bi_r=0.4)
    P.expr(T("L36", seg=1) + 0.3, "moved", 0.8, m_smile=0.4, wet=0.9)
    P.arm(T("L36") - 0.1, "r", P_HEART_R, 0.9)
    P.arm(T("L36", "end") + 0.15, "r", None, 0.8)
    # bread: Jesus smiles, breaks it and gives half to Peter
    tf = TF
    J.pose(tf, 0.01, yaw=18, pitch=2, roll=0).look(tf, 0.35, 0.05).expr(tf, "warm", 0.01, m_smile=0.45, wet=0.0)
    J.arm(tf, "r", G_BREAD_R, 0.01)
    J.arm(tf, "l", G_BREAD_L, 0.01)
    J.arm(tf + 1.2, "r", G_GIVE_R, 1.4)                                       # breaks it and holds half out
    J.look(tf + 0.2, 0.15, 0.45, 0.3).look(tf + 1.5, 0.4, 0.05, 0.3)
    J.arm(tf + 3.3, "r", None, 1.2)                                           # lets go
    P.pose(tf, 0.01, yaw=-18, pitch=2).look(tf, -0.35, 0.05).expr(tf, "moved", 0.01, m_smile=0.45, wet=0.8)
    P.arm(tf + 1.7, "l", P_TAKE_L, 1.1)                                       # cupped hand under it
    P.look(tf + 1.9, -0.3, 0.4, 0.3).pose(tf + 1.9, 0.8, pitch=6)            # looks down at the bread
    P.arm(tf + 3.35, "l", P_KEEP_L, 0.9)                                      # and draws it close
    P.look(tf + 3.5, -0.38, 0.05, 0.35).pose(tf + 3.4, 0.9, pitch=2).expr(tf + 3.5, "moved", 0.8, m_smile=0.55, wet=0.9)
    M.pose(tf, 0.01, yaw=-20, pitch=0).look(tf, -0.4, 0.05).expr(tf, "joy", 0.01, wet=0.6)
    # L37 the prayer: eyes lifted, holding his half of the bread
    tpr = T("L37") - 0.45
    J.arm(tpr, "r", None, 0.01)
    J.arm(tpr, "l", G_PRAY_L, 0.01)
    J.pose(tpr, 0.01, yaw=10, pitch=-10, roll=-2).look(tpr, 0.1, -0.6).expr(tpr, "peace", 0.01, m_smile=0.2, wet=0.0)
    J.expr(T("L37", seg=1), "peace", 0.8, m_smile=0.25, bi_l=0.2, bi_r=0.2)
    J.pose(T("L37", seg=2) - 0.2, 1.2, pitch=-13, roll=-3)
    # "...and even if they leave me" - he looks out along the shore where they went
    J.look(T("L37", seg=3) - 0.4, 0.5, -0.05, 0.5).pose(T("L37", seg=3) - 0.5, 1.4, yaw=24, pitch=-2, roll=0)
    J.expr(T("L37", seg=3), "compassion", 1.0, m_smile=0.15, wet=0.0)
    # "...with a part of you too" - eyes lifted to the Father once more
    J.look(T("L37", word="with") - 0.3, 0.2, -0.65, 0.4).pose(T("L37", word="with") - 0.4, 1.2, yaw=14, pitch=-10)
    J.expr(T("L37", word="with"), "peace", 0.9, m_smile=0.3, wet=0.0)
    # then a quiet smile to his friends as the title rises
    J.look(T("L37", "end") + 0.6, 0.4, 0.05, 0.5).pose(T("L37", "end") + 0.5, 1.3, yaw=18, pitch=2, roll=0)
    J.expr(T("L37", "end") + 0.6, "warm", 1.0, m_smile=0.4, wet=0.0)
    J.blinks(tpr, 0.6)
    P.pose(T("L37", seg=3) - 0.3, 0.01, yaw=-18, pitch=2).look(T("L37", seg=3) - 0.3, -0.35, 0.05).expr(T("L37", seg=3) - 0.3, "peace", 0.01, m_smile=0.35)
    P.arm(T("L37", seg=3) - 0.3, "l", P_KEEP_L, 0.01)                         # still holding the bread he was given
    M.pose(T("L37", seg=3) - 0.3, 0.01, yaw=-20, pitch=0).look(T("L37", seg=3) - 0.3, -0.4, 0.05).expr(T("L37", seg=3) - 0.3, "moved", 0.01, m_smile=0.5, wet=0.5)
    return {"jesus": J, "peter": P, "miriam": M, "eli": E, "man2": X}


if __name__ == "__main__":
    for s in SHOTS:
        print(f"{s['t0']:7.2f} {s['name']}")
    print(len(SHOTS), "shots, total", T.total)
