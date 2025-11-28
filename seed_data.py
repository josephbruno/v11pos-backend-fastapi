"""
Seed sample data into the restaurant POS database
"""
import sys
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import random

from app.database import SessionLocal, engine
from app.models.user import User, ShiftSchedule, StaffPerformance
from app.models.product import Category, Product, Modifier, ModifierOption, ComboProduct, ComboItem
from app.models.customer import Customer, CustomerTag, LoyaltyRule, LoyaltyTransaction
from app.models.order import Order, OrderItem, OrderItemModifier, OrderStatusHistory, KOTGroup
from app.models.qr import QRTable, QRSession, QRSettings
from app.models.settings import TaxRule, Settings

# Password hashing
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")


def clear_existing_data(db: Session):
    """Clear existing data from all tables"""
    print("Clearing existing data...")
    
    # Delete in reverse order of dependencies
    db.query(OrderItemModifier).delete()
    db.query(OrderItem).delete()
    db.query(OrderStatusHistory).delete()
    db.query(KOTGroup).delete()
    db.query(Order).delete()
    
    db.query(LoyaltyTransaction).delete()
    db.query(LoyaltyRule).delete()
    
    db.query(ComboItem).delete()
    db.query(ComboProduct).delete()
    
    db.query(ModifierOption).delete()
    db.query(Modifier).delete()
    
    db.query(Product).delete()
    db.query(Category).delete()
    
    db.query(CustomerTag).delete()
    db.query(Customer).delete()
    
    db.query(ShiftSchedule).delete()
    db.query(StaffPerformance).delete()
    
    db.query(QRSession).delete()
    db.query(QRTable).delete()
    db.query(QRSettings).delete()
    
    db.query(TaxRule).delete()
    # Keep Settings as it might have important config
    
    # Keep Users - we need admin
    
    db.commit()
    print("✓ Existing data cleared")


def seed_users(db: Session):
    """Seed users"""
    print("\nSeeding users...")
    
    users_data = [
        {
            "name": "Manager John",
            "email": "manager@restaurant.com",
            "password": pwd_context.hash("Manager123!"),
            "phone": "1234567891",
            "role": "manager",
            "status": "active"
        },
        {
            "name": "Cashier Sarah",
            "email": "cashier@restaurant.com",
            "password": pwd_context.hash("Cashier123!"),
            "phone": "1234567892",
            "role": "cashier",
            "status": "active"
        },
        {
            "name": "Staff Mike",
            "email": "staff@restaurant.com",
            "password": pwd_context.hash("Staff123!"),
            "phone": "1234567893",
            "role": "staff",
            "status": "active"
        },
        {
            "name": "Cashier David",
            "email": "cashier2@restaurant.com",
            "password": pwd_context.hash("Cashier123!"),
            "phone": "1234567894",
            "role": "cashier",
            "status": "active"
        }
    ]
    
    created_users = []
    for user_data in users_data:
        # Check if user exists
        existing = db.query(User).filter(User.email == user_data["email"]).first()
        if existing:
            created_users.append(existing)
            print(f"  • User {user_data['email']} already exists, using existing")
        else:
            user = User(**user_data)
            db.add(user)
            created_users.append(user)
            db.flush()  # Flush to get the ID
            print(f"  • Created user {user_data['email']}")
    
    db.commit()
    print(f"✓ Total {len(created_users)} users available")
    return created_users


def seed_shift_schedules(db: Session, users):
    """Seed shift schedules"""
    print("\nSeeding shift schedules...")
    
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    shifts = []
    
    # Position mapping based on user role
    positions = {
        "manager": "Floor Manager",
        "cashier": "Cashier",
        "staff": "Server"
    }
    
    for user in users[:3]:  # First 3 users
        position = positions.get(user.role, "Staff")
        for day in days:
            shift = ShiftSchedule(
                user_id=user.id,
                day=day,
                start_time="09:00",
                end_time="17:00",
                position=position,
                is_active=True
            )
            db.add(shift)
            shifts.append(shift)
    
    db.commit()
    print(f"✓ Created {len(shifts)} shift schedules")
    return shifts


