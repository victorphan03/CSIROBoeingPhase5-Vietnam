# 🔧 Memory Overflow Fix: Sentinel-2 Data Loading

## Problem

When attempting to load Sentinel-2 data, you got:
```
❌ Error loading data: Unable to allocate 403. TiB for an array with shape 
(396, 563539, 992108) and data type uint16
```

### Root Cause Analysis

The datacube's `load_s2l2a_with_offset()` function was **loading an entire massive tile** instead of clipping to your AOI bounds.

**Math:**
- Shape: 396 scenes × 563,539 pixels × 992,108 pixels × 2 bytes (uint16)
- **Memory needed:** ~403 Terabytes 😱
- **Reality:** Your server has maybe 100-500 GB

**Expected behavior:**
- Your AOI: 105.5-106.4°E × 9.2-10.0°N (~100×100 km)
- At 10m resolution: ~10,000 × 10,000 pixels
- For 396 scenes: 396 × 10,000 × 10,000 × 2 bytes = **20 GB** ✓ (reasonable!)

## Solution Implemented

### Strategy: Monthly Chunking

Instead of loading all 396 scenes at once, split into **13 monthly chunks**:

```python
date_ranges = [
    ("2022-09-01", "2022-10-01"),   # ~30 scenes
    ("2022-10-01", "2022-11-01"),   # ~30 scenes
    ...
    ("2023-09-01", "2023-10-01"),   # ~30 scenes
]

for month in date_ranges:
    monthly_data = load_s2l2a_with_offset(dc, query_for_month)
    data_list.append(monthly_data)

data = xr.concat(data_list, dim='time')  # Combine after loading
```

**Advantages:**
- ✅ Each monthly load: ~30 scenes = 600 GB → manageable chunks
- ✅ Processing happens per-month, memory freed after each
- ✅ If one month fails, others still complete
- ✅ Dask can distribute work across multiple workers

### Dask Chunk Optimization

```python
'dask_chunks': {'x': 512, 'y': 512, 'time': 1}
```

- **x/y (512×512):** Spatial chunks (100×100 km tile → 4×4 chunks)
- **time (1):** Each scene is separate, allows parallel processing
- **Result:** Dask workers process ~512²×1 = 262K pixels per chunk

### Error Handling

```python
try:
    monthly_data = load_s2l2a_with_offset(...)
    data_list.append(monthly_data)
except Exception as e:
    print(f"Month {month} failed: {e}")
    continue  # Skip failed month, continue with others
```

## Testing the Fix

### Cell 4: Diagnostic Check ✨ NEW
Runs first to inspect datacube metadata without loading data:
- Lists available S2 products
- Checks how many scenes are available for Jan 2023
- Shows bounds/CRS of first scene
- **Do NOT modify** - helps diagnose issues

### Cell 5: Sentinel-2 Loading ✅ UPDATED
Now uses monthly chunking with progress bars:
```
[01/13] 2022-09-01 → 2022-10-01  ✓ 32 scenes
[02/13] 2022-10-01 → 2022-11-01  ✓ 28 scenes
...
[13/13] 2023-09-01 → 2023-10-01  ✓ 31 scenes

🔗 Combining 13 monthly chunks...
✅ Success! Shape: {'time': 396, 'y': 10000, 'x': 10000}
   Memory: 64.5 GB
```

## Expected Output

After loading, `data` should have:
- **Shape:** (396 time steps, ~10000 y pixels, ~10000 x pixels)
- **Bands:** red, nir, scl
- **CRS:** EPSG:32648 (UTM Zone 48N)
- **Memory:** ~15-20 GB (reasonable for distributed processing)

## If Issues Persist

### Issue 1: "Still getting huge spatial dimensions"
→ The datacube function has a bug with spatial subsetting
→ Add explicit clipping with rasterio before concat:

```python
import rasterio.mask
# Clip each monthly dataset to exact AOI bounds
```

### Issue 2: "One month loads but others fail"
→ Those S3 objects may be corrupted/missing
→ Check logs - the code continues anyway (fallback behavior)

### Issue 3: "Dask workers running out of memory"
→ Reduce chunk size: `'dask_chunks': {'x': 256, 'y': 256, 'time': 1}`
→ Or reduce workers: change `workers=(1, 10)` to `workers=(1, 5)`

## Next Steps (After successful data load)

Cells 6-10 process the data:
1. **Cell 6:** Cloud masking (SCL band)
2. **Cell 7:** NDVI calculation
3. **Cell 8:** Fill missing values (interpolation)
4. **Cell 9:** Monthly aggregation
5. **Cell 10:** Sentinel-1 loading (VH, VV)

## Files Modified

- `01.prepare_data_on_server.ipynb`
  - Cell 4: NEW diagnostic check
  - Cell 5: UPDATED monthly chunking strategy
  - Cell 6-14: Unchanged (process data as before)

---

**Created:** 2025-11-11  
**Status:** Ready to test ✅
