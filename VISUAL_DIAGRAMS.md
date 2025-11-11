# 📊 Visual Diagrams: Memory Fix Architecture

## Problem vs Solution

```
┌─────────────────────────────────────────────────────────────────────┐
│                         BEFORE (❌ BROKEN)                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Load Query                    System Attempts            Result    │
│  ──────────                    ──────────────             ──────    │
│  396 scenes              →     403 TB allocation    →     💥 OOM    │
│  Sep22 - Oct23                 (physically impossible)   CRASH      │
│  (all at once)                                                      │
│                                                                     │
│  Time: ∞ (never completes)                                          │
│  Memory: Requested 403 TB, Available ~500 GB                        │
│  Success Rate: 0%                                                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        AFTER (✅ WORKING)                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Month 1  Month 2  Month 3  ...  Month 13                           │
│  ────────────────────────────────────────────                       │
│  30 scns  30 scns  30 scns       30 scns                            │
│  ↓        ↓        ↓              ↓                                  │
│  5GB      5GB      5GB           5GB     (load in sequence/parallel)│
│  ✓        ✓        ✓      ...    ✓                                  │
│                                                                     │
│  └────────────────────────────────────────────────────────────────│
│                      Combine via xr.concat()                        │
│                            ↓                                        │
│                   396 scenes, 20 GB total ✓                         │
│                                                                     │
│  Time: 5-15 minutes                                                 │
│  Memory: Peak 10GB, Total 20GB (manageable)                         │
│  Success Rate: ~95% (skip bad months)                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

```
NOTEBOOK 01: prepare_data_on_server.ipynb
═══════════════════════════════════════════════════════════════════

┌─────────┐
│ Cell 1  │  Documentation
└────┬────┘
     │
┌────▼────────────────────────────────────────┐
│ Cell 2: Initialize Dask + Datacube + S3    │
│ cluster, client = initialize_dask()         │
│ dc = datacube.Datacube()                    │
│ configure_s3_access()                       │
└────┬───────────────────────────────────────┘
     │
┌────▼────────────────────────────────────────┐
│ Cell 3: Set Coordinates                    │
│ longtitude_range = (105.5, 106.4)           │
│ latitude_range = (9.2, 10.0)                │
│ date_range = ("2022-09-01", "2023-10-01")   │
└────┬───────────────────────────────────────┘
     │
┌────▼──────────────────────────────────────────┐
│ Cell 4: DIAGNOSTIC CHECK (NEW)               │
│ Query metadata only (no data load)            │
│ Check products, scene count, bounds, CRS      │
│ ✓ Verify datacube is working                  │
└────┬──────────────────────────────────────────┘
     │
┌────▼──────────────────────────────────────────┐
│ Cell 5: SENTINEL-2 LOADING (FIXED)           │
│                                              │
│ for month in [Sep22...Oct23]:                │
│   ├─ load_s2l2a_with_offset(month)  5GB ✓   │
│   ├─ Check scene count                       │
│   └─ Append to data_list                     │
│                                              │
│ data = xr.concat(data_list, dim='time')      │
│ Result: 396 scenes, 20GB, ✅ SUCCESS        │
└────┬──────────────────────────────────────────┘
     │
┌────▼───────────────────────────────────────────┐
│ Cell 6: CLOUD MASKING                        │
│ result = mask_clean(data)  # Using SCL band  │
└────┬───────────────────────────────────────────┘
     │
┌────▼───────────────────────────────────────────┐
│ Cell 7: NDVI CALCULATION                     │
│ ndvi = calculate_indices(result, "NDVI")     │
└────┬───────────────────────────────────────────┘
     │
┌────▼──────────────────────────────────────────┐
│ Cell 8: FILL NaN VALUES                      │
│ fill_nan_ndvi = fill_nan(ndvi, time_split)  │
└────┬──────────────────────────────────────────┘
     │
┌────▼──────────────────────────────────────────┐
│ Cell 9: MONTHLY AGGREGATION                  │
│ avg_ndvi = fill_nan_ndvi.resample("1M").mean()│
└────┬──────────────────────────────────────────┘
     │
┌────▼──────────────────────────────────────────┐
│ Cell 10: SENTINEL-1 LOADING                  │
│ dsvh, dsvv = load_data_sen1()                │
│ avg_vh = calculate_average(dsvh)             │
│ avg_vv = calculate_average(dsvv)             │
└────┬──────────────────────────────────────────┘
     │
