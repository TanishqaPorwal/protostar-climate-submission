"""Compare rebuilt outputs/ with the committed versions, value by value.

Usage (after export.py and policy_analysis.py):  python code/compare_outputs.py
Values are rounded to 2 decimals, so floating-point differences between platforms can move
the last digit by 0.01. That is allowed; anything larger, or any change in rows, columns,
city IDs, names or flags, fails.
"""

import io
import json
import os
import subprocess
import sys

import pandas as pd

TOL = 0.0101
CI = os.environ.get("GITHUB_ACTIONS") == "true"


def note(msg: str, level: str = "notice") -> None:
    """Print; on GitHub Actions also as an annotation, which is visible without opening the log."""
    print(f"::{level}::{msg}" if CI else f"  {msg}")


def committed(path: str) -> str:
    return subprocess.run(["git", "show", f"HEAD:{path}"], capture_output=True, text=True, check=True).stdout


def compare_frames(new: pd.DataFrame, old: pd.DataFrame, label: str) -> list[str]:
    if list(new.columns) != list(old.columns) or len(new) != len(old):
        return [f"{label}: shape or columns changed ({new.shape} vs {old.shape})"]
    # Row order is not part of the content: cdd_change_by_city.csv is sorted by a rounded
    # percentage, and ties come out in a different order on different platforms.
    key = [c for c in ("city_id", "year") if c in new.columns]
    new, old = (f.sort_values(key).reset_index(drop=True) for f in (new, old))
    problems = []
    for col in new.columns:
        a, b = new[col], old[col]
        if pd.api.types.is_float_dtype(a) and pd.api.types.is_float_dtype(b):
            diff = (a - b).abs()
            bad = ~((diff <= TOL) | (a.isna() & b.isna()))
            if bad.any():
                problems.append(f"{label}.{col}: {bad.sum()} values differ, max {diff.max():.4f}")
            elif diff.max() > 0:
                note(f"{label}.{col}: {(diff > 0).sum()} values differ by at most {diff.max():.4f} (allowed)")
        elif not a.astype(str).equals(b.astype(str)):
            problems.append(f"{label}.{col}: non-numeric values changed")
    return problems


def geo_frame(text: str) -> pd.DataFrame:
    return pd.DataFrame([{**f["properties"], "lon": f["geometry"]["coordinates"][0],
                          "lat": f["geometry"]["coordinates"][1]} for f in json.loads(text)["features"]])


problems = []
try:
  for path in ["outputs/forecasts_wide.csv", "outputs/cdd_change_by_city.csv"]:
    problems += compare_frames(pd.read_csv(path), pd.read_csv(io.StringIO(committed(path))), path)
  path = "outputs/forecasts.geojson"
  problems += compare_frames(geo_frame(open(path).read()), geo_frame(committed(path)), path)
except Exception as e:  # report crashes as an annotation too
  problems.append(f"comparison crashed: {type(e).__name__}: {e}")

if problems:
    for msg in problems:
        note(msg, "error")
    sys.exit("Outputs changed:\n- " + "\n- ".join(problems))
print("OK: rebuilt outputs/ match the committed files (within 0.01 rounding).")
