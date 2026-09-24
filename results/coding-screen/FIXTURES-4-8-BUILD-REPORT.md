# Coding Model Screening Campaign: Fixtures 4-8 Build Report

**Date:** 2026-07-11  
**Builder:** Agent (automated)  
**Status:** Complete and verified

## Build Summary

Created 5 new self-contained practice repositories (fixtures 4-8) for coding model capability screening. Each fixture targets a distinct coding skill and includes:

- Clean main branch with no solution code committed
- Failing tests or incomplete code that makes the task clear
- README.md with natural-language task prompt
- .gitignore for Python/shell artifacts
- Test framework setup (pytest or bash)
- Verification banking documents proving tests fail before fix and pass after fix

## Fixtures Built

| Fixture | Type | Language | Task | Status |
|---------|------|----------|------|--------|
| 4 | Feature | Python | Add env var override support | Ready |
| 5 | Refactor | Python | Extract duplicate CSV parsing logic | Ready |
| 6 | Debug | Python | Fix ModuleNotFoundError | Ready |
| 7 | Ambiguous | Python | Implement filter with documented assumptions | Ready |
| 8 | Robustness | Bash | Fix fragile backup script | Ready |

## Locations

**Fixture Repositories:**
```
/home/agent-spark/sparkbench/spikes/coding-screen/fixtures/
├── fixture-4-feature/         (env var override)
├── fixture-5-refactor/        (DRY: extract common code)
├── fixture-6-debug/           (fix import error)
├── fixture-7-ambiguous/       (feature with ambiguities)
└── fixture-8-shell/           (shell robustness)
```

**Verification Evidence:**
```
/home/agent-spark/sparkbench/results/coding-screen/banking/
├── fixture-verification-4.md  (env var: 2 tests fail before, pass after)
├── fixture-verification-5.md  (refactor: 10 tests pass throughout)
├── fixture-verification-6.md  (debug: collection error before, pass after)
├── fixture-verification-7.md  (ambiguous: 5 core pass, +1 new test)
└── fixture-verification-8.md  (robustness: 4 tests fail before, pass after)
```

**Index and Documentation:**
```
/home/agent-spark/sparkbench/spikes/coding-screen/
└── FIXTURES-INDEX.md          (comprehensive reference)
```

## Verification Results

### Fixture 4: Feature Implementation (env var override)
- Tests before: 5 pass, 2 fail
- Root issue: Environment variable override logic not implemented
- Tests after fix: 7 pass (100%)

### Fixture 5: Code Refactoring (DRY)
- Tests before: 10 pass (regression gate)
- Root issue: 25 lines of duplicate CSV parsing logic across 2 modules
- Tests after fix: 10 pass (100%) - no regression

### Fixture 6: Debugging (import error)
- Tests before: collection fails with ModuleNotFoundError
- Root issue: Line 5 of config.py imports non-existent 'unknown_lib'
- Tests after fix: 4 pass (100%)

### Fixture 7: Ambiguous Requirements
- Tests before: 5 pass (core functionality)
- Root issue: Feature request needs interpretation; no filtering method exists
- Ambiguities resolved: status format, matching strategy, return behavior
- Tests after fix: 6 pass (100%) - core + new filtering test

### Fixture 8: Shell Robustness
- Tests before: 4 tests, 2 pass, 2 fail (spaces break unquoted variables; missing error checks)
- Root issues: Unquoted vars, no dest validation, bare for loops
- Tests after fix: 4 pass (100%)

## Acceptance Criteria Checklist

- [x] All fixtures have clean main branches
- [x] No solution code committed (incomplete/buggy states preserved)
- [x] Failing tests or incomplete code clearly indicate the task
- [x] All .gitignore files exclude __pycache__, .pytest_cache, build/
- [x] README.md in each fixture has natural-language task prompt
- [x] No spoilers in README (solution approach not described)
- [x] Test frameworks configured (pytest for Python, bash for shell)
- [x] All fixtures committed to repos with clear messages
- [x] Verification banking documents generated (before/after evidence)
- [x] No test modifications needed for screening (models work with provided tests)

## Key Characteristics

### Skill Progression
1. **Fixture 4** (Medium) - Extends existing code with new feature; tests provided
2. **Fixture 5** (Medium) - Identifies and eliminates duplication while maintaining tests
3. **Fixture 6** (Easy) - Locates and fixes obvious bug from traceback
4. **Fixture 7** (Medium) - Interprets vague requirement; documents design decisions
5. **Fixture 8** (Medium) - Shell best practices; edge case handling

### Test Coverage by Type
- **Failing-tests fixtures:** 4 (2 fail), 6 (collection error), 8 (2 fail)
- **Passing-tests fixtures:** 5 (refactor regression gate), 7 (core + new feature)

### Time-to-completion Estimate
- Fixture 4: ~15-20 minutes
- Fixture 5: ~15-20 minutes
- Fixture 6: ~5-10 minutes
- Fixture 7: ~20-25 minutes (interpretation + implementation + test)
- Fixture 8: ~15-20 minutes

## Setup Instructions for Screening

For each fixture:

```bash
cd /home/agent-spark/sparkbench/spikes/coding-screen/fixtures/fixture-N-*/
```

**Python fixtures (4, 5, 6, 7):**
```bash
pip install -r requirements.txt
pytest -v
```

**Shell fixture (8):**
```bash
bash test_backup.sh
```

## Notes

- All fixtures use pinned dependency versions (reproducible)
- Pre-commit hooks enforce TODO/STUB discipline (fixtures comply)
- Verification banking is internal to sparkbench (not distributed with fixtures)
- Each README clearly states the task without revealing the solution approach
- Test assertions are tight enough to fail on incomplete implementations
- Existing tests form a regression gate (models can't break working code)

## Next Steps

1. **Model Testing:** Submit fixtures to models for screening
2. **Evaluation:** Assess model's ability to:
   - Understand error messages and task descriptions
   - Implement features correctly
   - Maintain code quality and test coverage
   - Document design decisions (fixture 7)
   - Apply shell best practices (fixture 8)
3. **Feedback:** Analyze model performance across different task types
4. **Iteration:** Refine fixtures based on model performance patterns
