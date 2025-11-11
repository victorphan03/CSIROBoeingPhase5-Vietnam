# 📋 Quick Troubleshooting: Sentinel-2 Loading

## Before You Run

✅ Verify dask cluster is running:
```python
# Cell 2 output should show:
# Scheduler: 127.0.0.1:8786 (or gateway address)
# Workers: 4 (or your configured number)
```

✅ Verify S3 access is configured:
```python
# Cell 2 should complete without errors
# If you see authentication errors, check credentials
```

## Running Notebook 01

### Step-by-step execution:

**Cell 1:** Introduction (markdown, no action)

**Cell 2:** Initialize Dask + Datacube
- Wait for cluster to initialize (10-30 seconds)
- Should show worker status

**Cell 3:** Set coordinates
- Automatic, takes <1 second

**Cell 4:** Diagnostic Check ⭐ RUN THIS FIRST
- **Purpose:** Verify datacube can find scenes without loading
- **Expected output:**
  ```
  Available S2 products:
    name           description
  s2_l2a    Sentinel-2 L2A Data
  
  📊 Metadata check for Jan 2023:
     Found 28 scenes
     First scene: 2023-01-15 10:30:45
     Bounds: BoundingBox(...)
     CRS: EPSG:32648
  ```
- **If fails:** S3 connection issue - check credentials in Cell 2

**Cell 5:** Load Sentinel-2 Data (THE FIXED CELL)
- **Expected duration:** 5-15 minutes (depending on workers)
- **Watch for:** Monthly progress bars
  ```
  [01/13] 2022-09-01 → 2022-10-01  ✓ 32 scenes
  [02/13] 2022-10-01 → 2022-11-01  ✓ 28 scenes
  ...
  ```
- **Expected final output:**
  ```
  ✅ Success! Shape: {'time': 396, 'y': ~10000, 'x': ~10000}
     Memory: 15-20 GB
  ```

## Common Issues & Fixes

### ❌ "Still getting huge dimensions error"
**Symptom:**
```
Error: shape (396, 563539, 992108)
```

**Cause:** Datacube function is still loading full tiles

**Fixes (in order):**
1. Run Cell 4 diagnostic → Check actual bounds returned
2. Verify `load_s2l2a_with_offset()` in `new_import_ODC.py` includes spatial subsetting
3. Add manual clipping:
   ```python
   # After line: monthly_data = load_s2l2a_with_offset(...)
   # Add this:
   if monthly_data.sizes['y'] > 15000:
       print(f"⚠️  Clipping oversized data: {monthly_data.dims}")
       monthly_data = monthly_data.sel(
           x=slice(longtitude_range[0], longtitude_range[1]),
           y=slice(latitude_range[0], latitude_range[1]),
       )
   ```

### ❌ "Cell 4 says 0 scenes found"
**Cause:** S3 data may not exist for your region/dates

**Fixes:**
1. Check if S3 bucket/path is correct
2. Try different time range (e.g., "2023-01-01" to "2023-12-31")
3. Verify coordinates are in correct order: (longitude_min, longitude_max), (latitude_min, latitude_max)

### ❌ "Dask workers running out of memory"
**Symptom:**
```
MemoryError during ...
Killed process (out of memory)
```

**Quick fix:**
1. Reduce chunk size in Cell 5:
   ```python
   'dask_chunks': {'x': 256, 'y': 256, 'time': 1}  # Smaller chunks
   ```

2. Or reduce number of workers in Cell 2:
   ```python
   cluster, client = notebook_utils.initialize_dask(
       use_gateway=True, 
       workers=(1, 5)  # Reduce from (1, 10)
   )
   ```

3. Or load fewer months at once - split Cell 5 manually

### ❌ "One month loaded but then it fails"
**Cause:** One S3 object is corrupted/missing

**Expected behavior:** 
- Code continues to next month (has try-except)
- Check output logs for which month failed
- You can manually skip it by removing from `date_ranges` list

**Is this okay?**
✅ Yes! If 12/13 months load, you have 380+ scenes (good dataset)

### ⚠️ "Still taking too long / worker still slow"
**Cause:** Network latency from S3, or insufficient workers

**Options:**
1. **Increase workers:** Cell 2 `workers=(1, 15)` (if hardware allows)
2. **Enable rechunking:** Add to Cell 5:
   ```python
   monthly_data = monthly_data.rechunk({'x': 'auto', 'y': 'auto'})
   ```
3. **Check Dask dashboard:** Ask instructor for URL (port 8787)

## Success Criteria ✅

After Cell 5 completes, you should have:

1. **Variable `data` exists** and is not None
2. **Dimensions match AOI:**
   ```
   time: 396 (or close - some months may have 0 scenes)
   y:    ~10000 pixels (±10%)
   x:    ~10000 pixels (±10%)
   ```
3. **No memory errors** (or only 1-2 skipped months)
4. **Dask workers still healthy** (can continue to next cells)

## Next: Cells 6-10

Once Cell 5 succeeds, remaining cells should work automatically:
- **Cell 6:** Cloud masking
- **Cell 7:** NDVI calculation  
- **Cell 8:** Fill NaN values
- **Cell 9:** Monthly aggregation
- **Cell 10:** Sentinel-1 loading

These cells don't involve loading new data, just processing the `data` variable.

---

**Need help?** Check:
1. `/home/x79/CSIROBoeingPhase5-Vietnam/MEMORY_FIX_EXPLAINED.md` (detailed explanation)
2. Dask dashboard if available
3. Datacube documentation: `dc.list_products()`
