# Spare token bug fixes: a public shelf

This folder holds seven small bug fixes for six public software projects.

An AI chatbot (Claude) wrote every fix. Charles asked the chatbot to spend leftover weekly subscription allowance on small open bug reports so volunteer maintainers would carry less weight.

Nobody has sent any of these fixes to the projects. The fixes wait here so that any person or any chatbot can pick one up and check the fix and send the fix on.

## Read this before using a fix

- An AI wrote the fixes. No human has reviewed the fixes.
- Nobody has run the fixes against the projects' own test suites. The chatbot only checked that the changed Python files still compile and ran one small separate check for fix 7.
- The chatbot read the full bug report for only one of the seven. The other six fixes came from the bug report title plus the code.
- Nobody checked whether another person already sent a fix for the same bug.
- A project may have moved on since 9 November 2026 so a fix may no longer apply cleanly.
- Please run the project's tests and read the project's contribution rules before sending anything. A wrong fix costs a volunteer maintainer time.

## The fixes

Each file in the fixes folder is a standard patch file. Apply one with: git apply and then the file name.

1. fixes/1-json-rpc-135.patch
   Project: pavlov99/json-rpc (bug report 135). License: MIT.
   Setting an error on a response left the old result in place. The fix removes the result when an error is set. Includes a test.

2. fixes/2-mcp-task-app-128.patch
   Project: Robbo-lab/mcp-task-app (bug report 128). License: MIT.
   Every task got the time the program started instead of the time the task was created. The fix makes the default time get worked out fresh for each task. No test included. This project looks like a teaching project so the maintainer may want students to fix the bug.

3. fixes/3-gulliver-107.patch
   Project: laaielichter/Gulliver (bug report 107). License: MIT.
   A huge number for the days option crashed the program. The fix returns a clear error message instead. Includes a test.

4. fixes/4-kraft-1344.patch
   Project: itsOmidKarami/kraft (bug report 1344). License: Apache 2.0.
   One update call skipped the shared error handling the other calls use. The fix routes the call through the same handling. Includes a test case.

5. fixes/5-gulliver-108.patch
   Project: laaielichter/Gulliver (bug report 108). License: MIT.
   A huge time period crashed the period reader. The fix raises a clear "period is too large" error instead. Includes a test line.

6. fixes/6-agenticresourceregistry-1971.patch
   Project: AgenticResourceRegistry/AgenticResourceRegistry (bug report 1971). License: Apache 2.0.
   Five places on the website told people to type a command that does not exist. The fix adds the missing word so the screens show the real command. Text change only.

7. fixes/7-repowise-5357.patch
   Project: repowise-dev/repowise (bug report 5357). License: AGPL 3.0.
   A heading inside a code sample was mistaken for a real section heading. The fix makes the section finder skip code samples. Includes a test.

## Licenses

Each patch contains a few lines of the original project's code. Each patch stays under the license of the project the patch belongs to. The license names above come from the license file in each project on 9 November 2026.

## If you maintain one of these projects

Take the fix or ignore the fix or ask for the file to be removed. No reply is owed to anyone.
