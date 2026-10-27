"""Who is on screen, where they sit, and what they can look at (diner world coords)."""
import rig

CHAR = {"hale": rig.HALE, "kai": rig.KAI}
SPEAKER = {"hale": "HALE", "kai": "KAI"}
OTHER = {"hale": "kai", "kai": "hale"}
BASE_PLACE = {"hale": (330.0, 1328.0, 0.80), "kai": (750.0, 1328.0, 0.82)}
MIRROR = {"hale": False, "kai": True}
DEFAULT_POSE = {"hale": "rest", "kai": "rest"}

GAZE_POINTS = {
    "tv": (892.0, 160.0),
    "window": (540.0, 640.0),
    "window_l": (330.0, 700.0),
    "street": (720.0, 880.0),
    "cuffs": (400.0, 1352.0),
    "mug_hale": (468.0, 1300.0),
    "mug_kai": (640.0, 1300.0),
    "sketch": (700.0, 1352.0),
    "table": (540.0, 1350.0),
    "door": (-300.0, 1050.0),
    "center": (540.0, 1180.0),
    "fists": (545.0, 1168.0),
}
