#!/usr/bin/env python3
"""Builds the voice acting for who-saves-the-hero.html with Piper TTS.

  pip install piper-tts
  node tools/extract-lines.js > tools/lines.json
  python3 tools/build-voices.py --voices DIR   # DIR holds the Piper .onnx/.onnx.json voice files

Writes audio/voice/<key>.mp3 for every spoken line and fills in the VOICES
duration table inside the HTML so the timeline paces itself to the speech.
Voice models come from https://huggingface.co/rhasspy/piper-voices
"""
import argparse, json, os, re, subprocess, tempfile, wave

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, 'who-saves-the-hero.html')
OUT = os.path.join(ROOT, 'audio', 'voice')

# speaker -> (model, length_scale, extra ffmpeg filter)
CAST = {
    'n':    ('en_US-norman-medium', 1.16, None),                      # narrator, unhurried storyteller
    'hero': ('en_US-ryan-high', 1.06, None),
    'th':   ('en_US-ryan-high', 1.18, 'volume=0.8,aecho=0.8:0.6:60:0.28,lowpass=f=5200'),  # inner voice
    'crim': ('en_GB-northern_english_male-medium', 1.02, None),
    'cop':  ('en_US-bryce-medium', 1.0, None),
}
CROWD = ['en_US-amy-medium', 'en_US-kusal-medium', 'en_US-joe-medium', 'en_US-john-medium', 'en_US-danny-low']


def say(text):
    """Text as it should be spoken rather than read."""
    t = text.replace('—', ', ').replace('...', ', ')
    t = re.sub(r'\b([A-Z]{2,})\b', lambda m: m.group(1).capitalize() if m.group(1) != 'I' else 'I', t)
    t = t.replace('W-what', 'W, what').replace('uhh', 'uh').replace('?!', '?')
    return re.sub(r'\s*,\s*,', ',', t).strip(' ,')


def piper(text, model, scale, voices, wav):
    subprocess.run(['piper', '-m', os.path.join(voices, model + '.onnx'), '-f', wav,
                    '--length-scale', str(scale), '--sentence-silence', '0.25', '--noise-scale', '0.7'],
                   input=text.encode(), check=True, capture_output=True)


def ff(*args):
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', *args], check=True)


def duration(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def build_line(line, voices, tmp):
    spk, text, key = line['speaker'], line['text'], line['key']
    raw = os.path.join(tmp, key + '.wav')
    if spk == 'crowd':
        parts = []
        for i, m in enumerate(CROWD):
            w = os.path.join(tmp, f'{key}_{i}.wav')
            piper(say(text), m, 0.95 + 0.04 * i, voices, w)
            parts.append(w)
        inputs = sum([['-i', w] for w in parts], [])
        delays = ''.join(f'[{i}]adelay={i * 110}|{i * 110},volume=0.5[a{i}];' for i in range(len(parts)))
        ff(*inputs, '-filter_complex', delays + ''.join(f'[a{i}]' for i in range(len(parts))) +
           f'amix=inputs={len(parts)}:normalize=0,aecho=0.8:0.5:40:0.2', raw)
    elif '*' in text:
        # bleep the swear: speak the words around it and drop a 1 kHz tone in the gap
        model, scale, _ = CAST[spk]
        before, after = re.split(r'\s*\S*\*+\S*\s*', text, maxsplit=1)
        a, b = os.path.join(tmp, key + '_a.wav'), os.path.join(tmp, key + '_b.wav')
        piper(say(before), model, scale, voices, a)
        piper(say(after), model, scale, voices, b)
        sr = wave.open(a).getframerate()
        ff('-i', a, '-f', 'lavfi', '-i', f'sine=frequency=1000:duration=0.42:sample_rate={sr}', '-i', b,
           '-filter_complex', '[1]volume=0.25[s];[0][s][2]concat=n=3:v=0:a=1', raw)
    else:
        model, scale, _ = CAST[spk]
        piper(say(text), model, scale, voices, raw)
    filt = CAST.get(spk, (None, None, None))[2]
    out = os.path.join(OUT, key + '.mp3')
    chain = 'silenceremove=start_periods=1:start_threshold=-50dB,areverse,silenceremove=start_periods=1:start_threshold=-50dB,areverse'
    if filt:
        chain += ',' + filt
    ff('-i', raw, '-af', chain + ',loudnorm=I=-17:TP=-1.5', '-ar', '24000', '-ac', '1', '-c:a', 'libmp3lame', '-b:a', '56k', out)
    return round(duration(out), 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--voices', required=True)
    ap.add_argument('--lines', default=os.path.join(ROOT, 'tools', 'lines.json'))
    args = ap.parse_args()
    lines = json.load(open(args.lines))
    os.makedirs(OUT, exist_ok=True)
    table, seen = {}, set()
    with tempfile.TemporaryDirectory() as tmp:
        for ln in lines:
            if ln['key'] in seen:
                continue
            seen.add(ln['key'])
            table[ln['key']] = build_line(ln, args.voices, tmp)
            print(f"{ln['part']}  {ln['speaker']:5} {table[ln['key']]:5.2f}s  {ln['text'][:60]}")
    for f in os.listdir(OUT):  # drop clips for lines that no longer exist
        if f.endswith('.mp3') and f[:-4] not in table:
            os.remove(os.path.join(OUT, f))
    html = open(HTML).read()
    html = re.sub(r'/\*VOICES\*/.*?/\*END-VOICES\*/', '/*VOICES*/' + json.dumps(table, separators=(',', ':')) + '/*END-VOICES*/', html, flags=re.S)
    open(HTML, 'w').write(html)
    print(f'{len(table)} clips, {sum(table.values()):.0f}s of speech')


if __name__ == '__main__':
    main()
