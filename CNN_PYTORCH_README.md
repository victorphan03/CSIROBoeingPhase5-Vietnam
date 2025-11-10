# CNN PyTorch Model for Land Use Classification

## Mô tả

Hai notebook mới được tạo để huấn luyện và dự đoán sử dụng đất bằng **CNN (Convolutional Neural Network) với PyTorch**.

### File được tạo:

1. **`04.train_CNN_PyTorch_ODC.ipynb`** - Huấn luyện mô hình CNN
   - Tải dữ liệu Sentinel-1 (VH, VV) và Sentinel-2 (NDVI)
   - Xử lý và chuẩn bị dữ liệu
   - Huấn luyện mô hình CNN với PyTorch
   - Vẽ đồ thị độ chính xác và loss
   - Lưu model

2. **`05.predict_CNN_PyTorch_ODC.ipynb`** - Dự đoán với model đã huấn luyện
   - Tải model đã lưu
   - Dự đoán cho toàn bộ khu vực
   - Xuất bản đồ phân loại
   - Lưu kết quả thành file GeoTIFF

### Module được cập nhật:

**`new_import_ODC.py`** - Thêm các hàm CNN với PyTorch:

```python
class CNN1D(nn.Module):
    """1D CNN model để phân loại sử dụng đất"""

def prepare_data_for_pytorch(X_train, X_val, X_test, y_train, y_val, y_test)
    """Chuẩn bị dữ liệu: normalize và convert to tensors"""

def train_cnn_pytorch(X_train, X_val, X_test, y_train, y_val, y_test, ...)
    """Huấn luyện CNN model"""

def plot_pytorch_training_history(history)
    """Vẽ đồ thị huấn luyện"""

def save_pytorch_model(model, scaler, model_name)
    """Lưu model"""

def load_pytorch_model(model_name, device)
    """Tải model"""
```

## Kiến trúc CNN

```
Input (samples, 1, 35)
  ↓
Block 1: Conv1D(64) → BatchNorm → Conv1D(64) → BatchNorm → MaxPool → Dropout
  ↓
Block 2: Conv1D(128) → BatchNorm → Conv1D(128) → BatchNorm → MaxPool → Dropout
  ↓
Block 3: Conv1D(256) → BatchNorm → Conv1D(256) → BatchNorm → GlobalAvgPool → Dropout
  ↓
FC Layer 1: Dense(256) → BatchNorm → Dropout
  ↓
FC Layer 2: Dense(128) → BatchNorm → Dropout
  ↓
Output: Dense(8) → Softmax
```

## Đặc trưng (Features)

- **Sentinel-1**: VH, VV (Synthetic Aperture Radar) - 2 kênh × 12 tháng = 24 features
- **Sentinel-2**: NDVI (Normalized Difference Vegetation Index) - 1 chỉ số × 12 tháng = 12 features
- **Tổng cộng**: 35 features (24 + 12) - 1 time series

## Phân loại (8 lớp)

- 0: Lúa tôm
- 1: Lúa
- 2: Cây hằng năm (CHN)
- 3: Cây lâu năm (CLN)
- 4: Thổ nhưỡng (TS)
- 5: Sông
- 6: Đất xây dựng
- 7: Rừng

## Hyperparameters

```python
- Epochs: 100
- Batch size: 32
- Learning rate: 1e-3 (với ReduceLROnPlateau)
- Optimizer: Adam
- Loss function: CrossEntropyLoss
- Early stopping patience: 15 epochs
- Dropout rate: 0.5
```

## PyTorch Requirements

```bash
pip install torch torchvision torchaudio
```

## GPU Support

Model hỗ trợ training trên GPU. Nếu có CUDA:

```python
device = 'cuda'  # GPU
# hoặc
device = 'cpu'   # CPU
```

## Luồng công việc

### Huấn luyện (04.train_CNN_PyTorch_ODC.ipynb)

1. Import modules
2. Kiểm tra GPU
3. Kết nối Dask cluster
4. Tải dữ liệu Sentinel-2 từ S3
5. Xử lý dữ liệu (masking cloud, fill NaN)
6. Tính toán NDVI
7. Tải dữ liệu Sentinel-1 (VH, VV)
8. Tải dữ liệu huấn luyện (1130 điểm)
9. Chia dữ liệu (train/val/test)
10. Huấn luyện CNN model
11. Vẽ đồ thị
12. Lưu model

### Dự đoán (05.predict_CNN_PyTorch_ODC.ipynb)

1. Import modules
2. Kiểm tra GPU
3. Kết nối Dask cluster
4. Tải dữ liệu Sentinel-2 và Sentinel-1
5. Xử lý dữ liệu
6. Tải model đã huấn luyện
7. Dự đoán cho toàn bộ khu vực (theo batch)
8. Tạo bản đồ phân loại
9. Lưu kết quả thành GeoTIFF

## Output

- **Model**: `model_train/model_cnn_pytorch.pth`
  - Chứa: model weights, model architecture, scaler
- **Classification Map**: `prediction_results/classification_map_cnn_pytorch.tif`
  - GeoTIFF raster với 8 lớp phân loại

## Ưu điểm của CNN so với Random Forest

1. **Tự động trích xuất features** - CNN học được các pattern phức tạp
2. **Xử lý dữ liệu time series tốt hơn** - Conv1D capture temporal patterns
3. **Regularization tốt** - BatchNorm + Dropout giảm overfitting
4. **Scalability** - GPU acceleration cho dataset lớn
5. **Transfer learning** - Có thể fine-tune pre-trained models

## Ghi chú

- Model sử dụng Conv1D vì dữ liệu là 1D time series (35 features)
- Early stopping dừa trên validation loss để tránh overfitting
- Learning rate reduction tự động giảm learning rate khi validation loss không cải thiện
- Scaler được lưu cùng với model để normalize dữ liệu trong phase dự đoán

## Liên hệ

Nếu có câu hỏi về implementation, hãy kiểm tra:
- `new_import_ODC.py` - Định nghĩa hàm và model
- `04.train_CNN_PyTorch_ODC.ipynb` - Huấn luyện
- `05.predict_CNN_PyTorch_ODC.ipynb` - Dự đoán
