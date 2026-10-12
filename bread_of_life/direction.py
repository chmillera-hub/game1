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

NECK = {"jesus": 1.72, "peter": 1.70, "miriam": 1.62, "eli": 1.72, "man2": 1.72}
EYE_Y = {"jesus": 0.03, "peter": 0.03, "miriam": 0.06, "eli": 0.04, "man2": 0.03}


def place(who, x, eye_y, S, **kw):
    """Character placement with the eyes at screen height eye_y (pixels)."""
    y = eye_y + (NECK[who] - EYE_Y[who]) * S
    d = dict(who=who, x=x, y=y, S=S)
    d.update(kw)
    return d


SHOTS = []

# Gesture vocabulary (arm targets are wrist positions in body units from the neck base)
G_TEACH_R = dict(target=(1.85, 2.1), hand="open", hand_ang=-104)
G_OFFER_R = dict(target=(2.1, 1.65), hand="open", hand_ang=-108)
G_UP_R = dict(target=(1.45, -0.35), hand="open", hand_ang=-160)
G_HEART_L = dict(target=(-0.4, 1.55), hand="flat", hand_ang=-68, thumb=-1, hand_scale=0.85)
G_FIRM_R = dict(target=(0.95, 1.85), hand="relaxed", hand_ang=-135)


def shot(t0, name, plate, pcam, chars, blur=0.0, cam=None, light=None, fx=(), grade="morning",
         trans=None, extras=None, title=None):
    SHOTS.append(dict(t0=t0, name=name, plate=plate, pcam=pcam, chars=chars, blur=blur,
                      cam=cam or {}, light=light or {}, fx=list(fx), grade=grade, trans=trans,
                      extras=extras or [], title=title))


# Lighting presets ------------------------------------------------------------
L_J_MORN = dict(light_x=-0.75, light_y=-0.5, rim=0.55, rim_x=-1.0)      # Jesus, sun behind-left
L_C_MORN = dict(light_x=0.7, light_y=-0.55, rim=0.25, rim_x=1.0)        # crowd, sun from right
L_SYN_J = dict(light_x=-0.55, light_y=-0.85, rim=0.45, rim_x=-1.0)
L_SYN_C = dict(light_x=-0.6, light_y=-0.8, rim=0.2, rim_x=-1.0)
L_DUSK_J = dict(light_x=0.8, light_y=-0.2, rim=0.7, rim_x=1.0)
L_DUSK_C = dict(light_x=-0.35, light_y=-0.3, rim=0.65, rim_x=-1.0)

# Crowd sprite layouts (seed, x, y, scale, yaw)
CROWD_SHORE = [(201, 90, 600, 1.0, -15), (202, 250, 585, 0.9, 10), (203, 600, 610, 1.05, -20),
               (204, 470, 590, 0.85, -5), (205, 690, 600, 0.95, -25), (206, 350, 575, 0.8, 15)]
CROWD_SYN = [(301, 70, 700, 1.0, -15), (302, 210, 690, 0.95, -20), (303, 350, 705, 1.0, -10),
             (304, 500, 695, 0.95, -18), (305, 650, 700, 1.0, -22), (306, 140, 640, 0.8, -12),
             (307, 430, 635, 0.8, -20), (308, 600, 640, 0.8, -15)]

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
shot(11.4, "ms_jesus_peter", "lake_morning", (0.45, 0.43, 0.95),
     [place("peter", 210, 455, 74, blur=1.6), place("jesus", 430, 470, 86)], blur=3.5,
     cam=dict(z0=1.0, z1=1.03, fx=360, fy=500), light=L_J_MORN, fx=["sun_glow", "bokeh_water"])
shot(16.6, "mcu_eli_arrives", "land_morning", (0.5, 0.42, 1.0),
     [place("miriam", 520, 470, 78, blur=3.0), place("eli", 330, 455, 118)], blur=6,
     cam=dict(z0=1.0, z1=1.04, fx=330, fy=455), light=L_C_MORN, extras=CROWD_SHORE, fx=["bokeh_land"])
shot(T("L03", "end") + 0.25, "cu_peter_knowing", "lake_morning", (0.35, 0.40, 1.1),
     [place("peter", 360, 440, 150)], blur=8, light=L_J_MORN, fx=["bokeh_water"],
     cam=dict(z0=1.0, z1=1.03, fx=360, fy=440))
shot(T("L04") - 0.5, "cu_jesus_l04", "lake_morning", (0.40, 0.40, 1.0),
     [place("jesus", 330, 430, 158)], blur=8, cam=dict(z0=1.0, z1=1.05, fx=330, fy=430),
     light=L_J_MORN, fx=["sun_glow", "bokeh_water"])
shot(T("L04", word="ate") - 0.35, "cu_eli_caught", "land_morning", (0.52, 0.42, 1.05),
     [place("eli", 390, 440, 150)], blur=8, light=L_C_MORN, extras=CROWD_SHORE[:3], fx=["bokeh_land"],
     cam=dict(z0=1.0, z1=1.02, fx=390, fy=440))
shot(T("L04", "end") - 0.6, "cu_miriam_listen", "land_morning", (0.46, 0.42, 1.05),
     [place("miriam", 380, 450, 150)], blur=8, light=L_C_MORN, extras=CROWD_SHORE[3:], fx=["bokeh_land"],
     cam=dict(z0=1.0, z1=1.02, fx=380, fy=450))
shot(T("L05") - 0.35, "mcu_jesus_l05", "lake_morning", (0.40, 0.41, 1.0),
     [place("jesus", 320, 455, 118)], blur=6, cam=dict(z0=1.0, z1=1.05, fx=320, fy=455),
     light=L_J_MORN, fx=["sun_glow", "bokeh_water"])
shot(T("L05", seg=2) - 0.15, "cu_miriam_l05", "land_morning", (0.46, 0.42, 1.05),
     [place("miriam", 380, 450, 155)], blur=8, light=L_C_MORN, extras=CROWD_SHORE[3:], fx=["bokeh_land"])
shot(T("L06") - 0.25, "cu_jesus_l06", "lake_morning", (0.38, 0.40, 1.0),
     [place("jesus", 340, 430, 160)], blur=8, cam=dict(z0=1.02, z1=1.06, fx=340, fy=430),
     light=L_J_MORN, fx=["sun_glow", "bokeh_water", "god_rays"])
