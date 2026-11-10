# Fix 142: security-checker: six small spots the lint tool flags can be written more simply

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: refactor: 細かな書き換えの指摘を解消する (FURB188・FURB192・PERF401・PLC0207・RET501)
- Bug report: number 690 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/690))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/142-security-checker-690.patch](fixes/142-security-checker-690.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/142-security-checker-690.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-142-security-checker-690.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-142-security-checker-690.html

## The bug

The lint rules FURB188 and FURB192 and PERF401 and PLC0207 and RET501 report small spots: a suffix and a prefix cut by hand and sorted(...)[0] where min works and an append loop where a comprehension works and a split that splits more often than needed and an explicit return None.

## The fix

Six one-spot rewrites with no change in behaviour: removesuffix in anthropic_messages.py and removeprefix in scanners/base.py and min in osv.py and a generator expression in context/builder.py and split with maxsplit=1 in consensus.py and the bare return None removed in process/runner.py.

## Files changed

- src/security_checker/aggregate/consensus.py
- src/security_checker/context/builder.py
- src/security_checker/providers/http/dialects/anthropic_messages.py
- src/security_checker/providers/process/runner.py
- src/security_checker/scanners/base.py
- src/security_checker/scanners/osv.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 142-security-checker-690.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 690.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report also names scanners/unimplemented.py line 53. That file no longer exists in the newest code so the patch leaves that spot out. Nobody ran the lint tool or the project's tests. Fix 148 on this shelf adds a test for the function changed in scanners/base.py and both patches apply together.

## Search words

security-checker ruff FURB188 FURB192 PERF401 PLC0207 RET501 removesuffix removeprefix min maxsplit return None

## The full patch

`````diff
diff --git a/src/security_checker/aggregate/consensus.py b/src/security_checker/aggregate/consensus.py
index eb5bd04..b3f06a7 100644
--- a/src/security_checker/aggregate/consensus.py
+++ b/src/security_checker/aggregate/consensus.py
@@ -277,7 +277,7 @@ def _headline(verdict: ReviewVerdict, limit: int = SUMMARY_LIMIT) -> str:
 
 def _first_sentence(text: str, limit: int) -> str:
     """先頭の 1 文を返す. 収まらなければ文・節の区切りまで戻して詰める."""
-    line = " ".join(text.split("\n")[0].split()).strip()
+    line = " ".join(text.split("\n", maxsplit=1)[0].split()).strip()
     if len(line) <= limit:
         return line
     window = line[:limit]
diff --git a/src/security_checker/context/builder.py b/src/security_checker/context/builder.py
index 5fa69f4..4456afc 100644
--- a/src/security_checker/context/builder.py
+++ b/src/security_checker/context/builder.py
@@ -178,10 +178,7 @@ def _mask_long_tokens_on_line(text: str, candidate: Candidate) -> str:
     """
     if candidate.location is None:
         return text
-    masked_lines: list[str] = []
-    for line in text.splitlines():
-        masked_lines.append(_mask_quoted(line))
-    return "\n".join(masked_lines)
+    return "\n".join(_mask_quoted(line) for line in text.splitlines())
 
 
 def _mask_detected_lines(text: str, first_line: int, candidate: Candidate) -> str:
diff --git a/src/security_checker/providers/http/dialects/anthropic_messages.py b/src/security_checker/providers/http/dialects/anthropic_messages.py
index 62bcf33..272d7b8 100644
--- a/src/security_checker/providers/http/dialects/anthropic_messages.py
+++ b/src/security_checker/providers/http/dialects/anthropic_messages.py
@@ -44,8 +44,7 @@ class AnthropicMessagesDialect:
         # base_url に /v1 を含めて書く人と含めない人の両方がいる。
         # どちらでも同じ URL になるよう正規化する (二重の /v1 を作らない)。
         trimmed = base_url.rstrip("/")
-        if trimmed.endswith("/v1"):
-            trimmed = trimmed[: -len("/v1")]
+        trimmed = trimmed.removesuffix("/v1")
         return f"{trimmed}/v1/messages"
 
     def headers(self, api_key: str | None) -> dict[str, str]:
diff --git a/src/security_checker/providers/process/runner.py b/src/security_checker/providers/process/runner.py
index 49e2670..ff3c89c 100644
--- a/src/security_checker/providers/process/runner.py
+++ b/src/security_checker/providers/process/runner.py
@@ -120,7 +120,6 @@ class ProcessProvider:
 
     async def aclose(self) -> None:
         """プロセスは 1 回ごとに完結するため、保持する資源はない."""
-        return None
 
     # --- 内部 -------------------------------------------------------------
 
diff --git a/src/security_checker/scanners/base.py b/src/security_checker/scanners/base.py
index bb8f154..b640e3e 100644
--- a/src/security_checker/scanners/base.py
+++ b/src/security_checker/scanners/base.py
@@ -262,9 +262,7 @@ def relative_path(raw_path: str, root: Path) -> str:
             cleaned = candidate.resolve().relative_to(root.resolve()).as_posix()
         except ValueError:
             cleaned = candidate.name
-    if cleaned.startswith("./"):
-        cleaned = cleaned[2:]
-    return cleaned
+    return cleaned.removeprefix("./")
 
 
 def as_dict(value: Any) -> dict[str, Any]:
diff --git a/src/security_checker/scanners/osv.py b/src/security_checker/scanners/osv.py
index e1f2901..1e54742 100644
--- a/src/security_checker/scanners/osv.py
+++ b/src/security_checker/scanners/osv.py
@@ -132,7 +132,7 @@ def parse_osv(
                     continue
                 vulns = [vulns_by_id[i] for i in group_ids if i in vulns_by_id]
                 aliases = [a for a in as_dict(group).get("aliases") or [] if isinstance(a, str)]
-                primary = sorted(group_ids)[0]
+                primary = min(group_ids)
                 summary = next(
                     (str(v["summary"]) for v in vulns if isinstance(v.get("summary"), str)), ""
                 )
`````

[Back to the shelf](README.md)
