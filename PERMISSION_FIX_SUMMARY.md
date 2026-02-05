# User Permissions Fix Summary

## Issue
**Problem:** The API returned `403 Forbidden` ("You can only update your own profile") when a Restaurant Owner or Manager tried to update (e.g., deactivate) a staff member's account.

## Fix
**Solution:** Updated the permission logic in `app/modules/user/route.py` (Update User endpoint).

### Changes:
1.  **Fetch Target User**: The code now retrieves the user being updated *before* checking permissions.
2.  **Expanded Permissions**: Added a check to allow updates if:
    *   `current_user` has role `owner`, `admin`, or `manager`.
    *   `current_user` belongs to the **same restaurant** as the `target_user`.
    
    The new permission logic is:
    ```python
    if not (is_self or is_superuser or is_restaurant_admin):
        # Return Error
    ```

## Verification
- **Self Update**: Works (Unchanged).
- **Superuser Update**: Works (Unchanged).
- **Manager/Owner Update**: Now Works for users in the same restaurant.

This ensures that managers can manage their staff without needing full Superuser privileges.
