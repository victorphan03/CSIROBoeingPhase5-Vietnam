# 🎯 Simplified Workflow: Server Loads, Local Processes

## Overview

Workflow được đơn giản hóa để **tách rõ trách nhiệm**:
- **Server (Notebook 01):** Chỉ tải dữ liệu RAW từ S3, lưu NetCDF
- **Local (Notebook 02):** Tất cả xử lý + training model

## Why This Design?

### Lợi ích:
✅ **Server:** Tránh lãng phí tài nguyên cho xử lý → Tải nhanh, lưu ngay  
✅ **Local:** Kiểm soát toàn bộ quy trình → Dễ debug, dễ thay đổi tham số  
✅ **Tách biệt:** Server chỉ lo load, local chỉ lo xử lý  
✅ **Linh hoạt:** Có thể reprocess dữ liệu mà không cần quay lại server  

### So sánh:

**Cũ (All on Server):**
```
Server: Load → CloudMask → NDVI → Fill → Aggregation → Save → Transfer
Local: Unzip → Train
```
→ Server bị quá tải, chậm

**Mới (Simplified):**
```
Server: Load → Save RAW
Local: Load → CloudMask → NDVI → Fill → Aggregation → Train
```
→ Server chỉ làm việc nặng (loading), Local làm việc nhanh (processing)

---

## Workflow Chi Tiết

### Bước 1: Server - Tải Data Thô (Notebook 01)

**Thời gian:** 10-20 phút  
**Tài nguyên:** Network (S3 download)  
**Output:** 2 file NetCDF thô (~80-100 GB)

```
01.prepare_data_on_server.ipynb
├─ Cell 1: Intro
├─ Cell 2: Setup Dask + Datacube + S3
├─ Cell 3: Set coordinates
├─ Cell 4: Diagnostic (kiểm tra metadata)
├─ Cell 5: Load S2 (13 tháng) ← Monthly chunking
├─ Cell 6: Load S1 (raw)
├─ Cell 7: Save 2 file NetCDF
│   - sentinel2_raw.nc (S2 thô)
│   - sentinel1_raw.nc (S1 thô)
└─ Cell 8: Copy training shapefile + Close
```

**Output:**
```
data_for_training/
├─ sentinel2_raw.nc          (~50 GB)
├─ sentinel1_raw.nc          (~30 GB)
└─ train_data/
   ├─ *.shp, *.shx, *.dbf   (training points)
```

### Bước 2: Local - Tải & Xử Lý Data (Notebook 02)

**Thời gian:** 30-60 phút (CPU) hoặc 10-15 phút (GPU)  
**Tài nguyên:** CPU/GPU của máy local  
**Output:** Trained PyTorch CNN model

```
02.process_and_train_local.ipynb
├─ Cell 1: Import libraries
├─ Cell 2: Load NetCDF files
├─ Cell 3: Cloud masking ← Processing starts here
├─ Cell 4: Calculate NDVI
├─ Cell 5: Fill NaN (seasonal interpolation)
├─ Cell 6: Monthly aggregation
├─ Cell 7: Load training data & extract features
├─ Cell 8: Split train/val/test
├─ Cell 9: Train PyTorch CNN
├─ Cell 10: Evaluate on test set
└─ Cell 11: Save model
```

**Output:**
```
model_cnn_pytorch_local.pth          (Model weights)
model_cnn_pytorch_local_checkpoint.pth (Full checkpoint)
```

### Bước 3: Local - Dự Báo Toàn Bộ (Notebook 03)

**Thời gian:** 5-10 phút  
**Input:** Trained model + processed data  
**Output:** Classification maps (SHP, TIF)

```
03.predict_CNN_PyTorch_local.ipynb
├─ Load trained model
├─ Prepare full spatial data (cloud mask + NDVI + aggregation)
├─ Apply model to every pixel
└─ Save as shapefile/GeoTIFF
```

---

## File Structure

