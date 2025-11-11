# Quick Start Guide - PyTorch CNN Training Workflow

## TL;DR (Nhanh gọn)

1. **Server**: Chạy `01.prepare_data_on_server.ipynb` → Lưu data
2. **Local**: Download data → Chạy `02.train_CNN_PyTorch_local.ipynb` → Huấn luyện
3. **Local**: Chạy `03.predict_CNN_PyTorch_local.ipynb` → Dự đoán

---

## Step 1️⃣: Chuẩn Bị Data Trên Server

### Chạy notebook:
```
01.prepare_data_on_server.ipynb
```

### Khi hoàn thành, bạn sẽ có:
```
data_for_training/
├── average_ndvi.nc      (~50-100 MB)
├── average_vv.nc        (~50-100 MB)
├── average_vh.nc        (~50-100 MB)
└── train_data/
    └── ST_training data_updated_1130points_new.* (các file shp)
```

### Download data (từ terminal):
```bash
scp -r your_username@your_server_ip:/path/to/data_for_training ./
```

**File size**: Khoảng 150-300 MB (tùy vào độ phân giải)

---

## Step 2️⃣: Cài Đặt Environment Trên Local

### Tạo virtual environment:
```bash
python -m venv pytorch_env
source pytorch_env/bin/activate  # On Windows: pytorch_env\Scripts\activate
```

### Cài PyTorch (GPU - recommended):
```bash
# For NVIDIA GPU
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Or CPU only (nếu không có GPU)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### Cài dependencies:
```bash
pip install numpy xarray netcdf4 geopandas shapely scikit-learn matplotlib rasterio joblib
```

### Kiểm tra GPU:
```bash
python -c "import torch; print(f'GPU: {torch.cuda.is_available()}')"
```

---

## Step 3️⃣: Huấn Luyện Model

### Chạy notebook:
```
02.train_CNN_PyTorch_local.ipynb
```

### Điều gì sẽ xảy ra:
- ✅ Load data từ file NetCDF
- ✅ Trích xuất 1130 training points
- ✅ Huấn luyện CNN model (100 epochs tối đa)
- ✅ Hiển thị training curves
- ✅ Lưu model

### Thời gian:
- **GPU (NVIDIA)**: ~5-15 phút
- **GPU (Apple Silicon)**: ~10-20 phút
- **CPU**: ~30-60 phút

### Output files:
```
├── model_cnn_pytorch.pt          (50-100 MB)
├── model_cnn_pytorch_full.pt     (50-100 MB)
└── training_history.png
```

---

## Step 4️⃣: Dự Đoán Trên Dataset

### Chạy notebook:
```
03.predict_CNN_PyTorch_local.ipynb
```

### Điều gì sẽ xảy ra:
- ✅ Load trained model
- ✅ Predict trên toàn bộ ~11 triệu pixels
- ✅ Tạo classification map
- ✅ Lưu kết quả

### Thời gian:
- **GPU**: ~2-5 phút
- **CPU**: ~10-20 phút

### Output files:
```
├── land_use_prediction.nc       (NetCDF - 50-100 MB)
├── land_use_prediction.tif      (GeoTIFF - 50-100 MB)
├── prediction_map.png            (Visualization)
└── prediction_metadata.json      (Model info + accuracy)
```

---

## Key Features của Workflow

| Feature | Benefit |
|---------|---------|
| **Modular Design** | Các notebook độc lập, có thể chạy riêng lẻ |
| **GPU Support** | Tự động phát hiện và sử dụng GPU |
| **Normalization** | Tự động normalize dữ liệu |
| **Early Stopping** | Tránh overfitting |
| **Data Validation** | Kiểm tra dữ liệu trước training |
| **Visualization** | Vẽ training curves và prediction map |
| **Metadata** | Lưu model info và test accuracy |

---

## Các Model Output

### Training Phase
```
model_cnn_pytorch_full.pt
├── state_dict (weights)
├── num_classes (8)
├── input_size (35 features)
├── label_mapping (class names)
├── mean (normalization)
├── std (normalization)
├── test_accuracy (%)
└── test_loss
```

### Prediction Phase
```
land_use_prediction.nc
├── land_use_class (data array)
├── x, y coordinates
├── Spatial grid (1080x1080 pixels)
└── CRS (projection)
```

---

## Model Architecture (CNN)

```
Input (N, 1, 35)
    ↓
Conv1d(1, 64, 3) → BatchNorm → ReLU
Conv1d(64, 64, 3) → BatchNorm → ReLU
MaxPool(2) → Dropout(0.25)
    ↓
Conv1d(64, 128, 3) → BatchNorm → ReLU
Conv1d(128, 128, 3) → BatchNorm → ReLU
MaxPool(2) → Dropout(0.25)
    ↓
Conv1d(128, 256, 3) → BatchNorm → ReLU
Conv1d(256, 256, 3) → BatchNorm → ReLU
GlobalAvgPool → Dropout(0.25)
    ↓
FC(256, 128) → BatchNorm → ReLU → Dropout(0.5)
FC(128, 64) → BatchNorm → ReLU → Dropout(0.5)
FC(64, 8) → Softmax
    ↓
Output (N, 8)
```

**Parameters**: ~500K  
**Trainable**: ~450K

---

## Hyperparameters

```python
# Training
epochs = 100
batch_size = 32
learning_rate = 0.001
optimizer = Adam
loss = CrossEntropyLoss

# Regularization
dropout = [0.25, 0.5]
early_stopping_patience = 15
scheduler = ReduceLROnPlateau

# Splitting
train/val/test = 60/20/20
```

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| `FileNotFoundError` | Chạy notebook 01 trên server trước |
| `GPU not available` | Cài lại PyTorch với CUDA version đúng |
| `Out of memory` | Giảm batch_size hoặc dùng CPU |
| `Model file too large` | File ~100 MB là bình thường |
| `Prediction quá lâu` | Giảm batch_size trong predict |

---

## Expected Results

### Training Accuracy
- Train: ~85-95%
- Val: ~75-85%
- Test: ~75-85%

### Output
- Classification map: 1080x1080 pixels
- 8 classes: Lua tom, Lua, CHN, CLN, TS, Song, Dat xay dung, Rung
- Spatial resolution: 10m/pixel

---

## Next Steps

1. ✅ Data preparation trên server (30 phút - 2 giờ)
2. ✅ Download data xuống local (~1 giờ)
3. ✅ Training trên local (~30 phút - 2 giờ)
4. ✅ Prediction (~10 phút)
5. **Validation** (so sánh với ground truth)
6. **Optimization** (fine-tune hyperparameters)

---

## Support & Resources

- **PyTorch Docs**: https://pytorch.org/docs/stable/index.html
- **xarray Docs**: https://docs.xarray.dev/
- **GeoPandas Docs**: https://geopandas.org/

---

**Estimated Total Time**: 
- Server: 1-3 hours
- Local Training: 1-3 hours (GPU) / 3-6 hours (CPU)
- Prediction: 15 minutes
- **Total**: 2-9 hours depending on hardware

🚀 **Ready to start? Run notebook `01.prepare_data_on_server.ipynb` on server first!**
