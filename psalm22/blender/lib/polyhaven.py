"""Download + cache CC0 assets from Poly Haven (works inside Blender or plain Python).

    hdri_path("qwantani_sunset_puresky", "2k")            -> local .hdr path
    texture_maps("dry_ground_01", "1k")                    -> {"diff":..., "rough":..., "nor":..., "disp":..., "arm":...}
    model_blend("boulder_01", "1k")                        -> local .blend path (with textures beside it)

Catalogs (names + categories): /opt/assets/polyhaven/{hdris,textures,models}_catalog.txt
"""
import json, os, ssl, time, urllib.request

CACHE = "/opt/assets/polyhaven"
API = "https://api.polyhaven.com"


def _ctx():
    ca = os.environ.get("SSL_CERT_FILE") or "/root/.ccr/ca-bundle.crt"
    return ssl.create_default_context(cafile=ca) if os.path.exists(ca) else ssl.create_default_context()


def _get(url, tries=4):
    err = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "psalm22-film-pipeline/1.0 (blender)"})
            with urllib.request.urlopen(req, context=_ctx(), timeout=120) as r:
                return r.read()
        except Exception as e:  # network hiccup: retry with backoff
            err = e
            time.sleep(2 ** (i + 1))
    raise RuntimeError("download failed %s: %s" % (url, err))


def _download(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return dest
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    tmp = dest + ".part%d" % os.getpid()
    with open(tmp, "wb") as f:
        f.write(_get(url))
    os.replace(tmp, dest)
    return dest


def files(asset):
    p = os.path.join(CACHE, "_files", asset + ".json")
    if not os.path.exists(p):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        data = _get("%s/files/%s" % (API, asset))
        tmp = p + ".part%d" % os.getpid()
        open(tmp, "wb").write(data)
        os.replace(tmp, p)
    return json.load(open(p))


def hdri_path(asset, res="2k"):
    f = files(asset)["hdri"][res]["hdr"]
    return _download(f["url"], os.path.join(CACHE, "hdris", asset, os.path.basename(f["url"])))


def texture_maps(asset, res="1k"):
    """Return dict of local map paths. Keys: diff, rough, nor, disp, ao, arm (when available)."""
    f = files(asset)
    want = {"diff": ("Diffuse", "jpg"), "rough": ("Rough", "jpg"), "nor": ("nor_gl", "jpg"),
            "disp": ("Displacement", "png"), "ao": ("AO", "jpg"), "arm": ("arm", "jpg")}
    out = {}
    for key, (name, fmt) in want.items():
        if name in f and res in f[name]:
            entry = f[name][res].get(fmt) or f[name][res].get("jpg") or f[name][res].get("png")
            if entry:
                out[key] = _download(entry["url"], os.path.join(CACHE, "textures", asset, res, os.path.basename(entry["url"])))
    return out


def model_blend(asset, res="1k"):
    f = files(asset)["blend"][res]["blend"]
    base = os.path.join(CACHE, "models", asset, res)
    for rel, inc in f.get("include", {}).items():
        _download(inc["url"], os.path.join(base, rel))
    return _download(f["url"], os.path.join(base, os.path.basename(f["url"])))


def catalog(kind):
    return open(os.path.join(CACHE, kind + "_catalog.txt")).read().splitlines()
