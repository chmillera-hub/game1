# Fix 97: SMART toolkit: the zip-mode agent package includes the project's infrastructure folder

Status: UNSENT and UNTESTED. Free to take.

- Project: awslabs/social-messaging-agent-runtime-toolkit
- Bug report title: terraform: zip-mode agent archive includes the project's infrastructure/ directory
- Bug report: number 57 ([open the bug report](https://github.com/awslabs/social-messaging-agent-runtime-toolkit/issues/57))
- Project license: Apache-2.0
- Language: Terraform and Python
- Test included: yes
- Patch file: [fixes/97-social-messaging-agent-runtime-toolkit-57.patch](fixes/97-social-messaging-agent-runtime-toolkit-57.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/97-social-messaging-agent-runtime-toolkit-57.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-97-social-messaging-agent-runtime-toolkit-57.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-97-social-messaging-agent-runtime-toolkit-57.html

## The bug

The Docker-mode archive of the agent leaves out a project's infrastructure folder. The zip-mode archive did not. A zip-mode project that keeps Terraform or CDK code in that folder shipped the code inside the package that runs the agent.

## The fix

The zip-mode archive in infra-terraform/modules/runtime/codebuild.tf now lists infrastructure among the excluded names. tests/test_terraform_hardening.py gains a test that the two archives exclude the same fixed names. CHANGELOG.md gains one line.

## Files changed

- CHANGELOG.md
- infra-terraform/modules/runtime/codebuild.tf
- tests/test_terraform_hardening.py

## How to use the fix

1. Get a copy of the project awslabs/social-messaging-agent-runtime-toolkit.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 97-social-messaging-agent-runtime-toolkit-57.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 57.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot worked from the bug report title plus the code and did not read the full bug report text.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The chatbot ran a scratch copy of the comparison over the Terraform file: the two lists differed by infrastructure before the change and matched after. The chatbot did not run Terraform or the project's tests. The end of the bug report text was cut off in the search result. Fixes 72 and 96 and 97 and 99 on this shelf each add a line at the same spot of CHANGELOG.md so those patches do not apply one after another: apply one patch and add the other changelog lines by hand. The other files in those patches do not overlap.

## Search words

socialagent terraform archive_file agent_source_zip excludes infrastructure zip mode codebuild.tf AgentCore Runtime package

## The full patch

`````diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index 6ecb773..b8bbcd9 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -4,6 +4,9 @@ All notable changes to SMART, the Social Messaging Agent Runtime Toolkit, are re
 
 ## [Unreleased]
 
+### Fixed
+- The zip-mode agent archive leaves out a project's `infrastructure/` directory, as the Docker-mode archive already does.
+
 ## [2026.10.0] - 2026-11-05
 
 The first public release. Everything below was in the toolkit when it was published.
diff --git a/infra-terraform/modules/runtime/codebuild.tf b/infra-terraform/modules/runtime/codebuild.tf
index 3024f6f..333ab99 100644
--- a/infra-terraform/modules/runtime/codebuild.tf
+++ b/infra-terraform/modules/runtime/codebuild.tf
@@ -398,7 +398,7 @@ data "archive_file" "agent_source_zip" {
   # never read by the agent, and zipping them rebuilt the image on every deploy.
   # The fixed names only ever match at the project root; caches and
   # credentials at any depth come from agent_source_filter_excludes.
-  excludes = concat(["__pycache__", "*.pyc", "*.pyo", ".pytest_cache", ".venv", "handlers", "infra-terraform", "node_modules", ".git", ".socialagent", "socialagent.dev.yaml", "socialagent.test.yaml", "socialagent.prod.yaml"], local.agent_source_filter_excludes)
+  excludes = concat(["__pycache__", "*.pyc", "*.pyo", ".pytest_cache", ".venv", "handlers", "infrastructure", "infra-terraform", "node_modules", ".git", ".socialagent", "socialagent.dev.yaml", "socialagent.test.yaml", "socialagent.prod.yaml"], local.agent_source_filter_excludes)
 }
 
 resource "aws_s3_object" "agent_source_zip" {
diff --git a/tests/test_terraform_hardening.py b/tests/test_terraform_hardening.py
index 7c70ce8..591ffd4 100644
--- a/tests/test_terraform_hardening.py
+++ b/tests/test_terraform_hardening.py
@@ -1457,6 +1457,22 @@ def test_agent_source_archive_applies_the_filters(archive: str):
         assert f'"{name}"' in excludes.group(1), f"{archive} no longer excludes {name}"
 
 
+def test_both_agent_source_archives_exclude_the_same_fixed_names():
+    """The zip-mode archive kept a project's infrastructure/ directory, which
+    the Docker-mode archive leaves out, so Terraform or CDK code shipped in the
+    package that runs in AgentCore Runtime."""
+    tf = _code(CODEBUILD_TF.read_text())
+    fixed: dict[str, set[str]] = {}
+    for archive in ("agent_source", "agent_source_zip"):
+        block = _block(tf, f'data "archive_file" "{archive}"')
+        names = re.search(r"^\s*excludes\s*=\s*concat\(\[(.*?)\]", block, re.MULTILINE)
+        assert names, f"archive_file.{archive} has no list of fixed names"
+        fixed[archive] = set(re.findall(r'"([^"]+)"', names.group(1)))
+
+    assert "infrastructure" in fixed["agent_source_zip"]
+    assert fixed["agent_source"] == fixed["agent_source_zip"]
+
+
 # Paths that must still ship, and every dropped path with the `excludes` entry
 # it yields: the shallowest dropped directory, or the file itself with
 # filepath.Match syntax escaped.
`````

[Back to the shelf](README.md)
