# Spare token bug fixes: a public shelf

68 small ready-made bug fixes (patch files) for 34 public open source projects. Free to take.

An AI chatbot (Claude) wrote every fix. The first 26 fixes were written on 9 November 2026. Charles asked the chatbot to spend leftover weekly subscription allowance on small open bug reports so volunteer maintainers would carry less weight.

Nobody has sent any of these fixes to the projects. The fixes wait here so that any person or any AI model can pick one up and test the fix and send the fix on.

Projects covered: AgenticResourceRegistry/AgenticResourceRegistry and ahmetatar/agent-blueprint and FROWNINGdev/orm-lens and Hadeva-Dev/dawnmere and Hayuuka/sshhh and hslee16/Archy and iamvisheshsrivastava/microscopy-active-learning and itsOmidKarami/kraft and Jigsaw777/OpenKeet and JimmyDi/loop and KonstantinStarovoytov/kitden and laaielichter/Gulliver and laaielichter/Threesmith and Lucy-Robotics/huri-modules and maziyarpanahi/openmed and meridianlabs-ai/inspect_scout and mhmdaskari/overleaf-web-mcp and mila-iqia/cluv and Muneer320/klicky and oscarbol09/audiobard and OWASP/cve-lite-cli and pavlov99/json-rpc and prapaa-ai/agav and rai-opensource/spatialmath-python and remitsure/remitsure-frontend and repowise-dev/repowise and Robbo-lab/mcp-task-app and Santhosh-zeta/ColdGuard and svayatta/agent-custody and TMHSDigital/Free-Game-Dev-Assets and vignzpie/resume-agent-skills and vivekbhange-hub/repo-roast-skill and wandb/rai-toolkit and wheelgap/wheelgap.

Where the shelf lives:

- Main home on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes
- Plain website copy (easy for search engines and AI bots to read): https://chmillera-hub.github.io/game1/spare-token-bug-fixes/
- Machine-readable list for programs and AI models: [index.json](index.json) (direct address: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/index.json)

## Read this before using a fix

- An AI wrote the fixes. No human has reviewed the fixes.
- Nobody has run the fixes against the projects' own test suites. The chatbot only checked that the changed Python files still compile and ran small separate checks of the logic for 29 of the 68 fixes. Each fix page says what was checked.
- The chatbot read the full bug report text for at least 61 of the 68 fixes. The other fixes came from the bug report title plus the code. Each fix page says which. The chatbot could not read the comments under any bug report.
- Nobody checked whether another person already sent a fix for the same bug.
- Every patch applied cleanly to the newest code of its project on the day the patch was written. A project may have changed since then.
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

13. [rai-toolkit: malformed JSON dataset errors do not name the file](fix-13-rai-toolkit-131.md)
   Project: wandb/rai-toolkit. Bug report number 131. License: Apache-2.0. Test included: yes. Patch file: [13-rai-toolkit-131.patch](fixes/13-rai-toolkit-131.patch)

14. [inspect_scout: retry_refusals=True allows one retry instead of the default three](fix-14-inspect-scout-768.md)
   Project: meridianlabs-ai/inspect_scout. Bug report number 768. License: MIT. Test included: yes. Patch file: [14-inspect-scout-768.patch](fixes/14-inspect-scout-768.patch)

15. [audiobard: export_m4b crashes when the destination folder does not exist](fix-15-audiobard-120.md)
   Project: oscarbol09/audiobard. Bug report number 120. License: MIT. Test included: yes. Patch file: [15-audiobard-120.patch](fixes/15-audiobard-120.patch)

