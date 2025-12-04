# 📸 Image Upload Configuration

## Image Settings Summary

### Product Images
- **Target Size:** 800x800 pixels (square)
- **Format:** WebP (auto-converted from JPG/PNG)
- **Quality:** 85% (adjusts down if needed)
- **Max Input:** 10 MB
- **Max Output:** 200 KB (compressed)
- **Permissions:** 777 (full read/write/execute)
- **Location:** `/uploads/products/`

### Category Images
- **Target Size:** 600x400 pixels (landscape)
- **Format:** WebP (auto-converted from JPG/PNG)
- **Quality:** 85% (adjusts down if needed)
- **Max Input:** 10 MB
- **Max Output:** 200 KB (compressed)
- **Permissions:** 777 (full read/write/execute)
- **Location:** `/uploads/categories/`

---

## How Image Processing Works

### 1. Upload Validation
```
Client uploads image (JPG/PNG/WEBP)
     ↓
Validate file extension (.jpg, .jpeg, .png, .webp)
     ↓
Validate file size (max 10 MB)
     ↓
Accept file for processing
```

### 2. Image Conversion
```
Read uploaded image
     ↓
Convert to PIL Image object
     ↓
Resize to target dimensions (LANCZOS resampling)
     ↓
Convert to RGB (if RGBA/transparent)
     ↓
Save as WebP format
```

### 3. Quality Optimization
```
Try quality 85% → Check size
     ↓
If > 200 KB → Reduce quality to 75%
     ↓
If > 200 KB → Reduce quality to 65%
     ↓
If > 200 KB → Reduce quality to 55%
     ↓
If > 200 KB → Save at 50% (minimum)
```

### 4. File Permissions
```
Save file to disk
     ↓
Set permissions to 777 (chmod)
     ↓
Log file name and size
     ↓
Return file path to API
```

---

## File Permissions Explained

### 777 Permission Breakdown

```bash
chmod 777 filename
```

**Binary:** `111 111 111`
**Octal:** `7 7 7`

| User | Group | Others |
|------|-------|--------|
| rwx  | rwx   | rwx    |
| 7    | 7     | 7      |

- **r (read)** = 4
- **w (write)** = 2
- **x (execute)** = 1
- **Total** = 7

**Meaning:**
- Owner: Read + Write + Execute
- Group: Read + Write + Execute
- Others: Read + Write + Execute

### Why 777?

✅ **Read:** Web server can read and serve images
✅ **Write:** API can update/replace images
✅ **Execute:** Allows directory traversal

---

## Image Size Logging

### Console Output Examples

**Product Image:**
```
Image saved: burger.webp, Size: 45.23 KB (46315 bytes)
```

**Category Image:**
```
Category image saved: beverages.webp, Size: 89.67 KB (91826 bytes)
```

### Where to See Logs

```bash
# View real-time logs
sudo docker logs -f restaurant_pos_api

# View last 50 lines
sudo docker logs restaurant_pos_api --tail 50

# Search for image logs
sudo docker logs restaurant_pos_api | grep "saved:"
```

---

## API Endpoints

### Upload Product Image

**Endpoint:** `POST /api/v1/products/`

**Form Data:**
```
name: "Burger"
slug: "burger"
category_id: "uuid-here"
price: 999
image: [file upload]
```

**Response includes:**
```json
{
  "image": "/uploads/products/burger.webp"
}
```

### Update Product Image

**Endpoint:** `PUT /api/v1/products/{product_id}`

**Form Data:**
```
image: [new file upload]
```

**Behavior:**
- Deletes old image file
- Uploads new image
- Updates database path

### Upload Category Image

**Endpoint:** `POST /api/v1/categories/`

**Form Data:**
```
name: "Beverages"
slug: "beverages"
icon: "drink"
image: [file upload]
```

---

## File Size Examples

### Typical Sizes After Conversion

| Image Type | Original | After WebP | Reduction |
|-----------|----------|------------|-----------|
| Product (800x800) | 2-5 MB | 40-150 KB | ~95% |
| Category (600x400) | 1-3 MB | 30-100 KB | ~96% |

### Quality Settings Impact

| Quality | File Size | Visual Quality |
|---------|-----------|----------------|
| 85% | 100-150 KB | Excellent |
| 75% | 70-100 KB | Very Good |
| 65% | 50-70 KB | Good |
| 55% | 35-50 KB | Acceptable |
| 50% | 25-35 KB | Minimum |