shot(T("L07") - 0.6, "mcu_peter_l07", "lake_morning", (0.30, 0.42, 1.0),
     [place("jesus", 690, 470, 125, blur=3.5), place("peter", 300, 455, 125)], blur=6,
     light=L_J_MORN, fx=["bokeh_water"], cam=dict(z0=1.0, z1=1.03, fx=300, fy=455))
shot(T("L08") - 0.4, "cu_jesus_l08", "lake_morning", (0.48, 0.40, 1.0),
     [place("jesus", 380, 430, 158)], blur=8, light=L_J_MORN, fx=["sun_glow", "bokeh_water"],
     cam=dict(z0=1.0, z1=1.04, fx=380, fy=430))
shot(T("L09") - 0.45, "mcu_eli_l09", "land_morning", (0.52, 0.42, 1.0),
     [place("miriam", 560, 480, 82, blur=3.0), place("eli", 340, 455, 122)], blur=6, light=L_C_MORN,
     extras=CROWD_SHORE, fx=["bokeh_land"], cam=dict(z0=1.0, z1=1.04, fx=340, fy=455))
shot(T("L09", seg=1) + 0.4, "cu_jesus_listens_l09", "lake_morning", (0.40, 0.40, 1.0),
     [place("jesus", 330, 430, 158)], blur=8, light=L_J_MORN, fx=["sun_glow", "bokeh_water"])
shot(T("L09", seg=2) - 0.2, "cu_eli_l09b", "land_morning", (0.52, 0.42, 1.05),
     [place("eli", 380, 440, 152)], blur=8, light=L_C_MORN, extras=CROWD_SHORE[:3], fx=["bokeh_land"],
     cam=dict(z0=1.0, z1=1.03, fx=380, fy=440))
shot(T("L10") - 0.5, "cu_jesus_l10", "lake_morning", (0.40, 0.40, 1.0),
     [place("jesus", 330, 430, 160)], blur=8, cam=dict(z0=1.0, z1=1.07, fx=330, fy=430),
     light=L_J_MORN, fx=["sun_glow", "bokeh_water", "god_rays"])
shot(T("L10", seg=1) + 0.9, "cu_eli_l10", "land_morning", (0.52, 0.42, 1.05),
     [place("eli", 385, 440, 152)], blur=8, light=L_C_MORN, extras=CROWD_SHORE[:3], fx=["bokeh_land"],
     cam=dict(z0=1.0, z1=1.02, fx=385, fy=440))
shot(T("L10", seg=2) - 0.35, "cu_jesus_l10b", "lake_morning", (0.40, 0.40, 1.0),
     [place("jesus", 330, 430, 162)], blur=8, cam=dict(z0=1.02, z1=1.08, fx=330, fy=430),
     light=L_J_MORN, fx=["sun_glow", "bokeh_water", "god_rays"])
shot(T("L11", seg=1) - 0.2, "cu_miriam_hope", "land_morning", (0.46, 0.42, 1.05),
     [place("miriam", 380, 450, 158)], blur=8, light=L_C_MORN, fx=["bokeh_land"],
     cam=dict(z0=1.0, z1=1.03, fx=380, fy=450))
shot(T("L12") - 0.9, "cu_miriam_l12", "land_morning", (0.46, 0.42, 1.08),
     [place("miriam", 370, 455, 170)], blur=9, light=L_C_MORN, fx=["bokeh_land"],
     cam=dict(z0=1.0, z1=1.06, fx=370, fy=455))
shot(T("L13") - 1.2, "cu_jesus_l13", "lake_morning", (0.38, 0.40, 1.0),
     [place("jesus", 340, 440, 162)], blur=9, cam=dict(z0=1.0, z1=1.08, fx=340, fy=440),
     light=dict(L_J_MORN, rim=0.85), fx=["sun_glow_strong", "bokeh_water", "god_rays"])
shot(T("L14", seg=1) - 0.25, "cu_miriam_tear", "land_morning", (0.46, 0.42, 1.08),
     [place("miriam", 370, 455, 170)], blur=9, light=L_C_MORN, fx=["bokeh_land"],
     cam=dict(z0=1.02, z1=1.05, fx=370, fy=455))
shot(T("L14", "end") - 1.2, "ms_two_shot_end1", "lake_morning", (0.45, 0.43, 0.95),
     [place("miriam", 560, 500, 92, flip=False), place("jesus", 250, 470, 100)], blur=4,
     light=L_J_MORN, fx=["sun_glow", "bokeh_water", "god_rays"], cam=dict(z0=1.0, z1=1.04, fx=360, fy=500))

# =============================================================================
# SCENE 2 - SYNAGOGUE
# =============================================================================
s2 = T.scene_start["synagogue"]
shot(s1_end + 1.1, "syn_wide", "syn_side", (0.5, 0.48, 0.80),
     [place("jesus", 170, 560, 46, blur=0.5)], blur=1.0, cam=dict(z0=1.0, z1=1.06, fx=300, fy=600),
     light=L_SYN_J, fx=["beams", "dust", "syn_crowd_wide"], grade="synagogue", trans=("dissolve", 1.6))
shot(T("L16") - 0.6, "syn_eli_grumble", "syn_side", (0.62, 0.45, 1.05),
     [place("man2", 590, 520, 105, blur=2.0), place("eli", 300, 470, 130)], blur=6,
     light=L_SYN_C, fx=["beams", "dust"], grade="synagogue", cam=dict(z0=1.0, z1=1.03, fx=320, fy=470))
shot(T("L19") - 0.9, "syn_mcu_jesus_l19", "syn_front", (0.5, 0.42, 1.0),
     [place("jesus", 340, 460, 120)], blur=6, light=L_SYN_J, fx=["beams", "dust"], grade="synagogue",
     cam=dict(z0=1.0, z1=1.03, fx=340, fy=460))
shot(T("L20") - 0.6, "syn_cu_jesus_l20", "syn_front", (0.48, 0.40, 1.05),
     [place("jesus", 340, 435, 158)], blur=8, light=L_SYN_J, fx=["beams", "dust"], grade="synagogue",
     cam=dict(z0=1.0, z1=1.05, fx=340, fy=435))
