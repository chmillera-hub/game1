"""Generate voice lines: Kokoro reference voices -> Chatterbox expressive takes -> ASR check.

Run with the chatterbox venv:  /opt/cbx/bin/python tts_generate.py [line ids...]
Writes /opt/work/audio/lines/<id>.wav (24 kHz mono, trimmed) and <id>.json (take info).
"""
import json, os, re, sys, subprocess
import numpy as np
import soundfile as sf
import torch

sys.path.insert(0, os.path.dirname(__file__))
import screenplay as sp

OUT = "/opt/work/audio/lines"
REF = "/opt/work/audio/refs"
os.makedirs(OUT, exist_ok=True)
os.makedirs(REF, exist_ok=True)
torch.set_num_threads(int(os.environ.get("TTS_THREADS", "4")))

REF_TEXT = ("The evening light settled over the old city, and the streets grew quiet. "
            "Some people hurried home, while others lingered by the gate, talking softly.")


def tts_text(t):
    t = t.replace('"', "").replace("'I", "I").replace("gods'", "gods").replace("Son'", "Son")
    return re.sub(r"\s+", " ", t).strip()


def make_refs():
    need = [s for s in sp.CAST if not os.path.exists(f"{REF}/{s}.wav")]
    if not need:
        return
    code = (
        "import sys, numpy as np, soundfile as sf\n"
        "from kokoro import KPipeline\n"
        "pipes = {}\n"
        "for spk, voice, lang in [a.split(':') for a in sys.argv[2:]]:\n"
        "    p = pipes.setdefault(lang, KPipeline(lang_code=lang, repo_id='hexgrad/Kokoro-82M'))\n"
        "    a = np.concatenate([r.audio.numpy() for r in p(sys.argv[1], voice=voice, speed=0.95)])\n"
        f"    sf.write('{REF}/' + spk + '.wav', a, 24000)\n"
    )
    args = [f"{s}:{sp.CAST[s][0]}:{sp.CAST[s][1]}" for s in need]
    subprocess.run(["/opt/tts/bin/python", "-c", code, REF_TEXT] + args, check=True)


def trim(wav, sr, top_db=42, pad=0.04):
    import librosa
    _, (a, b) = librosa.effects.trim(wav, top_db=top_db, frame_length=512, hop_length=128)
    a = max(0, a - int(pad * sr))
    b = min(len(wav), b + int(pad * sr))
    out = wav[a:b].copy()
    fade = int(0.01 * sr)
    out[:fade] *= np.linspace(0, 1, fade)
    out[-fade:] *= np.linspace(1, 0, fade)
    return out


def main(ids):
    make_refs()
    from chatterbox.tts import ChatterboxTTS
    model = ChatterboxTTS.from_pretrained(device="cpu")
    lines = [l for l in sp.LINES if not ids or l["id"] in ids]
    for l in lines:
        take = int(os.environ.get("TAKE", "0"))
        path = f"{OUT}/{l['id']}.wav"
        if os.path.exists(path) and not ids:
            continue
        torch.manual_seed(1000 + take * 7919 + sum(map(ord, l["id"])))
        cfg = sp.CAST[l["speaker"]][2]
        wav = model.generate(tts_text(l["text"]), audio_prompt_path=f"{REF}/{l['speaker']}.wav",
                             exaggeration=l["ex"], cfg_weight=cfg, temperature=0.75)
        wav = wav.squeeze(0).numpy().astype(np.float32)
        wav = trim(wav, model.sr)
        sf.write(path, wav, model.sr)
        json.dump(dict(id=l["id"], take=take, sr=model.sr, dur=len(wav) / model.sr), open(f"{OUT}/{l['id']}.json", "w"))
        print("LINE", l["id"], round(len(wav) / model.sr, 2), flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