def seed_categories(db: Session):
    """Seed product categories"""
    print("\nSeeding categories...")
    
    categories_data = [
        {"name": "Appetizers", "slug": "appetizers", "description": "Starters and small bites", "sort_order": 1},
        {"name": "Main Course", "slug": "main-course", "description": "Main dishes and entrees", "sort_order": 2},
        {"name": "Burgers", "slug": "burgers", "description": "Delicious burgers", "sort_order": 3},
        {"name": "Pizza", "slug": "pizza", "description": "Wood-fired pizzas", "sort_order": 4},
        {"name": "Pasta", "slug": "pasta", "description": "Italian pasta dishes", "sort_order": 5},
        {"name": "Desserts", "slug": "desserts", "description": "Sweet treats", "sort_order": 6},
        {"name": "Beverages", "slug": "beverages", "description": "Drinks and refreshments", "sort_order": 7},
        {"name": "Coffee", "slug": "coffee", "description": "Coffee and espresso drinks", "sort_order": 8},
    ]
    
    categories = []
    for cat_data in categories_data:
        category = Category(**cat_data, active=True)
        db.add(category)
        categories.append(category)
    
    db.commit()
    print(f"✓ Created {len(categories)} categories")
    return categories


def seed_products(db: Session, categories):
    """Seed products"""
    print("\nSeeding products...")
    
    products_data = [
        # Appetizers
        {"name": "Spring Rolls", "category": "Appetizers", "price": 850, "description": "Crispy vegetable spring rolls", "available": True},
        {"name": "Garlic Bread", "category": "Appetizers", "price": 550, "description": "Toasted bread with garlic butter", "available": True},
        {"name": "Buffalo Wings", "category": "Appetizers", "price": 1250, "description": "Spicy chicken wings", "available": True},
        
        # Main Course
        {"name": "Grilled Chicken", "category": "Main Course", "price": 1850, "description": "Marinated grilled chicken breast", "available": True},
        {"name": "Beef Steak", "category": "Main Course", "price": 2850, "description": "Premium beef steak", "available": True},
        {"name": "Fish & Chips", "category": "Main Course", "price": 1650, "description": "Crispy battered fish with fries", "available": True},
        
        # Burgers
        {"name": "Classic Burger", "category": "Burgers", "price": 1250, "description": "Beef patty with lettuce and tomato", "available": True},
        {"name": "Cheese Burger", "category": "Burgers", "price": 1450, "description": "Burger with melted cheese", "available": True},
        {"name": "Chicken Burger", "category": "Burgers", "price": 1350, "description": "Grilled chicken burger", "available": True},
        {"name": "Veggie Burger", "category": "Burgers", "price": 1150, "description": "Plant-based burger", "available": True},
        
        # Pizza
        {"name": "Margherita Pizza", "category": "Pizza", "price": 1450, "description": "Classic tomato and mozzarella", "available": True},
        {"name": "Pepperoni Pizza", "category": "Pizza", "price": 1750, "description": "Loaded with pepperoni", "available": True},
        {"name": "BBQ Chicken Pizza", "category": "Pizza", "price": 1850, "description": "BBQ sauce with chicken", "available": True},
        {"name": "Vegetarian Pizza", "category": "Pizza", "price": 1650, "description": "Fresh vegetables", "available": True},
        
        # Pasta
        {"name": "Spaghetti Carbonara", "category": "Pasta", "price": 1550, "description": "Creamy pasta with bacon", "available": True},
        {"name": "Fettuccine Alfredo", "category": "Pasta", "price": 1450, "description": "Creamy alfredo sauce", "available": True},
        {"name": "Penne Arrabiata", "category": "Pasta", "price": 1350, "description": "Spicy tomato sauce", "available": True},
        
        # Desserts
        {"name": "Chocolate Cake", "category": "Desserts", "price": 650, "description": "Rich chocolate layer cake", "available": True},
        {"name": "Cheesecake", "category": "Desserts", "price": 750, "description": "New York style cheesecake", "available": True},
        {"name": "Ice Cream Sundae", "category": "Desserts", "price": 550, "description": "Ice cream with toppings", "available": True},
        {"name": "Tiramisu", "category": "Desserts", "price": 850, "description": "Italian coffee dessert", "available": True},
        
        # Beverages
        {"name": "Coca Cola", "category": "Beverages", "price": 250, "description": "Classic cola", "available": True},
        {"name": "Orange Juice", "category": "Beverages", "price": 350, "description": "Fresh orange juice", "available": True},
        {"name": "Iced Tea", "category": "Beverages", "price": 300, "description": "Refreshing iced tea", "available": True},
        {"name": "Mineral Water", "category": "Beverages", "price": 200, "description": "Bottled water", "available": True},
        
        # Coffee
        {"name": "Espresso", "category": "Coffee", "price": 350, "description": "Strong Italian coffee", "available": True},
        {"name": "Cappuccino", "category": "Coffee", "price": 450, "description": "Espresso with steamed milk", "available": True},
        {"name": "Latte", "category": "Coffee", "price": 500, "description": "Smooth coffee with milk", "available": True},
        {"name": "Americano", "category": "Coffee", "price": 400, "description": "Espresso with hot water", "available": True},
    ]
    
    cat_dict = {cat.name: cat for cat in categories}
    products = []
    
    for prod_data in products_data:
        category = cat_dict.get(prod_data.pop("category"))
        if category:
            product = Product(
                **prod_data,
                category_id=category.id,
                slug=prod_data["name"].lower().replace(" ", "-"),
                stock=100,
                cost=int(prod_data["price"] * 0.6)  # Cost is 60% of price
            )
            db.add(product)
            products.append(product)
    
    db.commit()
    print(f"✓ Created {len(products)} products")
    return products


