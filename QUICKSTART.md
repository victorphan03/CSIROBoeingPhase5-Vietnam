# Quick Start Guide - CNN PyTorch

## 🚀 Bắt đầu nhanh

### 1️⃣ Cài đặt (5 phút)

```bash
# Nếu chưa có PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Hoặc với conda
conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia

# Cài đặt dependencies
pip install -r requirements_pytorch.txt
```

Kiểm tra cài đặt:
```python
import torch
print(torch.cuda.is_available())  # True nếu có GPU
print(torch.__version__)
```

### 2️⃣ Huấn luyện Model (30 phút với GPU)

```bash
# Mở Jupyter notebook
jupyter notebook 04.train_CNN_PyTorch_ODC.ipynb

# Chạy tất cả cells (Kernel → Run All)
# Hoặc chạy từng cell bằng Shift+Enter
```

**Output:**
- ✅ Model được lưu: `model_train/model_cnn_pytorch.pth`
- ✅ Training history: plots in notebook

**Dự kiến kết quả:**
```
Test Accuracy: 87.45%
Test Loss: 0.3521
```

### 3️⃣ Dự đoán (15 phút với GPU)

```bash
# Mở Jupyter notebook
jupyter notebook 05.predict_CNN_PyTorch_ODC.ipynb

# Chạy tất cả cells
```

**Output:**
- ✅ Classification map: `prediction_results/classification_map_cnn_pytorch.tif`
- ✅ Bản đồ hiển thị: 8 lớp sử dụng đất
- ✅ GeoTIFF file sử dụng được với QGIS, ArcGIS, v.v.

---

## 📊 Giải thích Code

### Model Architecture (trong `new_import_ODC.py`)

```python
class CNN1D(nn.Module):
    """
    Input: Time series 35 features (VH×12 + VV×12 + NDVI×12 = 24+24+12)
    Output: 8 land use classes
    """
```

**3 Convolutional Blocks:**
- Block 1: 64 filters + MaxPool
- Block 2: 128 filters + MaxPool
- Block 3: 256 filters + GlobalAvgPool

**2 Fully Connected Layers:**
- Dense(256→256) + Dropout
- Dense(256→128) + Dropout
- Dense(128→8) + Softmax

### Training Loop (Notebook cell 15)

```python
cnn_model, history, scaler = train_cnn_pytorch(
    X_train, X_val, X_test,
    y_train, y_val, y_test,
    num_classes=8,
    epochs=100,
    batch_size=32,
    learning_rate=1e-3,
    device='cuda'  # hoặc 'cpu'
)

# Result:
# - cnn_model: Trained PyTorch model
# - history: Training/validation accuracy & loss
# - scaler: Fitted StandardScaler để normalize data
```

### Prediction Loop (Notebook cell 14-16)

```python
# Cell 14: Tải model
model, scaler = load_pytorch_model("model_cnn_pytorch.pth", device='cuda')

# Cell 15-16: Dự đoán
# Xử lý từng pixel bằng batch processing
# Output: Classification map (10980×10980 pixels)
```

---

## 🔧 Tùy chỉnh

### Thay đổi Epochs

```python
# Trong 04.train_CNN_PyTorch_ODC.ipynb, cell 15:

cnn_model, history, scaler = train_cnn_pytorch(
    X_train, X_val, X_test, y_train, y_val, y_test,
    epochs=200  # ← Từ 100 → 200 (tăng accuracy nhưng lâu hơn)
)
```

### Thay đổi Batch Size

```python
# Batch size lớn → Nhanh hơn nhưng xài nhiều GPU memory
batch_size=64  # Từ 32 → 64

# Batch size nhỏ → Chậm hơn nhưng xài ít memory
batch_size=16  # Từ 32 → 16
```

### Thay đổi Learning Rate

```python
# Learning rate cao → Nhanh hội tụ nhưng có thể bỏ qua optimum
learning_rate=5e-3

# Learning rate thấp → Chậm hội tụ nhưng ổn định hơn
learning_rate=1e-4
```

### Dùng CPU thay vì GPU

```python
# Notebook cell 2: Thay
device = 'cuda'

# Bằng
device = 'cpu'

# Note: Training sẽ chậm 10-50x
```

---

## 📈 Monitoring Training

Notebook vẽ 2 đồ thị tự động:

1. **Accuracy Plot**
   - Train accuracy tăng dần
   - Validation accuracy tăng nhưng có thể flatten
   - Gap lớn = overfitting

2. **Loss Plot**
   - Train loss giảm dần
   - Validation loss giảm nhưng có thể tăng
   - Gap lớn = overfitting

