# 阿里云服务器部署指南 - 修复内存不足问题

## ✅ GitHub 推送成功！

代码已成功推送到：https://github.com/disdorqin/DARIS

---

## 问题诊断：Killed 错误

### 原因分析
显示 `Killed` 表示**服务器内存不足**，系统 OOM Killer 强制终止了 pip 进程。

PyTorch 安装需要：
- 下载文件：约 75MB
- 解压安装：需要约 500MB-1GB 临时内存
- 如果服务器内存 < 1GB，会被强制终止

### 解决方案

#### 方案 1：增加 Swap 空间（推荐）

```bash
# 1. 检查当前 swap
free -h

# 2. 创建 2GB swap 文件
dd if=/dev/zero of=/swapfile bs=1M count=2048

# 3. 设置 swap 权限
chmod 600 /swapfile

# 4. 格式化 swap
mkswap /swapfile

# 5. 启用 swap
swapon /swapfile

# 6. 验证 swap 状态
free -h

# 7. 设置开机自动启用
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

#### 方案 2：使用更小的 PyTorch 版本

```bash
# 安装最小化 CPU 版 PyTorch（仅包含核心功能）
python3 -m pip install --default-timeout=1000 -i https://pypi.tuna.tsinghua.edu.cn/simple torch==1.10.2+cpu torchvision==0.11.3+cpu torchaudio==0.10.2 -f https://download.pytorch.org/whl/lts/1.10.2/cpu/torch_lts.html
```

#### 方案 3：分步安装（减少内存峰值）

```bash
# 1. 先安装 numpy（测试内存是否足够）
python3 -m pip install --default-timeout=1000 -i https://pypi.tuna.tsinghua.edu.cn/simple numpy

# 2. 安装其他小依赖
python3 -m pip install --default-timeout=1000 -i https://pypi.tuna.tsinghua.edu.cn/simple pandas matplotlib scikit-learn

# 3. 最后单独安装 PyTorch（关闭其他进程）
python3 -m pip install --default-timeout=1000 -i https://pypi.tuna.tsinghua.edu.cn/simple torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

---

## 完整部署步骤（修复内存问题）

### 步骤 1：SSH 登录服务器

```bash
ssh root@47.100.98.160 -p 22
# 密码：Zlt20060313#
```

### 步骤 2：检查内存状态

```bash
# 查看内存和 swap
free -h

# 查看 CPU 核心数
nproc
```

### 步骤 3：增加 Swap（如果内存 < 2GB）

```bash
# 创建 2GB swap
dd if=/dev/zero of=/swapfile bs=1M count=2048
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# 验证
free -h
```

### 步骤 4：创建工作目录并克隆代码

```bash
mkdir -p /home/workflow/DARIS
cd /home/workflow/DARIS
git clone https://github.com/disdorqin/DARIS.git .
cd code
```

### 步骤 5：升级 pip

```bash
python3 -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 步骤 6：安装依赖

```bash
# 安装 CPU 版 PyTorch（旧版本，内存占用更小）
python3 -m pip install --default-timeout=1000 -i https://pypi.tuna.tsinghua.edu.cn/simple torch==1.10.2+cpu torchvision==0.11.3+cpu torchaudio==0.10.2 -f https://download.pytorch.org/whl/lts/1.10.2/cpu/torch_lts.html

# 安装其他依赖
python3 -m pip install --default-timeout=1000 -i https://pypi.tuna.tsinghua.edu.cn/simple numpy pandas matplotlib scikit-learn
```

### 步骤 7：验证安装

```bash
python3 -c "import torch; print('PyTorch:', torch.__version__)"
```

### 步骤 8：运行测试

```bash
python3 test_model.py
```

---

## 一键部署脚本（修复内存问题）

```bash
#!/bin/bash
# 服务器部署脚本（修复内存不足）

WORK_DIR="/home/workflow/DARIS"
mkdir -p $WORK_DIR
cd $WORK_DIR

# 克隆代码
git clone https://github.com/disdorqin/DARIS.git .
cd code

# 检查内存
echo "=== 检查内存状态 ==="
free -h

# 如果内存 < 2GB，创建 swap
MEM=$(free -m | awk '/^Mem:/{print $2}')
if [ $MEM -lt 2000 ]; then
    echo "=== 内存不足 2GB，创建 2GB swap ==="
    dd if=/dev/zero of=/swapfile bs=1M count=2048
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    free -h
fi

# 升级 pip
echo "=== 升级 pip ==="
python3 -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

# 安装旧版 PyTorch（内存占用更小）
echo "=== 安装 PyTorch CPU 版（旧版，内存占用更小）==="
python3 -m pip install --default-timeout=1000 -i https://pypi.tuna.tsinghua.edu.cn/simple torch==1.10.2+cpu torchvision==0.11.3+cpu torchaudio==0.10.2 -f https://download.pytorch.org/whl/lts/1.10.2/cpu/torch_lts.html

# 安装其他依赖
echo "=== 安装其他依赖 ==="
python3 -m pip install --default-timeout=1000 -i https://pypi.tuna.tsinghua.edu.cn/simple numpy pandas matplotlib scikit-learn

# 验证安装
echo "=== 验证安装 ==="
python3 -c "import torch; print('PyTorch:', torch.__version__)"

# 运行测试
echo "=== 运行测试 ==="
python3 test_model.py

echo "=== 部署完成 ==="
```

---

## 服务器配置建议

### 最低配置要求

| 组件 | 最低要求 | 推荐配置 |
|------|----------|----------|
| 内存 | 1GB + 2GB swap | 2GB+ |
| CPU | 1 核心 | 2 核心 + |
| 存储 | 5GB | 10GB+ |

### 阿里云服务器升级

如果当前服务器配置太低，可以考虑：

1. **升级实例规格**：
   - 经济型：ecs.e-c1m1.large (1 核 1GB) → ecs.e-c1m2.large (1 核 2GB)
   - 突发性能型：ecs.t5-lc1m2.small (1 核 2GB)

2. **按量付费**：
   - 短期使用可以选择按量付费，更经济

---

## 完成验证清单

- [ ] SSH 登录成功
- [ ] 内存状态检查完成
- [ ] swap 创建成功（如果需要）
- [ ] 代码克隆成功
- [ ] pip 升级成功
- [ ] PyTorch CPU 版安装成功
- [ ] 依赖验证通过
- [ ] test_model.py 运行成功

---

## 预计安装时间

| 步骤 | 预计时间 |
|------|----------|
| swap 创建 | 2-5 分钟 |
| git clone | 1-2 分钟 |
| pip 升级 | 30 秒 |
| PyTorch 安装 | 5-10 分钟 |
| 其他依赖 | 2-5 分钟 |
| **总计** | **15-25 分钟** |

请耐心等待下载完成！