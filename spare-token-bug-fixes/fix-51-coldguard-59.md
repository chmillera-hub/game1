# Fix 51: ColdGuard: timestamps without a timezone are read in the server's local zone

Status: UNSENT and UNTESTED. Free to take.

- Project: Santhosh-zeta/ColdGuard
- Bug report title: fix(core): interpret naive timestamps in an explicit timezone (--tz), not the server's local zone
- Bug report: number 59 ([open the bug report](https://github.com/Santhosh-zeta/ColdGuard/issues/59))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/51-coldguard-59.patch](fixes/51-coldguard-59.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/51-coldguard-59.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-51-coldguard-59.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-51-coldguard-59.html

## The bug

parse_csv_log turned a timestamp without a timezone into a number using the local timezone of the machine. The same vaccine temperature log could give different elapsed times on a different server or across a daylight saving change.

## The fix

parse_csv_log in core/utils.py gains a tz parameter with the default Asia/Kolkata as the bug report asks. A timestamp without an offset is read in that zone. A timestamp with an offset is respected. An unknown zone name gives a clear error. coldguard_cli.py gains --tz. tests/test_parse_csv.py gains tests that set the TZ environment variable to three zones and compare exact numbers. README.md and CHANGELOG.md describe the flag.

## Files changed

- CHANGELOG.md
- README.md
- coldguard_cli.py
- core/utils.py
- tests/test_parse_csv.py

## How to use the fix

1. Get a copy of the project Santhosh-zeta/ColdGuard.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 51-coldguard-59.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 59.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The default behaviour changes: a file with no offsets was read in the machine's zone before and is read as Asia/Kolkata now. The bug report asks for that default. The API in api/main.py uses the same default and gets no new parameter because the bug report lists only the core file and the command line. The fix uses Python's zoneinfo module. On Windows zoneinfo needs the tzdata package and the fix does not add tzdata to the requirements. The Hindi README is not updated. The chatbot confirmed the expected numbers in the tests with a scratch script.

## Search words

ColdGuard parse_csv_log naive timestamp timezone local zone --tz Asia/Kolkata DST dateutil zoneinfo vaccine cold chain

## The full patch

`````diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index 9877e8d..b30a423 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -17,6 +17,7 @@ All notable changes to ColdGuard are documented here. Format follows [Keep a Cha
 - `CITATION.cff`, `.editorconfig`, translation issue template, REST API docs
 
 ### Fixed
+- Timestamps without a timezone are now read in an explicit zone (`tz` on `parse_csv_log`, `--tz` on the CLI, default `Asia/Kolkata`) instead of the server's local zone, so the same CSV gives the same result on every machine and across a DST change; timestamps with an offset (`+05:30`, `Z`) are unaffected (#59)
 - CSV import now auto-detects the delimiter (comma, semicolon, tab, pipe), accepts decimal commas, a UTF-8 BOM and Windows (cp1252) files, works with in-memory input, and error messages list the columns that were found (#127; based on the approach in #138 by @MM071022)
 - Security: forced patched `minimatch` (>=11.0.5) and `glob` (>=14.0.4) for the mobile app's transitive dependencies via npm `overrides`, resolving two moderate Dependabot alerts (GHSA-g3hv-75wg-m249, GHSA-3g3m-2fjr-6pw4); mobile tests and the Android bundle verified
 - Readings that are NaN or infinite are rejected with a clear error (HTTP 422 on both `/analyse` and `/export/dhis2`) instead of reporting a NaN potency
diff --git a/README.md b/README.md
index 3a4f54c..ab56b20 100644
--- a/README.md
+++ b/README.md
@@ -171,6 +171,13 @@ PYTHONPATH=. python coldguard_cli.py \
     --input data/raw/extended_excursion_25c.csv \
     --vaccine OPV \
     --output report.json
+
+# Timestamps without a timezone are read as Asia/Kolkata on every machine;
+# name another IANA zone with --tz. Timestamps with an offset (+05:30, Z) are respected.
+PYTHONPATH=. python coldguard_cli.py \
+    --input data/raw/demo_dpt_power_outage.csv \
+    --vaccine DPT \
+    --tz UTC
 ```
 
 ### Python API
diff --git a/coldguard_cli.py b/coldguard_cli.py
index bdba6aa..2195d74 100644
--- a/coldguard_cli.py
+++ b/coldguard_cli.py
@@ -165,6 +165,9 @@ def main():
                         help="Logger uncertainty in °C (default 0.5)")
     parser.add_argument("--seed", type=int, default=None, metavar="N",
                         help="RNG seed for reproducible results")
+    parser.add_argument("--tz", default="Asia/Kolkata", metavar="ZONE",
+                        help="Timezone for timestamps that carry no offset, as an IANA name "
+                             "(default Asia/Kolkata). Timestamps with an offset are respected")
     parser.add_argument("--output", "-o", metavar="FILE",
                         help="Write full JSON result to FILE instead of stdout summary")
     parser.add_argument("--json", action="store_true",
@@ -188,7 +191,7 @@ def main():
         sys.exit(1)
 
     try:
-        timestamps, temperatures = parse_csv_log(str(csv_path))
+        timestamps, temperatures = parse_csv_log(str(csv_path), tz=args.tz)
     except Exception as exc:
         if args.validate_only and (args.json or args.output):
             err_report = {
diff --git a/core/utils.py b/core/utils.py
index 35ac9c2..8982e7f 100644
--- a/core/utils.py
+++ b/core/utils.py
@@ -7,6 +7,7 @@ from __future__ import annotations
 import io
 from pathlib import Path
 from typing import IO, Any, Dict, List, Optional, Tuple, Union
+from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
 
 import numpy as np
 import pandas as pd
@@ -65,12 +66,24 @@ def _detect_delimiter(text: str) -> str:
     return best if counts[best] > 0 else ","
 
 
-def parse_csv_log(filepath: Union[str, Path, IO]) -> Tuple[np.ndarray, np.ndarray]:
+#: Zone a timestamp without an offset is read in, unless the caller says otherwise.
+DEFAULT_TZ = "Asia/Kolkata"
+
+
+def parse_csv_log(
+    filepath: Union[str, Path, IO], tz: str = DEFAULT_TZ
+) -> Tuple[np.ndarray, np.ndarray]:
     """Parse a temperature log CSV (a path or an open text/binary file object).
 
     Expected columns: ``timestamp`` (ISO-8601 or Unix) and a temperature column
     (``temperature_celsius``, or any column name containing ``temp``).
 
+    A timestamp without a timezone is read in the zone ``tz`` (an IANA name,
+    default ``Asia/Kolkata``), never in the machine's local zone, so the same
+    file gives the same result on every server and across a DST change. A
+    timestamp that carries its own offset (``+05:30``, ``Z``) is respected, and
+    Unix timestamps are unaffected.
+
     Handles the common export variants automatically:
 
     - delimiter: comma, semicolon, tab or pipe (detected from the header line)
@@ -87,9 +100,16 @@ def parse_csv_log(filepath: Union[str, Path, IO]) -> Tuple[np.ndarray, np.ndarra
     Raises
     ------
     ValueError
-        If the file cannot be parsed. Messages name the columns that were found
-        or the offending row, so the user can fix the file.
+        If the file cannot be parsed, or ``tz`` is not a known timezone name.
+        Messages name the columns that were found or the offending row, so the
+        user can fix the file.
     """
+    try:
+        zone = ZoneInfo(tz)
+    except (ZoneInfoNotFoundError, ValueError, TypeError) as exc:
+        raise ValueError(
+            f"Unknown timezone {tz!r}. Use an IANA name such as 'Asia/Kolkata' or 'UTC'."
+        ) from exc
     text, label = _read_text(filepath)
     delimiter = _detect_delimiter(text)
     try:
@@ -118,8 +138,10 @@ def parse_csv_log(filepath: Union[str, Path, IO]) -> Tuple[np.ndarray, np.ndarra
     if pd.api.types.is_numeric_dtype(ts_raw):
         timestamps = ts_raw.values.astype(float)
     else:
+        parsed = (dtparser.parse(str(t)) for t in ts_raw)
         timestamps = np.array(
-            [dtparser.parse(str(t)).timestamp() for t in ts_raw], dtype=float
+            [(d if d.tzinfo is not None else d.replace(tzinfo=zone)).timestamp() for d in parsed],
+            dtype=float,
         )
 
     # Temperatures: numbers as-is; text columns may use a decimal comma ("5,2").
diff --git a/tests/test_parse_csv.py b/tests/test_parse_csv.py
index 7a95bd3..45d2a64 100644
--- a/tests/test_parse_csv.py
+++ b/tests/test_parse_csv.py
@@ -1,5 +1,6 @@
 """parse_csv_log must cope with the exports real loggers and spreadsheets produce."""
 import io
+import time
 
 import numpy as np
 import pytest
@@ -90,3 +91,51 @@ def test_non_numeric_temperature_names_the_row(tmp_path):
 def test_empty_file_is_a_value_error(tmp_path):
     with pytest.raises(ValueError):
         parse_text("", tmp_path=tmp_path)
+
+
+# --- timezone of timestamps without an offset ---------------------------------
+
+NAIVE = "timestamp,temperature_celsius\n2024-01-01T00:00:00,5.0\n2024-01-01T06:00:00,6.0\n"
+# 2024-01-01T00:00:00 in Asia/Kolkata (+05:30) is 2023-12-31T18:30:00Z.
+KOLKATA_MIDNIGHT = 1704047400.0
+UTC_MIDNIGHT = 1704067200.0
+
+
+def _set_tz(monkeypatch, name):
+    monkeypatch.setenv("TZ", name)
+    if hasattr(time, "tzset"):  # not on Windows
+        time.tzset()
+
+
+@pytest.fixture(autouse=True)
+def _restore_tz():
+    yield
+    if hasattr(time, "tzset"):
+        time.tzset()
+
+
+@pytest.mark.parametrize("machine_tz", ["UTC", "America/New_York", "Asia/Tokyo"])
+def test_naive_timestamps_do_not_depend_on_the_machine_timezone(monkeypatch, machine_tz):
+    _set_tz(monkeypatch, machine_tz)
+    ts, _ = parse_csv_log(io.StringIO(NAIVE))
+    assert ts.tolist() == [KOLKATA_MIDNIGHT, KOLKATA_MIDNIGHT + 6 * 3600]
+
+
+def test_tz_parameter_sets_the_zone_of_naive_timestamps(monkeypatch):
+    _set_tz(monkeypatch, "America/New_York")
+    ts, _ = parse_csv_log(io.StringIO(NAIVE), tz="UTC")
+    assert ts.tolist() == [UTC_MIDNIGHT, UTC_MIDNIGHT + 6 * 3600]
+
+
+@pytest.mark.parametrize("stamp", ["2024-01-01T00:00:00Z", "2024-01-01T05:30:00+05:30"])
+def test_timestamps_with_an_offset_are_respected(monkeypatch, stamp):
+    _set_tz(monkeypatch, "Asia/Tokyo")
+    text = f"timestamp,temperature_celsius\n{stamp},5.0\n"
+    for tz in ("Asia/Kolkata", "America/New_York"):
+        ts, _ = parse_csv_log(io.StringIO(text), tz=tz)
+        assert ts.tolist() == [UTC_MIDNIGHT]
+
+
+def test_unknown_timezone_is_a_clear_error():
+    with pytest.raises(ValueError, match="Unknown timezone 'Mars/Olympus'"):
+        parse_csv_log(io.StringIO(NAIVE), tz="Mars/Olympus")
`````

[Back to the shelf](README.md)
