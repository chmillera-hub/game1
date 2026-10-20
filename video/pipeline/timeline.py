"""Build the master timeline from generated voice lines.

Run with the TTS venv:  /opt/tts/bin/python timeline.py
Reads /opt/work/audio/lines/<id>.wav, aligns words with faster-whisper, phonemizes with espeak-ng,
places lines back to back with each line's pause_after (+ scene-change gaps) and writes
/opt/work/timeline.json and /opt/work/audio/dialogue.wav (48 kHz mono).
"""
import json, os, re, subprocess, sys
import numpy as np
import soundfile as sf
import librosa

sys.path.insert(0, os.path.dirname(__file__))
import screenplay as sp

LINES_DIR = "/opt/work/audio/lines"
SR = 48000
LEAD_IN = 0.6           # seconds before the first line (picture starts immediately)
SCENE_GAP = {           # extra breathing room when the scene changes (seconds)
    ("colonnade", "street"): 0.6, ("street", "upper_room"): 1.4, ("upper_room", "apartment"): 0.5,
    ("apartment", "upper_room"): 0.3, ("upper_room", "sister"): 0.2, ("sister", "apartment"): 0.0,
    ("apartment", "sister"): 0.0, ("sister", "upper_room"): 0.4, ("upper_room", "cosmos"): 0.0,
    ("cosmos", "city"): 0.2, ("city", "upper_room"): 0.0, ("upper_room", "door"): 0.3, ("door", "upper_room"): 0.0,
}
TAIL = 3.0

IPA_VISEME = [  # longest symbols first
    ("aʊ", "aw_09"), ("ɔɪ", "oy_10"), ("aɪ", "ay_11"), ("eɪ", "ey_eh_uh_04"), ("oʊ", "ow_08"),
    ("tʃ", "sh_ch_jh_zh_16"), ("dʒ", "sh_ch_jh_zh_16"), ("ɑː", "aa_02"), ("iː", "y_iy_ih_ix_06"),
    ("uː", "w_uw_07"), ("ɜː", "er_05"), ("ɔː", "ao_03"),
    ("æ", "aa_ah_ax_01"), ("ə", "aa_ah_ax_01"), ("ʌ", "aa_ah_ax_01"), ("ɐ", "aa_ah_ax_01"), ("ɑ", "aa_02"),
    ("a", "aa_02"), ("ɔ", "ao_03"), ("ɛ", "ey_eh_uh_04"), ("e", "ey_eh_uh_04"), ("ʊ", "ey_eh_uh_04"),
    ("ɝ", "er_05"), ("ɚ", "er_05"), ("ɜ", "er_05"), ("i", "y_iy_ih_ix_06"), ("ɪ", "y_iy_ih_ix_06"),
    ("ᵻ", "y_iy_ih_ix_06"), ("j", "y_iy_ih_ix_06"), ("w", "w_uw_07"), ("u", "w_uw_07"), ("o", "ow_08"),
    ("h", "h_12"), ("ɹ", "r_13"), ("r", "r_13"), ("l", "l_14"), ("s", "s_z_15"), ("z", "s_z_15"),
    ("ʃ", "sh_ch_jh_zh_16"), ("ʒ", "sh_ch_jh_zh_16"), ("ð", "th_dh_17"), ("θ", "th_dh_17"),
    ("f", "f_v_18"), ("v", "f_v_18"), ("d", "d_t_n_19"), ("t", "d_t_n_19"), ("n", "d_t_n_19"),
    ("ɾ", "d_t_n_19"), ("k", "k_g_ng_20"), ("g", "k_g_ng_20"), ("ɡ", "k_g_ng_20"), ("ŋ", "k_g_ng_20"),
    ("p", "p_b_m_21"), ("b", "p_b_m_21"), ("m", "p_b_m_21"), ("ʔ", "sil_00"),
]
VOWELS = {"aw_09", "oy_10", "ay_11", "ow_08", "aa_02", "aa_ah_ax_01", "ao_03", "ey_eh_uh_04", "er_05",
          "y_iy_ih_ix_06", "w_uw_07"}


TARGET_WPS = {"NARRATOR": 2.45, "JESUS": 2.35, "ELDER": 2.6, "YOUNG": 2.3, "PETER": 2.9, "JOHN": 2.3,
              "WOMAN": 2.3, "SISTER": 2.3}


def pace(y, sr, line):
    """Slow rushed takes toward a natural speaking rate (rubberband keeps pitch and formants)."""
    n_words = len(line["text"].split())
    dur = len(y) / sr
    if dur <= 0 or n_words < 3:
        return y
    wps = n_words / dur
    tgt = TARGET_WPS.get(line["speaker"], 2.5)
    tempo = float(np.clip(tgt / wps, 0.80, 1.0))
    if tempo > 0.985:
        return y
    tmp_in, tmp_out = "/tmp/pace_in.wav", "/tmp/pace_out.wav"
    sf.write(tmp_in, y, sr)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp_in, "-af",
                    f"rubberband=tempo={tempo:.4f}:formant=preserved:pitchq=quality:window=standard",
                    tmp_out], check=True)
    out, _ = sf.read(tmp_out)
    line["tempo"] = tempo
    return out.astype(np.float32)


