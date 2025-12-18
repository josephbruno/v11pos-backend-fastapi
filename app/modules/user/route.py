from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.response import success_response, error_response
from app.modules.user.model import User
from app.modules.user.schema import UserCreate, UserUpdate, UserResponse
from app.modules.user.service import UserService


router = APIRouter(prefix="/users", tags=["Users"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new user
    
    - **email**: Valid email address (unique)
    - **username**: Username (unique, 3-100 characters)
    - **password**: Password (minimum 6 characters)
    - **full_name**: Optional full name
    """
    try:
        # Check if email already exists
        existing_user = await UserService.get_user_by_email(db, user_data.email)
        if existing_user:
            return error_response(
                message="User creation failed",
                error_code="EMAIL_EXISTS",
                error_details="Email already exists"
            )
        
        # Check if username already exists
        existing_username = await UserService.get_user_by_username(db, user_data.username)
        if existing_username:
            return error_response(
                message="User creation failed",
                error_code="USERNAME_EXISTS",
                error_details="Username already exists"
            )
        
        user = await UserService.create_user(db, user_data)
        
        return success_response(
            message="User created successfully",
            data=UserResponse.model_validate(user).model_dump()
        )
    
    except IntegrityError:
        return error_response(
            message="User creation failed",
            error_code="INTEGRITY_ERROR",
            error_details="Email or username already exists"
        )
    except Exception as e:
        return error_response(
            message="User creation failed",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.get("", response_model=None)
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of users (requires authentication)
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    """
    try:
        users = await UserService.get_users(db, skip=skip, limit=limit)
        users_data = [UserResponse.model_validate(user).model_dump() for user in users]
        
        return success_response(
            message="Users retrieved successfully",
            data=users_data
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve users",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.get("/restaurant/{restaurant_id}", response_model=None)
async def get_users_by_restaurant(
    restaurant_id: str,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of users by restaurant ID (requires authentication)
    
    - **restaurant_id**: Restaurant ID to filter users
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    """
    try:
        users = await UserService.get_users_by_restaurant(
            db,
            restaurant_id,
            skip=skip,
            limit=limit
        )
        users_data = [UserResponse.model_validate(user).model_dump() for user in users]
        
        return success_response(
            message=f"Users retrieved successfully for restaurant {restaurant_id}",
            data={
                "restaurant_id": restaurant_id,
                "count": len(users_data),
                "users": users_data
            }
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve users by restaurant",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.get("/me", response_model=None)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current authenticated user information
    """
    return success_response(
        message="User retrieved successfully",
        data=UserResponse.model_validate(current_user).model_dump()
    )


@router.get("/{user_id}", response_model=None)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get user by ID (requires authentication)
    """
    try:
        user = await UserService.get_user_by_id(db, user_id)
        
        if not user:
            return error_response(
                message="User not found",
                error_code="USER_NOT_FOUND",
                error_details=f"User with ID {user_id} does not exist"
            )
        
        return success_response(
            message="User retrieved successfully",
            data=UserResponse.model_validate(user).model_dump()
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve user",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.put("/{user_id}", response_model=None)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update user (requires authentication)
    """
    try:
        # Check if user is updating their own profile or is superuser
        if current_user.id != user_id and not current_user.is_superuser:
            return error_response(
                message="Update failed",
                error_code="FORBIDDEN",
                error_details="You can only update your own profile"
            )
        
        user = await UserService.update_user(db, user_id, user_data)
        
        if not user:
            return error_response(
                message="User not found",
                error_code="USER_NOT_FOUND",
                error_details=f"User with ID {user_id} does not exist"
            )
        
        return success_response(
            message="User updated successfully",
            data=UserResponse.model_validate(user).model_dump()
        )
    except IntegrityError:
        return error_response(
            message="Update failed",
            error_code="INTEGRITY_ERROR",
            error_details="Email or username already exists"
        )
    except Exception as e:
        return error_response(
            message="Failed to update user",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.delete("/{user_id}", response_model=None)
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete user (requires superuser privileges)
    """
    try:
        if not current_user.is_superuser:
            return error_response(
                message="Delete failed",
                error_code="FORBIDDEN",
                error_details="Only superusers can delete users"
            )
        
        deleted = await UserService.delete_user(db, user_id)
        
        if not deleted:
            return error_response(
                message="User not found",
                error_code="USER_NOT_FOUND",
                error_details=f"User with ID {user_id} does not exist"
            )
        
        return success_response(
            message="User deleted successfully",
            data={"deleted_user_id": user_id}
        )
    except Exception as e:
        return error_response(
            message="Failed to delete user",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )
