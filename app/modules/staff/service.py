from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, extract
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime, date, timedelta
import uuid

from app.modules.staff.model import (
    Role, RolePermission, Staff, Shift, Attendance, 
    LeaveApplication, LeaveBalance, UserRole, PermissionType,
    AttendanceStatus, LeaveStatus, LeaveType
)
from app.modules.staff.schema import (
    RoleCreate, RoleUpdate, StaffCreate, StaffUpdate,
    ShiftCreate, ShiftUpdate, AttendanceCheckIn, AttendanceCheckOut,
    AttendanceManualEntry, AttendanceUpdate, LeaveApplicationCreate,
    LeaveApplicationUpdate, LeaveApproval
)
from fastapi import HTTPException, status


class StaffService:
    """Service for staff and role management operations"""

    # ============= Role Management =============

    @staticmethod
    async def create_role(
        db: AsyncSession,
        restaurant_id: str,
        role_data: RoleCreate,
        user_id: str
    ) -> Role:
        """Create a new role with permissions"""
        # Check if role code already exists for restaurant
        existing = await db.execute(
            select(Role).where(
                and_(
                    Role.restaurant_id == restaurant_id,
                    Role.code == role_data.code
                )
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role with code {role_data.code} already exists"
            )

        # Create role
        role = Role(
            id=str(uuid.uuid4()),
            restaurant_id=restaurant_id,
            name=role_data.name,
            code=role_data.code,
            description=role_data.description,
            level=role_data.level,
            created_by=user_id,
            updated_by=user_id
        )
        db.add(role)
        await db.flush()

        # Add permissions
        for permission in role_data.permissions:
            role_permission = RolePermission(
                id=str(uuid.uuid4()),
                role_id=role.id,
                permission=permission,
                created_by=user_id
            )
            db.add(role_permission)

        await db.commit()
        await db.refresh(role)
        return role

    @staticmethod
    async def get_role_by_id(db: AsyncSession, role_id: str) -> Optional[Role]:
        """Get role by ID with permissions"""
        result = await db.execute(
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.id == role_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_roles_by_restaurant(
        db: AsyncSession,
        restaurant_id: str,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Role]:
        """Get all roles for a restaurant"""
        query = select(Role).options(selectinload(Role.permissions)).where(
            Role.restaurant_id == restaurant_id
        )

        if is_active is not None:
            query = query.where(Role.is_active == is_active)

        query = query.order_by(Role.level.desc(), Role.name).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update_role(
        db: AsyncSession,
        role_id: str,
        role_data: RoleUpdate,
        user_id: str
    ) -> Role:
        """Update role"""
        role = await StaffService.get_role_by_id(db, role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )

        if role.is_system_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify system role"
            )

        # Update fields
        update_data = role_data.model_dump(exclude_unset=True, exclude={'permissions'})
        for field, value in update_data.items():
            setattr(role, field, value)

        role.updated_by = user_id
        role.updated_at = datetime.utcnow()

        # Update permissions if provided
        if role_data.permissions is not None:
            # Delete existing permissions
            await db.execute(
                select(RolePermission).where(RolePermission.role_id == role_id)
            )
            existing_perms = (await db.execute(
                select(RolePermission).where(RolePermission.role_id == role_id)
            )).scalars().all()
            
            for perm in existing_perms:
                await db.delete(perm)

            # Add new permissions
            for permission in role_data.permissions:
                role_permission = RolePermission(
                    id=str(uuid.uuid4()),
                    role_id=role.id,
                    permission=permission,
                    created_by=user_id
                )
                db.add(role_permission)

        await db.commit()
        await db.refresh(role)
        return role

    @staticmethod
    async def check_permission(
        db: AsyncSession,
        role_id: str,
        permission: PermissionType
    ) -> bool:
        """Check if role has specific permission"""
        result = await db.execute(
            select(RolePermission).where(
                and_(
                    RolePermission.role_id == role_id,
                    RolePermission.permission == permission
                )
            )
        )
        return result.scalar_one_or_none() is not None

    # ============= Staff Management =============

    @staticmethod
    async def create_staff(
        db: AsyncSession,
        restaurant_id: str,
        staff_data: StaffCreate,
        user_id: str
    ) -> Staff:
        """Create a new staff member"""
        # Check if employee code already exists
        existing = await db.execute(
            select(Staff).where(Staff.employee_code == staff_data.employee_code)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Employee code {staff_data.employee_code} already exists"
            )

        # Convert salary to paise/cents
        basic_salary = int(staff_data.basic_salary * 100) if staff_data.basic_salary else None
        allowances = int(staff_data.allowances * 100) if staff_data.allowances else None
        total_salary = (basic_salary or 0) + (allowances or 0) if (basic_salary or allowances) else None

        # Create staff
        staff = Staff(
            id=str(uuid.uuid4()),
            restaurant_id=restaurant_id,
            user_id=staff_data.user_id,
            role_id=staff_data.role_id,
            employee_code=staff_data.employee_code,
            first_name=staff_data.first_name,
            last_name=staff_data.last_name,
            email=staff_data.email,
            phone=staff_data.phone,
            alternate_phone=staff_data.alternate_phone,
            address_line1=staff_data.address_line1,
            address_line2=staff_data.address_line2,
            city=staff_data.city,
            state=staff_data.state,
            postal_code=staff_data.postal_code,
            country=staff_data.country,
            emergency_contact_name=staff_data.emergency_contact_name,
            emergency_contact_phone=staff_data.emergency_contact_phone,
            emergency_contact_relation=staff_data.emergency_contact_relation,
            date_of_joining=staff_data.date_of_joining,
            employment_type=staff_data.employment_type,
            department=staff_data.department,
            designation=staff_data.designation,
            basic_salary=basic_salary,
            allowances=allowances,
            total_salary=total_salary,
            aadhar_number=staff_data.aadhar_number,
            pan_number=staff_data.pan_number,
            bank_account_number=staff_data.bank_account_number,
            bank_name=staff_data.bank_name,
            bank_ifsc_code=staff_data.bank_ifsc_code,
            default_shift_type=staff_data.default_shift_type,
            working_days_per_week=staff_data.working_days_per_week,
            photo_url=staff_data.photo_url,
            notes=staff_data.notes,
            created_by=user_id,
            updated_by=user_id
        )
        db.add(staff)

        # Initialize leave balances for current year
        current_year = datetime.utcnow().year
        leave_allocations = {
            LeaveType.SICK_LEAVE: 7,
            LeaveType.CASUAL_LEAVE: 7,
            LeaveType.EARNED_LEAVE: 15,
        }

        for leave_type, allocation in leave_allocations.items():
            leave_balance = LeaveBalance(
                id=str(uuid.uuid4()),
                restaurant_id=restaurant_id,
                staff_id=staff.id,
                year=current_year,
                leave_type=leave_type,
                total_allocated=allocation,
                used=0,
                remaining=allocation,
                carried_forward=0
            )
            db.add(leave_balance)

        await db.commit()
        await db.refresh(staff)
        return staff

    @staticmethod
    async def get_staff_by_id(
        db: AsyncSession, 
        staff_id: str
    ) -> Optional[Staff]:
        """Get staff by ID with role"""
        result = await db.execute(
            select(Staff)
            .options(selectinload(Staff.role).selectinload(Role.permissions))
            .where(Staff.id == staff_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_staff_by_employee_code(
        db: AsyncSession,
        employee_code: str
    ) -> Optional[Staff]:
        """Get staff by employee code"""
        result = await db.execute(
            select(Staff).where(Staff.employee_code == employee_code)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_staff_by_restaurant(
        db: AsyncSession,
        restaurant_id: str,
        role_id: Optional[str] = None,
        department: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Staff]:
        """Get all staff for a restaurant with filters"""
        query = select(Staff).options(
            selectinload(Staff.role).selectinload(Role.permissions)
        ).where(Staff.restaurant_id == restaurant_id)

        if role_id:
            query = query.where(Staff.role_id == role_id)

        if department:
            query = query.where(Staff.department == department)

        if is_active is not None:
            query = query.where(Staff.is_active == is_active)

        if search:
            search_filter = or_(
                Staff.first_name.ilike(f"%{search}%"),
                Staff.last_name.ilike(f"%{search}%"),
                Staff.employee_code.ilike(f"%{search}%"),
                Staff.phone.ilike(f"%{search}%"),
                Staff.email.ilike(f"%{search}%")
            )
            query = query.where(search_filter)

        query = query.order_by(Staff.first_name, Staff.last_name).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update_staff(
        db: AsyncSession,
        staff_id: str,
        staff_data: StaffUpdate,
        user_id: str
    ) -> Staff:
        """Update staff details"""
        staff = await StaffService.get_staff_by_id(db, staff_id)
        if not staff:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Staff not found"
            )

        # Update fields
        update_data = staff_data.model_dump(exclude_unset=True, exclude={'basic_salary', 'allowances'})
        for field, value in update_data.items():
            setattr(staff, field, value)

        # Update salary if provided
        if staff_data.basic_salary is not None:
            staff.basic_salary = int(staff_data.basic_salary * 100)
        if staff_data.allowances is not None:
            staff.allowances = int(staff_data.allowances * 100)

        if staff.basic_salary or staff.allowances:
            staff.total_salary = (staff.basic_salary or 0) + (staff.allowances or 0)

        staff.updated_by = user_id
        staff.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(staff)
        return staff

    @staticmethod
    async def delete_staff(db: AsyncSession, staff_id: str) -> None:
        """Deactivate staff (soft delete)"""
        staff = await StaffService.get_staff_by_id(db, staff_id)
        if not staff:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Staff not found"
            )

        staff.is_active = False
        staff.date_of_leaving = date.today()
        await db.commit()

    # ============= Shift Management =============

    @staticmethod
    async def create_shift(
        db: AsyncSession,
        restaurant_id: str,
        shift_data: ShiftCreate,
        user_id: str
    ) -> Shift:
        """Create a shift for staff"""
        # Verify staff exists
        staff = await StaffService.get_staff_by_id(db, shift_data.staff_id)
        if not staff or staff.restaurant_id != restaurant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Staff not found"
            )

        # Check if shift already exists for this staff on this date
        existing = await db.execute(
            select(Shift).where(
                and_(
                    Shift.staff_id == shift_data.staff_id,
                    Shift.shift_date == shift_data.shift_date
                )
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Shift already exists for this staff on this date"
            )

        shift = Shift(
            id=str(uuid.uuid4()),
            restaurant_id=restaurant_id,
            staff_id=shift_data.staff_id,
            shift_date=shift_data.shift_date,
            shift_type=shift_data.shift_type,
            start_time=shift_data.start_time,
            end_time=shift_data.end_time,
            break_duration_minutes=shift_data.break_duration_minutes,
            notes=shift_data.notes,
            created_by=user_id
        )
        db.add(shift)
        await db.commit()
        await db.refresh(shift)
        return shift

    @staticmethod
    async def get_shifts_by_date_range(
        db: AsyncSession,
        restaurant_id: str,
        start_date: date,
        end_date: date,
        staff_id: Optional[str] = None
    ) -> List[Shift]:
        """Get shifts for date range"""
        query = select(Shift).where(
            and_(
                Shift.restaurant_id == restaurant_id,
                Shift.shift_date >= start_date,
                Shift.shift_date <= end_date
            )
        )

        if staff_id:
            query = query.where(Shift.staff_id == staff_id)

        query = query.order_by(Shift.shift_date, Shift.start_time)
        result = await db.execute(query)
        return result.scalars().all()

    # ============= Attendance Management =============

    @staticmethod
    async def check_in(
        db: AsyncSession,
        restaurant_id: str,
        check_in_data: AttendanceCheckIn,
        ip_address: Optional[str] = None
    ) -> Attendance:
        """Staff check-in"""
        # Verify staff
        staff = await StaffService.get_staff_by_id(db, check_in_data.staff_id)
        if not staff or staff.restaurant_id != restaurant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Staff not found"
            )

        # Check if already checked in today
        today = date.today()
        existing = await db.execute(
            select(Attendance).where(
                and_(
                    Attendance.staff_id == check_in_data.staff_id,
                    Attendance.attendance_date == today,
                    Attendance.check_out_time.is_(None)
                )
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already checked in today"
            )

        check_in_time = datetime.utcnow()

        # Check if late
        is_late = False
        late_by_minutes = 0
        if check_in_data.shift_id:
            shift = await db.get(Shift, check_in_data.shift_id)
            if shift:
                shift_start = datetime.combine(today, shift.start_time)
                if check_in_time > shift_start:
                    is_late = True
                    late_by_minutes = int((check_in_time - shift_start).total_seconds() / 60)

        attendance = Attendance(
            id=str(uuid.uuid4()),
            restaurant_id=restaurant_id,
            staff_id=check_in_data.staff_id,
            shift_id=check_in_data.shift_id,
            attendance_date=today,
            check_in_time=check_in_time,
            status=AttendanceStatus.PRESENT,
            is_late=is_late,
            late_by_minutes=late_by_minutes,
            check_in_location=check_in_data.check_in_location,
            check_in_ip=ip_address,
            remarks=check_in_data.remarks
        )
        db.add(attendance)
        await db.commit()
        await db.refresh(attendance)
        return attendance

    @staticmethod
    async def check_out(
        db: AsyncSession,
        attendance_id: str,
        check_out_data: AttendanceCheckOut,
        ip_address: Optional[str] = None
    ) -> Attendance:
        """Staff check-out"""
        attendance = await db.get(Attendance, attendance_id)
        if not attendance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attendance record not found"
            )

        if attendance.check_out_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already checked out"
            )

        check_out_time = datetime.utcnow()
        attendance.check_out_time = check_out_time
        attendance.check_out_location = check_out_data.check_out_location
        attendance.check_out_ip = ip_address

        if check_out_data.remarks:
            attendance.remarks = f"{attendance.remarks or ''}\n{check_out_data.remarks}".strip()

        # Calculate hours worked
        if attendance.check_in_time:
            duration = check_out_time - attendance.check_in_time
            total_minutes = duration.total_seconds() / 60

            # Subtract break time
            if attendance.shift_id:
                shift = await db.get(Shift, attendance.shift_id)
                if shift:
                    total_minutes -= shift.break_duration_minutes

            total_hours = total_minutes / 60
            attendance.total_hours_worked = round(total_hours, 2)

            # Calculate overtime (if more than 8 hours)
            if total_hours > 8:
                attendance.overtime_hours = round(total_hours - 8, 2)

        await db.commit()
        await db.refresh(attendance)
        return attendance

    @staticmethod
    async def create_manual_attendance(
        db: AsyncSession,
        restaurant_id: str,
        attendance_data: AttendanceManualEntry,
        user_id: str
    ) -> Attendance:
        """Create manual attendance entry"""
        # Check if attendance already exists
        existing = await db.execute(
            select(Attendance).where(
                and_(
                    Attendance.staff_id == attendance_data.staff_id,
                    Attendance.attendance_date == attendance_data.attendance_date
                )
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Attendance already exists for this date"
            )

        # Calculate hours if both check-in and check-out provided
        total_hours = None
        if attendance_data.check_in_time and attendance_data.check_out_time:
            duration = attendance_data.check_out_time - attendance_data.check_in_time
            total_hours = round(duration.total_seconds() / 3600, 2)

        attendance = Attendance(
            id=str(uuid.uuid4()),
            restaurant_id=restaurant_id,
            staff_id=attendance_data.staff_id,
            attendance_date=attendance_data.attendance_date,
            check_in_time=attendance_data.check_in_time,
            check_out_time=attendance_data.check_out_time,
            total_hours_worked=total_hours,
            status=attendance_data.status,
            remarks=attendance_data.remarks
        )
        db.add(attendance)
        await db.commit()
        await db.refresh(attendance)
        return attendance

    @staticmethod
    async def get_attendance_by_restaurant(
        db: AsyncSession,
        restaurant_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        staff_id: Optional[str] = None,
        status: Optional[AttendanceStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Attendance]:
        """Get attendance records with filters"""
        query = select(Attendance).where(Attendance.restaurant_id == restaurant_id)

        if start_date:
            query = query.where(Attendance.attendance_date >= start_date)
        if end_date:
            query = query.where(Attendance.attendance_date <= end_date)
        if staff_id:
            query = query.where(Attendance.staff_id == staff_id)
        if status:
            query = query.where(Attendance.status == status)

        query = query.order_by(Attendance.attendance_date.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    # ============= Leave Management =============

    @staticmethod
    async def create_leave_application(
        db: AsyncSession,
        restaurant_id: str,
        leave_data: LeaveApplicationCreate
    ) -> LeaveApplication:
        """Create leave application"""
        # Calculate total days
        delta = leave_data.end_date - leave_data.start_date
        total_days = delta.days + 1
        if leave_data.is_half_day:
            total_days = 0.5

        # Check leave balance
        leave_balance = await db.execute(
            select(LeaveBalance).where(
                and_(
                    LeaveBalance.staff_id == leave_data.staff_id,
                    LeaveBalance.year == leave_data.start_date.year,
                    LeaveBalance.leave_type == leave_data.leave_type
                )
            )
        )
        balance = leave_balance.scalar_one_or_none()

        if balance and balance.remaining < total_days:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient leave balance. Available: {balance.remaining} days"
            )

        leave_app = LeaveApplication(
            id=str(uuid.uuid4()),
            restaurant_id=restaurant_id,
            staff_id=leave_data.staff_id,
            leave_type=leave_data.leave_type,
            start_date=leave_data.start_date,
            end_date=leave_data.end_date,
            total_days=total_days,
            is_half_day=leave_data.is_half_day,
            reason=leave_data.reason,
            attachment_url=leave_data.attachment_url,
            contact_number=leave_data.contact_number
        )
        db.add(leave_app)
        await db.commit()
        await db.refresh(leave_app)
        return leave_app

    @staticmethod
    async def approve_leave(
        db: AsyncSession,
        leave_id: str,
        approval_data: LeaveApproval,
        user_id: str
    ) -> LeaveApplication:
        """Approve or reject leave"""
        leave_app = await db.get(LeaveApplication, leave_id)
        if not leave_app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Leave application not found"
            )

        if leave_app.status != LeaveStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Leave application already processed"
            )

        leave_app.status = approval_data.status
        leave_app.approved_by = user_id
        leave_app.approved_at = datetime.utcnow()
        leave_app.rejection_reason = approval_data.rejection_reason

        # Update leave balance if approved
        if approval_data.status == LeaveStatus.APPROVED:
            leave_balance = await db.execute(
                select(LeaveBalance).where(
                    and_(
                        LeaveBalance.staff_id == leave_app.staff_id,
                        LeaveBalance.year == leave_app.start_date.year,
                        LeaveBalance.leave_type == leave_app.leave_type
                    )
                )
            )
            balance = leave_balance.scalar_one_or_none()
            if balance:
                balance.used += leave_app.total_days
                balance.remaining -= leave_app.total_days

            # Update staff leave status
            staff = await db.get(Staff, leave_app.staff_id)
            if staff:
                staff.is_on_leave = True

        await db.commit()
        await db.refresh(leave_app)
        return leave_app

    @staticmethod
    async def get_leave_balance(
        db: AsyncSession,
        staff_id: str,
        year: Optional[int] = None
    ) -> List[LeaveBalance]:
        """Get leave balance for staff"""
        if year is None:
            year = datetime.utcnow().year

        result = await db.execute(
            select(LeaveBalance).where(
                and_(
                    LeaveBalance.staff_id == staff_id,
                    LeaveBalance.year == year
                )
            )
        )
        return result.scalars().all()
