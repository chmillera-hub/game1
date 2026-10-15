"""Final render queue: renders shots at final quality in memory-bounded chunks, resumable.

    python3 psalm22/render_queue.py                    # all shots in timeline order
    python3 psalm22/render_queue.py s00 s20c s01a      # just these
    python3 psalm22/render_queue.py --quality draft    # e.g. a draft pass
    python3 psalm22/render_queue.py --workers 2        # two shots at once (LP_NUM_THREADS split)

Per shot: renders frames with `--frames auto:a-b --skip-existing` (12 fps when the shot sets ctx.interp),
then runs comp/interp.py for interp shots. Progress + timings: $WORK/logs/queue.log
"""
import json, os, subprocess, sys, time, threading

ROOT = os.path.dirname(os.path.abspath(__file__))
WORK = os.environ.get("WORK", "/opt/work/psalm22")
RUN = os.path.join(ROOT, "blender", "run.sh")
CHUNK = int(os.environ.get("CHUNK", "48"))
LOG = os.path.join(WORK, "logs")
os.makedirs(LOG, exist_ok=True)
lock = threading.Lock()


def log(msg):
    line = time.strftime("%H:%M:%S ") + msg
    with lock:
        print(line, flush=True)
        open(os.path.join(LOG, "queue.log"), "a").write(line + "\n")


def frames_dir(sid, q):
    return os.path.join(WORK, "frames", sid, q)


def meta(sid, q):
    p = os.path.join(frames_dir(sid, q), "meta.json")
    return json.load(open(p)) if os.path.exists(p) else None


def missing(sid, q, n, interp, keep=()):
    d = frames_dir(sid, q)
    want = sorted(set(range(1, n + 1, 2)) | set(keep)) if interp else range(1, n + 1)
    return [f for f in want if not (os.path.exists(os.path.join(d, "%04d.png" % f)) and os.path.getsize(os.path.join(d, "%04d.png" % f)) > 0)]


def run_chunk(sid, q, a, b, env):
    t = time.time()
    lf = open(os.path.join(LOG, "%s_%s.log" % (sid, q)), "a")
    r = subprocess.run([RUN, "--shot", sid, "--quality", q, "--frames", "auto:%d-%d" % (a, b), "--skip-existing"],
                       stdout=lf, stderr=subprocess.STDOUT, env=env)
    return r.returncode, time.time() - t


def render_shot(shot, q, env):
    sid, n = shot["id"], shot["render_frames"]
    t0 = time.time()
    m = meta(sid, q)
    if m is None:  # first chunk tells us interp / bake needs
        rc, dt = run_chunk(sid, q, 1, min(n, CHUNK), env)
        m = meta(sid, q)
        if rc != 0 or m is None:
            log("FAIL %s first chunk rc=%s (see logs/%s_%s.log)" % (sid, rc, sid, q))
            return False
    interp, bake = m.get("interp", False), m.get("needs_bake", False)
    keep = [f for f in m.get("interp_keep", []) if 1 <= f <= n]
    tries = 0
    while True:
        todo = missing(sid, q, n, interp, keep)
        if not todo:
            break
        tries += 1
        if tries > 6:
            log("FAIL %s still missing %d frames after retries" % (sid, len(todo)))
            return False
        a = todo[0]
        b = n if bake else min(n, a + CHUNK - 1)   # bake shots: one process (bake once)
        rc, dt = run_chunk(sid, q, a, b, env)
        done = len(todo) - len(missing(sid, q, n, interp, keep))
        log("%s %s frames %d-%d rc=%d %.0fs (%d new, %.1fs/frame)" % (sid, q, a, b, rc, dt, done, dt / max(1, done)))
        if done:
            tries = 0
    if interp:
        t = time.time()
        r = subprocess.run(["/opt/venv/bin/python", os.path.join(ROOT, "comp", "interp.py"), "--shot", sid, "--quality", q],
                           stdout=open(os.path.join(LOG, "%s_%s_interp.log" % (sid, q)), "a"), stderr=subprocess.STDOUT)
        log("%s interp rc=%d %.0fs" % (sid, r.returncode, time.time() - t))
    log("DONE %s (%d frames, interp=%s) in %.1f min" % (sid, n, interp, (time.time() - t0) / 60))
    return True


def main():
    args = sys.argv[1:]
    q = "final"
    workers = 1
    if "--quality" in args:
        i = args.index("--quality"); q = args[i + 1]; del args[i:i + 2]
    if "--workers" in args:
        i = args.index("--workers"); workers = int(args[i + 1]); del args[i:i + 2]
    tl = json.load(open(os.path.join(ROOT, "timeline.json")))
    shots = [s for s in tl["shots"] if not args or s["id"] in args]
    if args:
        shots.sort(key=lambda s: args.index(s["id"]))
    env = dict(os.environ)
    env["RENDER_SLOTS"] = env.get("RENDER_SLOTS", str(max(workers, 1)))
    if workers > 1:
        env["LP_NUM_THREADS"] = str(max(1, 4 // workers))
    log("queue start: %d shots, quality=%s, workers=%d" % (len(shots), q, workers))
    pending = list(shots)

    def worker():
        while True:
            with lock:
                if not pending:
                    return
                s = pending.pop(0)
            if os.path.exists(os.path.join(ROOT, "blender", "shots", s["id"] + ".py")):
                render_shot(s, q, env)
            else:
                log("SKIP %s (no shot script)" % s["id"])

    th = [threading.Thread(target=worker) for _ in range(workers)]
    for t in th:
        t.start()
    for t in th:
        t.join()
    log("queue finished")


if __name__ == "__main__":
    main()
