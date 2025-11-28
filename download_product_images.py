"""
Download sample product images and update database
"""
import os
import requests
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from app.database import SessionLocal
from sqlalchemy import text

# Create uploads directory if it doesn't exist
UPLOADS_DIR = Path(__file__).parent / "uploads" / "products"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Sample images from placeholder services (publicly available)
PRODUCT_IMAGES = {
    # Appetizers
    "spring-rolls": "https://images.unsplash.com/photo-1534422298391-e4f8c172dddb?w=400",
    "garlic-bread": "https://images.unsplash.com/photo-1573140401552-388e3a0c713d?w=400",
    "buffalo-wings": "https://images.unsplash.com/photo-1608039829572-78524f79c4c7?w=400",
    
    # Main Course
    "grilled-chicken": "https://images.unsplash.com/photo-1598103442097-8b74394b95c6?w=400",
    "beef-steak": "https://images.unsplash.com/photo-1600891964092-4316c288032e?w=400",
    "fish-chips": "https://images.unsplash.com/photo-1580217593608-61931cefc821?w=400",
    
    # Burgers
    "classic-burger": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400",
    "cheese-burger": "https://images.unsplash.com/photo-1550547660-d9450f859349?w=400",
    "chicken-burger": "https://images.unsplash.com/photo-1606755962773-d324e0a13086?w=400",
    "veggie-burger": "https://images.unsplash.com/photo-1520072959219-c595dc870360?w=400",
    
    # Pizza
    "margherita-pizza": "https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=400",
    "pepperoni-pizza": "https://images.unsplash.com/photo-1628840042765-356cda07504e?w=400",
    "bbq-chicken-pizza": "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400",
    "vegetarian-pizza": "https://images.unsplash.com/photo-1511689660979-10d2b1aada49?w=400",
    
    # Pasta
    "spaghetti-carbonara": "https://images.unsplash.com/photo-1612874742237-6526221588e3?w=400",
    "fettuccine-alfredo": "https://images.unsplash.com/photo-1645112411341-6c4fd023714a?w=400",
    "penne-arrabiata": "https://images.unsplash.com/photo-1621996346565-e3dbc646d9a9?w=400",
    
    # Desserts
    "chocolate-cake": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=400",
    "cheesecake": "https://images.unsplash.com/photo-1533134486753-c833f0ed4866?w=400",
    "ice-cream-sundae": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=400",
    "tiramisu": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=400",
    
    # Beverages
    "coca-cola": "https://images.unsplash.com/photo-1554866585-cd94860890b7?w=400",
    "orange-juice": "https://images.unsplash.com/photo-1600271886742-f049cd451bba?w=400",
    "iced-tea": "https://images.unsplash.com/photo-1556679343-c7306c1976bc?w=400",
    "mineral-water": "https://images.unsplash.com/photo-1548839140-29a749e1cf4d?w=400",
    
    # Coffee
    "espresso": "https://images.unsplash.com/photo-1510591509098-f4fdc6d0ff04?w=400",
    "cappuccino": "https://images.unsplash.com/photo-1572442388796-11668a67e53d?w=400",
    "latte": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=400",
    "americano": "https://images.unsplash.com/photo-1497935586351-b67a49e012bf?w=400",
}

def download_image(url, filename):
    """Download image from URL"""
    try:
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        filepath = UPLOADS_DIR / filename
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        print(f"✓ Downloaded: {filename}")
        return f"/uploads/products/{filename}"
    except Exception as e:
        print(f"✗ Failed to download {filename}: {e}")
        return None

def update_product_images():
    """Update database with image paths"""
    db = SessionLocal()
    
    try:
        for slug, url in PRODUCT_IMAGES.items():
            # Download image
            filename = f"{slug}.jpg"
            image_path = download_image(url, filename)
            
            if image_path:
                # Update product in database
                query = text("""
                    UPDATE products 
                    SET image = :image_path
                    WHERE slug = :slug
                """)
                result = db.execute(query, {"image_path": image_path, "slug": slug})
                db.commit()
                
                if result.rowcount > 0:
                    print(f"  ✓ Updated product: {slug}")
                else:
                    print(f"  ⚠ Product not found: {slug}")
        
        print(f"\n✅ Image download and database update complete!")
        print(f"📁 Images saved to: {UPLOADS_DIR}")
        
        # Show summary
        query = text("SELECT COUNT(*) as count FROM products WHERE image IS NOT NULL")
        result = db.execute(query).fetchone()
        print(f"📊 Products with images: {result[0]}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🖼️  Starting product image download...")
    print(f"📂 Target directory: {UPLOADS_DIR}")
    print(f"📥 Downloading {len(PRODUCT_IMAGES)} images...\n")
    
    update_product_images()
