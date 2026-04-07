# 阿里云 GPU 服务器配置指南

## 服务器信息

| 项目 | 配置 |
|------|------|
| IP 地址 | 47.100.98.160 |
| 用户 | root |
| 工作目录 | /home/root/DARIS/ |

## 本地配置

### 虚拟环境

**环境名称**: `daris-research` (conda)
**位置**: `C:\ProgramData\anaconda3\envs\daris-research`

### PyTorch GPU 版本

**CUDA 版本**: 12.1 (兼容本地 CUDA 12.6)
**安装命令**:
```bash
conda activate daris-research
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

**验证**:
```bash
python -c "import torch; print('CUDA:', torch.cuda.is_available())"
```

---

## 阿里云服务器配置步骤

### 步骤 1: SSH 连接测试

```bash
ssh root@47.100.98.160
```

### 步骤 2: 检查服务器 GPU 配置

```bash
nvidia-smi
```

### 步骤 3: 检查 Python 环境

```bash
which python
python --version
pip list | grep torch
```

### 步骤 4: 安装 GPU 版 PyTorch（如未安装）

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 步骤 5: 部署 DARIS 项目

```bash
cd /home/root
git clone https://github.com/disdorqin/DARIS.git
cd DARIS
pip install -r openclaw_requirements.txt
```

### 步骤 6: 配置环境变量

在服务器上创建 `.env` 文件，配置大模型 API 密钥等。

### 步骤 7: 运行测试

```bash
conda activate daris-research
python openclaw_main.py --request "执行文献调研" --rounds 1
```

---

## 本地运行（使用本地 GPU）

### 启动命令

```bash
conda activate daris-research
python openclaw_main.py --no-callback --request "今日找负荷预测方向文献，执行全自动流程一轮" --rounds 1
```

### 使用 GPU 运行

所有使用 `daris-research` 环境的脚本都会自动使用本地 GPU（RTX 4060）。

---

## 数据传输

### 上传数据到阿里云

```bash
scp -r 6_experiment_execution/data/ root@47.100.98.160:/home/root/DARIS/6_experiment_execution/data/
```

### 从阿里云下载结果

```bash
scp -r root@47.100.98.160:/home/root/DARIS/8_knowledge_asset/final_report/ ./8_knowledge_asset/final_report/
```

---

## 常见问题

### Q1: SSH 连接超时
- 检查服务器是否运行
- 检查安全组是否开放 22 端口
- 检查密码是否正确

### Q2: GPU 不可用
- 执行 `nvidia-smi` 确认 GPU 状态
- 确认安装的是 GPU 版 PyTorch
- 重新安装：`pip uninstall torch torchvision torchaudio && pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121`

### Q3: 磁盘空间不足
- 执行 `df -h` 查看磁盘使用
- 清理缓存：`pip cache purge`

---

## 相关文档

- [DARIS 完整使用指南](./DARIS 完整使用指南.md)
- [GPU_PyTorch 手动安装指南](./GPU_PyTorch 手动安装指南.md)