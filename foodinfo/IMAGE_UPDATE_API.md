# Image Update API for food-safety-check and barcode Endpoints

## Overview
Both the `food-safety-check/` and `barcode/` endpoints now support three HTTP methods for different use cases:

- **POST**: Create a new scan with full analysis
- **PATCH**: Update an existing scan with new image and re-run full analysis  
- **PUT**: Update only the image of an existing scan (lightweight, no re-analysis)

## PUT Method - Lightweight Image Update

### Purpose
Update only the image of an existing scan without re-running OCR, nutrition analysis, safety checks, or AI insights. This is perfect when you just want to replace a blurry image with a clearer one.

### API Usage

**For food-safety-check endpoint:**
```json
PUT /food-safety-check/
{
    "image": <new_image_file>,
    "scan_id": 123
}
```

**For barcode endpoint:**
```json
PUT /barcode/
{
    "image": <new_image_file>,
    "scan_id": 123
}
```

### What It Does
1. ✅ **Validates** the scan belongs to the authenticated user
2. ✅ **Saves** the new image to storage
3. ✅ **Updates** only the image URLs in the database:
   - `image_url` field
   - `product_image_url` field  
   - `nutrition_data.product_image.full` field
4. ✅ **Preserves** all existing analysis data (OCR text, nutrition, safety status, etc.)

### What It Does NOT Do
- ❌ No OCR processing
- ❌ No nutrition analysis
- ❌ No safety validation
- ❌ No AI insights
- ❌ No scan count increment

### Response

```json
{
    "scan_id": 123,
    "product_name": "Product Name",
    "image_url": "https://storage.com/food_labels/new-uuid.jpg",
    "updated_existing_scan": true,
    "message": "Image updated successfully. All other data remains unchanged.",
    "extracted_text": "Original OCR text...",
    "nutrition_data": { /* Original nutrition data */ },
    "safety_status": "SAFE",
    "is_favorite": false
}
```

### Error Responses

**400 Bad Request** - Missing scan_id:
```json
{
    "error": "scan_id is required for PUT requests"
}
```

**404 Not Found** - Scan doesn't exist or access denied:
```json
{
    "error": "Scan not found or access denied"
}
```

**500 Internal Server Error** - Image upload failed:
```json
{
    "error": "Image upload failed"
}
```

## Comparison of Methods

| Method | Purpose | Analysis | Performance | Use Case |
|--------|---------|----------|-------------|----------|
| **POST** | Create new scan | Full analysis | Slow (5-10s) | First-time scanning |
| **PATCH** | Update scan with re-analysis | Full analysis | Slow (5-10s) | Better image + re-analysis needed |
| **PUT** | Update image only | No analysis | Fast (1-2s) | Just replace blurry image |

## Available Endpoints

Both endpoints support the same functionality:

- **`/food-safety-check/`** - For OCR-based food label scanning
- **`/barcode/`** - For barcode-based product scanning

## Use Cases for PUT Method

1. **Image Quality Improvement**: Replace a blurry photo with a clearer one
2. **Image Compression**: Replace a large image with a compressed version
3. **Image Rotation**: Fix orientation without losing analysis data
4. **Quick Updates**: Fast image replacement without waiting for full analysis

## Security

- Users can only update their own scans
- Scan ownership is validated before any updates
- No scan count is incremented (preserves user limits)

## Performance Benefits

- **Fast**: No OCR, AI, or safety processing
- **Efficient**: Only updates image URLs
- **Preserves Data**: All existing analysis remains intact
- **Lightweight**: Minimal server resources used
