# 🔄 UUID Migration - User Model Update

## ⚠️ IMPORTANT: Breaking Change

The User model has been updated to use **UUID (String)** as the primary key instead of **auto-increment integer**. This is a **breaking change** that requires database recreation or complex migration.

---

## ✅ Changes Made

### 1. **User Model** (`app/modules/user/model.py`)
```python
# Before
id: Mapped[int] = mapped_column(primary_key=True, index=True)

# After
id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
```

### 2. **All Foreign Keys Updated**
Updated all references to `user_id` from `Integer` to `String(36)`:

- ✅ `app/modules/user/service.py` - All methods
- ✅ `app/modules/user/route.py` - All endpoints
- ✅ `app/modules/user/schema.py` - UserResponse
- ✅ `app/modules/restaurant/model.py` - All FK references
- ✅ `app/modules/restaurant/service.py` - All methods
- ✅ `app/modules/restaurant/schema.py` - RestaurantOwnerResponse
- ✅ `app/modules/auth/model.py` - LoginLog.user_id
- ✅ `app/modules/auth/service.py` - get_logs_by_user_id
- ✅ `app/core/dependencies.py` - JWT payload

---

## 📊 Affected Tables

### Tables with user_id Foreign Keys:
1. **restaurant_owners** - user_id, invited_by
2. **subscriptions** - cancelled_by
3. **restaurant_invitations** - invited_by, accepted_by
4. **login_logs** - user_id

---

## 🔧 Migration Options

### Option 1: Fresh Database (Recommended for Development)
```bash
# Drop all tables and recreate
./docker.sh down
mysql -u root -proot -e "DROP DATABASE restaurant_pos; CREATE DATABASE restaurant_pos;"
./docker.sh up
./docker.sh migrate:up
```

### Option 2: Complex Migration (Production)
This requires:
1. Create new UUID column
2. Generate UUIDs for existing users
3. Update all foreign key references
4. Drop old integer column
5. Rename UUID column to `id`

**Note:** This is complex and error-prone. Recommended only for production with existing data.

---

## 📝 Updated Code Files

### Models
- ✅ `app/modules/user/model.py` - UUID primary key
- ✅ `app/modules/restaurant/model.py` - String FK references
- ✅ `app/modules/auth/model.py` - String user_id + Optional import

### Schemas
- ✅ `app/modules/user/schema.py` - id: str
- ✅ `app/modules/restaurant/schema.py` - user_id: str

### Services
- ✅ `app/modules/user/service.py` - user_id: str parameters
- ✅ `app/modules/restaurant/service.py` - user_id: str parameters
- ✅ `app/modules/auth/service.py` - user_id: str parameters

### Routes
- ✅ `app/modules/user/route.py` - user_id: str path parameters

### Core
- ✅ `app/core/dependencies.py` - user_id: str from JWT

---

## 🎯 Benefits of UUID

### 1. **Consistency**
- All models now use UUID (User + Restaurant modules)
- Uniform ID format across the system

### 2. **Security**
- Non-sequential IDs prevent enumeration attacks
- Harder to guess valid user IDs

### 3. **Scalability**
- UUIDs can be generated client-side
- No database round-trip needed for ID generation
- Better for distributed systems

### 4. **Multi-tenancy**
- Consistent with Restaurant module design
- Easier to merge data from multiple sources

---

## 🧪 Testing After Migration

### 1. Create User
```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "uuid@example.com",
    "username": "uuiduser",
    "password": "test123"
  }'
```

**Expected Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",  // UUID format
  "email": "uuid@example.com",
  ...
}
```

### 2. Login and Check JWT
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "uuid@example.com",
    "password": "test123"
  }'
```

The JWT payload should contain UUID in `sub` claim.

### 3. Get User by ID
```bash
curl http://localhost:8000/users/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer TOKEN"
```

---

## ⚠️ Breaking Changes

### API Endpoints
All user ID path parameters now expect UUID strings:
- `GET /users/{user_id}` - Now requires UUID
- `PUT /users/{user_id}` - Now requires UUID
- `DELETE /users/{user_id}` - Now requires UUID

### JWT Tokens
- Old tokens with integer `sub` will be invalid
- All users need to re-login after migration

### Database
- Existing integer user IDs incompatible
- Foreign key constraints need updating

---

## 🚀 Next Steps

1. **Backup existing data** (if any)
2. **Drop and recreate database**
3. **Run migrations**
4. **Test all user endpoints**
5. **Test restaurant-user relationships**
6. **Verify login logging**

---

## 📋 Checklist

- [x] User model updated to UUID
- [x] All foreign keys updated to String(36)
- [x] All service methods updated
- [x] All route parameters updated
- [x] All schemas updated
- [x] JWT dependencies updated
- [x] Optional import added to auth model
- [ ] Database migration created
- [ ] Database migrated
- [ ] All endpoints tested

---

## 💡 Recommendation

**For development:** Drop and recreate the database to avoid migration complexity.

**For production:** Plan a maintenance window and follow the complex migration path with proper backups.

---

**Status:** ✅ Code Updated, ⏳ Database Migration Pending
