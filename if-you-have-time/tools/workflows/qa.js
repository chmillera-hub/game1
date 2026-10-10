export const meta = {
  name: 'iyht-final-qa',
  description: 'Whole-film QA of the rendered "If You Have Time" (4 review lenses), then fix findings grouped by file',
  phases: [
    { title: 'Review', detail: 'continuity, acting/lip-sync, AV sync/audio, encode quality' },
    { title: 'Fix', detail: 'one fixer per file group' },
  ],
}

const ROOT = '/home/user/game1/if-you-have-time'
const COMMON = `
You are on the finishing team of "IF YOU HAVE TIME", a 3m52s portrait (720x1280, 24 fps) animated short generated entirely with code in ${ROOT}.
Read ${ROOT}/BIBLE.md (story, shot list section 4, continuity section 9) and skim ${ROOT}/build/timeline.json (scene spans, line times, beats,
music cues, sfx times). The whole film is RENDERED:
  ${ROOT}/build/video_master.mkv   high-quality master (x264 crf 8, yuv444)
  ${ROOT}/build/drafts/if_you_have_time_draft1.mp4 final deliverable (H.264 + AAC, target < 15 MB)
  ${ROOT}/build/mix.wav            final 48 kHz stereo mix
Code: anim/scenes/s0..s5.py (scene direction), anim/char_rae.py, anim/char_quill.py, anim/env.py, anim/fx.py, audio/*.py, script_data.py.
Useful tools (run from ${ROOT}):
  - extract frames: ffmpeg -v error -ss <t> -i build/video_master.mkv -frames:v 1 out.png
  - contact sheet from video: ffmpeg -v error -ss <t0> -t <dur> -i build/video_master.mkv -vf "fps=2,scale=180:-1,tile=8x5" -frames:v 1 sheet.png
  - exact frames from code: python3 -m anim.preview sheet OUT.png t1 t2 ... --cols 6 --scale 0.3
  - spectrogram with timeline overlay: python3 tools/spectro.py build/mix.wav OUT.png [--start S --end E]
  - speech recognition: faster_whisper WhisperModel('small.en', device='cpu', compute_type='int8', download_root='/home/user/models/whisper');
    pass a float32 numpy array resampled to 16 kHz (soundfile + scipy.signal.resample_poly), NOT a path.
Put all your outputs under ${ROOT}/build/tests/qa_<your-lens>/. LOOK at every image you make with the Read tool.
4 shared CPU cores: at most 2 heavy processes. Do not git commit.`

const IMG_BUDGET = `
HARD MEMORY LIMIT (the machine has crashed twice from agents viewing too many large images): view at most ~25 images in total with
the Read tool. Every image you view must be <= 1400 px on its longest side and saved as JPEG quality ~80 (PIL .save(..., quality=80) or
ffmpeg -q:v 4), so each is a few hundred KB. Put many frames into ONE downscaled contact sheet instead of viewing frames one by one, and
prefer numeric checks (frame-difference scans, pixel probes, ffprobe/ffmpeg measurements, PSNR/SSIM, whisper transcripts) over looking.`

const FINDINGS = {
  type: 'object',
  properties: {
    summary: { type: 'string' },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          severity: { type: 'string', enum: ['high', 'medium', 'low'] },
          group: { type: 'string', enum: ['s05', 's1', 's2', 's34', 'rae', 'quill', 'envfx', 'audio', 'encode'] },
          time: { type: 'string', description: 'absolute time(s) or range in seconds' },
          issue: { type: 'string' },
          evidence: { type: 'string', description: 'path(s) of image/measurement showing it' },
          fix: { type: 'string', description: 'concrete proposed fix' },
        },
        required: ['severity', 'group', 'time', 'issue', 'evidence', 'fix'],
      },
    },
  },
  required: ['summary', 'findings'],
}

const GROUP_NOTE = `Each finding's "group" names the file group that must change: s05 = anim/scenes/s0.py+s5.py, s1 = anim/scenes/s1.py,
s2 = anim/scenes/s2.py, s34 = anim/scenes/s3.py+s4.py, rae = anim/char_rae.py, quill = anim/char_quill.py, envfx = anim/env.py+fx.py,
audio = audio/*.py or script_data.py timing/gains, encode = build.py encode settings. Severity: high = a viewer would notice/it breaks the
story or looks broken; medium = noticeable polish issue; low = nitpick. Only report real, verified problems (look at the frames!). Do NOT edit files.`