16. [audiobard: the Spanish title don matches inside the English contraction don't](fix-16-audiobard-130.md)
   Project: oscarbol09/audiobard. Bug report number 130. License: MIT. Test included: yes. Patch file: [16-audiobard-130.patch](fixes/16-audiobard-130.patch)

17. [spatialmath-python: InterpSplineSE3 rejects negative start times and mishandles a zero time span](fix-17-spatialmath-287.md)
   Project: rai-opensource/spatialmath-python. Bug report number 287. License: MIT. Test included: yes. Patch file: [17-spatialmath-287.patch](fixes/17-spatialmath-287.patch)

18. [huri-modules: test_install.sh reads $target before setting the variable (SC2318)](fix-18-huri-modules-14.md)
   Project: Lucy-Robotics/huri-modules. Bug report number 14. License: GPL-3.0. Test included: no. Patch file: [18-huri-modules-14.patch](fixes/18-huri-modules-14.patch)

19. [huri-modules: RemoteEmbedder ignores --no-verify-ssl and never verifies TLS](fix-19-huri-modules-12.md)
   Project: Lucy-Robotics/huri-modules. Bug report number 12. License: GPL-3.0. Test included: yes. Patch file: [19-huri-modules-12.patch](fixes/19-huri-modules-12.patch)

20. [agent-blueprint: lint rule unused-produced-field ignores fields read by policies.escalation](fix-20-agent-blueprint-84.md)
   Project: ahmetatar/agent-blueprint. Bug report number 84. License: MIT. Test included: yes. Patch file: [20-agent-blueprint-84.patch](fixes/20-agent-blueprint-84.patch)

21. [Gulliver: inspect quietly clamps --limit and --scan values outside the allowed range](fix-21-gulliver-97.md)
   Project: laaielichter/Gulliver. Bug report number 97. License: MIT. Test included: yes. Patch file: [21-gulliver-97.patch](fixes/21-gulliver-97.patch)

22. [microscopy-active-learning: pretrain trains zero steps when the dataset is smaller than the batch size](fix-22-microscopy-al-21.md)
   Project: iamvisheshsrivastava/microscopy-active-learning. Bug report number 21. License: MIT. Test included: yes. Patch file: [22-microscopy-al-21.patch](fixes/22-microscopy-al-21.patch)

23. [orm-lens: suggest-indexes proposes an index that already exists when Meta.indexes names the foreign key column](fix-23-orm-lens-225.md)
   Project: FROWNINGdev/orm-lens. Bug report number 225. License: MIT. Test included: yes. Patch file: [23-orm-lens-225.patch](fixes/23-orm-lens-225.patch)

24. [openmed: drift report compares score histograms that use different bin counts](fix-24-openmed-4546.md)
   Project: maziyarpanahi/openmed. Bug report number 4546. License: Apache-2.0. Test included: yes. Patch file: [24-openmed-4546.patch](fixes/24-openmed-4546.patch)

25. [repo-roast-skill: the Bailiff cannot parse cited paths that contain spaces](fix-25-repo-roast-skill-1.md)
   Project: vivekbhange-hub/repo-roast-skill. Bug report number 1. License: MIT. Test included: yes. Patch file: [25-repo-roast-skill-1.patch](fixes/25-repo-roast-skill-1.patch)

26. [kitden: add panels show one gap too many above the hint](fix-26-kitden-21.md)
   Project: KonstantinStarovoytov/kitden. Bug report number 21. License: Apache-2.0. Test included: yes. Patch file: [26-kitden-21.patch](fixes/26-kitden-21.patch)

27. [orm-lens: drift reports a moved model as unmigrated because operations inside SeparateDatabaseAndState are skipped](fix-27-orm-lens-220.md)
   Project: FROWNINGdev/orm-lens. Bug report number 220. License: MIT. Test included: yes. Patch file: [27-orm-lens-220.patch](fixes/27-orm-lens-220.patch)

28. [orm-lens: suggest-indexes counts lookups from test files and proposes indexes that production code never uses](fix-28-orm-lens-224.md)
   Project: FROWNINGdev/orm-lens. Bug report number 224. License: MIT. Test included: yes. Patch file: [28-orm-lens-224.patch](fixes/28-orm-lens-224.patch)

29. [repo-roast-skill: facts.py says 'not a git repo' when pointed at a subfolder of a repository](fix-29-repo-roast-skill-2.md)
   Project: vivekbhange-hub/repo-roast-skill. Bug report number 2. License: MIT. Test included: yes. Patch file: [29-repo-roast-skill-2.patch](fixes/29-repo-roast-skill-2.patch)

30. [repo-roast-skill: roast-rematch can compare round three against round one instead of round two](fix-30-repo-roast-skill-3.md)
   Project: vivekbhange-hub/repo-roast-skill. Bug report number 3. License: MIT. Test included: yes. Patch file: [30-repo-roast-skill-3.patch](fixes/30-repo-roast-skill-3.patch)

31. [kraft: the console command palette lists Textual's own Maximize and Screenshot commands](fix-31-kraft-1345.md)
   Project: itsOmidKarami/kraft. Bug report number 1345. License: Apache-2.0. Test included: yes. Patch file: [31-kraft-1345.patch](fixes/31-kraft-1345.patch)

32. [kraft docs: the storage guide's policy.yaml block reads like a whole file](fix-32-kraft-1347.md)
   Project: itsOmidKarami/kraft. Bug report number 1347. License: Apache-2.0. Test included: no. Patch file: [32-kraft-1347.patch](fixes/32-kraft-1347.patch)

33. [dawnmere: uninstall says 'add this by hand' for a config file with comments and does not say what to remove](fix-33-dawnmere-16.md)
   Project: Hadeva-Dev/dawnmere. Bug report number 16. License: MIT. Test included: yes. Patch file: [33-dawnmere-16.patch](fixes/33-dawnmere-16.patch)

34. [Archy: graph --format dot writes node names unescaped so a quote mark in a path gives invalid DOT](fix-34-archy-781.md)
   Project: hslee16/Archy. Bug report number 781. License: MIT. Test included: yes. Patch file: [34-archy-781.patch](fixes/34-archy-781.patch)

35. [Archy: the trend table shows UTC times with no zone so the times read as local time](fix-35-archy-754.md)
   Project: hslee16/Archy. Bug report number 754. License: MIT. Test included: yes. Patch file: [35-archy-754.patch](fixes/35-archy-754.patch)

36. [Archy: the tree-sitter version floor admits versions that lack QueryCursor so every command crashes at import](fix-36-archy-764.md)
   Project: hslee16/Archy. Bug report number 764. License: MIT. Test included: no. Patch file: [36-archy-764.patch](fixes/36-archy-764.patch)

37. [Archy: check and brief with --format json leave out coverage.governs_nothing](fix-37-archy-796.md)
   Project: hslee16/Archy. Bug report number 796. License: MIT. Test included: yes. Patch file: [37-archy-796.patch](fixes/37-archy-796.patch)

38. [kraft: the document viewer adds a second banner landmark](fix-38-kraft-1116.md)
   Project: itsOmidKarami/kraft. Bug report number 1116. License: Apache-2.0. Test included: yes. Patch file: [38-kraft-1116.patch](fixes/38-kraft-1116.patch)

39. [orm-lens: a plain class above an if block hides every model declared below it](fix-39-orm-lens-226.md)
   Project: FROWNINGdev/orm-lens. Bug report number 226. License: MIT. Test included: yes. Patch file: [39-orm-lens-226.patch](fixes/39-orm-lens-226.patch)

40. [orm-lens: inherited fields come from the wrong abstract base when two apps define a base with the same name](fix-40-orm-lens-227.md)
   Project: FROWNINGdev/orm-lens. Bug report number 227. License: MIT. Test included: yes. Patch file: [40-orm-lens-227.patch](fixes/40-orm-lens-227.patch)

41. [Archy: a module with a non-ASCII file name is dropped from churn and co-change](fix-41-archy-761.md)
   Project: hslee16/Archy. Bug report number 761. License: MIT. Test included: yes. Patch file: [41-archy-761.patch](fixes/41-archy-761.patch)

42. [Archy: a module that imports itself counts as its own importer and ranks first as central and fragile](fix-42-archy-752.md)
   Project: hslee16/Archy. Bug report number 752. License: MIT. Test included: yes. Patch file: [42-archy-752.patch](fixes/42-archy-752.patch)

43. [Archy: score --strict with no recorded history says passed with no reason in JSON and on MCP](fix-43-archy-642.md)
   Project: hslee16/Archy. Bug report number 642. License: MIT. Test included: yes. Patch file: [43-archy-642.patch](fixes/43-archy-642.patch)

44. [kraft: a changed file with a non-ASCII name shows no diff on the review page](fix-44-kraft-1348.md)
   Project: itsOmidKarami/kraft. Bug report number 1348. License: Apache-2.0. Test included: yes. Patch file: [44-kraft-1348.patch](fixes/44-kraft-1348.patch)

45. [Archy: simulate still says overall +0.000 in JSON and on MCP when no edge resolved](fix-45-archy-795.md)
   Project: hslee16/Archy. Bug report number 795. License: MIT. Test included: yes. Patch file: [45-archy-795.patch](fixes/45-archy-795.patch)

46. [cluv: submit exits with code 0 when every submission failed](fix-46-cluv-257.md)
   Project: mila-iqia/cluv. Bug report number 257. License: MIT. Test included: yes. Patch file: [46-cluv-257.patch](fixes/46-cluv-257.patch)

47. [Archy: archy_graph accepts an invalid direction or depth or max_nodes unless the call takes the path that reads the value](fix-47-archy-779.md)
   Project: hslee16/Archy. Bug report number 779. License: MIT. Test included: yes. Patch file: [47-archy-779.patch](fixes/47-archy-779.patch)

48. [Archy: three safety tests fail on mcp 2.x and the mcp 2.x CI job does not run them](fix-48-archy-768.md)
   Project: hslee16/Archy. Bug report number 768. License: MIT. Test included: yes. Patch file: [48-archy-768.patch](fixes/48-archy-768.patch)

49. [sshhh docs: the timeout chain says pip 150s is less than the 120s window handoff](fix-49-sshhh-13.md)
   Project: Hayuuka/sshhh. Bug report number 13. License: MIT. Test included: yes. Patch file: [49-sshhh-13.patch](fixes/49-sshhh-13.patch)

50. [sshhh: the generic redaction rule wipes normal output that contains pwd = and a path](fix-50-sshhh-11.md)
   Project: Hayuuka/sshhh. Bug report number 11. License: MIT. Test included: yes. Patch file: [50-sshhh-11.patch](fixes/50-sshhh-11.patch)

51. [ColdGuard: timestamps without a timezone are read in the server's local zone](fix-51-coldguard-59.md)
   Project: Santhosh-zeta/ColdGuard. Bug report number 59. License: MIT. Test included: yes. Patch file: [51-coldguard-59.patch](fixes/51-coldguard-59.patch)

52. [overleaf-web-mcp: an empty OVERLEAF_BASE_URL or OVERLEAF_COOKIE_JAR_FILE stops the server instead of using the default](fix-52-overleaf-web-mcp-53.md)
   Project: mhmdaskari/overleaf-web-mcp. Bug report number 53. License: MIT. Test included: yes. Patch file: [52-overleaf-web-mcp-53.patch](fixes/52-overleaf-web-mcp-53.patch)

53. [cve-lite-cli: recommendedAction says npm install on pnpm and Yarn and Bun projects](fix-53-cve-lite-cli-1583.md)
   Project: OWASP/cve-lite-cli. Bug report number 1583. License: MIT. Test included: yes. Patch file: [53-cve-lite-cli-1583.patch](fixes/53-cve-lite-cli-1583.patch)

54. [resume-agent-skills: Phase 4 says Section 17 framings but framings are Section 19](fix-54-resume-agent-skills-3.md)
   Project: vignzpie/resume-agent-skills. Bug report number 3. License: MIT. Test included: no. Patch file: [54-resume-agent-skills-3.patch](fixes/54-resume-agent-skills-3.patch)

55. [Threesmith: review and assets hide every finding when --limit is abc or 0](fix-55-threesmith-26.md)
   Project: laaielichter/Threesmith. Bug report number 26. License: MIT. Test included: yes. Patch file: [55-threesmith-26.patch](fixes/55-threesmith-26.patch)

56. [Threesmith: undo --steps abc says Nothing to undo and --steps 0 undoes one write](fix-56-threesmith-27.md)
   Project: laaielichter/Threesmith. Bug report number 27. License: MIT. Test included: yes. Patch file: [56-threesmith-27.patch](fixes/56-threesmith-27.patch)

57. [Threesmith: model lint ignores --max-triangles abc and the model scores 100 out of 100](fix-57-threesmith-28.md)
   Project: laaielichter/Threesmith. Bug report number 28. License: MIT. Test included: yes. Patch file: [57-threesmith-28.patch](fixes/57-threesmith-28.patch)

58. [klicky: the docs checker reports a broken link for a Markdown link in angle brackets that has spaces](fix-58-klicky-125.md)
   Project: Muneer320/klicky. Bug report number 125. License: MIT. Test included: yes. Patch file: [58-klicky-125.patch](fixes/58-klicky-125.patch)

59. [remitsure-frontend: the receipt page keeps polling after the remittance is settled](fix-59-remitsure-frontend-2.md)
   Project: remitsure/remitsure-frontend. Bug report number 2. License: MIT. Test included: yes. Patch file: [59-remitsure-frontend-2.patch](fixes/59-remitsure-frontend-2.patch)

60. [remitsure-frontend: an invalid receipt link says Could not reach the API instead of saying the link is not valid](fix-60-remitsure-frontend-1.md)
   Project: remitsure/remitsure-frontend. Bug report number 1. License: MIT. Test included: yes. Patch file: [60-remitsure-frontend-1.patch](fixes/60-remitsure-frontend-1.patch)

61. [remitsure-frontend: dashboard payee names only cover the first 20 payees](fix-61-remitsure-frontend-5.md)
   Project: remitsure/remitsure-frontend. Bug report number 5. License: MIT. Test included: yes. Patch file: [61-remitsure-frontend-5.patch](fixes/61-remitsure-frontend-5.patch)

62. [loop: session titles split a joined emoji by removing the zero width joiner](fix-62-loop-116.md)
   Project: JimmyDi/loop. Bug report number 116. License: MIT. Test included: yes. Patch file: [62-loop-116.patch](fixes/62-loop-116.patch)

63. [loop: a stale clipboard result overwrites the latest copy status](fix-63-loop-115.md)
   Project: JimmyDi/loop. Bug report number 115. License: MIT. Test included: yes. Patch file: [63-loop-115.patch](fixes/63-loop-115.patch)

64. [loop: cleaning a session title removes the visible text between two terminal escape sequences](fix-64-loop-117.md)
   Project: JimmyDi/loop. Bug report number 117. License: MIT. Test included: yes. Patch file: [64-loop-117.patch](fixes/64-loop-117.patch)

65. [Free-Game-Dev-Assets: the link check reports a short server outage as dead links](fix-65-free-game-dev-assets-275.md)
   Project: TMHSDigital/Free-Game-Dev-Assets. Bug report number 275. License: CC0-1.0. Test included: yes. Patch file: [65-free-game-dev-assets-275.patch](fixes/65-free-game-dev-assets-275.patch)

66. [agav: /undo with a mistyped argument reverts a file](fix-66-agav-681.md)
   Project: prapaa-ai/agav. Bug report number 681. License: Apache-2.0. Test included: yes. Patch file: [66-agav-681.patch](fixes/66-agav-681.patch)

67. [agent-custody: door receipts are exported to OpenTelemetry as CLIENT spans](fix-67-agent-custody-265.md)
   Project: svayatta/agent-custody. Bug report number 265. License: Apache-2.0. Test included: yes. Patch file: [67-agent-custody-265.patch](fixes/67-agent-custody-265.patch)

68. [OpenKeet: a newly added document is not ticked when building an interview pack](fix-68-openkeet-15.md)
   Project: Jigsaw777/OpenKeet. Bug report number 15. License: MIT. Test included: yes. Patch file: [68-openkeet-15.patch](fixes/68-openkeet-15.patch)

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
