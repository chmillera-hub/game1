# Fix 197: security-checker: twelve modules each lack one docstring

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: docs: docstring が 1 つだけ欠けているモジュールをまとめて埋める
- Bug report: number 432 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/432))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/197-security-checker-432.patch](fixes/197-security-checker-432.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/197-security-checker-432.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-197-security-checker-432.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-197-security-checker-432.html

## The bug

The lint rule D1 reports one public name without a docstring in each of twelve modules: discover_plugin_aggregators and available_presets and outcomes_by_case and overlaps and total_tokens and write_baseline and failed and rank_for and SuppressionRules and matches and write_markdown and one __init__.

## The fix

Each of the twelve items gets a one-line Japanese docstring that says what the item does.

## Files changed

- src/security_checker/aggregate/registry.py
- src/security_checker/config/loader.py
- src/security_checker/eval/runner.py
- src/security_checker/github/pr.py
- src/security_checker/models/verdict.py
- src/security_checker/policy/baseline.py
- src/security_checker/policy/engine.py
- src/security_checker/policy/score.py
- src/security_checker/policy/suppress.py
- src/security_checker/providers/presets/loader.py
- src/security_checker/report/markdown.py
- src/security_checker/review/structured.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 197-security-checker-432.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 432.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Fix 179 on this shelf changes the lines right below one of the docstrings (rank_for in policy/score.py) so patches 179 and 197 do not apply together: apply one and add the other change by hand. Docstrings only with no change in behaviour. The chatbot wrote the Japanese text and a native reader should check the wording. Nobody ran the lint tool.

## Search words

security-checker docstring D1 ruff twelve modules rank_for write_baseline SuppressionRules matches write_markdown total_tokens

## The full patch

`````diff
diff --git a/src/security_checker/aggregate/registry.py b/src/security_checker/aggregate/registry.py
index f3e2c72..76a9242 100644
--- a/src/security_checker/aggregate/registry.py
+++ b/src/security_checker/aggregate/registry.py
@@ -21,6 +21,7 @@ BUILTIN_AGGREGATORS: dict[str, Callable[..., Aggregator]] = {
 
 
 def discover_plugin_aggregators() -> tuple[dict[str, Callable[..., Aggregator]], list[str]]:
+    """entry point から Aggregator のプラグインを集める. 読み込めないものは警告にして続ける."""
     found: dict[str, Callable[..., Aggregator]] = {}
     warnings: list[str] = []
     for entry in entry_points(group=ENTRY_POINT_GROUP):
diff --git a/src/security_checker/config/loader.py b/src/security_checker/config/loader.py
index d1fecb5..72cc084 100644
--- a/src/security_checker/config/loader.py
+++ b/src/security_checker/config/loader.py
@@ -75,6 +75,7 @@ def find_local_config_file(root: Path) -> Path | None:
 
 
 def available_presets() -> list[str]:
+    """同梱している設定プリセットの名前 (拡張子なし) を名前順に返す."""
     return sorted(path.stem for path in PRESET_DIR.glob("*.yml"))
 
 
diff --git a/src/security_checker/eval/runner.py b/src/security_checker/eval/runner.py
index bd36a9c..fd51a10 100644
--- a/src/security_checker/eval/runner.py
+++ b/src/security_checker/eval/runner.py
@@ -233,4 +233,5 @@ def _usd(metrics: Metrics) -> str:
 
 
 def outcomes_by_case(outcomes: Sequence[CaseOutcome]) -> dict[str, CaseOutcome]:
+    """ケース ID から結果を引けるようにする."""
     return {outcome.case_id: outcome for outcome in outcomes}
diff --git a/src/security_checker/github/pr.py b/src/security_checker/github/pr.py
index d412df7..d0ce320 100644
--- a/src/security_checker/github/pr.py
+++ b/src/security_checker/github/pr.py
@@ -41,6 +41,7 @@ class DiffScope:
     changed_files: frozenset[str] = frozenset()
 
     def overlaps(self, path: str, start: int, end: int) -> bool:
+        """`path` の `start`〜`end` 行 (両端を含む) が、追加・変更された行と 1 行でも重なるか."""
         return any(lo <= end and start <= hi for lo, hi in self.added.get(path, ()))
 
     def is_commentable(self, path: str, line: int) -> bool:
diff --git a/src/security_checker/models/verdict.py b/src/security_checker/models/verdict.py
index 33b7c9b..5ae2c97 100644
--- a/src/security_checker/models/verdict.py
+++ b/src/security_checker/models/verdict.py
@@ -44,6 +44,7 @@ class Usage(BaseModel):
 
     @property
     def total_tokens(self) -> int:
+        """入力と出力のトークン数の合計."""
         return self.input_tokens + self.output_tokens
 
     def merge(self, other: Usage) -> Usage:
diff --git a/src/security_checker/policy/baseline.py b/src/security_checker/policy/baseline.py
index 4680006..0b0ebc0 100644
--- a/src/security_checker/policy/baseline.py
+++ b/src/security_checker/policy/baseline.py
@@ -130,6 +130,7 @@ def _existing_salt(path: Path) -> str | None:
 
 
 def write_baseline(path: Path, candidates: list[Candidate], *, tool_version: str) -> Path:
+    """候補を baseline として `path` に書く. 既存のファイルがあれば、その salt を引き継ぐ."""
     path.parent.mkdir(parents=True, exist_ok=True)
     payload = render_baseline(candidates, tool_version=tool_version, salt=_existing_salt(path))
     path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
diff --git a/src/security_checker/policy/engine.py b/src/security_checker/policy/engine.py
index 50f0e06..23e10b4 100644
--- a/src/security_checker/policy/engine.py
+++ b/src/security_checker/policy/engine.py
@@ -23,6 +23,7 @@ class PolicyDecision:
 
     @property
     def failed(self) -> bool:
+        """終了コードが OK でなければ True."""
         return self.exit_code is not ExitCode.OK
 
 
diff --git a/src/security_checker/policy/score.py b/src/security_checker/policy/score.py
index 95ea466..5828a9c 100644
--- a/src/security_checker/policy/score.py
+++ b/src/security_checker/policy/score.py
@@ -28,6 +28,7 @@ CATEGORY_CAP = 40
 
 
 def rank_for(value: int) -> Literal["A", "B", "C", "D"]:
+    """点数 (0〜100) をランクにする. 90 以上が A、70 以上が B、50 以上が C、それ未満が D."""
     if value >= 90:
         return "A"
     if value >= 70:
diff --git a/src/security_checker/policy/suppress.py b/src/security_checker/policy/suppress.py
index a4c7f6c..8ae928d 100644
--- a/src/security_checker/policy/suppress.py
+++ b/src/security_checker/policy/suppress.py
@@ -23,6 +23,7 @@ from security_checker.policy.ignore import AnnotationReader, IgnoreFile, load_ig
 
 @dataclass
 class SuppressionRules:
+    """抑制の規則をまとめたもの. baseline・ignore ファイル・コード内注釈と、読み込み時の警告."""
     baseline: Baseline = field(default_factory=Baseline)
     ignore: IgnoreFile | None = None
     annotations: AnnotationReader | None = None
diff --git a/src/security_checker/providers/presets/loader.py b/src/security_checker/providers/presets/loader.py
index cba8989..da5bfe2 100644
--- a/src/security_checker/providers/presets/loader.py
+++ b/src/security_checker/providers/presets/loader.py
@@ -38,6 +38,7 @@ class PresetMatch(BaseModel):
     model: str | None = None  # 正規表現
 
     def matches(self, base_url: str, model: str) -> bool:
+        """`base_url` のホストと `model` が条件に合うか. 条件が 1 つも無ければ常に False."""
         if self.host is not None:
             host = urlparse(base_url).hostname or ""
             if host != self.host:
diff --git a/src/security_checker/report/markdown.py b/src/security_checker/report/markdown.py
index d78c871..4d4d66c 100644
--- a/src/security_checker/report/markdown.py
+++ b/src/security_checker/report/markdown.py
@@ -70,6 +70,7 @@ def render_markdown(report: Report, decision: PolicyDecision) -> str:
 
 
 def write_markdown(report: Report, decision: PolicyDecision, output_dir: Path) -> Path:
+    """`output_dir` に report.md を書き、そのパスを返す. ディレクトリが無ければ作る."""
     output_dir.mkdir(parents=True, exist_ok=True)
     path = output_dir / "report.md"
     path.write_text(render_markdown(report, decision), encoding="utf-8")
diff --git a/src/security_checker/review/structured.py b/src/security_checker/review/structured.py
index eb316a0..29da569 100644
--- a/src/security_checker/review/structured.py
+++ b/src/security_checker/review/structured.py
@@ -126,6 +126,7 @@ class SchemaViolationError(Exception):
     """検証に失敗した. message は修復プロンプトにそのまま載せる."""
 
     def __init__(self, message: str, *, raw_text: str) -> None:
+        """`raw_text` は検証に失敗した応答の原文. 修復の再送とトレースに使う."""
         super().__init__(message)
         self.raw_text = raw_text
`````

[Back to the shelf](README.md)
