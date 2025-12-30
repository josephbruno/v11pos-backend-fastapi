from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import date

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.staff.service import StaffService
from app.modules.staff.schema import (
    RoleCreate, RoleUpdate, RoleResponse,
    StaffCreate, StaffUpdate, StaffResponse,
    ShiftCreate, ShiftUpdate, ShiftResponse,
    AttendanceCheckIn, AttendanceCheckOut, AttendanceManualEntry,
    AttendanceUpdate, AttendanceResponse,
    LeaveApplicationCreate, LeaveApplicationUpdate, LeaveApproval,
    LeaveApplicationResponse, LeaveBalanceResponse
)
from app.modules.staff.model import AttendanceStatus, LeaveStatus


router = APIRouter(prefix="/staff", tags=["Staff Management"])


# ============= Role Management Endpoints =============

@router.post("/roles", response_model=RoleResponse, status_code=201)
async def create_role(
    role_data: RoleCreate,
    restaurant_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new role with permissions.
    Requires CREATE_STAFF permission.
    """
    return await StaffService.create_role(
        db=db,
        restaurant_id=restaurant_id,
        role_data=role_data,
        user_id=current_user["id"]
    )


@router.get("/roles/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get role by ID with permissions"""
    role = await StaffService.get_role_by_id(db, role_id)
    if not role:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    return role


@router.get("/roles/restaurant/{restaurant_id}", response_model=List[RoleResponse])
async def get_restaurant_roles(
    restaurant_id: str,
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all roles for a restaurant"""
    return await StaffService.get_roles_by_restaurant(
        db=db,
        restaurant_id=restaurant_id,
        is_active=is_active,
        skip=skip,
        limit=limit
    )


@router.put("/roles/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: str,
    role_data: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update role details and permissions"""
    return await StaffService.update_role(
        db=db,
        role_id=role_id,
        role_data=role_data,
        user_id=current_user["id"]
    )


# ============= Staff Management Endpoints =============

@router.post("/members", response_model=StaffResponse, status_code=201)
async def create_staff(
    staff_data: StaffCreate,
    restaurant_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new staff member.
    Requires CREATE_STAFF permission.
    """
    return await StaffService.create_staff(
        db=db,
        restaurant_id=restaurant_id,
        staff_data=staff_data,
        user_id=current_user["id"]
    )


@router.get("/members/{staff_id}", response_model=StaffResponse)
async def get_staff(
    staff_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get staff member by ID"""
    staff = await StaffService.get_staff_by_id(db, staff_id)
    if not staff:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff not found"
        )
    return staff


@router.get("/members/code/{employee_code}", response_model=StaffResponse)
async def get_staff_by_code(
    employee_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get staff member by employee code"""
    staff = await StaffService.get_staff_by_employee_code(db, employee_code)
    if not staff:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff not found"
        )
    return staff


@router.get("/members/restaurant/{restaurant_id}", response_model=List[StaffResponse])
async def get_restaurant_staff(
    restaurant_id: str,
    role_id: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all staff members for a restaurant.
    Supports filtering by role, department, active status, and search.
    """
    return await StaffService.get_staff_by_restaurant(
        db=db,
        restaurant_id=restaurant_id,
        role_id=role_id,
        department=department,
        is_active=is_active,
        search=search,
        skip=skip,
        limit=limit
    )


@router.put("/members/{staff_id}", response_model=StaffResponse)
async def update_staff(
    staff_id: str,
    staff_data: StaffUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update staff member details"""
    return await StaffService.update_staff(
        db=db,
        staff_id=staff_id,
        staff_data=staff_data,
        user_id=current_user["id"]
    )


@router.delete("/members/{staff_id}", status_code=204)
async def delete_staff(
    staff_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Deactivate staff member (soft delete).
    Sets is_active=False and date_of_leaving.
    """
    await StaffService.delete_staff(db, staff_id)
    return None


# ============= Shift Management Endpoints =============

@router.post("/shifts", response_model=ShiftResponse, status_code=201)
async def create_shift(
    shift_data: ShiftCreate,
    restaurant_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a shift for staff member.
    Requires MANAGE_SETTINGS permission.
    """
    return await StaffService.create_shift(
        db=db,
        restaurant_id=restaurant_id,
        shift_data=shift_data,
        user_id=current_user["id"]
    )


@router.get("/shifts/restaurant/{restaurant_id}", response_model=List[ShiftResponse])
async def get_shifts(
    restaurant_id: str,
    start_date: date = Query(...),
    end_date: date = Query(...),
    staff_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get shifts for date range. Optionally filter by staff."""
    return await StaffService.get_shifts_by_date_range(
        db=db,
        restaurant_id=restaurant_id,
        start_date=start_date,
        end_date=end_date,
        staff_id=staff_id
    )


# ============= Attendance Management Endpoints =============

@router.post("/attendance/check-in", response_model=AttendanceResponse, status_code=201)
async def check_in(
    check_in_data: AttendanceCheckIn,
    request: Request,
    restaurant_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Staff check-in.
    Records check-in time, location, and IP address.
    """
    ip_address = request.client.host if request.client else None
    return await StaffService.check_in(
        db=db,
        restaurant_id=restaurant_id,
        check_in_data=check_in_data,
        ip_address=ip_address
    )


@router.post("/attendance/{attendance_id}/check-out", response_model=AttendanceResponse)
async def check_out(
    attendance_id: str,
    check_out_data: AttendanceCheckOut,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Staff check-out.
    Records check-out time, calculates hours worked and overtime.
    """
    ip_address = request.client.host if request.client else None
    return await StaffService.check_out(
        db=db,
        attendance_id=attendance_id,
        check_out_data=check_out_data,
        ip_address=ip_address
    )


@router.post("/attendance/manual", response_model=AttendanceResponse, status_code=201)
async def create_manual_attendance(
    attendance_data: AttendanceManualEntry,
    restaurant_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create manual attendance entry.
    Requires MANAGE_SETTINGS permission.
    """
    return await StaffService.create_manual_attendance(
        db=db,
        restaurant_id=restaurant_id,
        attendance_data=attendance_data,
        user_id=current_user["id"]
    )


@router.get("/attendance/restaurant/{restaurant_id}", response_model=List[AttendanceResponse])
async def get_attendance(
    restaurant_id: str,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    staff_id: Optional[str] = Query(None),
    status: Optional[AttendanceStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get attendance records with filters.
    Filter by date range, staff, and status.
    """
    return await StaffService.get_attendance_by_restaurant(
        db=db,
        restaurant_id=restaurant_id,
        start_date=start_date,
        end_date=end_date,
        staff_id=staff_id,
        status=status,
        skip=skip,
        limit=limit
    )


# ============= Leave Management Endpoints =============

@router.post("/leave-applications", response_model=LeaveApplicationResponse, status_code=201)
async def create_leave_application(
    leave_data: LeaveApplicationCreate,
    restaurant_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create leave application.
    Automatically calculates total days and checks leave balance.
    """
    return await StaffService.create_leave_application(
        db=db,
        restaurant_id=restaurant_id,
        leave_data=leave_data
    )


@router.post("/leave-applications/{leave_id}/approve", response_model=LeaveApplicationResponse)
async def approve_leave(
    leave_id: str,
    approval_data: LeaveApproval,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Approve or reject leave application.
    Requires APPROVE_LEAVE permission.
    Updates leave balance if approved.
    """
    return await StaffService.approve_leave(
        db=db,
        leave_id=leave_id,
        approval_data=approval_data,
        user_id=current_user["id"]
    )


@router.get("/leave-balance/{staff_id}", response_model=List[LeaveBalanceResponse])
async def get_leave_balance(
    staff_id: str,
    year: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get leave balance for staff member.
    If year not provided, returns current year balance.
    """
    return await StaffService.get_leave_balance(
        db=db,
        staff_id=staff_id,
        year=year
    )
