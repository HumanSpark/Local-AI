# Fixture 5 Verification: Refactoring (Extract Duplicate Code)

## Task
Identify duplicate CSV parsing logic in `module_a.py` and `module_b.py`, extract the common function into `shared.py`, and refactor both modules to use it.

## Tests Before Fix

All 10 tests pass before refactoring:
```
test_module_a.py::test_parse_csv PASSED
test_module_a.py::test_normalize_keys PASSED
test_module_a.py::test_convert_integers PASSED
test_module_a.py::test_preserve_non_numeric PASSED
test_module_a.py::test_empty_csv PASSED
test_module_b.py::test_parse_csv PASSED
test_module_b.py::test_normalize_keys PASSED
test_module_b.py::test_convert_integers PASSED
test_module_b.py::test_preserve_non_numeric PASSED
test_module_b.py::test_empty_csv PASSED

============================== 10 passed in 0.02s =======================================
```

## Duplication Identified

Both `module_a.py` and `module_b.py` (lines 8-33) contained identical logic:
- CSV parsing with `csv.DictReader`
- Key normalization (lowercase + strip whitespace)
- Integer conversion for numeric strings
- Building result list of normalized dictionaries

## Reference Fix Applied

1. **Created `shared.py`** with common function `normalize_csv_data()`
2. **Updated `module_a.py`** to import and use the shared function:
   ```python
   from shared import normalize_csv_data
   
   def process_data_a(data_string: str) -> List[Dict[str, Any]]:
       return normalize_csv_data(data_string)
   ```
3. **Updated `module_b.py`** identically to use the shared function

## Tests After Fix

All 10 tests still pass (regression gate confirmed):
```
test_module_a.py::test_parse_csv PASSED
test_module_a.py::test_normalize_keys PASSED
test_module_a.py::test_convert_integers PASSED
test_module_a.py::test_preserve_non_numeric PASSED
test_module_a.py::test_empty_csv PASSED
test_module_b.py::test_parse_csv PASSED
test_module_b.py::test_normalize_keys PASSED
test_module_b.py::test_convert_integers PASSED
test_module_b.py::test_preserve_non_numeric PASSED
test_module_b.py::test_empty_csv PASSED

============================== 10 passed in 0.01s =======================================
```

## Key Implementation Points
- Public API unchanged: `process_data_a()` and `process_data_b()` signatures identical
- All existing tests pass without modification (true regression gate)
- 25 lines of duplication eliminated
- Code now maintainable: changes to parsing logic only need to be made in one place
