from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime, date, time
from app.modules.staff.model import (
    UserRole, PermissionType, ShiftType, AttendanceStatus, 
    LeaveType, LeaveStatus
)


# ============= Role Schemas =============

class RolePermissionCreate(BaseModel):
    permission: PermissionType


class RolePermissionResponse(BaseModel):
    id: str
    permission: PermissionType
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    code: UserRole
    description: Optional[str] = None
    level: int = Field(default=0, ge=0, le=10)
    permissions: List[PermissionType] = []


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    level: Optional[int] = Field(None, ge=0, le=10)
    is_active: Optional[bool] = None
    permissions: Optional[List[PermissionType]] = None


class RoleResponse(BaseModel):
    id: str
    restaurant_id: str
    name: str
    code: UserRole
    description: Optional[str]
    level: int
    is_system_role: bool
    is_active: bool
    permissions: List[RolePermissionResponse] = []
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============= Staff Schemas =============

class StaffCreate(BaseModel):
    user_id: Optional[str] = None
    role_id: str
    
    # Personal Information
    employee_code: str = Field(..., min_length=2, max_length=50)
    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone: str = Field(..., min_length=10, max_length=20)
    alternate_phone: Optional[str] = None
    
    # Address
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "India"
    
    # Emergency Contact
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    
    # Employment Details
    date_of_joining: date
    employment_type: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    
    # Salary Information (in rupees, will be converted to paise)
    basic_salary: Optional[float] = None
    allowances: Optional[float] = None
    
    # Documents
    aadhar_number: Optional[str] = None
    pan_number: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_name: Optional[str] = None
    bank_ifsc_code: Optional[str] = None
    
    # Work Schedule
    default_shift_type: Optional[ShiftType] = None
    working_days_per_week: int = 6
    
    # Profile
    photo_url: Optional[str] = None
    notes: Optional[str] = None


class StaffUpdate(BaseModel):
    role_id: Optional[str] = None
    first_name: Optional[str] = Field(None, min_length=2, max_length=100)
    last_name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    alternate_phone: Optional[str] = None
    
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    
    date_of_leaving: Optional[date] = None
    employment_type: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    
    basic_salary: Optional[float] = None
    allowances: Optional[float] = None
    
    aadhar_number: Optional[str] = None
    pan_number: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_name: Optional[str] = None
    bank_ifsc_code: Optional[str] = None
    
    default_shift_type: Optional[ShiftType] = None
    working_days_per_week: Optional[int] = None
    
    is_active: Optional[bool] = None
    photo_url: Optional[str] = None
    notes: Optional[str] = None


class StaffResponse(BaseModel):
    id: str
    restaurant_id: str
    user_id: Optional[str]
    role_id: str
    
    employee_code: str
    first_name: str
    last_name: str
    email: Optional[str]
    phone: str
    alternate_phone: Optional[str]
    
    address_line1: Optional[str]
    address_line2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    postal_code: Optional[str]
    country: str
    
    emergency_contact_name: Optional[str]
    emergency_contact_phone: Optional[str]
    emergency_contact_relation: Optional[str]
    
    date_of_joining: date
    date_of_leaving: Optional[date]
    employment_type: Optional[str]
    department: Optional[str]
    designation: Optional[str]
    
    basic_salary: Optional[int]
    allowances: Optional[int]
    total_salary: Optional[int]
    
    aadhar_number: Optional[str]
    pan_number: Optional[str]
    bank_account_number: Optional[str]
    bank_name: Optional[str]
    bank_ifsc_code: Optional[str]
    
    default_shift_type: Optional[ShiftType]
    working_days_per_week: int
    
    is_active: bool
    is_on_leave: bool
    photo_url: Optional[str]
    notes: Optional[str]
    
    created_at: datetime
    updated_at: datetime
    
    role: Optional[RoleResponse] = None
    
    model_config = ConfigDict(from_attributes=True)


# ============= Shift Schemas =============

