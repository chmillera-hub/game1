# Fix 24: openmed: drift report compares score histograms that use different bin counts

Status: UNSENT and UNTESTED. Free to take.

- Project: maziyarpanahi/openmed
- Bug report title: Reject drift windows whose score histograms use a different bin count
- Bug report: number 4546 ([open the bug report](https://github.com/maziyarpanahi/openmed/issues/4546))
- Project license: Apache-2.0
- Language: Python
- Test included: yes
- Patch file: [fixes/24-openmed-4546.patch](fixes/24-openmed-4546.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/24-openmed-4546.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-24-openmed-4546.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-24-openmed-4546.html

## The bug

compute_drift_report accepts a reference window with a 10-bin score histogram and an observation window with a 20-bin score histogram. Buckets are named by index so the two windows are compared bucket by bucket as if the buckets meant the same thing. The report then shows drift that is only a change of binning or hides real drift.

## The fix

compute_drift_report in openmed/eval/drift_monitor.py now raises DriftInputError when the two score histograms differ in length. The message names both lengths and contains no bucket values. The all-zero default histogram follows the same rule. New tests cover matching and mismatched and default histograms. A changelog line is included.

## Files changed

- CHANGELOG.md
- openmed/eval/drift_monitor.py
- tests/unit/eval/test_drift_monitor.py

## How to use the fix

1. Get a copy of the project maziyarpanahi/openmed.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 24-openmed-4546.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 4546.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 9 November 2026 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 9 November 2026 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.

## Search words

openmed drift_monitor compute_drift_report score_histogram bin count mismatch DriftInputError PSI 10 bins 20 bins

## The full patch

`````diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index b89a831..673e262 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -9,6 +9,9 @@ and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0
 
 ### Fixed
 
+- `compute_drift_report` raises `DriftInputError` when the reference and
+  observation score histograms have different bin counts, naming both lengths,
+  instead of comparing differently binned windows bucket by bucket (#4546).
 - Reject missing, repeated, or unsupported content types on the local privacy
   proxy's chat routes before reading the request body (#5185).
 
diff --git a/openmed/eval/drift_monitor.py b/openmed/eval/drift_monitor.py
index 4125996..1109917 100644
--- a/openmed/eval/drift_monitor.py
+++ b/openmed/eval/drift_monitor.py
@@ -477,6 +477,18 @@ def compute_drift_report(
         reference_window = _as_window(reference)
         observation_window = _as_window(observation)
 
+        # Score buckets are named by index, so two windows binned differently
+        # would be compared bucket-for-bucket as if they meant the same thing:
+        # PSI would then report a binning change as drift, or hide real drift.
+        reference_bins = len(reference_window.score_histogram)
+        observation_bins = len(observation_window.score_histogram)
+        if reference_bins != observation_bins:
+            raise DriftInputError(
+                "score_histogram bin counts differ: the reference window has "
+                f"{reference_bins} bins and the observation window has "
+                f"{observation_bins} bins"
+            )
+
         families = tuple(
             _family_divergence(
                 family,
diff --git a/tests/unit/eval/test_drift_monitor.py b/tests/unit/eval/test_drift_monitor.py
index beab804..78571a5 100644
--- a/tests/unit/eval/test_drift_monitor.py
+++ b/tests/unit/eval/test_drift_monitor.py
@@ -24,6 +24,7 @@ from openmed.eval.drift_monitor import (
     VERDICT_DRIFT,
     VERDICT_STABLE,
     DriftAggregateWindow,
+    DriftInputError,
     DriftPrivacyError,
     assert_no_raw_text,
     build_drift_window,
@@ -268,3 +269,63 @@ def test_computation_opens_no_socket(monkeypatch):
     )
     assert report.drift_detected
     assert attempts == []
+
+
+
+def _window_with_scores(window_id: str, scores: list[int] | None) -> dict:
+    payload = _baseline_window(window_id).to_dict()
+    if scores is None:
+        payload.pop("score_histogram")  # falls back to the all-zero default histogram
+    else:
+        payload["score_histogram"] = scores
+    return payload
+
+
+_TEN_BINS = list(_BASE_SCORES)
+_TWENTY_BINS = [value for value in _BASE_SCORES for _ in range(2)]
+
+
+def test_matching_score_bin_counts_behave_as_before():
+    twenty = list(_TWENTY_BINS)
+    report = compute_drift_report(
+        _window_with_scores("reference", twenty),
+        _window_with_scores("observation", twenty),
+    )
+    assert report.verdict == VERDICT_STABLE
+
+
+@pytest.mark.parametrize(
+    ("reference_scores", "observation_scores", "reference_bins", "observation_bins"),
+    [
+        (_TEN_BINS, _TWENTY_BINS, 10, 20),
+        (_TWENTY_BINS, _TEN_BINS, 20, 10),
+        # The all-zero default histogram has DEFAULT_SCORE_BINS (10) bins and
+        # follows the same rule.
+        (None, _TWENTY_BINS, 10, 20),
+        (_TWENTY_BINS, None, 20, 10),
+    ],
+    ids=["10-vs-20", "20-vs-10", "default-vs-20", "20-vs-default"],
+)
+def test_mismatched_score_bin_counts_are_rejected(
+    reference_scores, observation_scores, reference_bins, observation_bins
+):
+    with pytest.raises(DriftInputError) as exc_info:
+        compute_drift_report(
+            _window_with_scores("reference", reference_scores),
+            _window_with_scores("observation", observation_scores),
+        )
+
+    message = str(exc_info.value)
+    assert f"{reference_bins} bins" in message
+    assert f"{observation_bins} bins" in message
+    # The message names the two lengths only: no bucket values.
+    for value in _BASE_SCORES:
+        assert str(value) not in message
+
+
+def test_default_score_histograms_on_both_sides_still_compare():
+    report = compute_drift_report(
+        _window_with_scores("reference", None),
+        _window_with_scores("observation", None),
+    )
+    assert report.reference_window_id == "reference"
`````

[Back to the shelf](README.md)
