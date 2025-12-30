from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum, Date, Time, Numeric
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import enum


class UserRole(str, enum.Enum):
    """User role types"""
    ADMIN = "admin"
    MANAGER = "manager"
    CASHIER = "cashier"
    CAPTAIN = "captain"
    KITCHEN_STAFF = "kitchen_staff"
    WAITER = "waiter"
    DELIVERY_BOY = "delivery_boy"


class PermissionType(str, enum.Enum):
    """Permission types for granular access control"""
    # Order Management
    CREATE_ORDER = "create_order"
    VIEW_ORDER = "view_order"
    UPDATE_ORDER = "update_order"
    DELETE_ORDER = "delete_order"
    CANCEL_ORDER = "cancel_order"
    REFUND_ORDER = "refund_order"
    
    # Product Management
    CREATE_PRODUCT = "create_product"
    VIEW_PRODUCT = "view_product"
    UPDATE_PRODUCT = "update_product"
    DELETE_PRODUCT = "delete_product"
    
    # Inventory Management
    CREATE_INGREDIENT = "create_ingredient"
    VIEW_INGREDIENT = "view_ingredient"
    UPDATE_INGREDIENT = "update_ingredient"
    DELETE_INGREDIENT = "delete_ingredient"
    CREATE_PURCHASE_ORDER = "create_purchase_order"
    RECEIVE_PURCHASE_ORDER = "receive_purchase_order"
    
    # User Management
    CREATE_USER = "create_user"
    VIEW_USER = "view_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    
    # Staff Management
    CREATE_STAFF = "create_staff"
    VIEW_STAFF = "view_staff"
    UPDATE_STAFF = "update_staff"
    DELETE_STAFF = "delete_staff"
    APPROVE_LEAVE = "approve_leave"
    
    # Restaurant Management
    CREATE_RESTAURANT = "create_restaurant"
    VIEW_RESTAURANT = "view_restaurant"
    UPDATE_RESTAURANT = "update_restaurant"
    DELETE_RESTAURANT = "delete_restaurant"
    
    # Table Management
    CREATE_TABLE = "create_table"
    VIEW_TABLE = "view_table"
    UPDATE_TABLE = "update_table"
    DELETE_TABLE = "delete_table"
    
    # Reports & Analytics
    VIEW_REPORTS = "view_reports"
    VIEW_SALES_REPORT = "view_sales_report"
    VIEW_INVENTORY_REPORT = "view_inventory_report"
    VIEW_STAFF_REPORT = "view_staff_report"
    
    # Financial
    VIEW_FINANCIAL = "view_financial"
    MANAGE_PAYMENT = "manage_payment"
    GIVE_DISCOUNT = "give_discount"
    
    # Kitchen Operations
    VIEW_KOT = "view_kot"
    UPDATE_KOT_STATUS = "update_kot_status"
    
    # Settings
    MANAGE_SETTINGS = "manage_settings"


class ShiftType(str, enum.Enum):
    """Shift types"""
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"
    FULL_DAY = "full_day"


class AttendanceStatus(str, enum.Enum):
    """Attendance status types"""
    PRESENT = "present"
    ABSENT = "absent"
    HALF_DAY = "half_day"
    LATE = "late"
    ON_LEAVE = "on_leave"


class LeaveType(str, enum.Enum):
    """Leave types"""
    SICK_LEAVE = "sick_leave"
    CASUAL_LEAVE = "casual_leave"
    EARNED_LEAVE = "earned_leave"
    MATERNITY_LEAVE = "maternity_leave"
    PATERNITY_LEAVE = "paternity_leave"
    UNPAID_LEAVE = "unpaid_leave"