```
/home/x79/CSIROBoeingPhase5-Vietnam/
│
├─ 01.prepare_data_on_server.ipynb    ← RUN ON SERVER
│  └─ Output: data_for_training/ (80-100 GB)
│
├─ 02.process_and_train_local.ipynb   ← RUN LOCALLY
│  ├─ Input: data_for_training/ (from server)
│  └─ Output: model_cnn_pytorch_local.pth
│
├─ 03.predict_CNN_PyTorch_local.ipynb ← RUN LOCALLY
│  ├─ Input: model + processed data
│  └─ Output: prediction maps (SHP/TIF)
│
└─ new_import_ODC.py (helper functions)
```

---

## Timeline & Resource Usage

### Server Timeline:
```
Time    Action                          Duration    CPU   Memory   Network
────────────────────────────────────────────────────────────────────────────
00:00   Dask init                       30 sec      Low   Moderate  -
00:01   Set coordinates                 1 sec       -     -         -
00:02   Diagnostic check                30 sec      Low   Low       High (query)
00:03   Load S2 monthly chunks (13×)    12 min      Moderate High    High (download)
00:15   Load S1                         2 min       Moderate High    High
00:17   Save NetCDF                     3 min       Low   Moderate  -
00:20   Copy training data              1 min       -     -         -
00:21   DONE ✅                                      Total: ~80-100 GB saved
```

### Local Timeline (CPU):
```
Time    Action                          Duration
──────────────────────────────────────────────────
00:00   Load NetCDF                     2 min
00:02   Cloud mask                      3 min
00:05   NDVI + Fill                     5 min
00:10   Aggregation                     3 min
00:13   Load training data              1 min
00:14   Train CNN (50 epochs)           30-40 min
00:45   Evaluate                        1 min
00:46   Save model                      1 min
00:47   DONE ✅                         Total: ~50 min
```

### Local Timeline (GPU):
```
Same as above but:
  - Train CNN: 5-10 min instead of 30-40 min
  - Total: ~20-30 min
```

---

## Data Flow Diagram

```
┌──────────────────────────────────────────────────────────┐
│  SERVER (Notebook 01)                                    │
│  ────────────────────                                    │
│                                                          │
│  [AWS S3]  →  [Datacube]  →  [NetCDF]  →  [Download]   │
│  396 scenes    monthly       2 files       80-100 GB    │
│  (Raw S2+S1)   chunks        raw data      data_for_    │
│               (avoid OOM)                  training/    │
│                                                          │
└──────────────────────────────────────────────────────────┘
                         ⬇️ Transfer (SCP/FTP)
┌──────────────────────────────────────────────────────────┐
│  LOCAL MACHINE (Notebook 02)                             │
│  ──────────────────────────────────                      │
│                                                          │
│  [NetCDF]  →  [CloudMask]  →  [NDVI]  →  [FillNaN]    │
│  raw data      SCL band        red/nir   seasonal       │
│                                          interp         │
│     ⬇️                                                   │
│  [Aggregation]  →  [Train Data]  →  [CNN Training]     │
│  monthly            extract              PyTorch       │
│  averages           features             50 epochs     │
│                                                          │
│                                     ⬇️                   │
│                          [Trained Model (100 MB)]       │
│                                                          │
└──────────────────────────────────────────────────────────┘
                         ⬇️ (Notebook 03)
┌──────────────────────────────────────────────────────────┐
│  LOCAL MACHINE (Notebook 03)                             │
│  ──────────────────────────────────                      │
│                                                          │
│  [Trained Model]  +  [Aggregated Data]  →  [Predict]   │
│  100 MB               (monthly avg)         All pixels  │
│                                                          │
│                          ⬇️                              │
│              [Classification Maps (SHP/TIF)]            │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## Processing Parameters

### Notebook 01 (Server):
```python
date_range = ("2022-09-01", "2023-10-01")
longtitude_range = (105.5, 106.4)  # ~90 km
latitude_range = (9.2, 10.0)       # ~90 km
resolution = (-10, 10)              # 10 m/pixel
dask_chunks = {'x': 512, 'y': 512, 'time': 1}
```

### Notebook 02 (Local):
```python
# Cloud masking: Using SCL band
# NDVI calculation: (NIR - Red) / (NIR + Red)
# Fill NaN: Seasonal interpolation (4 seasons)
# Aggregation: Monthly averages (13 months)