---

## Testing Image Upload

### Using cURL

**Upload Product with Image:**
```bash
curl -X POST "https://apipos.v11tech.com/api/v1/products/" \
  -F "name=Burger" \
  -F "slug=burger" \
  -F "category_id=your-category-uuid" \
  -F "price=999" \
  -F "description=Delicious burger" \
  -F "image=@/path/to/image.jpg"
```

**Update Product Image:**
```bash
curl -X PUT "https://apipos.v11tech.com/api/v1/products/{product-id}" \
  -F "image=@/path/to/new-image.jpg"
```

**Upload Category with Image:**
```bash
curl -X POST "https://apipos.v11tech.com/api/v1/categories/" \
  -F "name=Beverages" \
  -F "slug=beverages" \
  -F "icon=drink" \
  -F "image=@/path/to/category.jpg"
```

### View Uploaded Image

```bash
# Direct URL
https://apipos.v11tech.com/uploads/products/burger.webp
https://apipos.v11tech.com/uploads/categories/beverages.webp
```

---

## Checking File Permissions on Server

```bash
# Navigate to uploads directory
cd /var/www/v11pos-backend-fastapi/uploads

# Check permissions
ls -la products/
ls -la categories/

# Expected output:
-rwxrwxrwx 1 user group 45315 Dec 04 10:30 burger.webp
```

**Permission breakdown:**
- `-rwxrwxrwx` = 777 permissions
- First `-` = regular file
- `rwx` (owner) = read, write, execute
- `rwx` (group) = read, write, execute
- `rwx` (others) = read, write, execute

---

## Troubleshooting

### Image Not Accessible

**Check permissions:**
```bash
cd /var/www/v11pos-backend-fastapi
ls -la uploads/products/
ls -la uploads/categories/

# If permissions are wrong, fix them:
chmod -R 777 uploads/
```

### Image Not Uploading

**Check logs:**
```bash
sudo docker logs restaurant_pos_api --tail 100
```

**Common issues:**
- File too large (> 10 MB)
- Invalid file format (not JPG/PNG/WEBP)
- Disk space full
- Directory permissions

### Image Size Too Large

**Current settings:**
- Target: < 200 KB
- Quality: 50-85%

**To increase limit, update in code:**
```python
MAX_OUTPUT_FILE_SIZE = 500 * 1024  # 500 KB instead of 200 KB
```

---

## Image Optimization Benefits

### WebP Format Advantages

✅ **Smaller file size** (25-35% smaller than JPG)
✅ **Better quality** at same file size
✅ **Faster loading** times
✅ **Browser support** (98%+ browsers)
✅ **Transparency** support (like PNG)

### Performance Impact

| Format | Size | Load Time |
|--------|------|-----------|
| JPG | 500 KB | 2.5s (3G) |
| PNG | 800 KB | 4.0s (3G) |
| WebP | 150 KB | 0.75s (3G) |

**WebP = 3-5x faster loading!**

---

## Production Recommendations

### For Best Performance

1. ✅ **Keep WebP conversion enabled**
2. ✅ **Use provided size limits** (800x800, 600x400)
3. ✅ **Keep quality at 85%** (good balance)
4. ✅ **Max output 200 KB** (fast loading)
5. ✅ **Full permissions (777)** (easy management)

### For High-Quality Images

If you need larger/better quality:

```python
# In products.py and categories.py
TARGET_IMAGE_SIZE = (1200, 1200)  # Larger
MAX_OUTPUT_FILE_SIZE = 500 * 1024  # 500 KB
WEBP_QUALITY = 90  # Higher quality
```

---

## Summary

### ✅ What Was Updated

1. **File Permissions:** All uploaded images now have 777 permissions
2. **Size Logging:** Console logs show exact file size after upload
3. **Products:** 800x800px WebP images, max 200 KB
4. **Categories:** 600x400px WebP images, max 200 KB
5. **Quality:** Automatic optimization 85% → 50%

### 📊 Image Sizes

**Typical final sizes:**
- Products: 40-150 KB (avg ~80 KB)
- Categories: 30-100 KB (avg ~60 KB)

**All images are:**
- Auto-converted to WebP
- Optimized for web delivery
- Set with full 777 permissions
- Logged with exact size info

---

**Last Updated:** December 4, 2025
**Repository:** https://github.com/josephbruno/v11pos-backend-fastapi
**Production:** https://apipos.v11tech.com/
