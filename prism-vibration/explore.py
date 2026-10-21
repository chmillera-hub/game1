import numpy as np
from prism_sim import *
np.set_printoptions(suppress=True, linewidth=150)
cols = np.array([400, 450, 500, 550, 600, 650, 700.])
ns = n_glass(cols)
print("screen sensitivity dx/dtheta (mm/deg) when ROCKING the prism, per colour", cols)
for th in [57, 58, 59, 60, 62, 63, 63.6, 64, 65, 66, 67, 70, 75, 80]:
    b = Bench(rot_for_incidence(th))
    e = 0.01
    xp = b.positions(rot_for_incidence(th + e), n=ns); xm = b.positions(rot_for_incidence(th - e), n=ns)
    x0 = b.positions(n=ns)
    print(f"{th:5}", ((xp - xm) / (2 * e)).round(2), " spectrum 400..700 span mm", (x0[0] - x0[-1]).round(1))
print("\nTranslation of prism by 1 mm (x then y) at theta=64: screen shift mm per colour")
b = Bench(rot_for_incidence(64))
x0 = b.positions(n=ns)
print((b.positions(shift=(1, 0), n=ns) - x0).round(4))
print((b.positions(shift=(0, 1), n=ns) - x0).round(4))
print("\nBeam angle wobble (beam pivoting about its entry point), screen dx per deg of beam tilt")
for th in [57, 58, 59, 60, 62, 64, 66, 70, 75]:
    b = Bench(rot_for_incidence(th))
    p1, _, _, _ = trace(BEAM_START, BEAM_DIR, 1.79, b.ref_rot)
    e = np.radians(0.01)
    xp = b.positions(beam_angle=e, beam_pivot=p1, n=ns); xm = b.positions(beam_angle=-e, beam_pivot=p1, n=ns)
    print(f"{th:5}", ((xp - xm) / 0.02).round(2))
