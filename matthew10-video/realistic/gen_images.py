"""Generate the photoreal shot images (SDXL Lightning, CPU bfloat16).

Usage: python gen_images.py shots.json OUT_DIR [shot_id ...]
Shots with a `ref` use IP-Adapter Plus-Face with a face crop of that reference
image, so Maya stays the same person across scenes. Shots with an `init` image
(a raw frame of the 2D version) are photo-realized from it with img2img, which
keeps the staging of group shots that text prompts alone cannot place; their
people are then repainted one by one (`inpaint` boxes, each with its own prompt)
so each keeps their own age, look and clothes. Existing images are kept.
"""
import ctypes
import gc
import json
import os
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import torch
from diffusers import (DPMSolverMultistepScheduler, StableDiffusionXLImg2ImgPipeline, StableDiffusionXLInpaintPipeline,
                       StableDiffusionXLPipeline)
from PIL import Image, ImageDraw, ImageFilter

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


def cover(img, w, h):
    """Scale and centre-crop img to exactly w x h."""
    k = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * k), round(img.height * k)), Image.LANCZOS)
    x, y = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))


def inpaint(pipe, img, regions, neg, embs, refs=None):
    """Repaint each region (box + prompt, optionally a face reference) on an upscaled
    crop around it, then blend it back. refs: reference faces when the IP-Adapter is loaded."""
    inp = StableDiffusionXLInpaintPipeline(**pipe.components)
    inp.set_progress_bar_config(disable=True)
    for r in regions:
        boxes = r["box"] if isinstance(r["box"][0], (list, tuple)) else [r["box"]]   # one rect or a union of rects
        kw = {}
        if refs:
            # while the adapter is loaded every call needs an image; scale 0 switches it off
            inp.set_ip_adapter_scale(r.get("ip", 0.6) if r.get("ref") else 0.0)
            kw["ip_adapter_image"] = refs[r["ref"]] if r.get("ref") else next(iter(refs.values()))
        x0, y0 = min(b[0] for b in boxes), min(b[1] for b in boxes)
        x1, y1 = max(b[2] for b in boxes), max(b[3] for b in boxes)
        m = 96
        X0, Y0 = max(0, x0 - m), max(0, y0 - m)
        X1, Y1 = min(img.width, x1 + m), min(img.height, y1 + m)
        crop = img.crop((X0, Y0, X1, Y1))
        k = max(1.0, 832 / max(crop.size))
        w8, h8 = int(crop.width * k) // 8 * 8, int(crop.height * k) // 8 * 8
        big = crop.resize((w8, h8), Image.LANCZOS)
        mask = Image.new("L", (w8, h8), 0)
        sx, sy = w8 / crop.width, h8 / crop.height
        for b in boxes:
            ImageDraw.Draw(mask).rounded_rectangle(((b[0] - X0) * sx, (b[1] - Y0) * sy, (b[2] - X0) * sx, (b[3] - Y0) * sy),
                                                   radius=int(28 * sx), fill=255)
        emb = embs[(r["prompt"], neg)]
        t = time.time()
        with torch.inference_mode():
            out = inp(image=big, mask_image=mask, width=w8, height=h8, strength=r.get("strength", 0.9),
                      num_inference_steps=8, guidance_scale=CFG, generator=torch.Generator().manual_seed(r.get("seed", 1)),
                      **emb, **kw).images[0]
        soft = mask.filter(ImageFilter.GaussianBlur(10 * sx)).resize(crop.size, Image.LANCZOS)
        img.paste(Image.composite(out.resize(crop.size, Image.LANCZOS), crop, soft), (X0, Y0))
        print(f"   inpaint {r['box']} {time.time() - t:5.1f}s", flush=True)
    return img


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
    def need_ip(s):
        return bool(s.get("ref")) or any(r.get("ref") for r in s.get("inpaint", []))

    todo.sort(key=need_ip)   # load the IP-Adapter once, after the references exist
    if not todo:
        print("nothing to do")
        return
    t = time.time()
    pipe = StableDiffusionXLPipeline.from_pretrained(MODEL, torch_dtype=torch.bfloat16, variant="fp16", use_safetensors=True)
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config, algorithm_type="sde-dpmsolver++",
                                                             use_karras_sigmas=True)
    pipe.set_progress_bar_config(disable=True)
    print(f"loaded in {time.time() - t:.0f}s", flush=True)

    # Encode every prompt now, then drop the text encoders (1.6 GB): with the
    # IP-Adapter loaded the process otherwise sits near the machine's memory limit.
    def negative(s):
        return s["negative"].replace("open mouth, teeth, frown lines, ", "") if s["id"].startswith("expr_") else s["negative"]

    embs = {}
    for s in todo:
        for p in [s["prompt"]] + [r["prompt"] for r in s.get("inpaint", [])]:
            embs[(p, negative(s))] = encode_long(pipe, p, negative(s))
    pipe.register_modules(text_encoder=None, text_encoder_2=None)
    gc.collect()
    ctypes.CDLL("libc.so.6").malloc_trim(0)
    fa = None
    i2i = None
    ip_loaded = False
    refs = {}
    for s in todo:
        kw = {}
        if need_ip(s):
            if not ip_loaded:
                pipe.load_ip_adapter(IPA, subfolder="sdxl_models", weight_name="ip-adapter-plus-face_sdxl_vit-h.safetensors",
                                     image_encoder_folder="models/image_encoder", torch_dtype=torch.bfloat16)
                ip_loaded = True
            for ref in {s.get("ref")} | {r.get("ref") for r in s.get("inpaint", [])}:
                if ref and ref not in refs:
                    fa = fa or face_detector()
                    refs[ref] = face_crop(fa, out / f"{ref}.png")
                    refs[ref].save(out / f"{ref}_face.png")
            pipe.set_ip_adapter_scale(s.get("ip", 0.6) if s.get("ref") else 0.0)
            kw["ip_adapter_image"] = refs[s["ref"]] if s.get("ref") else next(iter(refs.values()))
        elif ip_loaded:
            pipe.unload_ip_adapter()
            ip_loaded = False
        tf = os.environ.get("THREADS_FILE")
        if tf and os.path.exists(tf):
            torch.set_num_threads(int(open(tf).read().strip()))   # adjustable while running
        neg = negative(s)
        t = time.time()
        g = torch.Generator().manual_seed(s["seed"])
        base_path = out / f"{s['id']}_base.png"
        if s.get("inpaint") and base_path.exists():
            img = inpaint(pipe, Image.open(base_path).convert("RGB"), s["inpaint"], neg, embs, refs if ip_loaded else None)
            img.save(out / f"{s['id']}.png")
            print(f"{s['id']:20s} {time.time() - t:6.1f}s (inpainted)", flush=True)
            continue
        with torch.inference_mode():
            emb = embs[(s["prompt"], neg)]
            if s.get("init"):
                i2i = i2i or StableDiffusionXLImg2ImgPipeline(**pipe.components)
                i2i.set_progress_bar_config(disable=True)
                init = cover(Image.open(s["init"]).convert("RGB"), s["w"], s["h"])
                img = i2i(image=init, strength=s.get("strength", 0.75), num_inference_steps=8, guidance_scale=CFG,
                          generator=g, **emb, **kw).images[0]
            else:
                img = pipe(width=s["w"], height=s["h"], num_inference_steps=STEPS, guidance_scale=CFG, generator=g,
                           **emb, **kw).images[0]
        if s.get("inpaint"):
            img.save(base_path)
            img = inpaint(pipe, img, s["inpaint"], neg, embs, refs if ip_loaded else None)
        img.save(out / f"{s['id']}.png")
        print(f"{s['id']:20s} {time.time() - t:6.1f}s", flush=True)


if __name__ == "__main__":
    main()