# Training:
epochs = 50
batch_size = 32
learning_rate = 0.001
patience = 10 (early stopping)
split = 80% train, 10% val, 10% test
```

### Notebook 03 (Local):
```python
# Same processing as Notebook 02
# Apply model to every pixel
# Output: Classification map (8 classes)
```

---

## Data Quality Assurance

**Server (Notebook 01):**
- ✅ Diagnostic cell checks datacube metadata
- ✅ Monthly loading prevents OOM
- ✅ Error handling skips bad months
- ✅ File size validation before download

**Local (Notebook 02):**
- ✅ Data shape validation after loading
- ✅ NaN count reporting (before/after filling)
- ✅ Training progress monitoring (val loss, accuracy)
- ✅ Test accuracy + confusion matrix reporting

**Local (Notebook 03):**
- ✅ Prediction shape validation
- ✅ Class distribution analysis
- ✅ Output file size validation

---

## Troubleshooting

### Problem: "Server load too slow"
→ Check S3 bandwidth, Dask workers status  
→ Reduce number of workers temporarily

### Problem: "Local processing uses too much RAM"
→ Cloud mask operation: Reduce `dask_chunks` size
→ NDVI calculation: Process month by month
→ Training: Reduce batch size (32 → 16)

### Problem: "Model accuracy too low"
→ Check training data quality
→ Verify cloud masking effectiveness
→ Increase training epochs
→ Use data augmentation in `new_import_ODC.py`

### Problem: "Prediction takes too long"
→ Use GPU if available
→ Batch predictions by month
→ Reduce output resolution if needed

---

## Success Criteria

### Notebook 01 ✅
- [ ] All 13 months loaded with ✓ marks
- [ ] Data shape correct (~10,000 × 10,000 pixels)
- [ ] Memory usage 15-20 GB (not 403 TB!)
- [ ] 2 NetCDF files saved (~80-100 GB)
- [ ] Training shapefile copied

### Notebook 02 ✅
- [ ] NetCDF files loaded successfully
- [ ] Cloud masking reduces NaN count
- [ ] NDVI values in expected range [-0.5, 1.0]
- [ ] Monthly aggregation produces 13 timesteps
- [ ] Training completes without OOM
- [ ] Test accuracy ≥ 0.70 (70%)
- [ ] Model saved as .pth file

### Notebook 03 ✅
- [ ] Model loads successfully
- [ ] Predictions on full extent complete
- [ ] Classification map generated
- [ ] All 8 classes represented
- [ ] Output files saved (SHP/TIF)

---

## Advantages of This Design

1. **Resource Efficiency:**
   - Server: Only download/save (I/O bound)
   - Local: Only compute (CPU/GPU bound)

2. **Flexibility:**
   - Can reprocess locally without server
   - Can experiment with hyperparameters
   - Can apply to new regions easily

3. **Debugging:**
   - Local processing is much faster to iterate
   - Easy to visualize intermediate results
   - Can save intermediate results for inspection

4. **Scalability:**
   - Same pattern works for different regions
   - Can train multiple models in parallel locally
   - Server freed up for other tasks after initial load

5. **Reproducibility:**
   - All processing code on local machine
   - Easy to version control & document
   - Results fully reproducible

---

## Next Steps

1. ✅ Run Notebook 01 on server (10-20 min)
2. ✅ Download data to local machine (size: 80-100 GB)
3. ✅ Run Notebook 02 on local (30-60 min)
4. ✅ Run Notebook 03 on local (5-10 min)
5. ✅ Evaluate results

**Total time:** ~1-2 hours (including transfer)

---

**Created:** November 12, 2025  
**Status:** ✅ SIMPLIFIED WORKFLOW COMPLETE  
**Design Pattern:** Server loads → Local processes
