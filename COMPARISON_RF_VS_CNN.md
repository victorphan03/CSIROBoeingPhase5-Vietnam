# So sánh Random Forest vs CNN PyTorch

## Tóm tắt

| Tiêu chí | Random Forest | CNN PyTorch |
|----------|---------------|------------|
| **Loại model** | Tree-based ensemble | Deep learning |
| **Training time** | Nhanh (1-2 phút) | Chậm (10-30 phút) |
| **Memory** | Thấp (~100MB) | Cao (~500MB+) |
| **GPU support** | Không | Có |
| **Accuracy** | Tốt (thường 80-85%) | Rất tốt (80-90%+) |
| **Overfitting** | Ít xảy ra | Dễ xảy ra, cần regularization |
| **Interpretability** | Cao (feature importance) | Thấp (black box) |
| **Hyperparameter tuning** | Dễ (GridSearchCV) | Khó (nhiều tham số) |

## Chi tiết

### Random Forest (01.train_ODC.ipynb)

**Ưu điểm:**
- ✅ Nhanh - huấn luyện trong vài phút
- ✅ Ít dữ liệu training cần thiết
- ✅ Chống overfitting tốt
- ✅ Feature importance rõ ràng
- ✅ Không cần GPU
- ✅ Dễ deploy

**Nhược điểm:**
- ❌ Kém xử lý temporal patterns
- ❌ Không học được hierarchical features
- ❌ Accuracy bị giới hạn bởi design
- ❌ Khó scale với dataset rất lớn

**Code:**
```python
grid_search = train_with_rf(X_train, X_val, y_train, y_val)
# GridSearchCV tìm optimal hyperparameters
# Training: ~1-2 phút
# Accuracy: ~80-85%
```

### CNN PyTorch (04.train_CNN_PyTorch_ODC.ipynb)

**Ưu điểm:**
- ✅ Accuracy cao - học được patterns phức tạp
- ✅ Xử lý temporal data tốt - Conv1D capture time dependencies
- ✅ GPU acceleration - training nhanh trên GPU
- ✅ Automatic feature learning - không cần manual feature engineering
- ✅ Scalable - xử lý dataset lớn
- ✅ Transfer learning - có thể fine-tune

**Nhược điểm:**
- ❌ Chậm trên CPU (~10-30 phút)
- ❌ Cần nhiều dữ liệu training
- ❌ Dễ overfitting
- ❌ Khó interpretability
- ❌ Cần GPU để training nhanh
- ❌ Hyperparameter tuning phức tạp

**Code:**
```python
cnn_model, history, scaler = train_cnn_pytorch(
    X_train, X_val, X_test, 
    y_train, y_val, y_test,
    epochs=100, device='cuda'
)
# Training: ~10-30 phút (với GPU)
# Accuracy: ~85-90%+
```

## Lựa chọn Model

### Dùng Random Forest nếu:
- 🎯 Cần training nhanh
- 🎯 Dataset nhỏ (<10k samples)
- 🎯 Cần interpretability cao
- 🎯 Không có GPU
- 🎯 Production deployment đơn giản

### Dùng CNN PyTorch nếu:
- 🎯 Cần accuracy cao (>85%)
- 🎯 Dataset lớn (>10k samples)
- 🎯 Có GPU disponible
- 🎯 Temporal patterns quan trọng
- 🎯 Có thời gian cho research

## Dữ liệu so sánh (Ước tính)

### Training Time

```
CPU (Intel i7):
- Random Forest: 1-2 phút
- CNN (CPU): 30-60 phút

GPU (NVIDIA RTX3090):
- Random Forest: N/A
- CNN (GPU): 5-10 phút
```

### Memory Usage

```
Random Forest:
- Model: ~50-100 MB
- RAM: ~500 MB

CNN PyTorch:
- Model: ~5-10 MB
- RAM: ~1-2 GB (training)
- GPU: ~4-6 GB (batch_size=32)
```

### Accuracy (Ước tính trên 1130 training points)

```
Random Forest (GridSearchCV):
- Train: ~90%
- Val: ~82%
- Test: ~80-85%

CNN PyTorch:
- Train: ~95%
- Val: ~88%
- Test: ~85-90%
```

## Cách chạy

### Random Forest
```bash
# 01.train_ODC.ipynb
jupyter notebook 01.train_ODC.ipynb
# Chạy từ cell 1 đến cell cuối
# Kết quả: model_train/model_odc.joblib
```

### CNN PyTorch
```bash
# Huấn luyện
jupyter notebook 04.train_CNN_PyTorch_ODC.ipynb
# Chạy hết tất cả cells
# Kết quả: model_train/model_cnn_pytorch.pth

# Dự đoán
jupyter notebook 05.predict_CNN_PyTorch_ODC.ipynb
# Chạy hết tất cả cells
# Kết quả: prediction_results/classification_map_cnn_pytorch.tif
```

## Ensemble Approach

Có thể combine cả hai model:

```python
# 1. Train Random Forest
rf_pred = rf_model.predict(X_test)

# 2. Train CNN PyTorch
cnn_pred = cnn_model.predict(X_test)

# 3. Ensemble (voting)
ensemble_pred = mode([rf_pred, cnn_pred])
# hoặc weighted average
ensemble_pred = 0.4 * rf_pred + 0.6 * cnn_pred
```

## Tối ưu CNN PyTorch

Nếu muốn improve accuracy:

```python
# 1. Tăng epochs
epochs=200  # Từ 100 → 200

# 2. Adjust learning rate
learning_rate=5e-4  # Từ 1e-3 → 5e-4

# 3. Increase model capacity
# Thêm Conv1D blocks hoặc tăng filters

# 4. Data augmentation
# Thêm noise, rotation, scaling

# 5. Ensemble multiple models
# Train 3-5 models, voting/averaging
```

## Inference Speed

### Random Forest
```python
# Dự đoán 1 điểm
rf_pred = rf_model.predict(X_test_point)  # ~1 ms

# Dự đoán 10980×10980 = 120M pixels
# Thời gian: ~20 giờ
```

### CNN PyTorch
```python
# Dự đoán 1 điểm (GPU)
cnn_pred = model(X_test_point_tensor)  # ~0.1 ms

# Dự đoán 10980×10980 = 120M pixels (batch processing)
# Thời gian: ~30 phút (GPU)
```

CNN nhanh hơn rất nhiều trong inference trên GPU!

## Kết luận

- **Nếu cần nhanh + interpretable**: Random Forest ✅
- **Nếu cần accuracy cao + có GPU**: CNN PyTorch ✅
- **Nếu có thời gian + muốn best result**: Combine cả hai 🏆

## Tài liệu tham khảo

- PyTorch Docs: https://pytorch.org/docs/stable/index.html
- Scikit-learn RF: https://scikit-learn.org/stable/modules/ensemble.html
- CNN for time series: https://arxiv.org/abs/1611.06251
