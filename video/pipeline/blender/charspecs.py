"""Character specs for charbuild.py. Colors are linear RGB."""

ROBE_HIDE = {"bones": ["TORSO", "ARMS", "LEGS"], "zmin": 0.09}


def robe(main, belt, hem=0.93, skirt_bottom=0.07, sleeve=0.94, offset=0.013, v_neck=0.0, flare=0.1):
    return [
        dict(type="top", mat=main, hem_z=hem, sleeve=sleeve, offset=offset, neck_drop=0.012, v_neck=v_neck),
        dict(type="skirt", mat=main, top=1.07, bottom=skirt_bottom, flare=flare, fold_amp=0.05),
        dict(type="band", label="belt", mat=belt, kind="belt", z0=0.925, z1=1.0, offset=offset + 0.011, smooth=6,
             hips=True, folds=0.002),
        dict(type="legs", label="robe_legs", mat=main, offset=0.012),
    ]


def stole(mat, end=0.97, outer=0.13):
    return dict(type="band", label="tallit", mat=mat, kind="stole", offset=0.017, end=end, outer=outer, smooth=22,
                folds=0.003, solid=0.002)


SPECS = {
    "JESUS": dict(
        phenotype={"gender": 1.0, "age": 0.56, "muscle": 0.55, "weight": 0.42, "height": 0.56, "proportions": 0.65,
                   "race": {"caucasian": 0.6, "african": 0.12, "asian": 0.28}},
        skin="young_caucasian_male", skin_mult=(0.76, 0.62, 0.52), skin_brightness=-0.02, skin_rough=0.48,
        iris=((0.16, 0.085, 0.035), (0.05, 0.025, 0.01)),
        hair="long01", hair_color=(0.05, 0.032, 0.02), eyebrows="eyebrow001",
        beard=dict(melanin=0.72, redness=0.5, length=0.017, count=5000, children=10, down=0.008, normal=0.005,
                   radius=0.00028, kink=0.4, neck_depth=0.085),
        materials={
            "tunic": dict(color=(0.62, 0.55, 0.42), rough=0.85, fold_strength=0.3),
            "mantle": dict(color=(0.14, 0.025, 0.018), rough=0.75, sheen=0.7, fold_strength=0.5),
            "belt": dict(color=(0.25, 0.16, 0.08), rough=0.9),
        },
        clothes=robe("tunic", "belt", v_neck=0.05) + [
            dict(type="band", label="mantle", mat="mantle", kind="diagonal", line=(0.17, 1.46, -0.17, 0.90, 0.12),
                 offset=0.03, hips=True, smooth=18),
        ],
        hide_body=ROBE_HIDE,
    ),
    "ELDER": dict(
        phenotype={"gender": 1.0, "age": 0.86, "muscle": 0.4, "weight": 0.62, "height": 0.5, "proportions": 0.5,
                   "race": {"caucasian": 0.62, "african": 0.1, "asian": 0.28}},
        skin="old_caucasian_male", skin_mult=(0.8, 0.66, 0.56), skin_brightness=-0.03, skin_rough=0.55, pores=0.35,
        iris=((0.12, 0.08, 0.04), (0.04, 0.025, 0.012)),
        hair="", eyebrows="eyebrow010", hair_color=(0.35, 0.33, 0.31), hair_value=1.6,
        beard=dict(melanin=0.5, redness=0.1, gray=0.55, length=0.04, count=5000, children=10, down=0.02,
                   normal=0.004, neck_depth=0.11),
        materials={
            "robe": dict(color=(0.05, 0.07, 0.16), rough=0.8, sheen=0.5, fold_strength=0.4),
            "belt": dict(color=(0.30, 0.22, 0.08), rough=0.85),
            "tallit": dict(color=(0.75, 0.72, 0.64), rough=0.9, stripes=[(0.98, 1.02, (0.04, 0.05, 0.14)),
                                                                       (1.035, 1.055, (0.04, 0.05, 0.14))]),
            "cover": dict(color=(0.70, 0.66, 0.56), rough=0.9, fold_strength=0.3,
                          stripes=[(1.62, 1.635, (0.05, 0.06, 0.16))]),
        },
        clothes=robe("robe", "belt", offset=0.016, skirt_bottom=0.06, flare=0.11) + [
            stole("tallit", end=0.96, outer=0.15),
            dict(type="headcover", mat="cover", drape=0.17, offset=0.016),
        ],
        hide_body=ROBE_HIDE,
    ),
    "YOUNG": dict(
        phenotype={"gender": 1.0, "age": 0.45, "muscle": 0.45, "weight": 0.38, "height": 0.6, "proportions": 0.6,
                   "race": {"caucasian": 0.58, "african": 0.1, "asian": 0.32}},
        skin="young_caucasian_male2", skin_mult=(0.78, 0.63, 0.52), skin_brightness=-0.02,
        iris=((0.14, 0.08, 0.035), (0.045, 0.025, 0.01)),
        hair="short02", hair_color=(0.035, 0.024, 0.016), eyebrows="eyebrow002",
        beard=dict(melanin=0.85, redness=0.35, length=0.01, count=4500, children=8, down=0.004, normal=0.004,
                   neck_depth=0.08, density=0.85, radius=0.00025),
        materials={
            "robe": dict(color=(0.16, 0.17, 0.18), rough=0.82, sheen=0.4, fold_strength=0.4),
            "belt": dict(color=(0.08, 0.08, 0.09), rough=0.85),
            "tallit": dict(color=(0.78, 0.75, 0.67), rough=0.9, stripes=[(1.0, 1.03, (0.05, 0.05, 0.05))]),
        },
        clothes=robe("robe", "belt", sleeve=0.95, flare=0.09) + [stole("tallit", end=1.0, outer=0.12)],
        hide_body=ROBE_HIDE,
    ),
    "PH2": dict(
        phenotype={"gender": 1.0, "age": 0.72, "muscle": 0.5, "weight": 0.7, "height": 0.45, "proportions": 0.5,
                   "race": {"caucasian": 0.55, "african": 0.15, "asian": 0.3}},
        skin="middleage_caucasian_male", skin_mult=(0.74, 0.58, 0.46), skin_brightness=-0.03,
        hair="", eyebrows="eyebrow008", hair_color=(0.04, 0.03, 0.02),
        beard=dict(melanin=0.75, redness=0.25, gray=0.25, length=0.03, count=4500, children=8, down=0.016),
        materials={
            "robe": dict(color=(0.22, 0.12, 0.06), rough=0.85, fold_strength=0.4),
            "belt": dict(color=(0.12, 0.07, 0.03), rough=0.85),
            "tallit": dict(color=(0.74, 0.70, 0.62), rough=0.9, stripes=[(1.0, 1.04, (0.12, 0.06, 0.03))]),
            "cover": dict(color=(0.62, 0.58, 0.48), rough=0.9),
        },
        clothes=robe("robe", "belt", offset=0.016, skirt_bottom=0.06, flare=0.11) + [
            stole("tallit"), dict(type="headcover", mat="cover", drape=0.15, offset=0.016)],
        hide_body=ROBE_HIDE,
    ),
    "PH3": dict(
        phenotype={"gender": 1.0, "age": 0.64, "muscle": 0.5, "weight": 0.5, "height": 0.62, "proportions": 0.5,
                   "race": {"caucasian": 0.6, "african": 0.15, "asian": 0.25}},
        skin="middleage_caucasian_male", skin_mult=(0.76, 0.6, 0.48), skin_brightness=-0.02,
        hair="", eyebrows="eyebrow005", hair_color=(0.04, 0.03, 0.02),
        beard=dict(melanin=0.85, redness=0.3, gray=0.1, length=0.028, count=4500, children=8, down=0.014),
        materials={
            "robe": dict(color=(0.10, 0.14, 0.11), rough=0.85, fold_strength=0.4),
            "belt": dict(color=(0.25, 0.2, 0.1), rough=0.85),
            "tallit": dict(color=(0.76, 0.72, 0.64), rough=0.9, stripes=[(1.0, 1.04, (0.04, 0.05, 0.14))]),
            "cover": dict(color=(0.70, 0.67, 0.58), rough=0.9),
        },
        clothes=robe("robe", "belt", offset=0.015, skirt_bottom=0.06) + [
            stole("tallit"), dict(type="headcover", mat="cover", drape=0.15, offset=0.016)],
        hide_body=ROBE_HIDE,
    ),
    "PETER": dict(
        phenotype={"gender": 1.0, "age": 0.7, "muscle": 0.72, "weight": 0.66, "height": 0.48, "proportions": 0.45,
                   "race": {"caucasian": 0.62, "african": 0.12, "asian": 0.26}},
        skin="middleage_caucasian_male", skin_mult=(0.8, 0.64, 0.5), skin_brightness=-0.02, pores=0.35,
        iris=((0.13, 0.09, 0.05), (0.05, 0.03, 0.015)),
        hair="short02", hair_color=(0.11, 0.09, 0.075), hair_value=1.25, eyebrows="eyebrow009",
        beard=dict(melanin=0.8, redness=0.3, gray=0.4, length=0.024, count=5000, children=10, down=0.012,
                   kink=0.4, normal=0.005, radius=0.0003),
        materials={
            "tunic": dict(color=(0.30, 0.20, 0.12), rough=0.9, fold_strength=0.4),
            "belt": dict(color=(0.45, 0.32, 0.16), rough=0.9),
        },
        clothes=robe("tunic", "belt", sleeve=0.80, skirt_bottom=0.12, flare=0.09, offset=0.014),
        hide_body=ROBE_HIDE,
    ),
    "JOHN": dict(
        phenotype={"gender": 1.0, "age": 0.42, "muscle": 0.45, "weight": 0.35, "height": 0.55, "proportions": 0.6,
                   "race": {"caucasian": 0.55, "african": 0.12, "asian": 0.33}},
        skin="young_caucasian_male", skin_mult=(0.78, 0.63, 0.52), skin_brightness=-0.01,
        iris=((0.15, 0.09, 0.04), (0.05, 0.03, 0.012)),
        hair="short02", hair_color=(0.045, 0.03, 0.02), eyebrows="eyebrow002",
        beard=dict(melanin=0.9, stubble_only=True, neck_depth=0.07), stubble=0.35,
        materials={
            "tunic": dict(color=(0.55, 0.40, 0.22), rough=0.88, fold_strength=0.35),
            "mantle": dict(color=(0.10, 0.15, 0.22), rough=0.85, sheen=0.5, fold_strength=0.4),
            "belt": dict(color=(0.2, 0.13, 0.06), rough=0.9),
        },
        clothes=robe("tunic", "belt", sleeve=0.9, v_neck=0.04, skirt_bottom=0.09, flare=0.09) + [
            dict(type="band", label="mantle", mat="mantle", kind="diagonal", line=(-0.17, 1.46, 0.17, 0.92, 0.10),
                 offset=0.03, hips=True, smooth=18)],
        hide_body=ROBE_HIDE,
    ),
    "WOMAN": dict(
        phenotype={"gender": 0.0, "age": 0.5, "muscle": 0.45, "weight": 0.45, "height": 0.5, "proportions": 0.6,
                   "cupsize": 0.32, "firmness": 0.4, "race": {"caucasian": 0.7, "african": 0.1, "asian": 0.2}},
        skin="young_caucasian_female", skin_mult=(0.86, 0.74, 0.66), skin_rough=0.45,
        iris=((0.20, 0.13, 0.06), (0.07, 0.04, 0.02)),
        hair="ponytail01", hair_color=(0.06, 0.035, 0.02), eyebrows="eyebrow004", eyelashes="eyelashes02",
        materials={
            "sweater": dict(color=(0.42, 0.40, 0.36), rough=0.95, sheen=0.7, knit=True, bump_strength=0.35),
            "leggings": dict(color=(0.03, 0.03, 0.035), rough=0.6, sheen=0.2),
        },
        clothes=[
            dict(type="top", label="sweater", mat="sweater", hem_z=0.80, sleeve=1.02, offset=0.018, neck_drop=0.03,
                 folds=0.006, solid=0.004),
            dict(type="legs", label="leggings", mat="leggings", offset=0.003),
        ],
        hide_body={"bones": ["TORSO", "ARMS", "LEGS"], "zmin": 0.12},
    ),
    "SISTER": dict(
        phenotype={"gender": 0.0, "age": 0.58, "muscle": 0.45, "weight": 0.5, "height": 0.55, "proportions": 0.6,
                   "cupsize": 0.35, "firmness": 0.4, "race": {"caucasian": 0.7, "african": 0.1, "asian": 0.2}},
        skin="young_caucasian_female2", skin_mult=(0.86, 0.74, 0.66), skin_rough=0.45,
        iris=((0.20, 0.13, 0.06), (0.07, 0.04, 0.02)),
        hair="bob02", hair_color=(0.045, 0.028, 0.018), hair_value=0.55, eyebrows="eyebrow004", eyelashes="eyelashes02",
        materials={
            "cardigan": dict(color=(0.30, 0.10, 0.08), rough=0.95, sheen=0.6, knit=True, bump_strength=0.3),
            "jeans": dict(color=(0.06, 0.09, 0.16), rough=0.85, bump_scale=1500.0, bump_strength=0.3),
        },
        clothes=[
            dict(type="top", label="cardigan", mat="cardigan", hem_z=0.80, sleeve=0.98, offset=0.016, v_neck=0.06,
                 folds=0.006, solid=0.004),
            dict(type="legs", label="jeans", mat="jeans", offset=0.006),
        ],
        hide_body={"bones": ["TORSO", "ARMS", "LEGS"], "zmin": 0.12},
    ),
}

