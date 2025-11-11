# Project Index - Land Use Classification using CNN PyTorch

## 📚 Document Structure

### 🚀 Getting Started
| File | Purpose | Read Time |
|------|---------|-----------|
| **QUICKSTART_PYTORCH.md** | Hướng dẫn nhanh gọn (TL;DR) | 5 min |
| **LOCAL_TRAINING_WORKFLOW.md** | Chi tiết workflow 3 bước | 15 min |
| **PYTORCH_REQUIREMENTS.txt** | Cài đặt dependencies | 5 min |
| **PYTORCH_INSTALLATION.md** | Chi tiết cài PyTorch | 10 min |

---

## 📓 Jupyter Notebooks

### Step 1️⃣: Data Preparation (Server)
```
01.prepare_data_on_server.ipynb
├── Kết nối Dask cluster
├── Tải Sentinel-2, Sentinel-1 từ S3
├── Xử lý mây, tính NDVI
├── Lưu NetCDF files
└── ⏱️ Thời gian: 1-3 giờ (phụ thuộc vào số scene)
```

**Output**: `data_for_training/` (150-300 MB)

---

### Step 2️⃣: Model Training (Local Machine)
```
02.train_CNN_PyTorch_local.ipynb
├── Load data từ NetCDF files
├── Trích xuất features từ 1130 training points
├── Xây dựng CNN model
├── Huấn luyện (100 epochs max)
├── Plot training curves
└── ⏱️ Thời gian: 30 min - 2 giờ (GPU/CPU)
```

**Output**: 
- `model_cnn_pytorch.pt` (state dict)
- `model_cnn_pytorch_full.pt` (full model info)
- `training_history.png`

---

### Step 3️⃣: Prediction (Local Machine)
```
03.predict_CNN_PyTorch_local.ipynb
├── Load trained model
├── Predict trên 11M pixels
├── Tạo classification map
├── Lưu NetCDF, GeoTIFF, PNG
└── ⏱️ Thời gian: 10 min - 30 min (GPU/CPU)
```

**Output**:
- `land_use_prediction.nc`
- `land_use_prediction.tif`
- `prediction_map.png`
- `prediction_metadata.json`

---

## 🔧 Source Code

### Python Module
```
new_import_ODC.py
├── Load functions (Sentinel-1, 2, training data)
├── Data processing (masking, indices, resampling)
├── CNN PyTorch classes and functions
│   ├── CNNClassifier (model architecture)
│   ├── train_cnn_model()
│   ├── prepare_data_for_cnn()
│   └── save_cnn_model()
└── Utilities (normalization, evaluation)
```

**Key Functions**:
- `prepare_data_for_cnn()` - Chuẩn bị data format cho CNN
- `CNNClassifier()` - Model architecture
- `train_cnn_model()` - Training loop với early stopping
- `plot_training_history()` - Visualization

---

## 📊 Model Architecture

### CNN Design
```
Input Layer: (N, 1, 35)  # 35 features (12 months × 3 bands - NDVI, VV, VH)
    ↓
Block 1: Conv1d(64) → Conv1d(64) → MaxPool → Dropout
    ↓
Block 2: Conv1d(128) → Conv1d(128) → MaxPool → Dropout
    ↓
Block 3: Conv1d(256) → Conv1d(256) → GlobalAvgPool → Dropout
    ↓
Dense 1: FC(256 → 128) → ReLU → Dropout
    ↓
Dense 2: FC(128 → 64) → ReLU → Dropout
    ↓
Output: FC(64 → 8)  # 8 land use classes
```

**Total Parameters**: ~500K
**Trainable Parameters**: ~450K

---

## 🏷️ Land Use Classes

| Index | Label | VN Name | English Name |
|-------|-------|---------|--------------|
| 0 | Lua tom | Lúa Tôm | Rice-Shrimp |
| 1 | Lua | Lúa | Rice |
| 2 | CHN | Cây hằng năm | Perennial Crop |
| 3 | CLN | Cây lâu năm | Long-term Crop |
| 4 | TS | Thổ nhưỡng | Soil/Bare Land |
| 5 | Song | Sông | Water/River |
| 6 | Dat xay dung | Đất xây dựng | Built-up/Urban |
| 7 | Rung | Rừng | Forest |

---

## 📈 Data Flow

```
┌─────────────────┐
│  S3 Cloud       │
│  (Sentinel-1,2) │
└────────┬────────┘
         │
         ↓
┌─────────────────────────────┐
│ Server (01.prepare_data)    │
├─────────────────────────────┤
│ • Download from S3          │
│ • Mask clouds               │
│ • Calculate NDVI            │
│ • Resample to 10m           │
│ • Save as NetCDF            │
└────────┬────────────────────┘
         │ (Download ~150-300 MB)
         ↓
┌─────────────────────────────┐
│ Local Machine               │
├─────────────────────────────┤
│ data_for_training/          │
│ ├── average_ndvi.nc         │
│ ├── average_vv.nc           │
│ ├── average_vh.nc           │
│ └── train_data/*.shp        │
└────────┬────────────────────┘
         │
         ├──────────────────────────────┐
         ↓                              ↓
┌──────────────────────────┐  ┌────────────────────┐
│ 02.train_CNN_PyTorch    │  │ 03.predict_CNN_    │
│                          │  │    PyTorch         │
├──────────────────────────┤  ├────────────────────┤
│ • Extract features       │  │ • Load trained     │
│ • Split data (60/20/20)  │  │   model            │
│ • Normalize              │  │ • Predict on pixels│
│ • Train CNN              │  │ • Create map       │
│ • Save model             │  │ • Export formats   │
└────────┬─────────────────┘  └────────┬───────────┘
         │                             │
         ↓                             ↓
┌──────────────────────┐  ┌─────────────────────────┐
│ model_cnn_pytorch    │  │ land_use_prediction     │
│ _full.pt (~100 MB)   │  │ .nc/.tif/.png (~100 MB) │
└──────────────────────┘  └─────────────────────────┘
```

