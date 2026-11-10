# game1: a word game plus a public shelf of free bug fixes

This project holds two separate things.

1. A word equation game: [play the game](https://chmillera-hub.github.io/game1/word-equation-game.html).

2. A public shelf of small bug fixes for other people's open source software: [open the bug fix shelf](spare-token-bug-fixes/README.md).

## About the bug fix shelf

Main home of the shelf on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes

The shelf holds twelve small AI-written bug fixes (patch files) for eight public projects. Nobody has sent the fixes to the projects yet. Any person or any AI model is free to pick a fix up and test the fix and send the fix on.

1. [json-rpc: setting an error on a response leaves the old result in place](spare-token-bug-fixes/fix-1-json-rpc-135.md)
   Project: pavlov99/json-rpc. Bug report number 135. License: MIT. Test included: yes. Patch file: [1-json-rpc-135.patch](spare-token-bug-fixes/fixes/1-json-rpc-135.patch)

2. [mcp-task-app: every task gets the program start time as task_started](spare-token-bug-fixes/fix-2-mcp-task-app-128.md)
   Project: Robbo-lab/mcp-task-app. Bug report number 128. License: MIT. Test included: no. Patch file: [2-mcp-task-app-128.patch](spare-token-bug-fixes/fixes/2-mcp-task-app-128.patch)

3. [Gulliver: spend with a huge --days value crashes with OverflowError](spare-token-bug-fixes/fix-3-gulliver-107.md)
   Project: laaielichter/Gulliver. Bug report number 107. License: MIT. Test included: yes. Patch file: [3-gulliver-107.patch](spare-token-bug-fixes/fixes/3-gulliver-107.patch)

4. [kraft: update_repo skips the shared response handling](spare-token-bug-fixes/fix-4-kraft-1344.md)
   Project: itsOmidKarami/kraft. Bug report number 1344. License: Apache-2.0. Test included: yes. Patch file: [4-kraft-1344.patch](spare-token-bug-fixes/fixes/4-kraft-1344.patch)

5. [Gulliver: parse_period with a huge number crashes with OverflowError](spare-token-bug-fixes/fix-5-gulliver-108.md)
   Project: laaielichter/Gulliver. Bug report number 108. License: MIT. Test included: yes. Patch file: [5-gulliver-108.patch](spare-token-bug-fixes/fixes/5-gulliver-108.patch)

6. [AgenticResourceRegistry: web screens show the command observal pull which does not exist](spare-token-bug-fixes/fix-6-agenticresourceregistry-1971.md)
   Project: AgenticResourceRegistry/AgenticResourceRegistry. Bug report number 1971. License: Apache-2.0. Test included: no. Patch file: [6-agenticresourceregistry-1971.patch](spare-token-bug-fixes/fixes/6-agenticresourceregistry-1971.patch)

7. [repowise: a heading inside a code fence is treated as a real section heading](spare-token-bug-fixes/fix-7-repowise-5357.md)
   Project: repowise-dev/repowise. Bug report number 5357. License: AGPL-3.0. Test included: yes. Patch file: [7-repowise-5357.patch](spare-token-bug-fixes/fixes/7-repowise-5357.patch)

8. [orm-lens: objects = models.Manager() is parsed as a model field and drift fails the build](spare-token-bug-fixes/fix-8-orm-lens-219.md)
   Project: FROWNINGdev/orm-lens. Bug report number 219. License: MIT. Test included: yes. Patch file: [8-orm-lens-219.patch](spare-token-bug-fixes/fixes/8-orm-lens-219.patch)

9. [orm-lens: @receiver with a list or tuple of signals becomes one unknown custom edge](spare-token-bug-fixes/fix-9-orm-lens-221.md)
   Project: FROWNINGdev/orm-lens. Bug report number 221. License: MIT. Test included: yes. Patch file: [9-orm-lens-221.patch](spare-token-bug-fixes/fixes/9-orm-lens-221.patch)

10. [Gulliver: check accepts a negative --min-rows and a negative or NaN or infinite --max-change](spare-token-bug-fixes/fix-10-gulliver-106.md)
   Project: laaielichter/Gulliver. Bug report number 106. License: MIT. Test included: yes. Patch file: [10-gulliver-106.patch](spare-token-bug-fixes/fixes/10-gulliver-106.patch)

11. [wheelgap: a private-index lockfile package with no file list is still looked up on PyPI](spare-token-bug-fixes/fix-11-wheelgap-145.md)
   Project: wheelgap/wheelgap. Bug report number 145. License: MIT. Test included: yes. Patch file: [11-wheelgap-145.patch](spare-token-bug-fixes/fixes/11-wheelgap-145.patch)

12. [repowise: test_tool_overview.py fails when run alone because ov.health does not exist yet](spare-token-bug-fixes/fix-12-repowise-5368.md)
   Project: repowise-dev/repowise. Bug report number 5368. License: AGPL-3.0. Test included: yes. Patch file: [12-repowise-5368.patch](spare-token-bug-fixes/fixes/12-repowise-5368.patch)

Machine-readable list: [spare-token-bug-fixes/index.json](spare-token-bug-fixes/index.json)

The short version of the warnings: an AI wrote the fixes and no human reviewed the fixes and nobody ran the projects' own tests. The full warnings are on the shelf page.
