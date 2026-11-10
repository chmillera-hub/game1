# Fix 143: security-checker docs: the docs folder has no table of contents

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: docs: docs/ の目次 (docs/README.md) を置く
- Bug report: number 658 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/658))
- Project license: MIT
- Language: Markdown
- Test included: no
- Patch file: [fixes/143-security-checker-658.patch](fixes/143-security-checker-658.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/143-security-checker-658.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-143-security-checker-658.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-143-security-checker-658.html

## The bug

The docs folder holds 13 documents plus an adr folder. The only reading guide was a short list at the end of getting-started.md so a person who opens the docs folder on GitHub sees no table of contents.

## The fix

A new file docs/README.md lists every document under five purposes (try and adopt and configure and extend and understand the design) with a one-line description each. The text is in Japanese like the other docs.

## Files changed

- docs/README.md

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 143-security-checker-658.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 658.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Docs only. The chatbot wrote the Japanese text and a native reader should check the wording. A scratch script confirmed that every .md file in docs is linked and that no link is dead.

## Search words

security-checker docs README.md table of contents index 目次 documents list getting-started

## The full patch

`````diff
diff --git a/docs/README.md b/docs/README.md
new file mode 100644
index 0000000..653eea9
--- /dev/null
+++ b/docs/README.md
@@ -0,0 +1,32 @@
+# ドキュメントの目次
+
+目的別の案内です。初めての方は [getting-started.md](getting-started.md) から読んでください。
+
+## 試す
+
+- [getting-started.md](getting-started.md) — はじめに。手元で 1 回動かすまで
+
+## 導入する
+
+- [github-actions.md](github-actions.md) — GitHub Actions で使う。PR ごとに動かす
+- [adoption.md](adoption.md) — 複数のリポジトリへの導入と、必須チェックにするまで
+
+## 設定する
+
+- [configuration.md](configuration.md) — 設定の全項目
+- [scanners.md](scanners.md) — スキャナ
+- [aggregation.md](aggregation.md) — 集約。複数の Reviewer の判定をどうまとめるか
+- [prompts.md](prompts.md) — プロンプト
+
+## 拡張する
+
+- [providers.md](providers.md) — Reviewer を足す
+- [process-transport.md](process-transport.md) — `process` transport。API キーなしで Reviewer を用意する
+- [evaluation.md](evaluation.md) — 評価 (eval)
+
+## 設計を知る
+
+- [security-model.md](security-model.md) — セキュリティモデル。何が外部に送られるか
+- [DESIGN.md](DESIGN.md) — security-checker v2 の設計書
+- [adr/](adr/README.md) — 設計上の決定の記録 (ADR)
+- [NEXT-STEPS.md](NEXT-STEPS.md) — v2 の残作業と手続き書
`````

[Back to the shelf](README.md)
