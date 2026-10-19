"""Generate the photoreal shot images (SDXL Lightning, CPU bfloat16).

Usage: python gen_images.py shots.json OUT_DIR [shot_id ...]
Shots with a `ref` use IP-Adapter Plus-Face with a face crop of that reference
image, so Maya stays the same person across scenes. Existing images are kept.
"""
import json
import os
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import torch
from diffusers import DPMSolverMultistepScheduler, StableDiffusionXLPipeline
from PIL import Image

sys.path.insert(0, "/opt/real/LivePortrait")
from src.utils.face_analysis_diy import FaceAnalysisDIY  # noqa: E402

torch.set_num_threads(int(os.environ.get("THREADS", "4")))
MODEL = "/opt/real/models/realvisxl5l"
IPA = "/opt/real/models/ipadapter"
STEPS, CFG = 6, 1.6


@torch.no_grad()
def encode_long(pipe, prompt, negative):
    """SDXL text embeddings for prompts longer than CLIP's 77 tokens: the text is
    split into 75-token chunks, each encoded with BOS/EOS and concatenated along
    the sequence (positive and negative padded to the same number of chunks)."""
    def ids(tok, text):
        return tok(text, add_special_tokens=False, truncation=False).input_ids

    def chunks(tok, text, n=None):
        t = ids(tok, text)
        cs = [t[i:i + 75] for i in range(0, max(1, len(t)), 75)] or [[]]
        while n and len(cs) < n:
            cs.append([])
        out = []
        for c in cs:
            row = [tok.bos_token_id] + c + [tok.eos_token_id]
            row += [tok.pad_token_id] * (77 - len(row))
            out.append(row)
        return torch.tensor(out)

    def n_chunks(text):
        return max(1, -(-len(ids(pipe.tokenizer, text)) // 75))

    n = max(n_chunks(prompt), n_chunks(negative))
    embs, pooled = [], []
    for text in (prompt, negative):
        per = []
        pool = None
        for tok, enc in ((pipe.tokenizer, pipe.text_encoder), (pipe.tokenizer_2, pipe.text_encoder_2)):
            x = chunks(tok, text, n)
            o = enc(x, output_hidden_states=True)
            per.append(o.hidden_states[-2].reshape(1, -1, o.hidden_states[-2].shape[-1]))
            if enc is pipe.text_encoder_2:
                pool = o[0][:1]
        embs.append(torch.cat(per, dim=-1))
        pooled.append(pool)
    return {"prompt_embeds": embs[0], "negative_prompt_embeds": embs[1],
            "pooled_prompt_embeds": pooled[0], "negative_pooled_prompt_embeds": pooled[1]}


def face_detector():
    fa = FaceAnalysisDIY(name="buffalo_l", root="/opt/real/LivePortrait/pretrained_weights/insightface",
                         providers=["CPUExecutionProvider"])
    fa.prepare(ctx_id=-1, det_size=(512, 512), det_thresh=0.5)
    return fa


def face_crop(fa, path, pad=0.45):
    img = np.array(Image.open(path).convert("RGB"))
    faces = fa.get(cv2.cvtColor(img, cv2.COLOR_RGB2BGR), flag_do_landmark_2d_106=False)
    if not faces:
        return Image.fromarray(img)
    x0, y0, x1, y1 = faces[0].bbox
    w, h = x1 - x0, y1 - y0
    s = max(w, h) * (1 + pad * 2)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2 - h * 0.08
    box = [int(max(0, cx - s / 2)), int(max(0, cy - s / 2)), int(min(img.shape[1], cx + s / 2)), int(min(img.shape[0], cy + s / 2))]
    return Image.fromarray(img[box[1]:box[3], box[0]:box[2]]).resize((448, 448), Image.LANCZOS)


def main():
    shots = json.loads(Path(sys.argv[1]).read_text())
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    only = set(sys.argv[3:])
    todo = [s for s in shots if (not only or s["id"] in only) and not (out / f"{s['id']}.png").exists()]
    todo.sort(key=lambda s: bool(s.get("ref")))   # load the IP-Adapter once, after the reference exists
    if not todo:
        print("nothing to do")
        return
    t = time.time()
    pipe = StableDiffusionXLPipeline.from_pretrained(MODEL, torch_dtype=torch.bfloat16, variant="fp16", use_safetensors=True)
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config, algorithm_type="sde-dpmsolver++",
                                                             use_karras_sigmas=True)
    pipe.set_progress_bar_config(disable=True)
    print(f"loaded in {time.time() - t:.0f}s", flush=True)
    fa = None
    ip_loaded = False
    refs = {}
    for s in todo:
        kw = {}
        if s.get("ref"):
            if not ip_loaded:
                pipe.load_ip_adapter(IPA, subfolder="sdxl_models", weight_name="ip-adapter-plus-face_sdxl_vit-h.safetensors",
                                     image_encoder_folder="models/image_encoder", torch_dtype=torch.bfloat16)
                ip_loaded = True
            if s["ref"] not in refs:
                fa = fa or face_detector()
                refs[s["ref"]] = face_crop(fa, out / f"{s['ref']}.png")
                refs[s["ref"]].save(out / f"{s['ref']}_face.png")
            pipe.set_ip_adapter_scale(s.get("ip", 0.6))
            kw["ip_adapter_image"] = refs[s["ref"]]
        elif ip_loaded:
            pipe.unload_ip_adapter()
            ip_loaded = False
        tf = os.environ.get("THREADS_FILE")
        if tf and os.path.exists(tf):
            torch.set_num_threads(int(open(tf).read().strip()))   # adjustable while running
        neg = s["negative"]
        if s["id"].startswith("expr_"):
            neg = neg.replace("open mouth, teeth, frown lines, ", "")
        t = time.time()
        g = torch.Generator().manual_seed(s["seed"])
        with torch.inference_mode():
            emb = encode_long(pipe, s["prompt"], neg)
            img = pipe(width=s["w"], height=s["h"], num_inference_steps=STEPS, guidance_scale=CFG, generator=g,
                       **emb, **kw).images[0]
        img.save(out / f"{s['id']}.png")
        print(f"{s['id']:20s} {time.time() - t:6.1f}s", flush=True)


if __name__ == "__main__":
    main()