class LeaveStatus(str, enum.Enum):
    """Leave application status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class Role(Base):
    """Role model for access control"""
    __tablename__ = "roles"

    id = Column(String(36), primary_key=True)
    restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Role information
    name = Column(String(100), nullable=False)  # Display name
    code = Column(SQLEnum(UserRole), nullable=False, index=True)  # System role code
    description = Column(Text)
    
    # Hierarchy
    level = Column(Integer, default=0)  # Higher number = higher authority
    is_system_role = Column(Boolean, default=False)  # Cannot be deleted
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(36), ForeignKey("users.id"))
    updated_by = Column(String(36), ForeignKey("users.id"))
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="roles")
    permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")
    staff_members = relationship("Staff", back_populates="role")


class RolePermission(Base):
    """Role permission mapping"""
    __tablename__ = "role_permissions"

    id = Column(String(36), primary_key=True)
    role_id = Column(String(36), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Permission
    permission = Column(SQLEnum(PermissionType), nullable=False, index=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(36), ForeignKey("users.id"))
    
    # Relationships
    role = relationship("Role", back_populates="permissions")


class Staff(Base):
    """Staff member model"""
    __tablename__ = "staff"

    id = Column(String(36), primary_key=True)
    restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)  # Link to user account
    role_id = Column(String(36), ForeignKey("roles.id"), nullable=False, index=True)
    
    # Personal Information
    employee_code = Column(String(50), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), index=True)
    phone = Column(String(20), nullable=False, index=True)
    alternate_phone = Column(String(20))
    
    # Address
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100), default="India")
    
    # Emergency Contact
    emergency_contact_name = Column(String(100))
    emergency_contact_phone = Column(String(20))
    emergency_contact_relation = Column(String(50))
    
    # Employment Details
    date_of_joining = Column(Date, nullable=False)
    date_of_leaving = Column(Date)
    employment_type = Column(String(50))  # full_time, part_time, contract
    department = Column(String(100))
    designation = Column(String(100))
    
    # Salary Information (stored in paise/cents)
    basic_salary = Column(Integer)  # Monthly basic salary
    allowances = Column(Integer)  # Additional allowances
    total_salary = Column(Integer)  # Total monthly salary
    
    # Documents
    aadhar_number = Column(String(12))
    pan_number = Column(String(10))
    bank_account_number = Column(String(50))
    bank_name = Column(String(100))
    bank_ifsc_code = Column(String(11))
    
    # Work Schedule
    default_shift_type = Column(SQLEnum(ShiftType))
    working_days_per_week = Column(Integer, default=6)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_on_leave = Column(Boolean, default=False)
    
    # Profile
    photo_url = Column(String(500))
    notes = Column(Text)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(36), ForeignKey("users.id"))
    updated_by = Column(String(36), ForeignKey("users.id"))
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="staff")
    user = relationship("User", foreign_keys=[user_id])
    role = relationship("Role", back_populates="staff_members")
    attendance_records = relationship("Attendance", back_populates="staff", cascade="all, delete-orphan")
    shifts = relationship("Shift", back_populates="staff", cascade="all, delete-orphan")
    leave_applications = relationship("LeaveApplication", back_populates="staff", cascade="all, delete-orphan")


class Shift(Base):
    """Shift schedule model"""
    __tablename__ = "shifts"

    id = Column(String(36), primary_key=True)
    restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    staff_id = Column(String(36), ForeignKey("staff.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Shift Details
    shift_date = Column(Date, nullable=False, index=True)
    shift_type = Column(SQLEnum(ShiftType), nullable=False)
    
    # Time
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    
    # Break
    break_duration_minutes = Column(Integer, default=0)
    
    # Actual Time (for attendance)
    actual_start_time = Column(DateTime)
    actual_end_time = Column(DateTime)
    
    # Status
    is_assigned = Column(Boolean, default=True)
    is_completed = Column(Boolean, default=False)
    
    # Notes
    notes = Column(Text)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(36), ForeignKey("users.id"))
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="shifts")
    staff = relationship("Staff", back_populates="shifts")


class Attendance(Base):
    """Attendance tracking model"""
    __tablename__ = "attendance"

    id = Column(String(36), primary_key=True)
    restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    staff_id = Column(String(36), ForeignKey("staff.id", ondelete="CASCADE"), nullable=False, index=True)
    shift_id = Column(String(36), ForeignKey("shifts.id"), index=True)
    
    # Date
    attendance_date = Column(Date, nullable=False, index=True)
    
    # Time Tracking
    check_in_time = Column(DateTime)
    check_out_time = Column(DateTime)
    
    # Duration (in minutes)
    total_hours_worked = Column(Numeric(10, 2))
    overtime_hours = Column(Numeric(10, 2), default=0)
    
    # Status
    status = Column(SQLEnum(AttendanceStatus), nullable=False, default=AttendanceStatus.PRESENT, index=True)
    
    # Late arrival
    is_late = Column(Boolean, default=False)
    late_by_minutes = Column(Integer, default=0)
    
    # Location tracking
    check_in_location = Column(String(255))
    check_out_location = Column(String(255))
    
    # IP tracking
    check_in_ip = Column(String(50))
    check_out_ip = Column(String(50))
    
    # Notes
    remarks = Column(Text)
    
    # Approval
    is_approved = Column(Boolean, default=False)
    approved_by = Column(String(36), ForeignKey("users.id"))
    approved_at = Column(DateTime)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="attendance_records")
    staff = relationship("Staff", back_populates="attendance_records")
    shift = relationship("Shift")


class LeaveApplication(Base):
    """Leave application model"""
    __tablename__ = "leave_applications"

    id = Column(String(36), primary_key=True)
    restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    staff_id = Column(String(36), ForeignKey("staff.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Leave Details
    leave_type = Column(SQLEnum(LeaveType), nullable=False, index=True)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False)
    
    # Duration
    total_days = Column(Integer, nullable=False)
    is_half_day = Column(Boolean, default=False)
    
    # Reason
    reason = Column(Text, nullable=False)
    
    # Supporting Documents
    attachment_url = Column(String(500))
    
    # Status
    status = Column(SQLEnum(LeaveStatus), nullable=False, default=LeaveStatus.PENDING, index=True)
    
    # Approval
    approved_by = Column(String(36), ForeignKey("users.id"))
    approved_at = Column(DateTime)
    rejection_reason = Column(Text)
    
    # Contact during leave
    contact_number = Column(String(20))
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="leave_applications")
    staff = relationship("Staff", back_populates="leave_applications")
    approver = relationship("User", foreign_keys=[approved_by])


class LeaveBalance(Base):
    """Leave balance tracking"""
    __tablename__ = "leave_balances"

    id = Column(String(36), primary_key=True)
    restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    staff_id = Column(String(36), ForeignKey("staff.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Year
    year = Column(Integer, nullable=False, index=True)
    
    # Leave Type
    leave_type = Column(SQLEnum(LeaveType), nullable=False, index=True)
    
    # Balance
    total_allocated = Column(Integer, default=0)  # Total leaves for the year
    used = Column(Integer, default=0)  # Leaves used
    remaining = Column(Integer, default=0)  # Leaves remaining
    carried_forward = Column(Integer, default=0)  # From previous year
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    restaurant = relationship("Restaurant")
    staff = relationship("Staff")