shot(T("L20", seg=1) - 0.1, "syn_cu_eli_conflict", "syn_side", (0.6, 0.45, 1.05),
     [place("eli", 380, 440, 150)], blur=8, light=L_SYN_C, fx=["beams", "dust"], grade="synagogue")
shot(T("L20", "end") - 0.4, "syn_mcu_jesus_l21", "syn_front", (0.5, 0.42, 1.0),
     [place("jesus", 330, 460, 122)], blur=6, light=L_SYN_J, fx=["beams", "dust"], grade="synagogue",
     cam=dict(z0=1.0, z1=1.04, fx=330, fy=460))
shot(T("L21", seg=2) - 0.25, "syn_cu_miriam_l21", "syn_side", (0.4, 0.45, 1.05),
     [place("miriam", 370, 450, 152)], blur=8, light=L_SYN_C, fx=["beams", "dust"], grade="synagogue")
shot(T("L21", seg=2) + 2.6, "syn_mcu_jesus_l21b", "syn_front", (0.5, 0.42, 1.0),
     [place("jesus", 330, 460, 122)], blur=6, light=L_SYN_J, fx=["beams", "dust"], grade="synagogue")
shot(T("L22") - 1.0, "syn_cu_jesus_l22", "syn_front", (0.46, 0.40, 1.05),
     [place("jesus", 340, 440, 162)], blur=9, light=dict(L_SYN_J, rim=0.8), fx=["beams_strong", "dust"],
     grade="synagogue", cam=dict(z0=1.0, z1=1.08, fx=340, fy=440))
shot(T("L22", seg=1) + 0.2, "syn_cu_eli_l22", "syn_side", (0.6, 0.45, 1.05),
     [place("eli", 380, 440, 150)], blur=8, light=L_SYN_C, fx=["beams", "dust"], grade="synagogue")
shot(T("L22", "end") - 0.3, "syn_cu_jesus_l23", "syn_front", (0.46, 0.40, 1.05),
     [place("jesus", 340, 440, 164)], blur=9, light=dict(L_SYN_J, rim=0.8), fx=["beams_strong", "dust"],
     grade="synagogue", cam=dict(z0=1.02, z1=1.09, fx=340, fy=440))
shot(T("L23", "end") + 0.05, "syn_cu_peter_notices", "syn_side", (0.3, 0.45, 1.05),
     [place("peter", 380, 445, 150)], blur=8, light=L_SYN_C, fx=["beams", "dust"], grade="synagogue")
shot(T("L24") - 0.35, "syn_mcu_eli_l24", "syn_side", (0.62, 0.45, 1.0),
     [place("man2", 600, 540, 100, blur=2.5), place("eli", 330, 455, 132)], blur=6, light=L_SYN_C,
     fx=["beams", "dust"], grade="synagogue", cam=dict(z0=1.0, z1=1.05, fx=330, fy=455))
shot(T("L24", "end") + 0.15, "syn_uproar", "syn_side", (0.5, 0.48, 0.85),
     [], blur=2.5, light=L_SYN_C, fx=["beams", "dust", "syn_crowd_argue"], grade="synagogue",
     cam=dict(z0=1.0, z1=1.06, fx=360, fy=640))
shot(T("L25") - 1.6, "syn_cu_jesus_l25", "syn_front", (0.46, 0.40, 1.05),
     [place("jesus", 345, 440, 160)], blur=9, light=dict(L_SYN_J, rim=0.6), fx=["beams", "dust"],
     grade="synagogue_dark", cam=dict(z0=1.0, z1=1.12, fx=345, fy=430))
shot(T("L25", "end") + 0.2, "syn_miriam_gasp", "syn_side", (0.4, 0.45, 1.05),
     [place("miriam", 370, 450, 155)], blur=8, light=L_SYN_C, fx=["beams", "dust"], grade="synagogue")
shot(T("L25", "end") + 1.05, "syn_peter_steady", "syn_side", (0.3, 0.45, 1.05),
     [place("peter", 380, 445, 152)], blur=8, light=L_SYN_C, fx=["beams", "dust"], grade="synagogue")
shot(T("L26") + 0.5, "syn_mcu_jesus_l26", "syn_front", (0.5, 0.42, 1.0),
     [place("jesus", 330, 460, 124)], blur=6, light=L_SYN_J, fx=["beams", "dust"], grade="synagogue",
     cam=dict(z0=1.0, z1=1.05, fx=330, fy=460))
shot(T("L27") - 0.25, "syn_cu_jesus_l27", "syn_front", (0.47, 0.40, 1.05),
     [place("jesus", 345, 440, 158)], blur=9, light=dict(L_SYN_J, rim=0.6), fx=["beams", "dust"], grade="synagogue",
     cam=dict(z0=1.0, z1=1.04, fx=345, fy=440))
shot(T("L28") - 0.8, "syn_cu_jesus_l28", "syn_front", (0.46, 0.40, 1.05),
     [place("jesus", 340, 440, 165)], blur=9, light=dict(L_SYN_J, rim=0.7), fx=["beams_strong", "dust"],
     grade="synagogue", cam=dict(z0=1.0, z1=1.06, fx=340, fy=440))
shot(T("L29") - 0.45, "syn_mcu_jesus_l29", "syn_front", (0.5, 0.42, 1.0),
     [place("jesus", 330, 460, 124)], blur=6, light=L_SYN_J, fx=["beams", "dust"], grade="synagogue")
shot(T("L29", seg=1) - 0.1, "syn_cu_eli_unsettled", "syn_side", (0.6, 0.45, 1.05),
     [place("eli", 380, 440, 150)], blur=8, light=L_SYN_C, fx=["beams", "dust"], grade="synagogue")
shot(T("L29", seg=1) + 2.4, "syn_mcu_jesus_l29b", "syn_front", (0.5, 0.42, 1.0),
     [place("jesus", 330, 460, 124)], blur=6, light=L_SYN_J, fx=["beams", "dust"], grade="synagogue")
shot(T("L30", seg=1) - 0.15, "syn_cu_eli_l30", "syn_side", (0.6, 0.45, 1.05),
     [place("eli", 380, 440, 150)], blur=8, light=L_SYN_C, fx=["beams", "dust"], grade="synagogue",
     cam=dict(z0=1.0, z1=1.03, fx=380, fy=440))
