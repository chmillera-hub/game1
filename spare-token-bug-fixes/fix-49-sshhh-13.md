# Fix 49: sshhh docs: the timeout chain says pip 150s is less than the 120s window handoff

Status: UNSENT and UNTESTED. Free to take.

- Project: Hayuuka/sshhh
- Bug report title: [bug] 文档超时链算式写反：pip 150s &lt; 窗口交接 120s 不成立
- Bug report: number 13 ([open the bug report](https://github.com/Hayuuka/sshhh/issues/13))
- Project license: MIT
- Language: Markdown and Python (test)
- Test included: yes
- Patch file: [fixes/49-sshhh-13.patch](fixes/49-sshhh-13.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/49-sshhh-13.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-49-sshhh-13.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-49-sshhh-13.html

## The bug

SKILL.md and references/protocol.md both showed the line pip 150s < window handoff 120s < first call 300s. 150 is not less than 120. The intended meaning is that the worst case (pip 150s plus handoff 120s which is about 270s) stays under the 300s first call timeout.

## The fix

Both files now show the sum form the bug report asks for: pip 150s + window handoff 120s ≈ 270s < first call 300s. tests/test_docs.py gains checks that build the line from the code constants and that the old line is gone from both files.

## Files changed

- SKILL.md
- references/protocol.md
- tests/test_docs.py

## How to use the fix

1. Get a copy of the project Hayuuka/sshhh.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 49-sshhh-13.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 13.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report is written in Chinese and the chatbot read the report in Chinese. The sentence above the line in protocol.md still says that three timeouts grow from the inside out. The chatbot left that sentence alone because the bug report asks only for the line to change. The second suggestion in the bug report (one single source for the key numbers) is not included. Fixes 49 and 50 both belong to sshhh and apply together.

## Search words

sshhh SKILL.md protocol.md timeout chain pip 150s window handoff 120s 300s inequality written backwards 超时链

## The full patch

`````diff
diff --git a/SKILL.md b/SKILL.md
index 5902e8a..7a1467b 100644
--- a/SKILL.md
+++ b/SKILL.md
@@ -105,7 +105,7 @@ python scripts/sshhh.py run prod -- "--sudo some-tool --flag"
 内部超时链是刻意排的，保证你能拿到状态码，而不是被自己的超时打断：
 
 ```
-pip 安装 150s  <  窗口交接 120s  <  建议首次调用 300s
+pip 安装 150s + 窗口交接 120s ≈ 270s  <  建议首次调用 300s
 ```
 
 **窗口是独立进程**：它由系统资源管理器（explorer）拉起，不在本脚本的进程树
diff --git a/references/protocol.md b/references/protocol.md
index 448822e..297c21e 100644
--- a/references/protocol.md
+++ b/references/protocol.md
@@ -130,7 +130,7 @@ Windows 上 `CREATE_BREAKAWAY_FROM_JOB` 在多数作业对象里不起作用。
 三层超时由内向外递增，保证内层总能先超时并返回状态码，外层还来得及处理：
 
 ```
-pip 安装 150s  <  窗口交接 120s  <  建议首次调用 300s
+pip 安装 150s + 窗口交接 120s ≈ 270s  <  建议首次调用 300s
 ```
 
 - agent 的命令超时若 **< 150s**：pip 卡在网络上时 agent 会先被打断，
diff --git a/tests/test_docs.py b/tests/test_docs.py
index 4de8f1c..48e93ab 100644
--- a/tests/test_docs.py
+++ b/tests/test_docs.py
@@ -190,6 +190,16 @@ def main() -> int:
           "python 命令本身不存在" in skill_md)
     check("protocol.md 记录了 pip 超时数值",
           str(runtime.PIP_INSTALL_TIMEOUT) in protocol_md)
+    # 超时链：最坏情况是「装依赖 + 交接」之和小于建议的首次调用超时。
+    # 曾写成「pip 150s < 窗口交接 120s」，150 < 120 不成立。
+    worst = runtime.PIP_INSTALL_TIMEOUT + int(handoff_default)
+    chain = (f"pip 安装 {runtime.PIP_INSTALL_TIMEOUT}s + 窗口交接 "
+             f"{int(handoff_default)}s ≈ {worst}s  <  建议首次调用 300s")
+    check("最坏情况（pip + 交接）小于首次调用 300 秒", worst < 300, str(worst))
+    for name, text in (("SKILL.md", skill_md), ("protocol.md", protocol_md)):
+        check(f"{name} 的超时链算式成立且与代码一致", chain in text, chain)
+        check(f"{name} 不再写「150s  <  窗口交接 120s」",
+              "150s  <  窗口交接 120s" not in text)
     check("protocol.md 承认检测不到「完全没装 Python」",
           "机器完全没装 Python" in protocol_md)
     check("hint 文案是「升级」不是「首次安装」",
`````

[Back to the shelf](README.md)
