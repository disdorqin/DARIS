# GPU 版 PyTorch 手动安装指南

## 环境信息

**目标环境**: `daris-research` (conda)
**位置**: `C:\ProgramData\anaconda3\envs\daris-research`

## 安装步骤

### 步骤 1: 激活环境

```bash
conda activate daris-research
```

### 步骤 2: 确认当前 PyTorch 状态

```bash
pip list | findstr torch
```

应该只显示 `torchmetrics`，没有 `torch`、`torchvision`、`torchaudio`。

### 步骤 3: 安装 GPU 版 PyTorch

**方式 A: 使用 pip（推荐）**

```bash
conda activate daris-research
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**方式 B: 使用 conda**

```bash
conda activate daris-research
conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia
```

### 步骤 4: 验证安装

```bash
conda activate daris-research
python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
```

如果输出 `CUDA available: True`，则安装成功。

## 文件大小

- torch: 约 2.8 GB
- torchvision: 约 50 MB
- torchaudio: 约 3 MB

**总大小**: 约 2.85 GB

## 下载慢的解决方案

### 方案 1: 使用国内镜像

```bash
pip install torch torchvision torchaudio --index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

注意：清华镜像源可能没有 CUDA 版本，需要确认。

### 方案 2: 手动下载 wheel 文件

1. 访问 https://download.pytorch.org/whl/cu118/
2. 下载以下文件：
   - `torch-2.7.1%2Bcu118-cp311-cp311-win_amd64.whl`
   - `torchvision-0.22.1%2Bcu118-cp311-cp311-win_amd64.whl`
   - `torchaudio-2.7.1%2Bcu118-cp311-cp311-win_amd64.whl`
3. 本地安装：
   ```bash
   pip install path/to/torch-*.whl
   pip install path/to/torchvision-*.whl
   pip install path/to/torchaudio-*.whl
   ```

### 方案 3: 使用 IDM 等多线程下载工具

复制下载链接到 IDM，可以显著提升下载速度。

## 常见问题

### Q1: 下载速度慢
- 使用下载工具（如 IDM）
- 选择非高峰时段下载
- 使用国内镜像源

### Q2: 安装后 CUDA 不可用
- 确认安装的是 GPU 版本：`pip list | findstr torch`
- 检查 CUDA 驱动：`nvidia-smi`
- 重新安装：`pip uninstall torch torchvision torchaudio` 然后重新安装

### Q3: 磁盘空间不足
- 确保至少有 5GB 可用空间
- 清理 pip 缓存：`pip cache purge`

## 安装完成后的配置

安装完成后，所有使用 `daris-research` 环境的脚本都会自动使用 GPU。

启动命令示例：
```bash
conda activate daris-research
python openclaw_main.py --no-callback --request "执行文献调研" --rounds 1
```

## 相关文档

- [DARIS 完整使用指南](./DARIS 完整使用指南.md)
- [钉钉回调配置指南](./钉钉回调配置指南.md)