# Fix 1: json-rpc: setting an error on a response leaves the old result in place

Status: UNSENT and UNTESTED. Free to take.

- Project: pavlov99/json-rpc
- Bug report title: Response error setter pops 'value' instead of 'result'
- Bug report: number 135 ([open the bug report](https://github.com/pavlov99/json-rpc/issues/135))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/1-json-rpc-135.patch](fixes/1-json-rpc-135.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/1-json-rpc-135.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-1-json-rpc-135.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-1-json-rpc-135.html

## The bug

A JSON-RPC response object that already holds a result keeps the result after code sets an error on the response. The response then carries both a result and an error. The JSON-RPC rules allow only one of the two.

## The fix

The error setter in jsonrpc1.py and jsonrpc2.py removed a key named value that never exists. The fix removes the key named result and only when the error is set to a real value. A new test named test_error_setter_removes_result covers the case.

## Files changed

- jsonrpc/jsonrpc1.py
- jsonrpc/jsonrpc2.py
- jsonrpc/tests/test_jsonrpc2.py

## How to use the fix

1. Get a copy of the project pavlov99/json-rpc.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 1-json-rpc-135.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 135.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-09 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-09 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.

## Search words

JSONRPC20Response JSONRPC10Response error setter result and error both present _data.pop value json-rpc python

## The full patch

`````diff
diff --git a/jsonrpc/jsonrpc1.py b/jsonrpc/jsonrpc1.py
index 3fcbe9b..4adca51 100644
--- a/jsonrpc/jsonrpc1.py
+++ b/jsonrpc/jsonrpc1.py
@@ -134,8 +134,8 @@ class JSONRPC10Response(JSONRPCBaseResponse):
 
     @error.setter
     def error(self, value):
-        self._data.pop('value', None)
         if value:
+            self._data.pop('result', None)
             self._data["error"] = value
             # Test error
             JSONRPCError(**value)
diff --git a/jsonrpc/jsonrpc2.py b/jsonrpc/jsonrpc2.py
index 1231db0..3b84e2b 100644
--- a/jsonrpc/jsonrpc2.py
+++ b/jsonrpc/jsonrpc2.py
@@ -228,8 +228,8 @@ class JSONRPC20Response(JSONRPCBaseResponse):
 
     @error.setter
     def error(self, value):
-        self._data.pop('value', None)
         if value:
+            self._data.pop('result', None)
             self._data["error"] = value
             # Test error
             JSONRPCError(**value)
diff --git a/jsonrpc/tests/test_jsonrpc2.py b/jsonrpc/tests/test_jsonrpc2.py
index 32c1639..2158550 100644
--- a/jsonrpc/tests/test_jsonrpc2.py
+++ b/jsonrpc/tests/test_jsonrpc2.py
@@ -578,6 +578,11 @@ class TestJSONRPC20Response(unittest.TestCase):
         with self.assertRaises(ValueError):
             response.result = ""
 
+    def test_error_setter_removes_result(self):
+        response = JSONRPC20Response(result="")
+        response.error = {"code": 1, "message": ""}
+        self.assertNotIn("result", response.data)
+
     def test_validation_error_correct(self):
         JSONRPC20Response(**self.response_error_params)
`````

[Back to the shelf](README.md)
