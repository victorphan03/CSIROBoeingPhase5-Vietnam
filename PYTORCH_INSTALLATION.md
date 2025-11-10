# Hướng dẫn cài đặt PyTorch

## Cài đặt PyTorch

### Tùy chọn 1: Cài đặt với pip

```bash
# CPU only
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# GPU with CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# GPU with CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### Tùy chọn 2: Cài đặt với conda

```bash
# CPU only
conda install pytorch torchvision torchaudio cpuonly -c pytorch

# GPU with CUDA 11.8
conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia

# GPU with CUDA 12.1
conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia
```

### Tùy chọn 3: Trong environment hiện tại

```bash
# Với conda env đã có
conda activate env_01

# Cài đặt PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## Kiểm tra cài đặt

### Kiểm tra cơ bản

```python
import torch
print(torch.__version__)
# Output: 2.0.0 (hoặc phiên bản khác)
```

### Kiểm tra CUDA

```python
import torch

# Kiểm tra CUDA disponible
print(torch.cuda.is_available())  # True nếu có GPU

# Kiểm tra device
print(torch.cuda.get_device_name(0))  # Tên GPU

# Kiểm tra CUDA version
print(torch.version.cuda)  # CUDA version

# Kiểm tra số GPU
print(torch.cuda.device_count())  # Số GPU
```

### Kiểm tra tensor trên GPU

```python
import torch

# Tạo tensor trên CPU
x_cpu = torch.tensor([1, 2, 3])
print(x_cpu.device)  # cpu

# Tạo tensor trên GPU
x_gpu = torch.tensor([1, 2, 3]).to('cuda')
print(x_gpu.device)  # cuda:0

# Hoặc
if torch.cuda.is_available():
    device = 'cuda'
else:
    device = 'cpu'

x = torch.randn(1000, 1000).to(device)
```

## Xác định CUDA Version

### Trên Windows

```bash
# Mở Command Prompt
nvidia-smi
```

Output sẽ hiển thị:
- Driver Version (e.g., 537.13)
- CUDA Version (e.g., 12.1)

### Trên Linux/Mac

```bash
nvidia-smi
# hoặc
nvcc --version
```

## Chọn PyTorch version phù hợp

| CUDA Version | PyTorch Command |
|---|---|
| No GPU (CPU) | `pip install torch ... --index-url https://download.pytorch.org/whl/cpu` |
| CUDA 11.7 | `pip install torch ... --index-url https://download.pytorch.org/whl/cu117` |
| CUDA 11.8 | `pip install torch ... --index-url https://download.pytorch.org/whl/cu118` |
| CUDA 12.1 | `pip install torch ... --index-url https://download.pytorch.org/whl/cu121` |

## Cài đặt các thư viện thêm

```bash
# Các thư viện cần cho notebook
pip install numpy pandas matplotlib scikit-learn
```

## Benchmark GPU

### Kiểm tra tốc độ GPU vs CPU

```python
import torch
import time

# Tạo dữ liệu
x_size = (10000, 10000)

# Test trên CPU
x_cpu = torch.randn(*x_size)
y_cpu = torch.randn(*x_size)

start = time.time()
z_cpu = torch.matmul(x_cpu, y_cpu)
cpu_time = time.time() - start
print(f"CPU time: {cpu_time:.4f}s")

# Test trên GPU (nếu có)
if torch.cuda.is_available():
    x_gpu = torch.randn(*x_size).cuda()
    y_gpu = torch.randn(*x_size).cuda()
    
    # Warmup
    torch.matmul(x_gpu, y_gpu)
    
    torch.cuda.synchronize()
    start = time.time()
    z_gpu = torch.matmul(x_gpu, y_gpu)
    torch.cuda.synchronize()
    gpu_time = time.time() - start
    print(f"GPU time: {gpu_time:.4f}s")
    print(f"Speedup: {cpu_time/gpu_time:.2f}x")
```

## Troubleshooting

### Problem: ImportError: No module named 'torch'

**Solution:**
```bash
pip install torch
# hoặc với chỉ định version
pip install torch==2.0.0
```

### Problem: CUDA out of memory

**Solution:**
```python
# Giảm batch size
batch_size = 16  # từ 32 → 16

# Hoặc clear GPU memory
torch.cuda.empty_cache()
```

### Problem: RuntimeError: CUDA out of memory

**Solution:**
```python
# Trên notebook
import gc
gc.collect()
torch.cuda.empty_cache()

# Hoặc reduce model size
model = model.to('cpu')  # Move to CPU để save GPU memory
```

### Problem: CUDA runtime error: device-side assert triggered

**Solution:**
Thường là lỗi dimension. Kiểm tra:
```python
# Kiểm tra input size
print(input_tensor.shape)

# Kiểm tra model input
print(model)
```

## Tối ưu hóa

### Enable GPU acceleration

```python
import torch

# Nếu muốn training nhanh nhất
device = 'cuda' if torch.cuda.is_available() else 'cpu'

# Hoặc force GPU
device = torch.device('cuda:0')  # Dùng GPU 0

# Model to device
model.to(device)

# Data to device
X_train_tensor.to(device)
```

### Sử dụng mixed precision (tăng tốc độ, tiết kiệm memory)

```python
from torch.cuda.amp import autocast, GradScaler

scaler = GradScaler()

for epoch in range(epochs):
    with autocast():
        outputs = model(X_batch)
        loss = criterion(outputs, y_batch)
    
    scaler.scale(loss).backward()
    scaler.step(optimizer)
    scaler.update()
```

### Multi-GPU training

```python
import torch.nn as nn

# Nếu có multiple GPUs
if torch.cuda.device_count() > 1:
    model = nn.DataParallel(model)

model.to(device)
```

## Kiểm tra môi trường

```python
import sys
import torch
import numpy as np
import sklearn

print(f"Python: {sys.version}")
print(f"PyTorch: {torch.__version__}")
print(f"NumPy: {np.__version__}")
print(f"Scikit-learn: {sklearn.__version__}")

# CUDA info
if torch.cuda.is_available():
    print(f"CUDA: Available")
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"CUDA Version: {torch.version.cuda}")
else:
    print(f"CUDA: Not available (CPU only)")
```

## Chạy Notebook với GPU

```bash
# Nếu muốn force GPU
CUDA_VISIBLE_DEVICES=0 jupyter notebook

# Nếu muốn CPU only
CUDA_VISIBLE_DEVICES="" jupyter notebook

# Hoặc trong notebook
import os
os.environ['CUDA_VISIBLE_DEVICES'] = '0'  # GPU 0
```

## Tài liệu

- PyTorch Installation: https://pytorch.org/get-started/locally/
- PyTorch Documentation: https://pytorch.org/docs/stable/
- CUDA Toolkit: https://developer.nvidia.com/cuda-toolkit
