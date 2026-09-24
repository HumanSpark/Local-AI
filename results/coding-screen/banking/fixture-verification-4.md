# Fixture 4 Verification: Feature Implementation (Environment Variable Overrides)

## Task
Add support for environment variable overrides in the YAML config loader. Environment variables named `APP_{KEY_NAME}` (uppercase, underscores replacing dots) should override YAML values.

## Tests Before Fix

When running `pytest test_config.py -v`, two new tests fail:

```
test_config.py::test_env_var_override FAILED
test_config.py::test_env_var_override_nested_key FAILED
```

### Failure Details
- `test_env_var_override`: Expected `config.get("database.host")` to return `"overridden-host"` when `APP_DATABASE_HOST` is set, but got `"localhost"` (from YAML)
- `test_env_var_override_nested_key`: Expected `config.get("app.name")` to return `"OverriddenApp"` when `APP_APP_NAME` is set, but got `"MyApp"` (from YAML)

### Existing Tests Status
5 existing tests pass before implementing the feature:
- test_load_config: PASSED
- test_get_top_level_key: PASSED
- test_get_nested_key: PASSED
- test_get_with_default: PASSED
- test_file_not_found: PASSED

## Reference Fix Applied

Modified `config.py` `get()` method to check environment variables before returning YAML values:

```python
def get(self, key: str, default: Any = None) -> Any:
    # Check for environment variable override
    env_key = f"APP_{key.upper().replace('.', '_')}"
    if env_key in os.environ:
        return os.environ[env_key]
    
    # ... rest of YAML lookup logic
```

## Tests After Fix

All 7 tests pass:

```
test_config.py::test_load_config PASSED
test_config.py::test_get_top_level_key PASSED
test_config.py::test_get_nested_key PASSED
test_config.py::test_get_with_default PASSED
test_config.py::test_file_not_found PASSED
test_config.py::test_env_var_override PASSED
test_config.py::test_env_var_override_nested_key PASSED

============================== 7 passed in 0.02s =======================================
```

## Key Implementation Points
- Environment variable names are built with `APP_` prefix + uppercase key with underscores replacing dots
- Environment variables override YAML values when present
- Missing environment variables fall through to YAML lookup
- Default values still work as before
