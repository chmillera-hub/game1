# Fix 2: mcp-task-app: every task gets the program start time as task_started

Status: UNSENT and UNTESTED. Free to take.

- Project: Robbo-lab/mcp-task-app
- Bug report title: [BUG] task_started default is fixed at import time
- Bug report: number 128 ([open the bug report](https://github.com/Robbo-lab/mcp-task-app/issues/128))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/2-mcp-task-app-128.patch](fixes/2-mcp-task-app-128.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/2-mcp-task-app-128.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-2-mcp-task-app-128.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-2-mcp-task-app-128.html

## The bug

Every new task shows the same task_started time. The time shown is the moment the program started and not the moment the task was created.

## The fix

The code called datetime.now() once when the program loaded and reused that one value as the default. The fix passes the function datetime.now to SQLAlchemy and uses Field(default_factory=datetime.now) in the Pydantic model so each task gets a fresh time. No test is included. The project looks like a teaching project so the maintainer may prefer that students fix the bug.

## Files changed

- app/data/database_objects.py
- app/data/pydantic_objects.py

## How to use the fix

1. Get a copy of the project Robbo-lab/mcp-task-app.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 2-mcp-task-app-128.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 128.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot worked from the bug report title plus the code and did not read the full bug report text.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-09 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-09 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.

## Search words

task_started default datetime.now() evaluated once at import SQLAlchemy Column default Pydantic default_factory same timestamp every row

## The full patch

`````diff
diff --git a/app/data/database_objects.py b/app/data/database_objects.py
index cd2b398..6612fa1 100644
--- a/app/data/database_objects.py
+++ b/app/data/database_objects.py
@@ -15,7 +15,7 @@ class DBTask(Base):
     type = Column(String(100), nullable=False)
     description = Column(String(1000), nullable=True)
     completed = Column(Boolean(), nullable=True, default=False)
-    task_started = Column(DATETIME(), nullable=True, default=datetime.now())
+    task_started = Column(DATETIME(), nullable=True, default=datetime.now)
     task_ended = Column(DATETIME(), nullable=True)
 
 
diff --git a/app/data/pydantic_objects.py b/app/data/pydantic_objects.py
index b367b08..a06a28d 100644
--- a/app/data/pydantic_objects.py
+++ b/app/data/pydantic_objects.py
@@ -1,6 +1,6 @@
 from datetime import datetime
 
-from pydantic import BaseModel
+from pydantic import BaseModel, Field
 
 
 # PLTask stands for Pydantic Task
@@ -12,5 +12,5 @@ class PLTask(BaseModel):
     type: str | None = None
     description: str | None = None
     completed: bool | None = False
-    task_started: datetime | None = datetime.now()
+    task_started: datetime | None = Field(default_factory=datetime.now)
     task_ended: datetime | None = None
`````

[Back to the shelf](README.md)
