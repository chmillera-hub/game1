# Fix 22: microscopy-active-learning: pretrain trains zero steps when the dataset is smaller than the batch size

Status: UNSENT and UNTESTED. Free to take.

- Project: iamvisheshsrivastava/microscopy-active-learning
- Bug report title: pretrain() silently trains zero steps when the dataset is smaller than the batch size
- Bug report: number 21 ([open the bug report](https://github.com/iamvisheshsrivastava/microscopy-active-learning/issues/21))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/22-microscopy-al-21.patch](fixes/22-microscopy-al-21.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/22-microscopy-al-21.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-22-microscopy-al-21.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-22-microscopy-al-21.html

## The bug

pretrain and pretrain_crossmodal only run full batches. With fewer images than the batch size the loop body never runs. No optimisation step happens and the function returns a loss history of 0.0 with no error.

## The fix

A new helper effective_batch in src/maldl/training/contrastive.py clamps the batch size to the dataset size with a warning and raises ValueError for fewer than 2 samples. Both training functions use the helper. New tests check that the encoder weights change and that the loss is above zero and that one sample is refused. The chatbot checked the batch arithmetic with a separate script.

## Files changed

- src/maldl/training/contrastive.py
- src/maldl/training/crossmodal.py
- tests/test_core.py

## How to use the fix

1. Get a copy of the project iamvisheshsrivastava/microscopy-active-learning.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 22-microscopy-al-21.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 21.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-09 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-09 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report allowed either clamping with a warning or raising an error. The patch clamps. A batch size below 2 now raises an error too.

## Search words

microscopy-active-learning maldl pretrain pretrain_crossmodal batch larger than dataset zero steps loss 0.0 contrastive NT-Xent

## The full patch

`````diff
diff --git a/src/maldl/training/contrastive.py b/src/maldl/training/contrastive.py
index 9fdb914..f666024 100644
--- a/src/maldl/training/contrastive.py
+++ b/src/maldl/training/contrastive.py
@@ -1,4 +1,6 @@
 """SimCLR-style self-supervised training with multi-scale random-resized crops."""
+import warnings
+
 import numpy as np
 import torch
 import torch.nn as nn
@@ -57,12 +59,31 @@ def nt_xent(z1, z2, tau=0.2):
     return F.cross_entropy(sim, tgt)
 
 
+def effective_batch(n, batch, what="pretrain"):
+    """Batch size to train with on a dataset of `n` samples.
+
+    The training loops only run full batches, so a dataset smaller than `batch` used to
+    train zero steps without any error. The batch is clamped to the dataset size (with a
+    warning). A contrastive loss needs at least 2 samples per batch, so fewer is an error.
+    """
+    if n < 2:
+        raise ValueError(f"{what} needs at least 2 samples for a contrastive batch, got {n}")
+    if batch < 2:
+        raise ValueError(f"{what} needs a batch size of at least 2, got {batch}")
+    if batch > n:
+        warnings.warn(f"{what}: batch size {batch} is larger than the dataset ({n} samples); "
+                      f"using batch={n}", stacklevel=3)
+        return n
+    return batch
+
+
 def pretrain(encoder, images, epochs=15, batch=64, lr=2e-3, seed=0, tau=0.2,
              strong=False, device="cpu"):
     """images: (N,C,H,W) numpy. Trains encoder in place; returns loss history."""
     if epochs <= 0:
         encoder.eval()
         return []
+    batch = effective_batch(len(images), batch, "pretrain")
     rng = np.random.default_rng(seed)
     torch.manual_seed(seed)
     x = torch.from_numpy(images)
diff --git a/src/maldl/training/crossmodal.py b/src/maldl/training/crossmodal.py
index 7ad8c49..8dc0cc9 100644
--- a/src/maldl/training/crossmodal.py
+++ b/src/maldl/training/crossmodal.py
@@ -9,7 +9,7 @@ import torch
 import torch.nn as nn
 import torch.nn.functional as F
 
-from .contrastive import intensity_jitter, random_resized_crop
+from .contrastive import effective_batch, intensity_jitter, random_resized_crop
 
 
 def pair_augment(sem, ebsd, rng, out=64, strong=False):
@@ -30,6 +30,7 @@ def pretrain_crossmodal(enc_sem, enc_ebsd, sem, ebsd, epochs=15, batch=64, lr=2e
     if epochs <= 0:
         enc_sem.eval(), enc_ebsd.eval()
         return []
+    batch = effective_batch(len(sem), batch, "pretrain_crossmodal")
     rng = np.random.default_rng(seed)
     torch.manual_seed(seed)
     xs, xe = torch.from_numpy(sem), torch.from_numpy(ebsd)
diff --git a/tests/test_core.py b/tests/test_core.py
index 816082a..754aac7 100644
--- a/tests/test_core.py
+++ b/tests/test_core.py
@@ -286,3 +286,32 @@ def test_crossmodal_learns_alignment():
     ts, te, ty, _ = make_paired_dataset(200, seed=2, size=32)
     m = retrieval_class_match(embed_projected(es, ts), embed_projected(ee, te), ty)
     assert m > 0.32  # chance is 0.25 (sd ~0.03 at n=200); seen 0.37-0.45 across platforms
+
+
+def test_pretrain_clamps_a_batch_larger_than_the_dataset():
+    # len(images) < batch used to train zero steps and return a fake loss of 0.0
+    x, _ = make_dataset(8, 0, size=32)
+    enc = Encoder()
+    before = [p.detach().clone() for p in enc.parameters()]
+    with pytest.warns(UserWarning, match="using batch=8"):
+        hist = pretrain(enc, x, epochs=1, batch=64)
+    assert len(hist) == 1 and hist[0] > 0.0
+    assert any(not torch.equal(a, b) for a, b in zip(before, enc.parameters()))
+
+
+def test_pretrain_crossmodal_clamps_a_batch_larger_than_the_dataset():
+    sem, ebsd, _, _ = make_paired_dataset(8, 0, size=32)
+    enc_sem, enc_ebsd = Encoder(in_ch=sem.shape[1]), Encoder(in_ch=ebsd.shape[1])
+    with pytest.warns(UserWarning, match="using batch=8"):
+        hist = pretrain_crossmodal(enc_sem, enc_ebsd, sem, ebsd, epochs=1, batch=64)
+    assert len(hist) == 1 and hist[0] > 0.0
+
+
+def test_pretrain_refuses_fewer_than_two_samples():
+    x, _ = make_dataset(8, 0, size=32)
+    with pytest.raises(ValueError, match="at least 2 samples"):
+        pretrain(Encoder(), x[:1], epochs=1, batch=64)
+    sem, ebsd, _, _ = make_paired_dataset(8, 0, size=32)
+    with pytest.raises(ValueError, match="at least 2 samples"):
+        pretrain_crossmodal(Encoder(in_ch=sem.shape[1]), Encoder(in_ch=ebsd.shape[1]),
+                            sem[:1], ebsd[:1], epochs=1, batch=64)
`````

[Back to the shelf](README.md)
