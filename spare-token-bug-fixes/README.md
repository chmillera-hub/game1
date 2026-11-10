# Spare token bug fixes: a public shelf

12 small ready-made bug fixes (patch files) for 8 public open source projects. Free to take.

An AI chatbot (Claude Fable 5.2) wrote every fix on 9 November 2026. Charles asked the chatbot to spend leftover weekly subscription allowance on small open bug reports so volunteer maintainers would carry less weight.

Nobody has sent any of these fixes to the projects. The fixes wait here so that any person or any AI model can pick one up and test the fix and send the fix on.

Projects covered: AgenticResourceRegistry/AgenticResourceRegistry and FROWNINGdev/orm-lens and itsOmidKarami/kraft and laaielichter/Gulliver and pavlov99/json-rpc and repowise-dev/repowise and Robbo-lab/mcp-task-app and wheelgap/wheelgap.

Where the shelf lives:

- Main home on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes
- Plain website copy (easy for search engines and AI bots to read): https://chmillera-hub.github.io/game1/spare-token-bug-fixes/
- Machine-readable list for programs and AI models: [index.json](index.json) (direct address: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/index.json)

## Read this before using a fix

- An AI wrote the fixes. No human has reviewed the fixes.
- Nobody has run the fixes against the projects' own test suites. The chatbot only checked that the changed Python files still compile and ran small separate checks of the logic for fixes 7 and 9 and 10.
- The chatbot read the full bug report text for six of the twelve fixes (fixes 8 to 12 plus one earlier fix). The other fixes came from the bug report title plus the code. The chatbot could not read the comments under any bug report.
- Nobody checked whether another person already sent a fix for the same bug.
- Every patch applied cleanly to the newest code of its project on 9 November 2026. A project may have changed since then.
- Please run the project's tests and read the project's contribution rules before sending anything. A wrong fix costs a volunteer maintainer time.

## The fixes

Each fix has a page of its own with the bug and the change and the full patch text.

1. [json-rpc: setting an error on a response leaves the old result in place](fix-1-json-rpc-135.md)
   Project: pavlov99/json-rpc. Bug report number 135. License: MIT. Test included: yes. Patch file: [1-json-rpc-135.patch](fixes/1-json-rpc-135.patch)

2. [mcp-task-app: every task gets the program start time as task_started](fix-2-mcp-task-app-128.md)
   Project: Robbo-lab/mcp-task-app. Bug report number 128. License: MIT. Test included: no. Patch file: [2-mcp-task-app-128.patch](fixes/2-mcp-task-app-128.patch)

3. [Gulliver: spend with a huge --days value crashes with OverflowError](fix-3-gulliver-107.md)
   Project: laaielichter/Gulliver. Bug report number 107. License: MIT. Test included: yes. Patch file: [3-gulliver-107.patch](fixes/3-gulliver-107.patch)

4. [kraft: update_repo skips the shared response handling](fix-4-kraft-1344.md)
   Project: itsOmidKarami/kraft. Bug report number 1344. License: Apache-2.0. Test included: yes. Patch file: [4-kraft-1344.patch](fixes/4-kraft-1344.patch)

5. [Gulliver: parse_period with a huge number crashes with OverflowError](fix-5-gulliver-108.md)
   Project: laaielichter/Gulliver. Bug report number 108. License: MIT. Test included: yes. Patch file: [5-gulliver-108.patch](fixes/5-gulliver-108.patch)

6. [AgenticResourceRegistry: web screens show the command observal pull which does not exist](fix-6-agenticresourceregistry-1971.md)
   Project: AgenticResourceRegistry/AgenticResourceRegistry. Bug report number 1971. License: Apache-2.0. Test included: no. Patch file: [6-agenticresourceregistry-1971.patch](fixes/6-agenticresourceregistry-1971.patch)

7. [repowise: a heading inside a code fence is treated as a real section heading](fix-7-repowise-5357.md)
   Project: repowise-dev/repowise. Bug report number 5357. License: AGPL-3.0. Test included: yes. Patch file: [7-repowise-5357.patch](fixes/7-repowise-5357.patch)

8. [orm-lens: objects = models.Manager() is parsed as a model field and drift fails the build](fix-8-orm-lens-219.md)
   Project: FROWNINGdev/orm-lens. Bug report number 219. License: MIT. Test included: yes. Patch file: [8-orm-lens-219.patch](fixes/8-orm-lens-219.patch)

9. [orm-lens: @receiver with a list or tuple of signals becomes one unknown custom edge](fix-9-orm-lens-221.md)
   Project: FROWNINGdev/orm-lens. Bug report number 221. License: MIT. Test included: yes. Patch file: [9-orm-lens-221.patch](fixes/9-orm-lens-221.patch)

10. [Gulliver: check accepts a negative --min-rows and a negative or NaN or infinite --max-change](fix-10-gulliver-106.md)
   Project: laaielichter/Gulliver. Bug report number 106. License: MIT. Test included: yes. Patch file: [10-gulliver-106.patch](fixes/10-gulliver-106.patch)

11. [wheelgap: a private-index lockfile package with no file list is still looked up on PyPI](fix-11-wheelgap-145.md)
   Project: wheelgap/wheelgap. Bug report number 145. License: MIT. Test included: yes. Patch file: [11-wheelgap-145.patch](fixes/11-wheelgap-145.patch)

12. [repowise: test_tool_overview.py fails when run alone because ov.health does not exist yet](fix-12-repowise-5368.md)
   Project: repowise-dev/repowise. Bug report number 5368. License: AGPL-3.0. Test included: yes. Patch file: [12-repowise-5368.patch](fixes/12-repowise-5368.patch)

## How to use a fix

1. Get a copy of the project.
2. Download the patch file.
3. Run: git apply and then the patch file name.
4. Run the project's own tests.
5. Open a pull request on the project that mentions the bug report number.

## For AI models and other programs

Read index.json first. Every entry gives the project and the bug report number and the direct address of the patch file and status flags. All status flags are plain true or false values. Please re-check that the bug report is still open before using a fix.

## Licenses

Each patch contains a few lines of the original project's code. Each patch stays under the license of the project the patch belongs to. The license names above come from the license file in each project on 9 November 2026.

## If you maintain one of these projects

Take the fix or ignore the fix or ask for the file to be removed. No reply is owed to anyone.
