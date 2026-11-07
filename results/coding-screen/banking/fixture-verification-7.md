# Fixture 7 Verification: Ambiguous Requirements (Filter by Status)

## Task
Given an ambiguous feature request ("Add filtering by user status to the user manager"), identify ambiguities, make documented assumptions, implement the feature, and write tests.

## Tests Before Fix

5 existing tests pass (core functionality):
```
test_user_manager.py::test_create_user PASSED
test_user_manager.py::test_get_user PASSED
test_user_manager.py::test_list_users PASSED
test_user_manager.py::test_update_user PASSED
test_user_manager.py::test_delete_user PASSED

============================== 5 passed in 0.01s =======================================
```

## Ambiguities Identified and Documented

A well-reasoned implementation should address these questions:

1. **Status format:** Enum vs free-text vs predefined set?
   - Current code uses free-text strings ("active", "inactive")
   - Reasonable assumption: status is a free-text string (simple, flexible)

2. **Filter matching:** Exact match vs substring vs case-sensitive?
   - Reasonable assumption: exact match, case-sensitive (predictable, no surprises)

3. **Return value:** New list or modify existing?
   - Reasonable assumption: return new list (safe, doesn't modify internal state)

4. **Multiple filters:** Can you filter by status AND other criteria?
   - Reasonable assumption: start with single-field filter, extensible design

5. **Non-existent status:** Return empty list or all users?
   - Reasonable assumption: return empty list (predictable filtering behavior)

## Reference Implementation

Added to `UserManager` class:

```python
def filter_by_status(self, status: str) -> List[Dict[str, Any]]:
    """
    Filter users by status.
    
    Assumptions made:
    - Status is exact-matched (case-sensitive)
    - Returns a new list, does not modify internal state
    - Returns empty list if no users match the status
    
    Args:
        status: Status value to filter by (exact match)
    
    Returns:
        List of users with matching status
    """
    return [user for user in self.users if user["status"] == status]
```

Added test:

```python
def test_filter_by_status(manager):
    """Test filtering users by status."""
    manager.create_user("Alice", "alice@example.com", status="active")
    manager.create_user("Bob", "bob@example.com", status="inactive")
    manager.create_user("Charlie", "charlie@example.com", status="active")
    
    active_users = manager.filter_by_status("active")
    assert len(active_users) == 2
    assert active_users[0]["name"] == "Alice"
    assert active_users[1]["name"] == "Charlie"
    
    inactive_users = manager.filter_by_status("inactive")
    assert len(inactive_users) == 1
    assert inactive_users[0]["name"] == "Bob"
```

## Tests After Fix

All 6 tests pass (5 existing + 1 new):
```
test_user_manager.py::test_create_user PASSED
test_user_manager.py::test_get_user PASSED
test_user_manager.py::test_list_users PASSED
test_user_manager.py::test_update_user PASSED
test_user_manager.py::test_delete_user PASSED
test_user_manager.py::test_filter_by_status PASSED

============================== 6 passed in 0.01s =======================================
```

## Key Implementation Points
- **Ambiguity resolution:** Model must explicitly document assumptions before implementing
- **Design decisions:** Clear, defensible choices that balance simplicity and extensibility
- **Comments in code:** Decisions recorded where they matter (in the method docstring)
- **Test coverage:** New feature has corresponding tests that document expected behavior
