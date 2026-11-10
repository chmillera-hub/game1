# Fix 50: sshhh: the generic redaction rule wipes normal output that contains pwd = and a path

Status: UNSENT and UNTESTED. Free to take.

- Project: Hayuuka/sshhh
- Bug report title: [bug] redact 通用规则误伤含 pwd = 的正常输出
- Bug report: number 11 ([open the bug report](https://github.com/Hayuuka/sshhh/issues/11))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/50-sshhh-11.patch](fixes/50-sshhh-11.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/50-sshhh-11.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-50-sshhh-11.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-50-sshhh-11.html

## The bug

The redaction rule treated pwd like password. Normal output such as pwd = /home/deploy or workdir=/app pwd=/app had the path replaced by [REDACTED]. A missing path misleads the AI agent that is debugging the remote machine.

## The fix

scripts/lib/redact.py keeps password and passwd in the first rule and gives pwd its own rule. The pwd rule does not redact a value that looks like a path (a value that starts with / or ~/ or ./ or ../). Any other pwd value is still redacted. A new file tests/test_redact.py covers both examples from the bug report and the password cases. Both README files list the new test file.

## Files changed

- README.en.md
- README.md
- scripts/lib/redact.py
- tests/test_redact.py

## How to use the fix

1. Get a copy of the project Hayuuka/sshhh.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 50-sshhh-11.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 11.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report offers two options: remove pwd from the rule or require a stronger context. The fix takes a third path that the chatbot chose: keep pwd and skip only path-like values. The reason: removing pwd would let a password in a string like Pwd=secret pass through unredacted and reach the AI agent's log. With this fix a pwd password that starts with / or ~/ or ./ still passes through unredacted. A password that the person stored in the vault is still replaced wherever the password appears. The maintainer may prefer the simpler removal.

## Search words

sshhh redact pwd password passwd REDACTED false positive pwd = /home/deploy workdir path 脱敏 误伤

## The full patch

`````diff
diff --git a/README.en.md b/README.en.md
index 7cc0920..05076f1 100644
--- a/README.en.md
+++ b/README.en.md
@@ -358,6 +358,7 @@ py -3.14 -m venv .venv
 .venv/Scripts/python.exe tests/test_flow.py   # main flow and status codes
 .venv/Scripts/python.exe tests/test_lock.py   # cross-process locking
 py -3.14 tests/test_docs.py                   # docs/code consistency
+py -3.14 tests/test_redact.py                 # redaction rules
 ```
 
 The tests spin up a real local SSH server — no mocks, no network needed.
diff --git a/README.md b/README.md
index 4bfd0eb..9e5f757 100644
--- a/README.md
+++ b/README.md
@@ -342,6 +342,7 @@ py -3.14 -m venv .venv
 .venv/Scripts/python.exe tests/test_flow.py   # 主流程与状态码
 .venv/Scripts/python.exe tests/test_lock.py   # 并发锁
 py -3.14 tests/test_docs.py                   # 文档与代码一致性
+py -3.14 tests/test_redact.py                 # 脱敏规则
 ```
 
 测试会起一个本地 SSH 服务端做真实连接，不依赖外网。
diff --git a/scripts/lib/redact.py b/scripts/lib/redact.py
index e69c6e0..d12b894 100644
--- a/scripts/lib/redact.py
+++ b/scripts/lib/redact.py
@@ -8,7 +8,11 @@ from urllib.parse import quote
 PLACEHOLDER = "[REDACTED]"
 
 _GENERIC = [
-    re.compile(r"(?i)((?:password|passwd|pwd)\s*[=:]\s*)(\S+)"),
+    re.compile(r"(?i)((?:password|passwd)\s*[=:]\s*)(\S+)"),
+    # `pwd` 也是「当前目录」：`pwd = /home/deploy`、`workdir=/app pwd=/app` 是正常输出，
+    # 抹掉路径会误导排障。值看起来是路径（/、~/、./、../ 开头）时不脱敏；
+    # 其余情况（如连接串里的 `Pwd=secret`）照旧脱敏。
+    re.compile(r"(?i)(pwd\s*[=:]\s*)(?!~?/|\.{1,2}/)(\S+)"),
     re.compile(r"(?i)(--password[= ])(\S+)"),
 ]
 
diff --git a/tests/test_redact.py b/tests/test_redact.py
new file mode 100644
index 0000000..ede9873
--- /dev/null
+++ b/tests/test_redact.py
@@ -0,0 +1,73 @@
+"""脱敏规则测试：通用规则不能误伤正常输出。
+
+`pwd` 既可能是密码字段，也是「当前目录」。路径信息被抹掉会误导排障，
+所以 `pwd = /home/deploy` 这类输出必须原样保留，真正的密码仍要脱敏。
+
+运行：
+    py -3.14 tests/test_redact.py
+"""
+
+from __future__ import annotations
+
+import sys
+from pathlib import Path
+
+SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
+sys.path.insert(0, str(SCRIPTS))
+
+from lib.redact import PLACEHOLDER, Redactor  # noqa: E402
+
+PASSED = 0
+FAILED = 0
+
+
+def check(name: str, cond: bool, detail: str = "") -> None:
+    global PASSED, FAILED
+    if cond:
+        PASSED += 1
+        print(f"  [ok] {name}")
+    else:
+        FAILED += 1
+        print(f"  [FAIL] {name}" + (f"  -> {detail}" if detail else ""))
+
+
+def main() -> int:
+    r = Redactor()
+
+    print("== pwd 是路径时不脱敏 ==")
+    for line in (
+        "pwd = /var/www",
+        "pwd = /home/deploy",
+        "workdir=/app pwd=/app",
+        "PWD=/root",
+        "pwd: ~/project",
+        "pwd=./build",
+        "pwd=../shared",
+    ):
+        out = r.clean(line)
+        check(f"原样保留：{line}", out == line, out)
+
+    print("\n== 密码仍然脱敏 ==")
+    for line, want in (
+        ("password=abc123", f"password={PLACEHOLDER}"),
+        ("Password: hunter2", f"Password: {PLACEHOLDER}"),
+        ("passwd = s3cret", f"passwd = {PLACEHOLDER}"),
+        ("mysql --password=abc123 -e status", f"mysql --password={PLACEHOLDER} -e status"),
+        ("Uid=app;Pwd=s3cret", f"Uid=app;Pwd={PLACEHOLDER}"),
+        ("pwd=abc123", f"pwd={PLACEHOLDER}"),
+    ):
+        out = r.clean(line)
+        check(f"脱敏：{line}", out == want, out)
+
+    print("\n== 已知密码不受路径豁免影响 ==")
+    known = Redactor(["/Sup3r/Secret"])
+    out = known.clean("pwd=/Sup3r/Secret")
+    check("已登记的密码即使像路径也被替换", "/Sup3r/Secret" not in out, out)
+
+    print("\n" + "=" * 46)
+    print(f"通过 {PASSED} 项，失败 {FAILED} 项")
+    return 0 if FAILED == 0 else 1
+
+
+if __name__ == "__main__":
+    sys.exit(main())
`````

[Back to the shelf](README.md)