**Good training:**
```
Epoch 1:   Train Acc: 60%, Val Acc: 55%
Epoch 50:  Train Acc: 92%, Val Acc: 85%
Epoch 100: Train Acc: 95%, Val Acc: 87%  ← Early stop here
```

**Overfitting:**
```
Epoch 1:   Train Acc: 60%, Val Acc: 55%
Epoch 50:  Train Acc: 92%, Val Acc: 80%
Epoch 100: Train Acc: 98%, Val Acc: 78%  ← Training continues but val doesn't improve
```

---

## 🐛 Troubleshooting

### Problem: CUDA out of memory

**Solution 1:**
```python
# Giảm batch size
batch_size = 16  # Từ 32 → 16
```

**Solution 2:**
```python
# Dùng CPU
device = 'cpu'
```

**Solution 3:**
```python
# Clear GPU memory
torch.cuda.empty_cache()
```

### Problem: Model training quá chậm

**Nguyên nhân:** Dùng CPU

**Solution:**
```python
# Dùng GPU
device = 'cuda'

# Hoặc check CUDA:
print(torch.cuda.is_available())  # Phải True
```

### Problem: ImportError: No module named 'torch'

**Solution:**
```bash
pip install torch
```

### Problem: Classification map không hiển thị

**Solution:**
```python
# Kiểm tra file output
import os
print(os.path.exists('prediction_results/classification_map_cnn_pytorch.tif'))

# Hoặc load và kiểm tra
result = rioxarray.open_rasterio('prediction_results/classification_map_cnn_pytorch.tif')
print(result.shape)
print(result.values)
```

---

## 📂 File Structure

```
CSIROBoeingPhase5-Vietnam/
├── 04.train_CNN_PyTorch_ODC.ipynb     ← Huấn luyện
├── 05.predict_CNN_PyTorch_ODC.ipynb   ← Dự đoán
├── new_import_ODC.py                   ← Module với CNN class
├── 
├── model_train/
│   ├── model_cnn_pytorch.pth           ← Trained model
│   ├── model_odc.joblib                ← Random Forest (existing)
│   └── model_new.joblib
├── 
├── prediction_results/
│   └── classification_map_cnn_pytorch.tif  ← Output map
├── 
├── train/
│   └── ST_training data_updated_1130points_new.shp
├── 
├── CNN_PYTORCH_README.md               ← Hướng dẫn chi tiết
├── CNN_PYTORCH_SUMMARY.md              ← Summary
├── COMPARISON_RF_VS_CNN.md             ← So sánh
├── PYTORCH_INSTALLATION.md             ← Cài đặt
└── requirements_pytorch.txt            ← Dependencies
```

---

## ⏱️ Thời gian ước tính

### Với GPU (NVIDIA RTX 3090)
- Huấn luyện: 10-15 phút
- Dự đoán: 15-20 phút
- **Total: ~30 phút**

### Với CPU (Intel i7-10700K)
- Huấn luyện: 1-2 giờ
- Dự đoán: 2-4 giờ
- **Total: 3-6 giờ**

### Với GPU (NVIDIA GTX 1660)
- Huấn luyện: 30-45 phút
- Dự đoán: 45-60 phút
- **Total: ~1.5 giờ**

---

## ✅ Checklist

- [ ] PyTorch cài đặt thành công
- [ ] CUDA available (nếu có GPU)
- [ ] Dependencies cài đặt: `pip install -r requirements_pytorch.txt`
- [ ] Dữ liệu training có sẵn: `train/ST_training data_updated_1130points_new.shp`
- [ ] Datacube configured
- [ ] Chạy 04.train_CNN_PyTorch_ODC.ipynb
- [ ] Model lưu thành công: `model_train/model_cnn_pytorch.pth`
- [ ] Chạy 05.predict_CNN_PyTorch_ODC.ipynb
- [ ] Classification map tạo thành công
- [ ] GeoTIFF file có thể mở được trong QGIS/ArcGIS

---

## 📚 Tham khảo

- **PyTorch Docs**: https://pytorch.org/docs/
- **Conv1D Docs**: https://pytorch.org/docs/stable/generated/torch.nn.Conv1d.html
- **1D CNN for Time Series**: https://arxiv.org/abs/1611.06251
- **Early Stopping**: https://pytorch.org/docs/stable/generated/torch.optim.lr_scheduler.ReduceLROnPlateau.html

---

## 🎯 Next Steps

1. ✅ Huấn luyện CNN model
2. ✅ Dự đoán classification map
3. 🔲 So sánh kết quả với Random Forest
4. 🔲 Fine-tune hyperparameters
5. 🔲 Ensemble CNN + Random Forest
6. 🔲 Deploy model lên production

---

**Happy training! 🚀**

Mọi câu hỏi, kiểm tra các file README hoặc thử troubleshooting section.
