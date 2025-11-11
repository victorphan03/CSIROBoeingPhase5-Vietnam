# Workflow: Prepare Data on Server → Train on Local → Predict on Local

## Tổng quan

Workflow này giải quyết vấn đề của bạn bằng cách chia công việc thành 3 bước:

1. **Server (01.prepare_data_on_server.ipynb)**: Tải dữ liệu từ S3, xử lý, lưu file
2. **Máy Local (02.train_CNN_PyTorch_local.ipynb)**: Load data, train model
3. **Máy Local (03.predict_CNN_PyTorch_local.ipynb)**: Dùng model để predict

---

## Bước 1: Chuẩn bị Dữ liệu trên Server

**File**: `01.prepare_data_on_server.ipynb`

### Quy trình:
- ✅ Kết nối Dask cluster
- ✅ Tải ảnh Sentinel-2 từ S3
- ✅ Xử lý mây (masking)
- ✅ Tính NDVI
- ✅ Điền giá trị mây bằng seasonal interpolation
- ✅ Tính giá trị trung bình theo tháng
- ✅ Tải ảnh Sentinel-1 (VH, VV)
- ✅ Lưu tất cả dữ liệu dưới dạng file NetCDF trong thư mục `data_for_training/`
- ✅ Copy training data (shapefile) vào `data_for_training/train_data/`

### Kết quả:
```
data_for_training/
├── average_ndvi.nc          # NDVI data (monthly average)
├── average_vv.nc            # Sentinel-1 VV data (monthly average)
├── average_vh.nc            # Sentinel-1 VH data (monthly average)
└── train_data/
    ├── ST_training data_updated_1130points_new.shp
    ├── ST_training data_updated_1130points_new.shx
    ├── ST_training data_updated_1130points_new.dbf
    └── ... (other shape files)
```

### Tải file xuống máy cá nhân:
```bash
# Từ server sang máy local
scp -r user@server:/path/to/data_for_training ./
```

---

## Bước 2: Huấn luyện Model trên Máy Local

**File**: `02.train_CNN_PyTorch_local.ipynb`

### Yêu cầu:
- ✅ Python 3.8+
- ✅ PyTorch đã cài đặt
- ✅ NumPy, xarray, geopandas, scikit-learn
- ✅ Thư mục `data_for_training/` có sẵn

### Cài đặt dependencies:
```bash
pip install torch torchvision torchaudio
pip install numpy xarray geopandas scikit-learn matplotlib
```

### Quy trình:
1. **Load dữ liệu**: 
   - Mở các file NetCDF (NDVI, VV, VH)
   - Load training points từ shapefile

2. **Chuẩn bị dữ liệu**:
   - Trích xuất giá trị từ các điểm training (35 features = 12 tháng × 3 bands - NDVI, VV, VH)
   - Chia dữ liệu: Train (60%), Val (20%), Test (20%)
   - Normalize dữ liệu

3. **Xây dựng CNN Model**:
   - 3 Conv blocks với BatchNorm + MaxPooling + Dropout
   - 2 Fully connected layers
   - Output: 8 classes (loại sử dụng đất)

4. **Huấn luyện**:
   - Adam optimizer với learning rate = 0.001
   - Early stopping (patience=15)
   - Learning rate scheduler (ReduceLROnPlateau)
   - Epochs: 100 (tối đa)

5. **Lưu model**:
   - `model_cnn_pytorch.pt` - Chỉ state dict
   - `model_cnn_pytorch_full.pt` - Full model info (state dict + metadata)

### Kết quả:
```
├── model_cnn_pytorch.pt          # PyTorch state dict
├── model_cnn_pytorch_full.pt     # Full model (+ normalization params)
├── model_cnn_pytorch_best.pt     # Best model checkpoint
└── training_history.png          # Training curves
```

---

## Bước 3: Dự đoán trên Máy Local

**File**: `03.predict_CNN_PyTorch_local.ipynb`

### Quy trình:
1. **Load model**: Mở file `model_cnn_pytorch_full.pt`

2. **Load dữ liệu**: 
   - Mở các file NetCDF
   - Reshape thành spatial grid

