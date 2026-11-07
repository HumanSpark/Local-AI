# Fixture 8 Verification: Shell Robustness (Backup Script)

## Task
Fix a fragile shell script that breaks on filenames with spaces and lacks proper error handling. Run tests iteratively until they all pass.

## Tests Before Fix

Running `bash test_backup.sh` shows 4 test failures:

```
Running backup.sh tests...
==============================
Testing files with spaces... FAIL - files not copied
Testing missing destination error handling... FAIL - should error on missing dest
Testing files with special characters... FAIL - not all files copied
Testing directory skipping... FAIL - backup script failed
==============================
Results: 0 passed, 4 failed
```

## Root Causes Identified

1. **Spaces in filenames break unquoted variables:**
   - Line 17: `for f in $DIR/*` → works
   - Line 19: `cp $f $DEST/` → **BREAKS** because unquoted `$f` with spaces gets split
   - Example: `cp /tmp/file with spaces.txt /tmp/dest/` becomes `cp /tmp/file with spaces.txt /tmp/dest/`

2. **No error checking for missing destination:**
   - Line 24: Warns but continues even if destination doesn't exist
   - Should fail with clear error message

3. **Unquoted variable in directory test:**
   - Line 31: `if [ -d $f ]` should be `if [ -d "$f" ]`

4. **Bare glob expansion issue:**
   - `for f in $DIR/*` works in this case but is fragile

## Reference Fix Applied

Rewrote `backup.sh` with robust patterns:

```bash
#!/bin/bash
set -e

DIR="${1:-.}"
DEST="${2:-.}"

# Add error checking upfront
if [ ! -d "$DIR" ]; then
    echo "Error: source directory does not exist: $DIR" >&2
    exit 1
fi

if [ ! -d "$DEST" ]; then
    echo "Error: destination directory does not exist: $DEST" >&2
    exit 1
fi

echo "Backing up from $DIR to $DEST"

# Use find + while read for proper handling of special chars
find "$DIR" -maxdepth 1 -type f -print0 | while IFS= read -r -d '' f; do
    if [ -f "$f" ]; then
        cp "$f" "$DEST/"
        echo "Copied $(basename "$f")"
    fi
done

echo "Backup complete"
```

**Key improvements:**
- Proper quoting: `"$DIR"`, `"$DEST"`, `"$f"`
- Error handling: Checks destination exists before operating
- Robust iteration: `find ... -print0 | while read -d ''` handles any filename
- Clear error messages: Sent to stderr with exit codes

## Tests After Fix

All 4 tests pass:

```
Running backup.sh tests...
==============================
Testing files with spaces... PASS
Testing missing destination error handling... PASS
Testing files with special characters... PASS
Testing directory skipping... PASS
==============================
Results: 4 passed, 0 failed
```

## Key Shell Scripting Practices
1. **Always quote variables:** `"$var"` not `$var`
2. **Check prerequisites:** Verify dirs/files exist before operations
3. **Use find + read for safety:** Handles arbitrary filenames
4. **Explicit error handling:** `set -e`, explicit checks, clear messages
5. **Send errors to stderr:** Use `>&2` for error output
6. **Exit codes matter:** Return non-zero on failure
