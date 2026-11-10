# Fix 17: spatialmath-python: InterpSplineSE3 rejects negative start times and mishandles a zero time span

Status: UNSENT and UNTESTED. Free to take.

- Project: rai-opensource/spatialmath-python
- Bug report title: InterpSplineSE3 rejects negative start times and mishandles a zero time span
- Bug report: number 287 ([open the bug report](https://github.com/rai-opensource/spatialmath-python/issues/287))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/17-spatialmath-287.patch](fixes/17-spatialmath-287.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/17-spatialmath-287.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-17-spatialmath-287.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-17-spatialmath-287.html

## The bug

InterpSplineSE3([-5, -3, -1], poses) raises ValueError because the constructor tests the last time point instead of the span between the first and the last. A span of zero is not caught and fails later with an unrelated SciPy error when normalize_time is on. The error message prints {self._e} literally because the f prefix is missing.

## The fix

The constructor in spatialmath/spline.py now checks the last time minus the first time and the message is a real f-string. The two length checks now run before the span check so a single time point still gets the message about needing two data points. New tests cover negative and offset start times with and without normalize_time and a zero span.

## Files changed

- spatialmath/spline.py
- tests/test_spline.py

## How to use the fix

1. Get a copy of the project rai-opensource/spatialmath-python.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 17-spatialmath-287.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 287.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-09 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-09 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report had one comment on 9 November 2026 and the chatbot could not read comments.

## Search words

spatialmath InterpSplineSE3 negative timepoints ValueError Difference between start and end timepoints is less than {self._e} zero time span normalize_time

## The full patch

`````diff
diff --git a/spatialmath/spline.py b/spatialmath/spline.py
index c0a99ca..5345c72 100644
--- a/spatialmath/spline.py
+++ b/spatialmath/spline.py
@@ -105,17 +105,19 @@ class InterpSplineSE3(SplineSE3):
         self.control_poses = control_poses
         self.timepoints = np.array(timepoints)
 
-        if self.timepoints[-1] < self._e:
-            raise ValueError(
-                "Difference between start and end timepoints is less than {self._e}"
-            )
-
         if len(self.control_poses) != len(self.timepoints):
             raise ValueError("Length of control_poses and timepoints must be equal.")
 
         if len(self.timepoints) < 2:
             raise ValueError("Need at least 2 data points to make a trajectory.")
 
+        # Check the span between the first and last time, not the last time itself:
+        # a trajectory may start at a negative or offset time.
+        if self.timepoints[-1] - self.timepoints[0] < self._e:
+            raise ValueError(
+                f"Difference between start and end timepoints is less than {self._e}"
+            )
+
         if normalize_time:
             self.timepoints = self.timepoints - self.timepoints[0]
             self.timepoints = self.timepoints / self.timepoints[-1]
diff --git a/tests/test_spline.py b/tests/test_spline.py
index e1fb56c..05f426a 100644
--- a/tests/test_spline.py
+++ b/tests/test_spline.py
@@ -73,6 +73,25 @@ class TestInterpSplineSE3:
             np.linspace(0, InterpSplineSE3._e, len(self.waypoints)), self.waypoints
         )
 
+    @pytest.mark.parametrize("start, end", [(-10.0, -1.0), (-5.0, 5.0), (100.0, 110.0)])
+    @pytest.mark.parametrize("normalize_time", [False, True])
+    def test_negative_and_offset_start_times(self, start, end, normalize_time):
+        times = np.linspace(start, end, len(self.waypoints))
+        spline = InterpSplineSE3(times, self.waypoints, normalize_time=normalize_time)
+        if normalize_time:
+            nt.assert_almost_equal(spline.timepoints[0], 0.0)
+            nt.assert_almost_equal(spline.timepoints[-1], 1.0)
+        for time, pose in zip(spline.timepoints, self.waypoints):
+            nt.assert_almost_equal(spline(time).angdist(pose), 0.0)
+            nt.assert_almost_equal(np.linalg.norm(spline(time).t - pose.t), 0.0)
+
+    @pytest.mark.parametrize("time", [0.0, 3.0, -3.0])
+    @pytest.mark.parametrize("normalize_time", [False, True])
+    def test_zero_time_span_is_rejected(self, time, normalize_time):
+        times = np.full(len(self.waypoints), time)
+        with pytest.raises(ValueError, match=f"less than {InterpSplineSE3._e}"):
+            InterpSplineSE3(times, self.waypoints, normalize_time=normalize_time)
+
     @pytest.mark.skipif(
         plt.get_backend().lower() == "agg" or os.environ.get("CI") == "true",
         reason="animate=True busy-waits on a timer callback that never "
`````

[Back to the shelf](README.md)
