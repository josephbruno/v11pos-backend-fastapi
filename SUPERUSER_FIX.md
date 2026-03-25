# Permission Logic Fix

## Issue
**Problem:** The `superadmin@restaurant.com` user was receiving `403 Forbidden` ("You do not have permission to update this user") when attempting to update other users.
**Cause:** The user record in the database had `is_superuser=False` but `is_superadmin=True`. The code was **only** checking `current_user.is_superuser`.

## Fix
**Solution:** Updated `app/modules/user/route.py` to check both flags.

```python
is_superuser = current_user.is_superuser or current_user.is_superadmin
```

This ensures that any user marked as `is_superadmin` (regardless of `is_superuser` flag) has full access privileges as expected.

## Verification
- Can now update any user when logged in as "Super Admin".
- Debug prints removed.