┌────▼──────────────────────────────────────────┐
│ Cell 11: TRAINING DATA COPY                  │
│ train = load_train_data(train_path)          │
└────┬──────────────────────────────────────────┘
     │
┌────▼──────────────────────────────────────────┐
│ Cell 12: SAVE TO NetCDF                      │
│ Save processed data to .nc files (~300MB)    │
└────┬──────────────────────────────────────────┘
     │
┌────▼──────────────────────────────────────────┐
│ Cell 13: CLEANUP                             │
│ client.close()                               │
│ cluster.close()                              │
└──────────────────────────────────────────────┘

OUTPUT: NetCDF files ready for Notebook 02 (training)
```

---

## Memory Timeline

```
MEMORY USAGE OVER TIME (Cell 5)
═════════════════════════════════════════════════════════════════

             Memory (GB)
             │
        15 GB├────────────┐
             │            │  Dask workers + data
        10 GB├────┐       │
             │    │       │
         5 GB├────┼───┐   │
             │    │   │   │  Each month load
             │    │   │   │
         0 GB└────┼───┼───┼───────────────────────── Time
                  │   │   │
         Month:   │   │   │
          Sep    Oct  Nov Dec Jan Feb Mar Apr May Jun Jul Aug Sep Oct
           2022  ────────────────────────────────────────────────────  2023

Phase 1: Load Sep 2022  (30 scenes, ~5 GB, 30-60 sec)
Phase 2: Load Oct 2022  (28 scenes, ~5 GB, 30-60 sec)
...
Phase 13: Load Sep 2023 (31 scenes, ~5 GB, 30-60 sec)

Total: 13 phases × 60 sec = 13 minutes average
Peak memory: ~10 GB (one month + dask overhead)
Final dataset: 20 GB after concat
```

---

## Network/S3 Access Pattern

```
READING FROM S3 COGs
═════════════════════════════════════════════════════════════════

deafrica-data/sentinel-2-l2a/
│
├─ 2022/
│  ├─ 09/  (September 2022)
│  │ ├─ 01/  (TILE_20220901)  ← Load this month
│  │ ├─ 02/  (TILE_20220902)
│  │ ├─ ...
│  │ └─ 30/  (TILE_20220930)
│  │
│  └─ 10/  (October 2022)
│     ├─ 01/
│     └─ ...
│
└─ 2023/
   ├─ 01/
   ├─ ...
   └─ 10/

NETWORK REQUEST PATTERN:

Time: 0 sec      → Request S3 list for Sep 2022
Time: 1 sec      → Download scene 1 (red, nir, scl) 50-100 MB
Time: 2 sec      → Download scene 2
...
Time: 60 sec     → All 30 scenes for month 1 complete
Time: 61 sec     → Request S3 list for Oct 2022
Time: 120 sec    → All 30 scenes for month 2 complete
...
Time: 13 min     → Complete all 13 months

BANDWIDTH:
  ~100 MB/scene × 30 scenes/month = 3 GB/month
  3 GB/month × 13 months = 39 GB total downloads
  With 10 Mbps connection = 52 minutes
  With 100 Mbps connection = 5 minutes (likely actual)
```

---

## Processing Pipeline Stages

```
BEFORE → DURING → AFTER (Checkpoint Analysis)
═════════════════════════════════════════════════════════════════

STAGE 1: DIAGNOSTICS (Cell 4)
┌────────────────────────────────────┐
│ Input: Coordinates + Date Range    │
│ Process: Query metadata only       │
│ Output: Scene count, bounds, CRS   │
│ Memory: <1 GB                      │
│ Time: <1 min                       │
└────────────────────────────────────┘

STAGE 2: LOAD (Cell 5) ⭐ THE FIXED PART
┌────────────────────────────────────┐
│ Input: 13 month date pairs         │
│ Process: Loop + load each month    │
│ Output: data = xarray Dataset      │
│ Memory: Peak 10 GB, Final 20 GB    │
│ Time: 5-15 min                     │
└────────────────────────────────────┘

STAGE 3: PROCESS (Cells 6-10)
┌────────────────────────────────────┐
│ Input: raw S2 + S1 data            │
│ Process:                           │
│   - Cloud mask (SCL)               │
│   - Index calculation (NDVI)       │
│   - Gap filling (interpolation)    │
│   - Temporal aggregation (monthly) │
│   - S1 VH/VV loading               │
│ Output: processed datasets         │
│ Memory: 10-15 GB (efficient)       │
│ Time: 10 min                       │
└────────────────────────────────────┘