class ShiftCreate(BaseModel):
    staff_id: str
    shift_date: date
    shift_type: ShiftType
    start_time: time
    end_time: time
    break_duration_minutes: int = 0
    notes: Optional[str] = None


class ShiftUpdate(BaseModel):
    shift_type: Optional[ShiftType] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    break_duration_minutes: Optional[int] = None
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    is_completed: Optional[bool] = None
    notes: Optional[str] = None


class ShiftResponse(BaseModel):
    id: str
    restaurant_id: str
    staff_id: str
    shift_date: date
    shift_type: ShiftType
    start_time: time
    end_time: time
    break_duration_minutes: int
    actual_start_time: Optional[datetime]
    actual_end_time: Optional[datetime]
    is_assigned: bool
    is_completed: bool
    notes: Optional[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============= Attendance Schemas =============

class AttendanceCheckIn(BaseModel):
    staff_id: str
    shift_id: Optional[str] = None
    check_in_location: Optional[str] = None
    remarks: Optional[str] = None


class AttendanceCheckOut(BaseModel):
    check_out_location: Optional[str] = None
    remarks: Optional[str] = None


class AttendanceManualEntry(BaseModel):
    staff_id: str
    attendance_date: date
    check_in_time: datetime
    check_out_time: Optional[datetime] = None
    status: AttendanceStatus = AttendanceStatus.PRESENT
    remarks: Optional[str] = None


class AttendanceUpdate(BaseModel):
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    status: Optional[AttendanceStatus] = None
    remarks: Optional[str] = None
    is_approved: Optional[bool] = None


class AttendanceResponse(BaseModel):
    id: str
    restaurant_id: str
    staff_id: str
    shift_id: Optional[str]
    attendance_date: date
    check_in_time: Optional[datetime]
    check_out_time: Optional[datetime]
    total_hours_worked: Optional[float]
    overtime_hours: Optional[float]
    status: AttendanceStatus
    is_late: bool
    late_by_minutes: int
    check_in_location: Optional[str]
    check_out_location: Optional[str]
    remarks: Optional[str]
    is_approved: bool
    approved_at: Optional[datetime]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============= Leave Schemas =============

class LeaveApplicationCreate(BaseModel):
    staff_id: str
    leave_type: LeaveType
    start_date: date
    end_date: date
    is_half_day: bool = False
    reason: str = Field(..., min_length=10)
    attachment_url: Optional[str] = None
    contact_number: Optional[str] = None


class LeaveApplicationUpdate(BaseModel):
    leave_type: Optional[LeaveType] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_half_day: Optional[bool] = None
    reason: Optional[str] = None
    attachment_url: Optional[str] = None
    contact_number: Optional[str] = None


class LeaveApproval(BaseModel):
    status: LeaveStatus
    rejection_reason: Optional[str] = None


class LeaveApplicationResponse(BaseModel):
    id: str
    restaurant_id: str
    staff_id: str
    leave_type: LeaveType
    start_date: date
    end_date: date
    total_days: int
    is_half_day: bool
    reason: str
    attachment_url: Optional[str]
    status: LeaveStatus
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    rejection_reason: Optional[str]
    contact_number: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class LeaveBalanceResponse(BaseModel):
    id: str
    restaurant_id: str
    staff_id: str
    year: int
    leave_type: LeaveType
    total_allocated: int
    used: int
    remaining: int
    carried_forward: int
    
    model_config = ConfigDict(from_attributes=True)


# ============= Report Schemas =============

class AttendanceSummary(BaseModel):
    staff_id: str
    employee_code: str
    staff_name: str
    total_days: int
    present_days: int
    absent_days: int
    half_days: int
    late_days: int
    leave_days: int
    total_hours_worked: float
    overtime_hours: float


class StaffPerformanceReport(BaseModel):
    staff_id: str
    employee_code: str
    staff_name: str
    role: str
    attendance_percentage: float
    punctuality_score: float
    leave_balance: dict
    active_since: date


class ShiftScheduleReport(BaseModel):
    shift_date: date
    shift_type: ShiftType
    total_staff_scheduled: int
    staff_details: List[dict]
