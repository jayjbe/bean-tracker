---
title: NaN and Infinity Bypass Positive Float Validation and Corrupt SQLite Inventory
date: 2026-06-22
category: logic-errors
module: input validation
problem_type: logic_error
component: tooling
symptoms:
  - Adding a bean with pounds=nan stores nan in SQLite without error
  - Adding a bean with pounds=inf stores inf in SQLite without error
  - Inventory list displays nan or inf in the Lbs column with no prior warning
root_cause: missing_validation
resolution_type: code_fix
severity: high
tags:
  - python
  - input-validation
  - ieee754
  - sqlite-corruption
  - float
---

# NaN and Infinity Bypass Positive Float Validation and Corrupt SQLite Inventory

## Problem

`_parse_positive_float` accepted `nan` and `inf` as valid user input because the positive-number guard `f <= 0` relies on comparison operators that do not work correctly for IEEE 754 special values. Both values were silently stored in SQLite's REAL column and displayed as garbage in the inventory listing.

## Symptoms

- `python beans.py add "Ethiopia" Ethiopia light nan` succeeded silently, storing `nan` in the database
- `python beans.py add "Ethiopia" Ethiopia light inf` succeeded silently, storing `inf` in the database
- The inventory listing displayed "nan" or "inf" in the Lbs column with no validation error ever raised

## What Didn't Work

- The existing `f <= 0` guard: `float('nan') <= 0` evaluates to `False` in Python (all IEEE 754 comparisons with NaN return `False`), so NaN passes as if it were a valid positive number. `float('inf') > 0` is `True`, so infinity also passes — the guard was never designed to exclude non-finite values.

## Solution

Add a `math.isfinite` check before the positivity check. `math` is in the standard library; no new dependency needed.

```python
import math

def _parse_positive_float(value, field="pounds"):
    try:
        f = float(value)
    except ValueError:
        print(f"Error: {field} must be a number.", file=sys.stderr)
        sys.exit(1)
    if not math.isfinite(f):
        print(f"Error: {field} must be a finite number.", file=sys.stderr)
        sys.exit(1)
    if f <= 0:
        print(f"Error: {field} must be a positive number.", file=sys.stderr)
        sys.exit(1)
    return f
```

The two guards are intentionally kept separate so the error messages remain distinct and actionable.

## Why This Works

IEEE 754 defines three categories of non-finite floating-point values: positive infinity, negative infinity, and NaN (Not a Number). Python's `float()` constructor produces all three from the string literals `"inf"`, `"-inf"`, and `"nan"`. Comparison operators (`<`, `<=`, `>`, `>=`) are defined to return `False` for any comparison involving NaN, which means a guard written as `f <= 0` cannot catch it. `math.isfinite(f)` bypasses comparison entirely — it inspects the IEEE 754 bit pattern directly and returns `True` only for ordinary finite numbers. This makes it the correct and idiomatic way to reject all special float values in a single check before any arithmetic or comparison is performed.

## Prevention

- Any function that parses a float from external input and applies a domain constraint must call `math.isfinite` before the domain check, not after. The pattern is: **parse → finite check → domain check**.
- Add paired unit tests for the `"nan"` and `"inf"` string literals whenever writing a float validator. The test names `test_nan_rejected` and `test_inf_rejected` make the intent explicit and catch regressions if the guard is ever rewritten.
- Do not rely on SQLite's `REAL` column type to reject non-finite values. SQLite stores Python's `nan` and `inf` without error and displays them as strings in query results.
- The same bug pattern applies to any numeric validator written with only a sign/magnitude check. If the code parses a user-supplied float and checks `> 0`, `< limit`, or `== expected`, add `math.isfinite()` first.

## Related Issues

- None (first occurrence in this repo)
