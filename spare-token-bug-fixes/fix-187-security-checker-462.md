# Fix 187: security-checker: the anonymous reviewer labels repeat from the 27th reviewer on

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: fix(aggregate): Judge に渡す匿名ラベルが 27 人目から重複する
- Bug report: number 462 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/462))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/187-security-checker-462.patch](fixes/187-security-checker-462.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/187-security-checker-462.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-187-security-checker-462.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-187-security-checker-462.html

## The bug

anonymize in src/security_checker/aggregate/judge.py made each label from index modulo 26. With 27 or more reviewers two opinions were both called Reviewer A and the judge could not tell them apart.

## The fix

A new function anonymous_label counts like spreadsheet columns (A to Z and then AA and AB and so on). A new file tests/unit/test_judge_anonymous_labels.py checks nine labels by hand and expects 30 opinions to get 30 different labels.

## Files changed

- src/security_checker/aggregate/judge.py
- tests/unit/test_judge_anonymous_labels.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 187-security-checker-462.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 462.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The chatbot ran a scratch copy of the label function: the nine expected labels match and the first 1000 labels are all different. The chatbot did not run the project's tests.

## Search words

security-checker judge anonymize Reviewer label ascii_uppercase index % 26 duplicate 27 reviewers AA AB

## The full patch

`````diff
diff --git a/src/security_checker/aggregate/judge.py b/src/security_checker/aggregate/judge.py
index c544c9a..5d5baae 100644
--- a/src/security_checker/aggregate/judge.py
+++ b/src/security_checker/aggregate/judge.py
@@ -33,6 +33,16 @@ from security_checker.review.prompts import PeerOpinion
 STRATEGY = "judge"
 
 
+def anonymous_label(index: int) -> str:
+    """0 → A、25 → Z、26 → AA。表計算の列名と同じ数え方で、何人いても重複しない."""
+    letters = ""
+    number = index + 1
+    while number > 0:
+        number, remainder = divmod(number - 1, len(string.ascii_uppercase))
+        letters = string.ascii_uppercase[remainder] + letters
+    return letters
+
+
 def anonymize(candidate_id: str, verdicts: Sequence[ReviewVerdict]) -> list[PeerOpinion]:
     """有効な判定だけを、名前を伏せて並べ替える."""
     valid = [verdict for verdict in verdicts if verdict.status is VerdictStatus.OK]
@@ -40,7 +50,7 @@ def anonymize(candidate_id: str, verdicts: Sequence[ReviewVerdict]) -> list[Peer
     random.Random(candidate_id).shuffle(shuffled)  # noqa: S311 - 暗号用途ではない
     return [
         PeerOpinion(
-            label=f"Reviewer {string.ascii_uppercase[index % 26]}",
+            label=f"Reviewer {anonymous_label(index)}",
             vulnerable=verdict.vulnerable,
             severity=verdict.severity.value,
             confidence=verdict.confidence,
diff --git a/tests/unit/test_judge_anonymous_labels.py b/tests/unit/test_judge_anonymous_labels.py
new file mode 100644
index 0000000..e7b1fea
--- /dev/null
+++ b/tests/unit/test_judge_anonymous_labels.py
@@ -0,0 +1,23 @@
+"""Judge に渡す匿名ラベルが、Reviewer が 27 以上でも重複しないこと."""
+
+from __future__ import annotations
+
+from security_checker.aggregate.judge import anonymize, anonymous_label
+from tests.factories import make_verdict
+
+
+def test_labels_count_like_spreadsheet_columns() -> None:
+    labels = [anonymous_label(index) for index in (0, 1, 25, 26, 27, 51, 52, 701, 702)]
+
+    assert labels == ["A", "B", "Z", "AA", "AB", "AZ", "BA", "ZZ", "AAA"]
+
+
+def test_thirty_opinions_get_unique_labels() -> None:
+    verdicts = [make_verdict(f"r{index}") for index in range(30)]
+
+    labels = [opinion.label for opinion in anonymize("c1", verdicts)]
+
+    assert len(labels) == 30
+    assert len(set(labels)) == 30
+    assert labels[0] == "Reviewer A"
+    assert labels[26] == "Reviewer AA"
`````

[Back to the shelf](README.md)