shot(T("L30", seg=2) - 0.45, "syn_cu_jesus_l30b", "syn_front", (0.46, 0.40, 1.05),
     [place("jesus", 340, 440, 168)], blur=9, light=dict(L_SYN_J, rim=0.85), fx=["beams_strong", "dust"],
     grade="synagogue", cam=dict(z0=1.04, z1=1.12, fx=340, fy=440))
shot(T("L30") - 0.6, "syn_cu_jesus_l30", "syn_front", (0.46, 0.40, 1.05),
     [place("jesus", 340, 440, 165)], blur=9, light=dict(L_SYN_J, rim=0.8), fx=["beams_strong", "dust"],
     grade="synagogue", cam=dict(z0=1.0, z1=1.1, fx=340, fy=440))

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
shot(T("L34") - 2.6, "dusk_cu_jesus", "lake_dusk", (0.62, 0.40, 1.05),
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
shot(T("L36", "end") + 0.5, "dusk_final", "lake_dusk", (0.6, 0.43, 0.95),
     [place("miriam", 640, 590, 74, blur=1.5), place("peter", 500, 580, 80), place("jesus", 230, 560, 85)],
     blur=4, light=L_DUSK_J, fx=["sun_glow_dusk", "bokeh_dusk", "bread"], grade="dusk",
     cam=dict(z0=1.0, z1=1.04, fx=360, fy=640), title="John 6")

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
    # Jesus: opening - looking out over the water, peaceful, a little wistful
    J.pose(0.0, 0.01, yaw=22, pitch=-2, roll=-2).look(0.0, 0.3, -0.08).expr(0.0, "gentle", 0.01, eo_l=1.0, eo_r=1.0, lo_l=0.1, lo_r=0.1)
    J.hold_eyes(0.0, 1.4)
    J.blink(2.2)
    J.look(3.6, 0.15, 0.05, 0.3).expr(3.4, "peace", 1.4, eo_l=0.9, eo_r=0.9)
    # ms with Peter: Jesus calm, Peter notices the crowd coming
    J.pose(11.4, 0.01, yaw=18, pitch=0, roll=0).look(11.4, 0.3, 0.0)
    P.pose(0.0, 0.01, yaw=14, pitch=0).look(0.0, 0.4, 0.0).expr(0.0, "neutral", 0.01)
    P.expr(12.6, "surprised", 0.4, m_open=0.1).look(12.6, 0.55, 0.0, 0.15).pose(12.4, 0.5, yaw=22, pitch=-2)
    P.look(14.6, -0.35, 0.05, 0.2).pose(14.4, 0.6, yaw=-6).expr(14.6, "knowing", 0.6)  # glances at Jesus
    J.look(14.9, -0.25, 0.0, 0.2).expr(15.0, "knowing", 0.6, m_smile=0.22)  # quiet shared look
    # Eli arrives: out of breath, eager -> puzzled -> suspicious
    E.pose(0.0, 0.01, yaw=-20, pitch=-2).look(0.0, -0.3, 0.0).expr(0.0, "anxious", 0.01)
    E.pose(T("L03") - 0.3, 0.4, yaw=-22, pitch=-4, roll=3)
    E.expr(T("L03") - 0.2, "surprised", 0.3, m_open=0.0)
    E.expr(T("L03", seg=1), "confused", 0.5)
    E.pose(T("L03", seg=1), 0.6, yaw=-18, pitch=0, roll=-4)
    E.expr(T("L03", seg=2) + 0.6, "suspicious", 0.6)
    E.pose(T("L03", seg=2) + 0.6, 0.8, yaw=-24, pitch=4, roll=2)
    M.pose(0.0, 0.01, yaw=-16, pitch=2).look(0.0, -0.35, 0.05).expr(0.0, "anxious", 0.01, bi_l=0.3, bi_r=0.3)
    # Peter's knowing beat: he knows Jesus walked on the water last night
    tp = T("L03", "end") + 0.25
    P.pose(tp - 0.2, 0.01, yaw=16, pitch=0, roll=0).look(tp - 0.2, 0.45, 0.0).expr(tp - 0.2, "neutral", 0.01)
    P.look(tp + 0.5, 0.65, -0.05, 0.15).pose(tp + 0.45, 0.4, yaw=26)       # glance at Jesus
    P.expr(tp + 0.75, "knowing", 0.5, m_smile=0.4).look(tp + 1.5, 0.1, 0.35, 0.25).pose(tp + 1.4, 0.6, yaw=10, pitch=8)
    P.arm(tp + 0.9, "r", dict(target=(0.35, 0.15), hand="relaxed", hand_ang=175), 0.6)  # rubs beard
    P.arm(tp + 2.6, "r", None, 0.6)
    P.nod(tp + 1.9, 2.5, 0.5)
    # L04 Jesus: gentle, perceptive, a little sad
    J.pose(T("L04") - 0.5, 0.01, yaw=17, pitch=1, roll=1).look(T("L04") - 0.5, 0.35, 0.05).expr(T("L04") - 0.5, "gentle", 0.01)
    J.expr(T("L04", seg=1), "compassion", 0.8)
    J.expr(T("L04", seg=2), "sad_smile", 1.0)
    J.pose(T("L04", seg=2), 1.0, yaw=19, pitch=3, roll=3)
    # Eli caught - glances away
    E.pose(T("L04", word="ate") - 0.35, 0.01, yaw=-20, pitch=0, roll=0).look(T("L04", word="ate") - 0.35, -0.35, 0.0).expr(T("L04", word="ate") - 0.35, "suspicious", 0.01)
    E.expr(T("L04", word="fill") - 0.2, "guilty", 0.6).look(T("L04", word="fill"), 0.15, 0.45, 0.25).pose(T("L04", word="fill"), 0.8, yaw=-8, pitch=7)
    # Miriam: looks down at her empty hands, then up
    tm = T("L04", "end") - 0.6
    M.pose(tm, 0.01, yaw=-18, pitch=6).look(tm, -0.1, 0.5).expr(tm, "ashamed", 0.01)
    M.look(tm + 1.2, -0.35, 0.0, 0.3).pose(tm + 1.1, 0.8, yaw=-20, pitch=0).expr(tm + 1.1, "hopeful", 0.8, wet=0.3)
    # L05 Jesus earnest, open-palm gesture
    J.pose(T("L05") - 0.35, 0.01, yaw=15, pitch=0, roll=0).look(T("L05") - 0.35, 0.35, 0.05).expr(T("L05") - 0.35, "compassion", 0.01)
    J.arm(T("L05", seg=1) - 0.3, "r", G_TEACH_R, 0.7)
    J.expr(T("L05", seg=1), "warm", 0.8)
    J.pose(T("L05", seg=1), 0.8, yaw=18, pitch=-2, hx=0.05)
    J.arm(T("L05", seg=2) + 1.6, "r", None, 0.8)
    # Miriam hearing "which the Son of Man will give you"
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
    P.arm(T("L07"), "r", dict(target=(0.9, -0.6), hand="relaxed", hand_ang=-160), 0.6)  # scratches his head
    P.arm(T("L07", seg=1), "r", dict(target=(1.3, 2.0), hand="open", hand_ang=-120), 0.6)
    P.expr(T("L07", seg=1), "anxious", 0.6, bi_l=0.35, bi_r=0.35)
    P.arm(T("L07", "end") + 0.8, "r", None, 0.7)
    J.pose(t7, 0.01, yaw=-8).look(t7, -0.3, 0.0).expr(t7, "gentle", 0.01)
    # L08 Jesus to Peter: warm smile
    J.pose(T("L08") - 0.4, 0.01, yaw=-14, pitch=0, roll=-2).look(T("L08") - 0.4, -0.35, 0.0).expr(T("L08") - 0.4, "warm", 0.01)
    J.expr(T("L08", seg=1), "warm", 0.5, m_smile=0.5)
    J.nod(T("L08", seg=1) + 0.4, 4, 0.6)
    P.nod(T("L08", seg=1) + 1.4, 3, 0.6)
    # L09 Eli: arms crossed, challenging, then lecturing
    t9 = T("L09") - 0.45
    E.pose(t9, 0.01, yaw=-20, pitch=2, roll=0).look(t9, -0.35, 0.0).expr(t9, "skeptical", 0.01)
    E.arm(t9, "r", dict(target=(-1.15, 2.35), hand="none"), 0.01)
    E.arm(t9, "l", dict(target=(1.15, 2.5), hand="none"), 0.01)
    E.pose(T("L09", seg=1), 0.8, pitch=-4, roll=-3)
    E.expr(T("L09", seg=1), "indignant", 0.6, bfur=0.3)
    E.arm(T("L09", seg=2) - 0.4, "l", None, 0.5)
    E.arm(T("L09", seg=2) - 0.2, "r", dict(target=(-0.4, -0.2), hand="point", hand_ang=170), 0.6)  # finger raised
    E.expr(T("L09", seg=2), "skeptical", 0.6, br_l=0.7)
    E.pose(T("L09", seg=2), 0.6, pitch=-6, yaw=-24)
    E.arm(T("L09", "end") + 0.5, "r", None, 0.7)
    M.pose(t9, 0.01, yaw=-14, pitch=2).look(t9, 0.25, 0.0).expr(t9, "anxious", 0.01)  # glances at Eli
    M.look(T("L09", seg=1), -0.3, 0.0, 0.3)
    # Jesus listening to Eli: calm, steady, a hint of patience
    tj9 = T("L09", seg=1) + 0.4
    J.pose(tj9, 0.01, yaw=17, pitch=1, roll=0).look(tj9, 0.35, 0.05).expr(tj9, "gentle", 0.01)
    J.expr(tj9 + 1.0, "compassion", 1.2).nod(tj9 + 2.2, 2.0, 0.7)
    # L10 Jesus: steady, then lifts eyes at "my Father"
    J.pose(T("L10") - 0.5, 0.01, yaw=17, pitch=0, roll=0).look(T("L10") - 0.5, 0.35, 0.05).expr(T("L10") - 0.5, "firm", 0.01, m_press=0.1)
    J.expr(T("L10", seg=1), "resolute", 0.8)
    J.look(T("L10", seg=2) + 0.6, 0.15, -0.6, 0.3).pose(T("L10", seg=2) + 0.5, 0.9, pitch=-9, roll=-2)
    J.expr(T("L10", seg=2) + 0.6, "peace", 0.8, m_smile=0.3)
    J.look(T("L10", "end") - 1.0, 0.33, 0.05, 0.3).pose(T("L10", "end") - 1.0, 0.8, pitch=0, roll=1)
    J.expr(T("L11"), "warm", 0.8)
    J.arm(T("L11") + 0.3, "l", G_HEART_L, 0.8)
    J.arm(T("L11", "end") - 0.6, "l", None, 0.8)
    # Eli bristles at "it is not society who has given you the bread from heaven"
    te10 = T("L10", seg=1) + 0.9
    E.arm(te10, "r", None, 0.01).arm(te10, "l", None, 0.01)
    E.pose(te10, 0.01, yaw=-20, pitch=0, roll=0).look(te10, -0.35, 0.0).expr(te10, "skeptical", 0.01)
    E.expr(te10 + 0.4, "surprised", 0.35, m_open=0.08, br_l=0.6, br_r=0.6)
    E.expr(te10 + 1.3, "confused", 0.8).pose(te10 + 1.2, 0.8, roll=4, pitch=-3)
    # Miriam: hope rising
    th = T("L11", seg=1) - 0.2
    M.pose(th, 0.01, yaw=-17, pitch=-1, roll=0).look(th, -0.38, -0.05).expr(th, "hopeful", 0.01, wet=0.6)
    M.expr(th + 1.2, "longing", 1.0, wet=0.9).pose(th + 1.0, 1.2, roll=-3, pitch=-3)
    # L12 Miriam's plea
    t12 = T("L12") - 0.9
    M.pose(t12, 0.01, yaw=-18, pitch=-2, roll=-2).look(t12, -0.4, -0.05).expr(t12, "longing", 0.01, wet=0.9)
    M.arm(t12 + 0.2, "l", dict(target=(-0.3, 1.25), hand="relaxed", hand_ang=-140, thumb=1, hand_scale=0.8), 0.8)
    M.expr(T("L12"), "pleading", 0.6)
    M.tear("l", T("L12", seg=1) + 0.2, T("L12", seg=1) + 3.0)
    M.hold_eyes(T("L12"), T("L12", "end"))
    # L13/L14 Jesus: "I am the bread of life"
    t13 = T("L13") - 1.2
    J.pose(t13, 0.01, yaw=20, pitch=2, roll=2).look(t13, 0.38, 0.12).expr(t13, "compassion", 0.01, wet=0.3)
    J.expr(t13 + 0.6, "moved", 1.0, wet=0.45, m_smile=0.25)
    J.arm(T("L13") - 0.2, "l", dict(target=(-0.4, 1.55), hand="flat", hand_ang=-68, thumb=-1, hand_scale=0.85), 0.9)
    J.hold_eyes(T("L13") - 0.5, T("L13", "end"))
    J.pose(T("L13", "end"), 1.2, pitch=4, roll=3)
    J.expr(T("L14"), "warm", 1.0, wet=0.35)
    J.arm(T("L14", seg=1), "l", None, 0.9)
    J.arm(T("L14", seg=1) - 0.3, "r", G_OFFER_R, 0.9)
    J.arm(T("L14", "end") + 0.8, "r", None, 1.0)
    # Miriam: tear falls, smile breaks through
    tt = T("L14", seg=1) - 0.25
    M.pose(tt, 0.01, yaw=-18, pitch=-1, roll=-2).look(tt, -0.4, -0.05).expr(tt, "moved", 0.01, wet=1.0, m_smile=0.1)
    M.tear("r", tt + 0.3, tt + 3.2)
    M.expr(tt + 1.4, "moved", 1.2, m_smile=0.55)
    M.arm(tt, "l", dict(target=(-0.3, 1.25), hand="relaxed", hand_ang=-140, thumb=1, hand_scale=0.8), 0.01)
    M.arm(tt + 2.5, "l", None, 1.0)
    # two-shot end of scene 1
    te1 = T("L14", "end") - 1.2
    J.pose(te1, 0.01, yaw=20, pitch=2, roll=0).look(te1, 0.4, 0.1).expr(te1, "warm", 0.01, wet=0.3)
    M.pose(te1, 0.01, yaw=-22, pitch=-1).look(te1, -0.45, -0.1).expr(te1, "moved", 0.01, m_smile=0.5, wet=0.8)

    # ---------------- SCENE 2 ----------------
    ts2 = T.scene_end["shore"] + 1.1
    J.pose(ts2, 0.01, yaw=20, pitch=0, roll=0).look(ts2, 0.3, 0.05).expr(ts2, "gentle", 0.01)
    J.arm(ts2 + 1.0, "r", G_TEACH_R, 1.0)
    J.arm(T("L16") - 1.0, "r", None, 0.8)
    # Eli grumbles to the man beside him
    tg = T("L16") - 0.6
    E.pose(tg, 0.01, yaw=14, pitch=3, roll=4).look(tg, 0.45, 0.05).expr(tg, "grumble", 0.01)
    X.pose(tg, 0.01, yaw=-26, pitch=2).look(tg, -0.4, 0.0).expr(tg, "suspicious", 0.01)
    E.look(T("L16", word="joseph") - 0.2, -0.4, 0.0, 0.2).pose(T("L16", word="joseph") - 0.3, 0.6, yaw=-18)  # glance at Jesus
    E.look(T("L16", "end") + 0.1, 0.45, 0.05, 0.2).pose(T("L16", "end"), 0.5, yaw=14)
    X.expr(T("L17") - 0.1, "indignant", 0.3).nod(T("L17") + 0.3, 3.0, 0.5)
    E.nod(T("L17") + 0.5, 3.0, 0.6)
    E.expr(T("L18"), "indignant", 0.4)
    E.arm(T("L18") + 0.1, "l", dict(target=(-1.4, 1.9), hand="open", hand_ang=115, thumb=1), 0.5)
    E.pose(T("L18"), 0.5, yaw=-10, roll=-3)
    E.look(T("L18"), -0.2, 0.0, 0.2)
    E.arm(T("L18", "end") + 0.6, "l", None, 0.6)
    # Jesus hears it
    t19 = T("L19") - 0.9
    J.pose(t19, 0.01, yaw=8, pitch=0, roll=0).look(t19, 0.1, 0.0).expr(t19, "gentle", 0.01)
    J.pose(t19 + 0.3, 0.7, yaw=22).look(t19 + 0.3, 0.4, 0.05, 0.2)
    J.expr(T("L19"), "firm", 0.4)
    J.expr(T("L19", "end") + 0.3, "compassion", 1.0)
    # L20
    t20 = T("L20") - 0.6
    J.pose(t20, 0.01, yaw=17, pitch=0, roll=0).look(t20, 0.35, 0.05).expr(t20, "compassion", 0.01)
    J.expr(T("L20", seg=1), "warm", 1.0)
    E.pose(T("L20", seg=1) - 0.1, 0.01, yaw=-18, pitch=2, roll=0).look(T("L20", seg=1) - 0.1, -0.35, 0.0).expr(T("L20", seg=1) - 0.1, "suspicious", 0.01)
    E.expr(T("L20", seg=1) + 1.2, "hurt", 1.2).look(T("L20", seg=1) + 1.6, 0.2, 0.35, 0.3).pose(T("L20", seg=1) + 1.5, 0.9, yaw=-8, pitch=6)
    # L21
    t21 = T("L20", "end") - 0.4
    J.pose(t21, 0.01, yaw=16, pitch=0).look(t21, 0.33, 0.05).expr(t21, "gentle", 0.01)
    J.arm(T("L21", seg=1) - 0.3, "r", G_UP_R, 0.8)  # hand lifted
    J.look(T("L21", seg=1), 0.2, -0.45, 0.3).pose(T("L21", seg=1), 0.8, pitch=-7)
    J.arm(T("L21", seg=2) - 0.1, "r", None, 0.9)
    J.look(T("L21", seg=2) + 0.1, 0.35, 0.05, 0.3).pose(T("L21", seg=2), 0.8, pitch=0)
    J.expr(T("L21", seg=2), "warm", 0.8)
    tm21 = T("L21", seg=2) - 0.25
    M.pose(tm21, 0.01, yaw=-18, pitch=0, roll=-2).look(tm21, -0.4, 0.0).expr(tm21, "moved", 0.01, m_smile=0.2, wet=0.5)
    M.nod(tm21 + 1.0, 2.5, 0.7)
    # L22 "I am the living bread" (strong beam)
    t22 = T("L22") - 1.0
    J.pose(t22, 0.01, yaw=18, pitch=0, roll=0).look(t22, 0.32, 0.05).expr(t22, "peace", 0.01)
    J.arm(T("L22") - 0.2, "l", dict(target=(-0.4, 1.55), hand="flat", hand_ang=-68, thumb=-1, hand_scale=0.85), 0.9)
    J.expr(T("L22"), "resolute", 0.6, m_smile=0.15)
    J.arm(T("L22", seg=1) + 0.4, "l", None, 0.9)
    J.expr(T("L22", seg=1), "warm", 0.8)
    # Eli: "Whoever eats this bread will live forever" - a skeptical frown
    te22 = T("L22", seg=1) + 0.2
    E.pose(te22, 0.01, yaw=-18, pitch=2, roll=0).look(te22, -0.35, 0.0).expr(te22, "suspicious", 0.01)
    E.expr(te22 + 0.6, "grumble", 0.6).pose(te22 + 0.6, 0.7, roll=-4, pitch=-2)
    J.pose(T("L22", "end") - 0.3, 0.01, yaw=18, pitch=0, roll=0).look(T("L22", "end") - 0.3, 0.33, 0.05)
    # L23 "This bread is my flesh" - sorrowful foreknowledge
    J.expr(T("L23") - 0.3, "compassion", 0.8)
    J.expr(T("L23", seg=1) - 0.2, "sorrow", 1.2, wet=0.6, m_smile=0.0)
    J.look(T("L23", seg=1) - 0.1, 0.2, 0.3, 0.4).pose(T("L23", seg=1) - 0.2, 1.0, pitch=6, roll=2)
    tp23 = T("L23", "end") + 0.1
    P.pose(tp23, 0.01, yaw=18, pitch=0, roll=3).look(tp23, 0.45, 0.0).expr(tp23, "anxious", 0.01, bi_l=0.6, bi_r=0.6, wet=0.4)
    P.look(tp23 + 0.5, 0.25, 0.3, 0.3).pose(tp23 + 0.45, 0.8, pitch=6)
    J.look(T("L23", "end") - 0.4, 0.35, 0.05, 0.4).pose(T("L23", "end") - 0.6, 1.0, pitch=1)
    # L24 Eli's outburst
    t24 = T("L24") - 0.5
    E.pose(t24, 0.01, yaw=-20, pitch=-2, roll=0).look(t24, -0.35, 0.0).expr(t24, "shocked", 0.01)
    E.expr(T("L24", seg=1), "indignant", 0.4, bfur=0.8)
    E.arm(T("L24", seg=1) - 0.1, "l", dict(target=(-1.6, 1.7), hand="open", hand_ang=120, thumb=1), 0.5)
    E.pose(T("L24", seg=1), 0.5, pitch=-6, roll=-4)
    E.arm(T("L24", "end") + 0.4, "l", None, 0.6)
    X.pose(t24, 0.01, yaw=-22).look(t24, -0.45, 0.0).expr(t24, "shocked", 0.01)
    X.pose(T("L24", seg=1) + 0.5, 0.4, yaw=18).look(T("L24", seg=1) + 0.5, 0.5, 0.0).expr(T("L24", seg=1) + 0.5, "confused", 0.4)
    # L25 Jesus intense
    t25 = T("L25") - 1.6
    J.pose(t25, 0.01, yaw=17, pitch=2, roll=0).look(t25, 0.35, 0.05).expr(t25, "sorrow", 0.01, wet=0.3)
    J.expr(T("L25") - 0.4, "intense", 0.8)
    J.hold_eyes(T("L25"), T("L25", "end"))
    J.pose(T("L25", seg=1), 1.2, pitch=-1, hx=0.06)
    J.expr(T("L25", seg=2), "intense", 0.6, bi_l=-0.2, bi_r=-0.2, wet=0.2)
    # reactions
    tmg = T("L25", "end") + 0.2
    M.pose(tmg, 0.01, yaw=-18, pitch=0, roll=0).look(tmg, -0.4, 0.0).expr(tmg, "shocked", 0.01)
    M.arm(tmg + 0.1, "l", dict(target=(-0.05, 0.4), hand="relaxed", hand_ang=-170, thumb=1), 0.35)  # hand to mouth
    M.expr(tmg + 0.4, "anxious", 0.6, eo_l=1.15, eo_r=1.15)
    tps = T("L25", "end") + 1.05
    P.pose(tps, 0.01, yaw=18, pitch=1, roll=0).look(tps, 0.45, 0.0).expr(tps, "confused", 0.01, bfur=0.4)
    P.expr(tps + 0.7, "resolute", 0.8, bfur=0.3)
    P.nod(tps + 1.0, 1.5, 0.8)
    M.arm(T("L26"), "l", None, 1.0)
    # L26/L27 strong, steady
    t26 = T("L26") + 0.5
    J.pose(t26, 0.01, yaw=16, pitch=0, roll=0, hx=0.0).look(t26, 0.35, 0.05).expr(t26, "resolute", 0.01)
    J.arm(T("L26", seg=1) - 0.2, "r", G_TEACH_R, 0.8)
    J.arm(T("L27") - 0.3, "r", G_FIRM_R, 0.7)
    J.expr(T("L27"), "firm", 0.6, m_press=0.0)
    J.arm(T("L27", "end") + 0.4, "r", None, 0.8)
    # L28 intimate
    t28 = T("L28") - 0.8
    J.pose(t28, 0.01, yaw=19, pitch=3, roll=2).look(t28, 0.38, 0.1).expr(t28, "compassion", 0.01, wet=0.3)
    J.arm(T("L28", seg=1) - 0.5, "l", dict(target=(-0.4, 1.55), hand="flat", hand_ang=-68, thumb=-1, hand_scale=0.85), 0.9)
    J.expr(T("L28", seg=1), "moved", 0.8, m_smile=0.35, wet=0.5)
    J.arm(T("L28", "end") + 0.5, "l", None, 0.9)
    # L29
    t29 = T("L29") - 0.45
    J.pose(t29, 0.01, yaw=16, pitch=0, roll=0).look(t29, 0.33, 0.05).expr(t29, "warm", 0.01)
    J.look(T("L29", word="living") - 0.1, 0.15, -0.5, 0.3).pose(T("L29", word="living") - 0.2, 0.8, pitch=-6)
    J.look(T("L29", seg=1), 0.35, 0.05, 0.3).pose(T("L29", seg=1), 0.8, pitch=0)
    te29 = T("L29", seg=1) - 0.1
    E.pose(te29, 0.01, yaw=-18, pitch=3, roll=0).look(te29, -0.35, 0.05).expr(te29, "hurt", 0.01)
    E.look(te29 + 1.0, 0.3, 0.3, 0.25).pose(te29 + 0.9, 0.9, yaw=-6, pitch=7).expr(te29 + 1.0, "guilty", 0.8)
    # Eli at "Your ancestors ate manna, and died..." - his own argument answered
    te30 = T("L30", seg=1) - 0.15
    E.pose(te30, 0.01, yaw=-18, pitch=2, roll=0).look(te30, -0.35, 0.0).expr(te30, "suspicious", 0.01)
    E.expr(te30 + 0.8, "guilty", 0.9).look(te30 + 1.0, 0.1, 0.45, 0.35).pose(te30 + 0.9, 1.0, yaw=-6, pitch=8)
    # L30 final, warm, eyes moist
    t30 = T("L30") - 0.6
    J.pose(t30, 0.01, yaw=18, pitch=1, roll=1).look(t30, 0.35, 0.05).expr(t30, "compassion", 0.01, wet=0.4)
    J.expr(T("L30", seg=1), "sorrow", 0.8, wet=0.6)
    J.expr(T("L30", seg=2), "moved", 1.0, m_smile=0.4, wet=0.7)
    J.arm(T("L30", seg=2) - 0.2, "r", G_OFFER_R, 0.9)
    J.arm(T("L30", "end") + 0.6, "r", None, 1.0)
    J.hold_eyes(T("L30", seg=2), T("L30", "end"))

    # ---------------- SCENE 3 ----------------
    s3 = T.scene_end["synagogue"] + 0.6
    te = T("L32") - 0.5
    E.pose(te, 0.01, yaw=-22, pitch=4, roll=0).look(te, -0.3, 0.1).expr(te, "hurt", 0.01)
    E.expr(T("L32"), "hurt", 0.4, bfur=0.5, wet=0.3)
    E.look(T("L32", seg=1) - 0.1, 0.3, 0.4, 0.3).pose(T("L32", seg=1) - 0.2, 0.8, yaw=-8, pitch=8)
    E.expr(T("L32", seg=1), "sorrow", 0.6, wet=0.4)
    # Jesus watching them leave
    tj = T("L34") - 2.6
    J.pose(tj, 0.01, yaw=24, pitch=1, roll=0).look(tj, 0.45, 0.0).expr(tj, "sorrow", 0.01, wet=0.6)
    J.blink(tj + 0.9)
    J.look(tj + 1.6, 0.0, 0.0, 0.3).pose(tj + 1.4, 1.2, yaw=-12, pitch=2)  # turns to Peter
    J.expr(T("L34"), "sorrow", 0.6, wet=0.8, bi_l=0.6, bi_r=0.6)
    J.look(T("L34"), -0.35, 0.05, 0.3)
    J.hold_eyes(T("L34"), T("L34", "end"))
    J.tear("r", T("L34", seg=1) + 0.2, T("L34", seg=1) + 3.5)
    # Peter's answer
    tp = T("L35") - 0.7
    P.pose(tp, 0.01, yaw=18, pitch=2, roll=0).look(tp, 0.4, 0.05).expr(tp, "tearful", 0.01, m_smile=-0.2)
    P.expr(T("L35"), "pleading", 0.5, wet=0.9)
    P.pose(T("L35", seg=1), 0.8, pitch=-2, roll=-3)
    P.expr(T("L35", seg=2), "moved", 0.8, m_smile=0.25, wet=1.0)
    P.tear("l", T("L35", seg=1) + 0.4, T("L35", seg=1) + 3.6)
    tpm = T("L36") - 0.2
    M.pose(tpm, 0.01, yaw=-20, pitch=0, roll=-2).look(tpm, -0.35, 0.0).expr(tpm, "moved", 0.01, m_smile=0.35, wet=1.0)
    M.nod(tpm + 0.5, 3, 0.7).nod(tpm + 1.3, 2.5, 0.7)
    tp2 = T("L36") + 1.6
    P.pose(tp2, 0.01, yaw=18, pitch=0, roll=0).look(tp2, 0.4, 0.05).expr(tp2, "resolute", 0.01, wet=0.8, bi_l=0.4, bi_r=0.4)
    P.expr(T("L36", seg=1) + 0.3, "moved", 0.8, m_smile=0.4, wet=0.9)
    # final: Jesus smiles through tears, offers bread
    tf = T("L36", "end") + 0.5
    J.pose(tf, 0.01, yaw=18, pitch=2, roll=0).look(tf, 0.35, 0.05).expr(tf, "moved", 0.01, m_smile=0.5, wet=0.7)
    J.arm(tf, "r", dict(target=(1.0, 2.45), hand="hold", hand_ang=-30), 0.01)
    J.arm(tf, "l", dict(target=(0.05, 2.55), hand="hold", hand_ang=25, thumb=1), 0.01)
    J.arm(tf + 1.2, "r", dict(target=(2.2, 2.3), hand="hold", hand_ang=-70), 1.2)  # breaks and offers half
    P.pose(tf, 0.01, yaw=-18, pitch=2).look(tf, -0.35, 0.05).expr(tf, "moved", 0.01, m_smile=0.45, wet=0.8)
    P.arm(tf + 1.8, "l", dict(target=(-1.05, 2.3), hand="hold", hand_ang=60, thumb=1), 1.0)
    M.pose(tf, 0.01, yaw=-20, pitch=0).look(tf, -0.4, 0.05).expr(tf, "joy", 0.01, wet=0.6)
    return {"jesus": J, "peter": P, "miriam": M, "eli": E, "man2": X}


if __name__ == "__main__":
    for s in SHOTS:
        print(f"{s['t0']:7.2f} {s['name']}")
    print(len(SHOTS), "shots, total", T.total)