def seed_modifiers(db: Session):
    """Seed modifiers and options"""
    print("\nSeeding modifiers...")
    
    modifiers_data = [
        {
            "name": "Size",
            "type": "single",
            "required": True,
            "category": "general",
            "options": [
                {"name": "Small", "price": 0},
                {"name": "Medium", "price": 200},
                {"name": "Large", "price": 400},
            ]
        },
        {
            "name": "Extra Toppings",
            "type": "multiple",
            "required": False,
            "category": "pizza",
            "options": [
                {"name": "Extra Cheese", "price": 150},
                {"name": "Mushrooms", "price": 100},
                {"name": "Olives", "price": 100},
                {"name": "Peppers", "price": 100},
                {"name": "Onions", "price": 80},
            ]
        },
        {
            "name": "Cooking Level",
            "type": "single",
            "required": True,
            "category": "meat",
            "options": [
                {"name": "Rare", "price": 0},
                {"name": "Medium Rare", "price": 0},
                {"name": "Medium", "price": 0},
                {"name": "Well Done", "price": 0},
            ]
        },
        {
            "name": "Extras",
            "type": "multiple",
            "required": False,
            "category": "burger",
            "options": [
                {"name": "Bacon", "price": 200},
                {"name": "Avocado", "price": 150},
                {"name": "Egg", "price": 100},
                {"name": "Extra Patty", "price": 300},
            ]
        },
    ]
    
    modifiers = []
    for mod_data in modifiers_data:
        options_data = mod_data.pop("options")
        modifier = Modifier(**mod_data)
        db.add(modifier)
        db.flush()
        
        for idx, opt_data in enumerate(options_data):
            option = ModifierOption(
                **opt_data,
                modifier_id=modifier.id,
                sort_order=idx
            )
            db.add(option)
        
        modifiers.append(modifier)
    
    db.commit()
    print(f"✓ Created {len(modifiers)} modifiers")
    return modifiers


def seed_customers(db: Session):
    """Seed customers"""
    print("\nSeeding customers...")
    
    customers_data = [
        {"name": "Alice Johnson", "phone": "5551234567", "email": "alice@email.com", "loyalty_points": 150},
        {"name": "Bob Smith", "phone": "5551234568", "email": "bob@email.com", "loyalty_points": 300},
        {"name": "Carol White", "phone": "5551234569", "email": "carol@email.com", "loyalty_points": 75},
        {"name": "David Brown", "phone": "5551234570", "email": "david@email.com", "loyalty_points": 500},
        {"name": "Emma Davis", "phone": "5551234571", "email": "emma@email.com", "loyalty_points": 200},
        {"name": "Frank Wilson", "phone": "5551234572", "email": "frank@email.com", "loyalty_points": 0},
        {"name": "Grace Lee", "phone": "5551234573", "email": "grace@email.com", "loyalty_points": 425},
        {"name": "Henry Miller", "phone": "5551234574", "email": "henry@email.com", "loyalty_points": 180},
    ]
    
    customers = []
    for cust_data in customers_data:
        customer = Customer(
            **cust_data,
            address=f"{random.randint(100, 999)} Main St",
            total_spent=cust_data["loyalty_points"] * 100,  # $1 per point
            visit_count=random.randint(1, 20)
        )
        db.add(customer)
        customers.append(customer)
    
    db.commit()
    print(f"✓ Created {len(customers)} customers")
    return customers


