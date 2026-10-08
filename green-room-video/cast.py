"""Everyone from the first two videos, reunited."""
from characters import Look
import importlib.util, os

_here = os.path.dirname(__file__)


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

_a = _load(os.path.join(_here, "..", "board-meeting-video", "cast.py"), "cast_a")
_b = _load(os.path.join(_here, "..", "long-dream-video", "cast.py"), "cast_b")
CEO, CFO, TYLER, PAM, JESUS, KID = _a.CEO, _a.CFO, _a.TYLER, _a.PAM, _a.JESUS, _a.CREATOR
CYAN, GOLD = _b.CYAN, _b.GOLD