SPECS["KID1"] = dict(
    phenotype={"gender": 0.0, "age": 0.1, "muscle": 0.5, "weight": 0.5, "height": 0.5, "proportions": 0.5,
               "race": {"caucasian": 0.7, "african": 0.1, "asian": 0.2}},
    skin="young_caucasian_female", skin_mult=(0.88, 0.76, 0.68), skin_rough=0.45,
    iris=((0.20, 0.13, 0.06), (0.07, 0.04, 0.02)),
    hair="ponytail01", hair_color=(0.10, 0.06, 0.03), eyebrows="eyebrow004", eyelashes="eyelashes02",
    materials={"shirt": dict(color=(0.75, 0.25, 0.22), rough=0.9, knit=True, bump_strength=0.2),
               "pants": dict(color=(0.08, 0.10, 0.18), rough=0.85)},
    clothes=[dict(type="top", label="shirt", mat="shirt", hem_z=0.42, sleeve=0.55, offset=0.012, neck_drop=0.03,
                  solid=0.003),
             dict(type="legs", label="pants", mat="pants", offset=0.008)],
    hide_body={"bones": ["TORSO", "ARMS", "LEGS"], "zmin": 0.08},
)
SPECS["KID2"] = dict(
    phenotype={"gender": 0.0, "age": 0.16, "muscle": 0.5, "weight": 0.45, "height": 0.5, "proportions": 0.5,
               "race": {"caucasian": 0.7, "african": 0.1, "asian": 0.2}},
    skin="young_caucasian_female2", skin_mult=(0.88, 0.76, 0.68), skin_rough=0.45,
    iris=((0.20, 0.13, 0.06), (0.07, 0.04, 0.02)),
    hair="bob01", hair_color=(0.07, 0.045, 0.025), eyebrows="eyebrow004", eyelashes="eyelashes02",
    materials={"shirt": dict(color=(0.25, 0.45, 0.70), rough=0.9, knit=True, bump_strength=0.2),
               "pants": dict(color=(0.10, 0.09, 0.08), rough=0.85)},
    clothes=[dict(type="top", label="shirt", mat="shirt", hem_z=0.55, sleeve=0.55, offset=0.012, neck_drop=0.03,
                  solid=0.003),
             dict(type="legs", label="pants", mat="pants", offset=0.008)],
    hide_body={"bones": ["TORSO", "ARMS", "LEGS"], "zmin": 0.08},
)