def seed_loyalty_rules(db: Session):
    """Seed loyalty rules"""
    print("\nSeeding loyalty rules...")
    
    rules_data = [
        {
            "name": "Standard Points - Earn 1 point per $1 spent",
            "earn_rate": 100,  # 1.00 points per dollar
            "redeem_rate": 100,  # 1.00 dollar per point
            "min_redeem_points": 100,
            "max_redeem_percentage": 50,
            "expiry_days": 365,
            "active": True,
            "priority": 1
        },
        {
            "name": "VIP Tier - 2x points on all purchases",
            "earn_rate": 200,  # 2.00 points per dollar
            "redeem_rate": 100,
            "min_redeem_points": 50,
            "max_redeem_percentage": 75,
            "expiry_days": 365,
            "active": True,
            "priority": 2,
            "applicable_tags": '["VIP"]'
        },
        {
            "name": "Premium Redemption - Reduced minimum",
            "earn_rate": 100,
            "redeem_rate": 100,
            "min_redeem_points": 25,
            "max_redeem_percentage": 30,
            "expiry_days": 180,
            "active": True,
            "priority": 3,
            "applicable_tags": '["Premium"]'
        }
    ]
    
    rules = []
    for rule_data in rules_data:
        rule = LoyaltyRule(**rule_data)
        db.add(rule)
        rules.append(rule)
    
    db.commit()
    print(f"✓ Created {len(rules)} loyalty rules")
    return rules


def seed_qr_tables(db: Session):
    """Seed QR tables"""
    print("\nSeeding QR tables...")
    
    table_data = [
        {"name": "Table 1", "location": "Main Hall", "capacity": 4},
        {"name": "Table 2", "location": "Main Hall", "capacity": 4},
        {"name": "Table 3", "location": "Main Hall", "capacity": 6},
        {"name": "Table 4", "location": "Main Hall", "capacity": 2},
        {"name": "Patio 1", "location": "Patio", "capacity": 4},
        {"name": "Patio 2", "location": "Patio", "capacity": 6},
        {"name": "VIP 1", "location": "VIP Room", "capacity": 8},
        {"name": "VIP 2", "location": "VIP Room", "capacity": 8},
    ]
    tables = []
    
    for i, data in enumerate(table_data, 1):
        qr_token = f"QR{random.randint(100000, 999999)}"
        table = QRTable(
            table_number=f"T{i:02d}",
            table_name=data["name"],
            qr_token=qr_token,
            qr_code_url=f"https://pos.restaurant.com/qr/{qr_token}",
            location=data["location"],
            capacity=data["capacity"],
            is_active=True,
            is_occupied=False
        )
        db.add(table)
        tables.append(table)
    
    db.commit()
    print(f"✓ Created {len(tables)} QR tables")
    return tables


def seed_tax_rules(db: Session):
    """Seed tax rules"""
    print("\nSeeding tax rules...")
    
    rules_data = [
        {
            "name": "Sales Tax (8%)",
            "type": "percentage",
            "percentage": 800,  # 8% stored as 800
            "applicable_on": "all",
            "active": True,
            "priority": 1,
            "is_compounded": False
        },
        {
            "name": "Dine-in Service Charge (5%)",
            "type": "percentage",
            "percentage": 500,  # 5% stored as 500
            "applicable_on": "dine_in",
            "active": True,
            "priority": 2,
            "is_compounded": False
        }
    ]
    
    rules = []
    for rule_data in rules_data:
        rule = TaxRule(**rule_data)
        db.add(rule)
        rules.append(rule)
    
    db.commit()
    print(f"✓ Created {len(rules)} tax rules")
    return rules