def phonemes(word):
    w = re.sub(r"[^A-Za-z']", "", word)
    if not w:
        return []
    ipa = subprocess.run(["espeak-ng", "-q", "--ipa", "-v", "en-us", w], capture_output=True, text=True).stdout
    ipa = re.sub(r"[ˈˌ‍\s‍]", "", ipa)
    out, i = [], 0
    while i < len(ipa):
        for sym, vis in IPA_VISEME:
            if ipa.startswith(sym, i):
                out.append(vis)
                i += len(sym)
                break
        else:
            i += 1
    return out


def emphasis(y, words):
    """Per-word emphasis 0..1 from relative loudness and pitch (drives brow raises and nods)."""
    if not words:
        return
    f0, vf, _ = librosa.pyin(y, fmin=60, fmax=420, sr=SR, frame_length=2048, hop_length=480)
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=480)[0]
    times = np.arange(len(rms)) * 480 / SR
    vals = []
    for w in words:
        m = (times >= w["start"]) & (times <= w["end"])
        r = float(rms[m].mean()) if m.any() else 0.0
        p = float(np.nanmean(f0[m[:len(f0)]])) if m[:len(f0)].any() and not np.all(np.isnan(f0[m[:len(f0)]])) else np.nan
        vals.append((r, p))
    r = np.array([v[0] for v in vals])
    p = np.array([v[1] for v in vals])
    rz = (r - r.mean()) / (r.std() + 1e-6)
    pm = np.nanmean(p) if np.any(~np.isnan(p)) else 0
    ps = np.nanstd(p) if np.any(~np.isnan(p)) else 1
    pz = np.where(np.isnan(p), 0, (p - pm) / (ps + 1e-6))
    e = 1 / (1 + np.exp(-(0.6 * rz + 0.8 * pz)))
    for w, v in zip(words, e):
        w["emph"] = round(float(v), 3)


def align_words(model, wav16, text):
    segs, _ = model.transcribe(wav16, word_timestamps=True, beam_size=5, language="en",
                               initial_prompt=text)
    words = []
    for s in segs:
        for w in s.words:
            words.append(dict(word=w.word.strip(), start=float(w.start), end=float(w.end)))
    return words


def wer(ref, hyp):
    r = re.sub(r"[^a-z' ]", " ", ref.lower()).split()
    h = re.sub(r"[^a-z' ]", " ", hyp.lower()).split()
    d = np.zeros((len(r) + 1, len(h) + 1))
    d[:, 0] = range(len(r) + 1)
    d[0, :] = range(len(h) + 1)
    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            d[i, j] = min(d[i - 1, j] + 1, d[i, j - 1] + 1, d[i - 1, j - 1] + (r[i - 1] != h[j - 1]))
    return d[-1, -1] / max(1, len(r))


def main():
    from faster_whisper import WhisperModel
    model = WhisperModel("small.en", device="cpu", compute_type="int8")
    t = LEAD_IN
    out_lines = []
    pieces = []
    prev_scene = None
    report = []
    for l in sp.LINES:
        path = f"{LINES_DIR}/{l['id']}.wav"
        if not os.path.exists(path):
            if "--partial" not in sys.argv:
                raise FileNotFoundError(path)
            sr = 24000
            y = np.zeros(int(sr * max(0.8, len(l["text"].split()) / 2.6)), dtype=np.float32)
        else:
            y, sr = sf.read(path)
            if y.ndim > 1:
                y = y.mean(axis=1)
        if prev_scene and prev_scene != l["scene"]:
            t += SCENE_GAP.get((prev_scene, l["scene"]), 0.4)
        prev_scene = l["scene"]
        if np.abs(y).max() > 0:
            y = pace(y.astype(np.float32), sr, l)
        y48 = librosa.resample(y.astype(np.float32), orig_sr=sr, target_sr=SR)
        y16 = librosa.resample(y.astype(np.float32), orig_sr=sr, target_sr=16000)
        words = align_words(model, y16, l["text"]) if np.abs(y).max() > 0 else []
        hyp = " ".join(w["word"] for w in words)
        err = wer(l["text"], hyp)
        report.append((l["id"], round(err, 3), hyp))
        dur = len(y48) / SR
        emphasis(y48, words)
        for w in words:
            w["phonemes"] = phonemes(w["word"])
            w["start"] += t
            w["end"] += t
        out_lines.append(dict(id=l["id"], speaker=l["speaker"], scene=l["scene"], emotion=l["emotion"], text=l["text"],
                              start=round(t, 4), end=round(t + dur, 4), words=words, wer=err,
                              tempo=l.get("tempo", 1.0), wav=f"/opt/work/audio/final/{l['id']}.wav"))
        os.makedirs("/opt/work/audio/final", exist_ok=True)
        sf.write(f"/opt/work/audio/final/{l['id']}.wav", y48, SR)
        pieces.append((t, y48))
        t += dur + l["pause_after"]
    total = t + TAIL
    mix = np.zeros(int(total * SR) + SR, dtype=np.float32)
    for st, y in pieces:
        i = int(st * SR)
        mix[i:i + len(y)] += y
    sf.write("/opt/work/audio/dialogue.wav", mix[:int(total * SR)], SR)
    json.dump(dict(duration=round(total, 4), fps=24, lines=out_lines), open("/opt/work/timeline.json", "w"), indent=1)
    for r in report:
        flag = "  <-- CHECK" if r[1] > 0.15 else ""
        print(f"{r[0]} wer={r[1]:.2f} | {r[2]}{flag}")
    print("TOTAL", round(total, 2), "s")


if __name__ == "__main__":
    main()