---

## 💻 System Requirements

### Minimum
- Python 3.8+
- 8 GB RAM
- 5 GB Disk space

### Recommended
- Python 3.10+
- 16 GB RAM
- 10 GB Disk space
- GPU (NVIDIA/AMD/Apple Silicon)

---

## 📦 Dependencies

### Core
- `torch>=2.0` - Deep learning framework
- `numpy>=1.21` - Numerical computing
- `xarray>=0.20` - Multi-dimensional arrays
- `geopandas>=0.10` - Geospatial operations

### Optional
- `rasterio>=1.2` - Raster I/O (GeoTIFF export)
- `jupyter>=1.0` - Notebook environment
- `matplotlib>=3.4` - Visualization

See `PYTORCH_REQUIREMENTS.txt` for full list

---

## ✨ Features

- ✅ **End-to-End Pipeline**: Từ S3 đến classification map
- ✅ **GPU Accelerated**: Hỗ trợ NVIDIA, AMD, Apple Silicon
- ✅ **Memory Efficient**: Batch processing, normalization
- ✅ **Modular Design**: Các notebook độc lập
- ✅ **Visualization**: Training curves, prediction maps
- ✅ **Metadata Tracking**: Model info, accuracy, label mapping
- ✅ **Multiple Output Formats**: NetCDF, GeoTIFF, PNG, JSON

---

## 🎯 Workflow Comparison

### Old Workflow (Random Forest on Server)
```
Server: Load Data → Train → Predict → Save
        ❌ Chậm (CPU only)
        ❌ Không linh hoạt
        ❌ Phải code trên server
```

### New Workflow (CNN PyTorch Local)
```
Server: Load Data → Save to Files
           ↓ (Download)
Local:  Load Data → Train → Predict → Save
        ✅ Nhanh (GPU)
        ✅ Linh hoạt
        ✅ Code trên máy cá nhân
```

---

## 📖 Quick Navigation

**I want to...**
- 🚀 Get started quickly → Read `QUICKSTART_PYTORCH.md`
- 📝 Understand the workflow → Read `LOCAL_TRAINING_WORKFLOW.md`
- 🔧 Set up environment → Read `PYTORCH_REQUIREMENTS.txt`
- 📓 See full code → Check notebooks (01, 02, 03)
- 🤖 Understand model → See `new_import_ODC.py` `CNNClassifier` class

---

## 📊 Expected Outputs

### Training Phase
```
✅ Model Accuracy
   Train: 88.5%
   Val: 82.3%
   Test: 81.2%

✅ Training Time: 45 min (GPU) / 90 min (CPU)
✅ Model Size: ~100 MB
```

### Prediction Phase
```
✅ Classification Map: 1080×1080 pixels
✅ Output Formats: NetCDF, GeoTIFF, PNG
✅ Prediction Time: 5 min (GPU) / 15 min (CPU)
✅ File Sizes: ~100 MB each
```

---

## 🐛 Troubleshooting

| Problem | Solution | File |
|---------|----------|------|
| `ModuleNotFoundError` | Install dependencies | `PYTORCH_REQUIREMENTS.txt` |
| GPU not detected | Check CUDA/drivers | `PYTORCH_INSTALLATION.md` |
| Out of memory | Reduce batch_size | Notebook comments |
| Data not found | Run server notebook first | Step 1 |

---

## 🔗 Related Files

### Original Notebooks (Reference)
- `01.train_ODC.ipynb` - Old Random Forest workflow
- `02.predict_ODC.ipynb` - Old prediction workflow
- `03.compare_ODC.ipynb` - Old comparison

### Documentation (Old)
- `CNN_PYTORCH_README.md` - Old CNN notes
- `CNN_PYTORCH_SUMMARY.md` - Old summary
- `COMPARISON_RF_VS_CNN.md` - RF vs CNN comparison
- `PYTORCH_INSTALLATION.md` - Original install guide

---

## 📋 File Checklist

Before running:
- [ ] `data_for_training/` exists with NetCDF files
- [ ] PyTorch installed and GPU detected
- [ ] Jupyter or IDE ready
- [ ] Enough disk space (~500 MB total)

---

## 🎓 Learning Resources

- **PyTorch Tutorial**: https://pytorch.org/tutorials/
- **CNN Basics**: https://cs231n.github.io/convolutional-networks/
- **xarray**: https://docs.xarray.dev/
- **GeoPandas**: https://geopandas.org/

---

## ✅ Checklist for Success

```
Preparation Phase
□ Read QUICKSTART_PYTORCH.md
□ Set up Python environment
□ Install all dependencies

Data Phase
□ Run 01.prepare_data_on_server.ipynb
□ Download data_for_training/ folder

Training Phase
□ Run 02.train_CNN_PyTorch_local.ipynb
□ Check training curves
□ Model achieves >75% test accuracy

Prediction Phase
□ Run 03.predict_CNN_PyTorch_local.ipynb
□ Generate classification map
□ Export to multiple formats

Validation Phase
□ Visually inspect prediction map
□ Compare with ground truth
□ Calculate accuracy metrics
```

---

**Last Updated**: November 2025  
**Version**: 1.0  
**Status**: Ready for Use ✅

🚀 **Start with**: `QUICKSTART_PYTORCH.md`
