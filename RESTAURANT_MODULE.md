# 🏪 Restaurant Module - Implementation Summary

## ✅ Status: Models & Schemas Created

I've created a comprehensive **Restaurant Module** for your multi-tenant POS SaaS platform with India-specific features.

---

## 📊 What's Been Created

### ✅ **Models** (`app/modules/restaurant/model.py`)

1. **Restaurant** - Core tenant model
   - Identity & Business Info
   - Contact Information
   - **India-Specific Fields:**
     - `gstin` - GST Number (15 chars)
     - `fssai_license` - FSSAI License (14 chars)
     - `pan_number` - PAN Card (10 chars)
   - **Tax Settings:**
     - `enable_gst` - Enable/disable GST
     - `cgst_rate` - Central GST rate
     - `sgst_rate` - State GST rate
     - `igst_rate` - Integrated GST rate
     - `service_charge_percentage`
   - Branding (logo, colors)
   - Settings (timezone: Asia/Kolkata, currency: INR)
   - Subscription & Billing
   - Plan Limits & Usage Tracking
   - Features & Status

2. **RestaurantOwner** - Links users to restaurants
   - Multi-ownership support
   - Role-based permissions
   - Invitation tracking

3. **SubscriptionPlan** - Available plans
   - Pricing (monthly/yearly in paise)
   - Limits (users, products, orders, locations)
   - Features list
   - Trial period

4. **Subscription** - Active subscriptions
   - Plan tracking
   - Billing cycle
   - Payment gateway integration
   - Cancellation handling

5. **Invoice** - Billing invoices
   - Invoice numbering
   - **India-Specific Tax Breakdown:**
     - `cgst_amount`
     - `sgst_amount`
     - `igst_amount`
   - Payment tracking
   - PDF generation support

6. **RestaurantInvitation** - Team invitations
   - Email-based invitations
   - Token-based acceptance
   - Expiration handling

### ✅ **Schemas** (`app/modules/restaurant/schema.py`)

Complete Pydantic v2 schemas for:
- Restaurant (Create, Update, Response)
- SubscriptionPlan (Create, Update, Response)
- Subscription (Create, Update, Response)
- Invoice (Create, Response)
- RestaurantInvitation (Create, Response)
- RestaurantOwner (Response)

All with proper validation and India-specific fields.

---

## 🇮🇳 India-Specific Features

### 1. **Business Registration**
- **GSTIN** - GST Identification Number (15 characters)
- **FSSAI License** - Food Safety License (14 characters)
- **PAN Number** - Permanent Account Number (10 characters)

### 2. **Tax Management**
- **CGST** - Central Goods and Services Tax
- **SGST** - State Goods and Services Tax
- **IGST** - Integrated Goods and Services Tax (for inter-state)
- **Service Charge** - Configurable percentage

### 3. **Localization**
- Default Timezone: `Asia/Kolkata`
- Default Currency: `INR` (Indian Rupees)
- Date Format: `DD/MM/YYYY` (Indian standard)
- Time Format: `24h`
- Pricing in **paise** (100 paise = 1 rupee)

### 4. **Invoice Tax Breakdown**
- Separate fields for CGST, SGST, IGST amounts
- Compliant with Indian GST regulations

---

## 🏗️ Database Schema

### Restaurant Table
```sql
- id (UUID)
- name, slug, business_name
- business_type (enum)
- cuisine_type (JSON array)
- email, phone, alternate_phone
- address, city, state, country, postal_code
- gstin, fssai_license, pan_number  -- India-specific
- logo, banner_image
- primary_color, accent_color
- timezone, currency, language
- enable_gst, cgst_rate, sgst_rate, igst_rate  -- Tax settings
- subscription_plan, subscription_status
- max_users, max_products, max_orders_per_month
- current_users, current_products, current_orders_this_month
- features (JSON)
- is_active, is_verified, is_suspended
- onboarding_completed, onboarding_step
- created_at, updated_at, last_activity, deleted_at
```

### Subscription Table
```sql
- id (UUID)
- restaurant_id (FK)
- plan, plan_name, status
- price_per_month, price_per_year, billing_cycle
- started_at, current_period_start, current_period_end
- trial_end, cancelled_at, ended_at
- payment_method, payment_gateway_customer_id
- cancel_at_period_end, cancellation_reason
```

### Invoice Table
```sql
- id (UUID)
- subscription_id (FK), restaurant_id (FK)
- invoice_number (unique)
- amount, tax, total, currency
- cgst_amount, sgst_amount, igst_amount  -- India-specific
- status, invoice_date, due_date, paid_at
- payment_method, pdf_url
```

---

## 📝 Next Steps

To complete the Restaurant module, I need to create:

1. **Service Layer** (`app/modules/restaurant/service.py`)
   - Restaurant CRUD operations
   - Subscription management
   - Invoice generation
   - Invitation handling
   - Usage limit enforcement

2. **API Routes** (`app/modules/restaurant/route.py`)
   - Restaurant management endpoints
   - Subscription endpoints
   - Invoice endpoints
   - Invitation endpoints

3. **Database Migration**
   - Alembic migration for all restaurant tables

4. **Integration**
   - Update `migrations/env.py` to import models
   - Register routes in `main.py`

Would you like me to continue with the Service and Routes implementation?

---

## 🎯 Key Features

✅ Multi-tenancy support
✅ India-specific compliance (GST, FSSAI, PAN)
✅ Subscription management
✅ Usage tracking & limits
✅ Invoice generation with tax breakdown
✅ Team invitations
✅ Soft delete support
✅ Onboarding workflow
✅ Branding customization
✅ Multiple business types
✅ Cuisine type tracking
✅ Location support (lat/long)
✅ Payment gateway integration ready

---

## 💡 Usage Example

```python
# Create a restaurant
restaurant = RestaurantCreate(
    name="Spice Garden",
    slug="spice-garden-mumbai",
    business_name="Spice Garden Pvt Ltd",
    business_type=BusinessType.RESTAURANT,
    cuisine_type=["indian", "north_indian"],
    email="contact@spicegarden.com",
    phone="+919876543210",
    address="123 MG Road",
    city="Mumbai",
    state="Maharashtra",
    postal_code="400001",
    gstin="27AABCU9603R1ZM",  # GST Number
    fssai_license="12345678901234",  # FSSAI License
    pan_number="AABCU9603R",  # PAN Card
    enable_gst=True,
    cgst_rate=2.5,
    sgst_rate=2.5
)
```

---

**Status**: ✅ Models and Schemas Complete
**Next**: Service Layer & API Routes
