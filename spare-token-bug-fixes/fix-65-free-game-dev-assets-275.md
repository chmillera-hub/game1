# Fix 65: Free-Game-Dev-Assets: the link check reports a short server outage as dead links

Status: UNSENT and UNTESTED. Free to take.

- Project: TMHSDigital/Free-Game-Dev-Assets
- Bug report title: Link check reports transient 5xx answers (GitHub outage) as dead links
- Bug report: number 275 ([open the bug report](https://github.com/TMHSDigital/Free-Game-Dev-Assets/issues/275))
- Project license: CC0-1.0
- Language: JavaScript
- Test included: yes
- Patch file: [fixes/65-free-game-dev-assets-275.patch](fixes/65-free-game-dev-assets-275.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/65-free-game-dev-assets-275.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-65-free-game-dev-assets-275.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-65-free-game-dev-assets-275.html

## The bug

The weekly link check counted every answer from 400 up as a dead link. During a short GitHub outage 70 entries answered 504 and the report listed all 70 as dead. A recheck the same day found all 70 alive. The one real problem in the report was easy to miss.

## The fix

classify in site/lib/link-check.mjs returns the kind unavailable for 502 and 503 and 504. site/check-links.mjs retries such an answer once and lists the entries in a collapsed section named Server unavailable that does not count as a problem. When one host answered that way for more than one entry the section starts with one summary line for the host. site/lib/lib.test.mjs gains checks for 502 and 503 and 504 and for codes that stay dead.

## Files changed

- site/check-links.mjs
- site/lib/lib.test.mjs
- site/lib/link-check.mjs

## How to use the fix

1. Get a copy of the project TMHSDigital/Free-Game-Dev-Assets.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 65-free-game-dev-assets-275.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 275.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report suggests an optional second retry after about 30 seconds. The fix keeps the existing single immediate retry and adds no delay. A licence page that answers 502 or 503 or 504 is no longer reported as dead and is not listed anywhere. Code 500 still counts as dead because the bug report names only 502 and 503 and 504. The chatbot checked the rule with a scratch script and checked the syntax of the three files with node --check. Nobody ran the project's tests.

## Search words

Free-Game-Dev-Assets link check classify 502 503 504 transient outage dead links unavailable could not check GitHub

## The full patch

`````diff
diff --git a/site/check-links.mjs b/site/check-links.mjs
index e535ce1..b399a9c 100644
--- a/site/check-links.mjs
+++ b/site/check-links.mjs
@@ -8,6 +8,9 @@
  * - stale: `verified` is older than --stale-days (365 by default)
  * - blocked: 401/403/429, which is usually a site refusing robots rather
  *   than a dead link; listed for a manual check, never counted as a problem
+ * - unavailable: 502/503/504, a gateway or server that is down at that
+ *   moment (an outage of one host hits every entry on it); retried once,
+ *   then listed as not checked this run, never counted as a problem
  * - maintenance: a github.com source whose repository is archived or has had
  *   no push in three years while its `maintenance` field does not say so, or
  *   the other way round. Uses the GitHub API; set GITHUB_TOKEN to lift the
@@ -84,7 +87,9 @@ async function run(entries) {
         let r = await check(entries[i]);
         // One retry for anything that did not answer cleanly, except a full
         // 20 s timeout: a second one would cost a worker 40 s per dead host.
-        if (r.kind === "dead" && !r.timedOut) r = await check(entries[i]);
+        // A 502/503/504 gets the same single retry; an outage that lasts is
+        // then reported as "could not check", not as dead.
+        if ((r.kind === "dead" && !r.timedOut) || r.kind === "unavailable") r = await check(entries[i]);
         // A refusal is not retried, and the checker never poses as a browser:
         // a host that refuses scripts goes on the manual list (config.json).
         results[i] = r;
@@ -131,6 +136,11 @@ const stale = entries.filter((e) => e.verified && e.verified < cutoff);
 const line = (r) => `- [ ] [\`${r.id}\`](${REPO}/blob/main/${r.rel}): ${reportUrl(r.url)}${r.detail ? ` (${r.detail})` : ""}`;
 
 const dead = pick("dead");
+// The host answered 502, 503 or 504: listed so nobody has to guess, not counted as a problem.
+const unavailable = pick("unavailable");
+const outageHosts = [...unavailable.reduce((m, r) => m.set(new URL(r.url).hostname, (m.get(new URL(r.url).hostname) || 0) + 1), new Map())]
+  .filter(([, n]) => n > 1)
+  .map(([host, n]) => `${host} answered 5xx for ${n} entries: likely an outage.`);
 const moved = pick("moved");
 const refused = pick("blocked");
 const blocked = refused.filter((r) => !manualHostReason(r.url, MANUAL_HOSTS));
@@ -167,6 +177,14 @@ const report = [
   "",
   ...(skipped.length ? skipped.map(line) : ["None."]),
   "",
+  `<details><summary>Server unavailable (${unavailable.length}): answered 502, 503 or 504, so the link could not be checked this run</summary>`,
+  "",
+  ...outageHosts,
+  ...(outageHosts.length ? [""] : []),
+  ...(unavailable.length ? unavailable.map(line) : ["None."]),
+  "",
+  "</details>",
+  "",
   `<details><summary>Refused the checker (${blocked.length}): usually bot blocking, check by hand</summary>`,
   "",
   ...(blocked.length ? blocked.map(line) : ["None."]),
diff --git a/site/lib/lib.test.mjs b/site/lib/lib.test.mjs
index 9794eb5..46304cb 100644
--- a/site/lib/lib.test.mjs
+++ b/site/lib/lib.test.mjs
@@ -890,6 +890,14 @@ eq("same .co.uk site is ok", classify("https://a.co.uk/x", 200, "https://www.a.c
 eq("github repo transfer is moved", classify("https://github.com/a/b", 200, "https://github.com/c/b").kind, "moved");
 eq("403 is blocked", classify("https://a.test/", 403, "https://a.test/").kind, "blocked");
 eq("404 is dead", classify("https://a.test/", 404, "https://a.test/").kind, "dead");
+// #275: a gateway or server that is down for a moment is not a dead link.
+for (const status of [502, 503, 504]) {
+  eq(`${status} is unavailable, not dead`, classify("https://github.com/a/b", status, "https://github.com/a/b").kind, "unavailable");
+  eq(`${status} keeps its status in the detail`, classify("https://github.com/a/b", status, "https://github.com/a/b").detail, `HTTP ${status}`);
+}
+for (const status of [400, 404, 410, 451, 500, 501]) {
+  eq(`${status} is still dead`, classify("https://a.test/", status, "https://a.test/").kind, "dead");
+}
 eq("report url is an inert code span", reportUrl("https://a.test/@x](y)`z"), "`https://a.test/@x](y)%60z`");
 
 // #64: one entry walker; hidden and scratch folders are not entries.
diff --git a/site/lib/link-check.mjs b/site/lib/link-check.mjs
index 3c2be31..0b0c325 100644
--- a/site/lib/link-check.mjs
+++ b/site/lib/link-check.mjs
@@ -57,9 +57,14 @@ export function evidenceUrls(evidence) {
 /** owner/repo of a github.com URL, lowercased. A transferred repository redirects within github.com. */
 export const repoOf = (url) => new URL(url).pathname.split("/").slice(1, 3).join("/").toLowerCase();
 
-/** What a finished request says about an entry. */
+/**
+ * What a finished request says about an entry. A 502, 503 or 504 means a
+ * gateway or the server was unavailable at that moment, not that the page is
+ * gone: one host's short outage would otherwise report every entry on it as dead.
+ */
 export function classify(entryUrl, status, finalUrl) {
   if ([401, 403, 429].includes(status)) return { kind: "blocked", detail: `HTTP ${status}` };
+  if ([502, 503, 504].includes(status)) return { kind: "unavailable", detail: `HTTP ${status}` };
   if (status >= 400) return { kind: "dead", detail: `HTTP ${status}` };
   const from = siteOf(new URL(entryUrl).hostname);
   const to = siteOf(new URL(finalUrl).hostname);
`````

[Back to the shelf](README.md)
