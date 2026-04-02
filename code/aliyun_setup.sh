#!/bin/bash
# 阿里云服务器环境配置脚本
# 使用方法：在服务器上运行 bash aliyun_setup.sh

echo "========================================"
echo "DARIS 阿里云服务器环境配置"
echo "========================================"

# 创建工作目录
WORK_DIR="/home/root/DARIS"
mkdir -p $WORK_DIR
cd $WORK_DIR

echo "工作目录：$WORK_DIR"

# 检查 Python 版本
echo ""
echo "检查 Python 环境..."
python3 --version

# 安装依赖
echo ""
echo "安装 Python 依赖..."
pip3 install torch numpy pandas matplotlib scikit-learn

# 验证安装
echo ""
echo "验证安装..."
python3 -c "import torch; import numpy; import pandas; print('依赖安装成功')"

echo ""
echo "========================================"
echo "环境配置完成"
echo "========================================"
echo "工作目录：$WORK_DIR"
echo "Python 版本：$(python3 --version)"
echo "PyTorch 版本：$(python3 -c 'import torch; print(torch.__version__)')"