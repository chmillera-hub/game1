# Fix 80: MyFinances: the frontend container always shows as unhealthy

Status: UNSENT and UNTESTED. Free to take.

- Project: jasonkryst/MyFinances
- Bug report title: maint: Frontend container healthcheck always fails (localhost resolves to ::1)
- Bug report: number 530 ([open the bug report](https://github.com/jasonkryst/MyFinances/issues/530))
- Project license: MIT
- Language: Dockerfile and YAML
- Test included: no
- Patch file: [fixes/80-myfinances-530.patch](fixes/80-myfinances-530.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/80-myfinances-530.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-80-myfinances-530.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-80-myfinances-530.html

## The bug

The health check of the frontend container asked for http://localhost:80/. Inside the container the name localhost points to the IPv6 address first and the web server only listens on IPv4. The health check failed every time and the container showed as unhealthy even though the site worked.

## The fix

The health checks in Dockerfile and docker-compose.yml now ask for http://127.0.0.1:80/ which is the first fix the bug report suggests.

## Files changed

- Dockerfile
- docker-compose.yml

## How to use the fix

1. Get a copy of the project jasonkryst/MyFinances.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 80-myfinances-530.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 530.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The chatbot did not build or start the container so nobody has seen the container report healthy with this patch. The bug report names a second option (make the web server also listen on IPv6) and the patch does not take that option. No test is included because the project has no test that starts the container. Fix 73 on this shelf is for the same project and touches different files.

## Search words

MyFinances frontend healthcheck unhealthy localhost ::1 IPv6 nginx listen 80 wget 127.0.0.1 Dockerfile docker-compose.yml

## The full patch

`````diff
diff --git a/Dockerfile b/Dockerfile
index cb94208..03560d6 100644
--- a/Dockerfile
+++ b/Dockerfile
@@ -49,6 +49,6 @@ USER nginx
 EXPOSE 80
 
 HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
-    CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1
+    CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:80/ || exit 1
 
 CMD ["nginx", "-g", "daemon off;"]
diff --git a/docker-compose.yml b/docker-compose.yml
index 2d8a516..6a5bb4b 100644
--- a/docker-compose.yml
+++ b/docker-compose.yml
@@ -33,7 +33,7 @@ services:
       - SETGID
       - NET_BIND_SERVICE
     healthcheck:
-      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:80/"]
+      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://127.0.0.1:80/"]
       interval: 30s
       timeout: 5s
       retries: 3
`````

[Back to the shelf](README.md)