3. **Predict trên toàn bộ dataset**:
   - Áp dụng normalization (mean/std từ training)
   - Predict từng batch để tiết kiệm memory
   - Reshape kết quả thành map

4. **Lưu kết quả**:
   - `land_use_prediction.nc` - NetCDF format
   - `land_use_prediction.tif` - GeoTIFF format (nếu có rasterio)
   - `prediction_map.png` - Visualization
   - `prediction_metadata.json` - Metadata (accuracy, label mapping, etc.)

### Kết quả:
```
├── land_use_prediction.nc       # NetCDF output
├── land_use_prediction.tif      # GeoTIFF output
├── prediction_map.png           # Visualization
└── prediction_metadata.json     # Metadata
```

---

## Full Workflow Diagram

```
┌─────────────────────────────────────────────────────────┐
│                      SERVER                             │
│  01.prepare_data_on_server.ipynb                       │
│  ✅ Load từ S3 (Sentinel-1, 2)                          │
│  ✅ Xử lý mây, tính NDVI                               │
│  ✅ Lưu NetCDF files                                   │
└──────────────┬──────────────────────────────────────────┘
               │ Download data_for_training/
               ↓
┌─────────────────────────────────────────────────────────┐
│                  LOCAL MACHINE                          │
│  02.train_CNN_PyTorch_local.ipynb                      │
│  ✅ Load data từ file                                  │
│  ✅ Trích xuất features từ training points             │
│  ✅ Huấn luyện CNN model                              │
│  ✅ Lưu model                                          │
└──────────────┬──────────────────────────────────────────┘
               │ model_cnn_pytorch_full.pt
               ↓
┌─────────────────────────────────────────────────────────┐
│                  LOCAL MACHINE                          │
│  03.predict_CNN_PyTorch_local.ipynb                    │
│  ✅ Load model                                         │
│  ✅ Predict trên toàn bộ dataset                       │
│  ✅ Lưu kết quả (NC, TIF, PNG, JSON)                  │
└──────────────┬──────────────────────────────────────────┘
               │ Optional: Upload kết quả lên server
               ↓
        (Server lưu trữ)
```

---

## Lợi Ích của Workflow này

| Tiêu chí | Trước | Sau |
|---------|------|-----|
| **Vị trí code** | Phải code trên server rồi up | Code trên máy local, không cần up |
| **Dữ liệu** | Không cần download | Download file nhỏ hơn (NetCDF thay vì raw data) |
| **Huấn luyện** | Chạy trên server | Chạy trên GPU local nhanh hơn |
| **Predict** | Chạy trên server | Chạy local, không chiếm server resource |
| **Phát triển** | Chậm (test trên server) | Nhanh (test local ngay) |

---

## Các file đã tạo

### Notebooks:
- `01.prepare_data_on_server.ipynb` - Chuẩn bị data trên server
- `02.train_CNN_PyTorch_local.ipynb` - Huấn luyện model trên local
- `03.predict_CNN_PyTorch_local.ipynb` - Predict trên local

### Documentation:
- `LOCAL_TRAINING_WORKFLOW.md` - File này (hướng dẫn chi tiết)
- `PYTORCH_REQUIREMENTS.txt` - Dependencies
- `PYTORCH_INSTALLATION.md` - Hướng dẫn cài PyTorch

---

## Troubleshooting

### Problem 1: Data files không tồn tại
```
❌ FileNotFoundError: Thư mục 'data_for_training' không tồn tại
```
**Solution**: Hãy chạy notebook 01 trên server và tải file xuống

### Problem 2: GPU không được nhận
```
GPU available: False
```
**Solution**: 
```bash
# Cài PyTorch với GPU support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Problem 3: Memory không đủ khi train
**Solution**: 
- Giảm batch_size (từ 32 xuống 16)
- Giảm epochs
- Giảm model complexity

### Problem 4: OutOfMemory khi predict
**Solution**:
- Giảm batch_size trong prediction (từ 128 xuống 64 hoặc 32)

---

## Tiếp theo

Sau khi có kết quả predict:
1. Upload `land_use_prediction.tif` lên server
2. So sánh với ground truth
3. Tính accuracy metrics
4. Có thể tinh chỉnh hyperparameters và retrain

Happy training! 🚀
