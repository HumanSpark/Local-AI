# Fixture 6 Verification: Debugging (Import Error)

## Task
Run failing tests, diagnose the error from the traceback, find and fix the bug in the source code.

## Tests Before Fix

Running `pytest test_app.py -v` fails with:

```
============================= test session starts ==============================
...
test_app.py:9: in <module>
    from app import App
app.py:5: in <module>
    from config import load_config
config.py:5: in <module>
    import unknown_lib
E   ModuleNotFoundError: No module named 'unknown_lib'
=========================== short test summary info ============================
ERROR test_app.py
========================= 1 error during collection ===========================
```

## Error Diagnosis

**Root Cause:** Line 5 of `config.py` imports a non-existent module `unknown_lib`:

```python
import unknown_lib  # This line is wrong
import json
```

This is a typo or leftover import. The module is never used, and the second import (`json`) is the one actually needed.

**Traceback Analysis:**
- Error occurs during test collection (when importing modules)
- Collection stops before any tests can run
- Stack shows: test_app.py → app.py → config.py → ModuleNotFoundError

## Reference Fix Applied

Removed the erroneous import from `config.py`:

```python
# Before:
import unknown_lib
import json

# After:
import json
```

## Tests After Fix

All 4 tests pass:

```
test_app.py::test_app_initialization PASSED
test_app.py::test_app_loads_config PASSED
test_app.py::test_app_get_setting PASSED
test_app.py::test_app_get_setting_default PASSED

============================== 4 passed in 0.01s =======================================
```

## Key Learning Points
- **Error traceback reading:** The bottom of the traceback shows the immediate cause; work upward to find the import chain
- **Collection vs runtime:** Collection errors happen before tests run; they indicate import/syntax issues
- **Dead code detection:** Unused imports like `unknown_lib` should be removed immediately