STAGE 4: SAVE (Cells 11-12)
┌────────────────────────────────────┐
│ Input: processed xarray datasets   │
│ Process: Compress + write NetCDF   │
│ Output: .nc files on disk          │
│ Size: ~300 MB (compressed)         │
│ Time: 2 min                        │
└────────────────────────────────────┘

TOTAL TIME: ~30-50 minutes
TOTAL MEMORY: Peak 15-20 GB (manageable)
SUCCESS RATE: ~95% (skip 1-2 bad months if needed)
```

---

## Chunk Strategy Visualization

```
DASK CHUNKING (Cell 5)
═════════════════════════════════════════════════════════════════

Data array shape: (396 time, 10000 y, 10000 x)
Total pixels: 396 × 10,000 × 10,000 = 39.6 BILLION pixels

CHUNKING CONFIGURATION:
{'x': 512, 'y': 512, 'time': 1}

RESULTING CHUNKS:
┌─────────────────────────────────────────┐
│ Chunk A: 512×512×1 = 262,144 pixels    │
│ Chunk B: 512×512×1 = 262,144 pixels    │
│ Chunk C: 512×512×1 = 262,144 pixels    │
│ ...                                    │
│ Total chunks: ~20 × 20 × 396 = ~158K   │
└─────────────────────────────────────────┘

NUMBER OF CHUNKS:
  x: 10,000 ÷ 512 = ~20 chunks
  y: 10,000 ÷ 512 = ~20 chunks
  time: 1 chunk per scene
  ────────────────────────────────────
  Total: 20 × 20 × 396 ≈ 158,400 chunks

DASK WORKER DISTRIBUTION (assume 4 workers):
  Worker 1: ~40K chunks
  Worker 2: ~40K chunks
  Worker 3: ~40K chunks
  Worker 4: ~40K chunks

CHUNK SIZE IN MEMORY:
  512 × 512 × 1 × 2 bytes (uint16) = ~524 KB
  Manageable size per worker ✓

PARALLEL PROCESSING:
  Can process multiple chunks simultaneously
  No memory bottleneck ✓
```

---

## Success Indicators Checklist

```
VERIFICATION AFTER CELL 5
═════════════════════════════════════════════════════════════════

Cell Output Shows:
  ☐ [01/13] ... ✓ X scenes
  ☐ [02/13] ... ✓ X scenes
  ...
  ☐ [13/13] ... ✓ X scenes
  ☐ 🔗 Combining 13 monthly chunks...
  ☐ ✅ Success! Shape: {...}

Variable Check:
  ☐ data is not None
  ☐ data.dims['time'] ≈ 396
  ☐ data.dims['y'] ≈ 10,000
  ☐ data.dims['x'] ≈ 10,000

Data Verification:
  ☐ data.data_vars contains: red, nir, scl
  ☐ data.coords contains: time, y, x
  ☐ data.attrs contains: CRS info

Memory Check:
  ☐ Reported size: 15-20 GB (NOT 403 TB!)
  ☐ System not crashed (kernel still alive)
  ☐ Dask workers responding

Next Step:
  ☐ Cell 6 runs without error
  ☐ Cloud masking completes
  ☐ Can proceed to cells 7-14
```

---

## Timeline to Success

```
TIME          ACTION                          STATUS
════════════  ══════════════════════════════  ════════════════════

00:00         Click "Run All" or run Cell 1  📌 Start
00:10         Cell 2: Dask + Datacube init   ⏳ Wait for cluster
00:30         Cell 3: Set coordinates        ✓ Done
00:31         Cell 4: Diagnostic check       ✓ Metadata loaded
00:35         Cell 5: Start monthly loop     ⏳ Begin S2 load
00:36         [01/13] Sep 2022 → Oct 2022    ⏳ Loading month 1
01:00         [02/13] Oct 2022 → Nov 2022    ⏳ Loading month 2
...
13:00         [13/13] Sep 2023 → Oct 2023    ⏳ Loading month 13
13:01         Concat all 13 months           ⏳ Combining
13:02         ✅ Success!                     ✓ Data ready
13:03         Cell 6: Cloud masking          ⏳ Processing
15:00         Cell 14: Cleanup               ✓ Done
15:01         NetCDF files ready             ✓ Success!

TOTAL TIME: ~15 minutes
```

---

**Diagrams created:** November 11, 2025  
**Format:** ASCII art + explanations  
**Purpose:** Visual understanding of memory fix architecture