def seed_combo_products(db: Session, categories, products):
    """Seed combo products"""
    print("\nSeeding combo products...")
    
    # Find relevant products
    burger_cat = next((c for c in categories if c.name == "Burgers"), None)
    beverage_cat = next((c for c in categories if c.name == "Beverages"), None)
    
    if not burger_cat or not beverage_cat:
        print("⚠ Skipping combos - categories not found")
        return []
    
    combos_data = [
        {
            "name": "Burger Combo",
            "description": "Burger with fries and drink",
            "price": 1800,
            "category_id": burger_cat.id
        },
        {
            "name": "Lunch Special",
            "description": "Any burger + side + drink",
            "price": 2200,
            "category_id": burger_cat.id
        }
    ]
    
    combos = []
    for combo_data in combos_data:
        combo = ComboProduct(
            **combo_data,
            slug=combo_data["name"].lower().replace(" ", "-"),
            available=True,
            featured=True
        )
        db.add(combo)
        combos.append(combo)
    
    db.commit()
    print(f"✓ Created {len(combos)} combo products")
    return combos


def seed_orders(db: Session, customers, products, users):
    """Seed sample orders"""
    print("\nSeeding orders...")
    
    if not products:
        print("⚠ No products available to create orders")
        return []
    
    orders = []
    
    for i in range(15):
        customer = random.choice(customers) if customers else None
        user = random.choice(users) if users else None
        
        # Create order
        order_date = datetime.utcnow() - timedelta(days=random.randint(0, 30))
        order = Order(
            order_number=f"ORD-{order_date.strftime('%y%m%d')}-{random.randint(1000, 9999)}",
            customer_id=customer.id if customer else None,
            customer_name=customer.name if customer else "Guest",
            created_by=user.id if user else None,
            order_type=random.choice(["dine_in", "takeaway", "delivery", "qr_order"]),
            status=random.choice(["confirmed", "preparing", "ready", "completed"]),
            payment_status=random.choice(["pending", "completed"]),
            payment_method=random.choice(["cash", "card", "online"]),
            subtotal=0,
            tax_total=0,
            total=0,
            created_at=order_date
        )
        db.add(order)
        db.flush()
        
        # Add order items
        num_items = random.randint(1, 5)
        order_subtotal = 0
        
        for _ in range(num_items):
            product = random.choice(products)
            quantity = random.randint(1, 3)
            item_price = product.price
            
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                product_name=product.name,
                quantity=quantity,
                unit_price=item_price,
                total_price=item_price * quantity,
                department="kitchen",
                special_instructions=None
            )
            db.add(order_item)
            order_subtotal += item_price * quantity
        
        # Update order totals
        tax_amount = int(order_subtotal * 0.08)  # 8% tax
        order.subtotal = order_subtotal
        order.tax_total = tax_amount
        order.total = order_subtotal + tax_amount
        
        orders.append(order)
    
    db.commit()
    print(f"✓ Created {len(orders)} orders")
    return orders


def main():
    """Main seeding function"""
    print("=" * 60)
    print("Restaurant POS - Sample Data Seeding")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Ask for confirmation
        response = input("\n⚠️  This will clear existing data and insert sample data. Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            return
        
        # Clear existing data (except users)
        clear_existing_data(db)
        
        # Seed data in order
        users = seed_users(db)
        seed_shift_schedules(db, users)
        categories = seed_categories(db)
        products = seed_products(db, categories)
        modifiers = seed_modifiers(db)
        customers = seed_customers(db)
        seed_loyalty_rules(db)
        seed_qr_tables(db)
        seed_tax_rules(db)
        seed_combo_products(db, categories, products)
        seed_orders(db, customers, products, users)
        
        print("\n" + "=" * 60)
        print("✅ Sample data seeding completed successfully!")
        print("=" * 60)
        print("\nSample Login Credentials:")
        print("  Admin:     admin@restaurant.com / Admin123!")
        print("  Manager:   manager@restaurant.com / Manager123!")
        print("  Cashier1:  cashier@restaurant.com / Cashier123!")
        print("  Staff:     staff@restaurant.com / Staff123!")
        print("  Cashier2:  cashier2@restaurant.com / Cashier123!")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
