# Fix 13: rai-toolkit: malformed JSON dataset errors do not name the file

Status: UNSENT and UNTESTED. Free to take.

- Project: wandb/rai-toolkit
- Bug report title: fix(datasets): include source paths in JSON syntax errors
- Bug report: number 131 ([open the bug report](https://github.com/wandb/rai-toolkit/issues/131))
- Project license: Apache-2.0
- Language: Python
- Test included: yes
- Patch file: [fixes/13-rai-toolkit-131.patch](fixes/13-rai-toolkit-131.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/13-rai-toolkit-131.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-13-rai-toolkit-131.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-13-rai-toolkit-131.html

## The bug

DatasetLoader.from_file() names the source file when a JSON dataset has the wrong shape. For malformed JSON the loader lets a bare JSONDecodeError through such as "Expecting ',' delimiter: line 3 column 3 (char 26)" with no file name. Failures are hard to trace when several datasets are loaded.

## The fix

DatasetLoader._load_json in rai_toolkit/evaluation/datasets.py now catches json.JSONDecodeError and raises ValueError with the path and the one-based line and column and the parser's short reason. The original error is kept as the cause. No dataset content appears in the message. New tests cover a direct array and a data wrapper and an empty file and two kinds of truncated JSON. The chatbot checked the expected line and column numbers with a separate script.

## Files changed

- rai_toolkit/evaluation/datasets.py
- tests/test_dataset_loader_json.py

## How to use the fix

1. Get a copy of the project wandb/rai-toolkit.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 13-rai-toolkit-131.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 131.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-09 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-09 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report asks contributors to check linked pull requests first. The chatbot could not see linked pull requests.

## Search words

rai-toolkit DatasetLoader from_file JSONDecodeError Expecting delimiter missing filename path line column invalid JSON

## The full patch

`````diff
diff --git a/rai_toolkit/evaluation/datasets.py b/rai_toolkit/evaluation/datasets.py
index 7c0210f..e56b8df 100644
--- a/rai_toolkit/evaluation/datasets.py
+++ b/rai_toolkit/evaluation/datasets.py
@@ -46,6 +46,9 @@ class DatasetLoader:
         JSON files accept an array of objects or an object with a ``data``
         array. Invalid dataset shapes raise ``ValueError`` with the filename;
         invalid rows also include their one-based array position, not a line number.
+        Malformed JSON raises ``ValueError`` with the filename, the one-based
+        physical line and column of the syntax error and the parser's reason; the
+        original ``json.JSONDecodeError`` is kept as the cause.
 
         Args:
             path: Path to CSV, JSON, or JSONL file.
@@ -96,7 +99,12 @@ class DatasetLoader:
     @staticmethod
     def _load_json(path: Path) -> list[dict[str, Any]]:
         with open(path, encoding="utf-8") as f:
-            data = json.load(f)
+            try:
+                data = json.load(f)
+            except json.JSONDecodeError as exc:
+                raise ValueError(
+                    f"{path}: line {exc.lineno}, column {exc.colno}: invalid JSON: {exc.msg}"
+                ) from exc
         if isinstance(data, dict):
             data = data.get("data")
         if not isinstance(data, list):
diff --git a/tests/test_dataset_loader_json.py b/tests/test_dataset_loader_json.py
index 95dbe83..90cd94f 100644
--- a/tests/test_dataset_loader_json.py
+++ b/tests/test_dataset_loader_json.py
@@ -117,3 +117,52 @@ def test_json_empty_arrays_return_empty_list(tmp_path, data):
     path.write_text(json.dumps(data), encoding="utf-8")
 
     assert DatasetLoader.from_file(path) == []
+
+
+@pytest.mark.parametrize(
+    ("text", "line", "column", "reason"),
+    [
+        # Direct array: a missing comma after earlier valid content.
+        ('[\n  {"prompt": "first"}\n  {"prompt": "second"}\n]\n', 3, 3, "Expecting ',' delimiter"),
+        # ``data`` wrapper: the same mistake one level down.
+        (
+            '{\n  "data": [\n    {"prompt": "first"}\n    {"prompt": "second"}\n  ]\n}\n',
+            4,
+            5,
+            "Expecting ',' delimiter",
+        ),
+        # Empty file.
+        ("", 1, 1, "Expecting value"),
+        # Truncated JSON: the array is never closed.
+        ('[\n  {"prompt": "private-dataset-content"},\n', 3, 1, "Expecting value"),
+        # Truncated JSON: a string is never closed.
+        ('[\n  {"prompt": "private-dataset-content', 2, 14, "Unterminated string starting at"),
+    ],
+    ids=["array", "data-wrapper", "empty-file", "truncated-array", "truncated-string"],
+)
+def test_json_syntax_errors_report_path_line_and_column(tmp_path, text, line, column, reason):
+    path = tmp_path / "rows.json"
+    path.write_text(text, encoding="utf-8")
+
+    with pytest.raises(ValueError) as exc_info:
+        DatasetLoader.from_file(path)
+
+    message = str(exc_info.value)
+    assert message.startswith(f"{path}: line {line}, column {column}: invalid JSON: ")
+    assert reason in message
+    assert "row " not in message
+    assert "private-dataset-content" not in message
+
+    cause = exc_info.value.__cause__
+    assert isinstance(cause, json.JSONDecodeError)
+    assert (cause.lineno, cause.colno) == (line, column)
+
+
+def test_json_syntax_error_is_not_a_bare_decode_error(tmp_path):
+    path = tmp_path / "rows.json"
+    path.write_text("[", encoding="utf-8")
+
+    with pytest.raises(ValueError) as exc_info:
+        DatasetLoader.from_file(path)
+
+    assert not isinstance(exc_info.value, json.JSONDecodeError)
`````

[Back to the shelf](README.md)