const LENSES = [
  { key: 'continuity', prompt: `YOUR LENS: story clarity, editing and continuity across the WHOLE film.
Make contact sheets of the entire master at 2 fps (in ~20 s chunks) and look at all of them; then dense (every-frame) strips across every
scene boundary (16.0, 58.98, 134.58, 148.52, 211.83) and across every hard cut you notice. Check: does the story read clearly even with the
sound off; pacing; shot variety; that character design, proportions, scale and lighting stay consistent across scenes and cuts; character
positions/props match across cuts (mug!, hands, kneeling/seated state, Quill's hands); no black/blank/broken frames, pops, jitter,
background voids at frame edges, awkward crops of faces, flashes that are too harsh, text legibility of the title, cards and end card.` },
  { key: 'acting', prompt: `YOUR LENS: performance, facial expression and lip-sync for EVERY dialogue line (build/timeline.json lines) and the key
silent beats (rae_freeze, the symphony reactions, the snap, each alternate's reaction, the exit, quill_smile).
For each line render a strip of frames from 0.2 s before start to 0.2 s after end (every 2nd frame) from the master: verify the speaker's
mouth visibly moves with the speech and closes in pauses/after the line, the expression fits the line's emotion (BIBLE section 4),
eyes/eyelids/brows are alive but not twitchy, the listener reacts, and the speaker's face is readable in frame. Flag robotic stillness,
over-acting, mouths open while silent, wrong character's mouth moving, faces too small/cropped/hidden during their line.` },
  { key: 'avsync', prompt: `YOUR LENS: audio-visual sync and the audio mix.
(1) For every SFX and music event in build/timeline.json, check the matching visual happens at the same moment (door slides vs door_open/
door_close, footsteps vs steps, bench_sit vs landing, sip vs sip, process_chitter/compose_done vs Quill's processing/eye flash, lights_down vs
dimming, snap_back vs the snap, holo_open/holo_select vs card fan/focus, music cue starts vs card selections, sym_climax burst vs the music
climax, send_chime vs send lights, whoosh_dive vs the dive flash). Report offsets > 2 frames that are noticeable.
(2) Audio: spectrogram of the whole mix (tools/spectro.py) and zoomed views; loudness per section; music ducking under dialogue; any clicks,
abrupt cuts, silence gaps that feel wrong, harsh SFX, VO too quiet/loud vs music. Run faster-whisper on the MIX for every dialogue line
(segment start-0.1 .. end+0.2) and compare to the script text to confirm intelligibility over the music; report lines that mis-transcribe
because of the mix (not because of an inherently odd word like 'theremin'). Also check the audio track in build/drafts/if_you_have_time_draft1.mp4 (AAC)
decodes and matches the mix length.` },
  { key: 'encode', prompt: `YOUR LENS: final deliverable + compression quality.
Check build/drafts/if_you_have_time_draft1.mp4: size < 15,000,000 bytes, 720x1280 portrait, 24 fps, H.264 High yuv420p, AAC stereo, duration matches,
faststart, plays from start to end (decode the whole thing with ffmpeg -f null and check for errors). Then compare encoded frames vs the master
at the hardest moments (the S0 dive and flash ~12-16 s, ribbons/memories ~70-95 s, galaxy swirl ~95-110 s, the burst ~111-118 s, falling sparks
~126-134 s, card fans, the lo-fi rain ~176-183 s, the end card): extract the same frames from both, compute PSNR/SSIM per frame (ffmpeg
-lavfi psnr/ssim), and LOOK at side-by-side crops for blocking, banding, smearing, mosquito noise, faces turning to mush. Identify the worst
moments and propose concrete fixes: encoder settings in build.py (e.g. aq, psy, bframes, keyint, deblock, tune, or rebalancing audio bitrate)
and/or visual simplifications in specific scene/fx code (e.g. reduce noisy sparkles, soften grain-like detail) that would free bits.
You may run experimental encodes into build/tests/qa_encode/ to prove a settings change (keep total size target 14,000,000 bytes).` },
]

const GROUP_FILES = {
  s05: 'anim/scenes/s0.py and anim/scenes/s5.py', s1: 'anim/scenes/s1.py', s2: 'anim/scenes/s2.py', s34: 'anim/scenes/s3.py and anim/scenes/s4.py',
  rae: 'anim/char_rae.py', quill: 'anim/char_quill.py', envfx: 'anim/env.py and anim/fx.py',
  audio: 'audio/music.py, audio/sfx.py, audio/mix.py, and (timing/gain only, keep line ids and beat names) script_data.py', encode: 'build.py (encode() settings only)',
}

phase('Review')
const reviews = (await parallel(LENSES.map(l => () =>
  agent(l.key === 'acting' ? `${COMMON}\n${l.prompt}\n${GROUP_NOTE}` : `${COMMON}\n${l.prompt}\n${GROUP_NOTE}\n${IMG_BUDGET}`, { label: `review:${l.key}`, phase: 'Review', schema: FINDINGS })
    .then(r => r && ({ lens: l.key, ...r }))))).filter(Boolean)

const all = reviews.flatMap(r => r.findings.map(f => ({ ...f, lens: r.lens })))
log(`${all.length} findings: ${all.filter(f => f.severity === 'high').length} high, ${all.filter(f => f.severity === 'medium').length} medium`)
const groups = {}
for (const f of all) (groups[f.group] = groups[f.group] || []).push(f)

phase('Fix')
const order = ['rae', 'quill', 'envfx', 's2', 's1', 's34', 's05', 'audio', 'encode']
const fixes = await parallel(order.filter(g => groups[g] && groups[g].length).map(g => () => {
  const list = groups[g].map((f, i) => `${i + 1}. [${f.severity}] (${f.lens}) t=${f.time}: ${f.issue}\n   evidence: ${f.evidence}\n   proposed fix: ${f.fix}`).join('\n')
  return agent(`${COMMON}
YOUR TASK: you own ${GROUP_FILES[g]} for this finishing pass. Independent reviewers watched the rendered film and raised these findings for your files:
${list}
Fix every high and medium finding (and lows that are cheap and safe), unless a finding is factually wrong - verify each against the code and
by rendering the exact frames (python3 -m anim.preview sheet ...) before and after; LOOK at them. Keep all public APIs and scene-boundary
continuity (BIBLE section 9) intact; other fixers are editing other files concurrently (scene owners may be adjusting for rig fixes and vice
versa), so keep changes local and minimal-risk. Do NOT re-render the whole film. For audio changes, re-run the affected audio step
(e.g. python3 audio/mix.py) and verify with measurements. For encode changes, prove them with a test encode into build/tests/qa_encode/.
${IMG_BUDGET}
Final answer: per finding - fixed (how, evidence path) / not fixed (why).`, { label: `fix:${g}`, phase: 'Fix' }).then(r => ({ group: g, report: r }))
}))

return { reviews: reviews.map(r => ({ lens: r.lens, summary: r.summary, n: r.findings.length })), findings: all, fixes: fixes.filter(Boolean) }
