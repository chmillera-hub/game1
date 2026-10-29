"""Build script/shots.json from script/timeline.json: which 3D shot covers which narration units."""
import json, math, os
HERE = os.path.dirname(os.path.abspath(__file__))
tl = json.load(open(f"{HERE}/timeline.json"))
U = {u["id"]: u for u in tl["units"]}
FPS = 24
# (id, module, params, first unit, last unit)   None = special timing
PLAN = [
    ("S00_title", "hills", {"variant": "title"}, None, None),
    ("S01_confront", "colonnade", {"variant": "confront"}, "u01", "u02"),
    ("S02_jars", "interior", {"variant": "jars"}, "u03", "u03"),
    ("S03_turnaway", "colonnade", {"variant": "turnaway"}, "u04", "u04"),
    ("S04_flock", "hills", {"variant": "flock_follow"}, "u05", "u06"),
    ("S05_pasture", "hills", {"variant": "pasture"}, "u07", "u07"),
    ("S06_lamb", "hills", {"variant": "lamb"}, "u08", "u08"),
    ("S07_heaven", "heaven", {"variant": "clouds_up"}, "u09", "u09"),
    ("S08_fold", "hills", {"variant": "fold_night"}, "u10", "u10"),
    ("S09_one", "colonnade", {"variant": "one_light"}, "u11", "u11"),
    ("S10_stones", "colonnade", {"variant": "stones"}, "u12", "u12"),
    ("S11_crowd", "colonnade", {"variant": "faces_crowd"}, "u13", "u15"),
    ("S12_accusers", "colonnade", {"variant": "accusers"}, "u16", "u16"),
    ("S13_accusers2", "colonnade", {"variant": "accusers2"}, "u17", "u17"),
    ("S14_scroll", "interior", {"variant": "scroll_a"}, "u18", "u19"),
    ("S15_scroll2", "interior", {"variant": "scroll_b"}, "u20", "u21"),
    ("S16_descend", "heaven", {"variant": "descend"}, "u22", "u22"),
    ("S17_lowangle", "colonnade", {"variant": "low_angle"}, "u23", "u23"),
    ("S18_baskets", "hills", {"variant": "baskets"}, "u24", "u25"),
    ("S19_father", "colonnade", {"variant": "father_in_me"}, "u26", "u26"),
    ("S20_escape", "colonnade", {"variant": "escape"}, "u27", "u27"),
    ("S21_chapter", "hills", {"variant": "chapter"}, None, None),
    ("S22_upper", "interior", {"variant": "upper_room"}, "u28", "u28"),
    ("S23_lamps", "interior", {"variant": "lamp_lighting"}, "u29", "u29"),
    ("S24_many", "hills", {"variant": "lamps_many"}, "u30", "u30"),
    ("S25_earth", "space", {"variant": "earth_night"}, "u31", "u31"),
    ("S26_glory", "hills", {"variant": "glory_crowd"}, "u32", "u32"),
    ("S27_converge", "hills", {"variant": "lights_converge"}, "u33", "u33"),
    ("S28_sunrise", "space", {"variant": "earth_sunrise"}, "u34", "u34"),
    ("S29_path", "hills", {"variant": "path_light"}, "u35", "u35"),
    ("S30_cosmos", "space", {"variant": "cosmos"}, "u36", "u36"),
    ("S31_gethsemane", "hills", {"variant": "gethsemane"}, "u37", "u37"),
    ("S32_dawn", "hills", {"variant": "dawn_walk"}, "u38", "u39"),
    ("S33_final", "hills", {"variant": "final_light"}, "u40", "u40"),
    ("S34_end", "hills", {"variant": "end_flock"}, None, None),
]
XF = {"S01_confront": 1.0, "S21_chapter": 1.2, "S22_upper": 1.2, "S34_end": 1.5, "S09_one": 0.9, "S33_final": 0.9}
starts = []
for i, (sid, mod, prm, a, b) in enumerate(PLAN):
    if sid == "S00_title": starts.append(0.0); continue
    if sid == "S21_chapter": starts.append(U["u27"]["end"] + 0.9); continue
    if sid == "S34_end": starts.append(U["u40"]["end"] + 1.7); continue
    prev_end = U[PLAN[i - 1][4]]["end"] if PLAN[i - 1][4] else U["u01"]["start"] - 0.5
    gap = U[a]["start"] - prev_end
    starts.append(U[a]["start"] - min(0.45, max(0.15, gap * 0.4)))
total = tl["duration"]
shots = []
for i, (sid, mod, prm, a, b) in enumerate(PLAN):
    st = starts[i]
    en = starts[i + 1] if i + 1 < len(PLAN) else total
    xin = XF.get(sid, 0.7) if i > 0 else 0.0
    xout = XF.get(PLAN[i + 1][0], 0.7) if i + 1 < len(PLAN) else 0.0
    f0 = max(0, math.floor((st - xin / 2) * FPS))
    f1 = min(math.ceil(total * FPS) - 1, math.ceil((en + xout / 2) * FPS) - 1)
    shots.append({"id": sid, "module": mod, "params": prm, "start": round(st, 3), "end": round(en, 3), "duration": round(en - st, 3),
                  "xfade_in": xin, "xfade_out": xout, "frame_start": f0, "frame_end": f1, "units": [a, b]})
json.dump({"fps": FPS, "duration": total, "shots": shots}, open(f"{HERE}/shots.json", "w"), indent=1)
tot = sum(s["frame_end"] - s["frame_start"] + 1 for s in shots)
for s in shots: print(f'{s["id"]:16s} {s["start"]:7.2f}-{s["end"]:7.2f} ({s["duration"]:5.2f}s) frames {s["frame_start"]}-{s["frame_end"]}')
print("total frames to render:", tot, " video frames:", math.ceil(total * FPS))
