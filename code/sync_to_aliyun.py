"""
阿里云服务器同步与调优启动脚本
环节 5：阿里云服务器自动化调优与实验迭代

功能：
1. SSH 同步代码到阿里云服务器
2. 检查服务器环境（Python、PyTorch）
3. 安装依赖
4. 启动 ARIS 调优流程

作者：DARIS 团队
日期：2026-04-01
"""

import os
import subprocess
import logging
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 服务器配置
SERVER_IP = os.getenv('ALIYUN_SERVER_IP', '47.100.98.160')
SERVER_PORT = os.getenv('ALIYUN_SERVER_PORT', '22')
SERVER_USER = os.getenv('ALIYUN_SERVER_USER', 'root')
SERVER_PASSWORD = os.getenv('ALIYUN_SERVER_PASSWORD', '')
SERVER_WORK_DIR = os.getenv('ALIYUN_SERVER_WORK_DIR', '/home/root/DARIS/')


def check_server_env():
    """检查服务器环境"""
    logger.info("=" * 60)
    logger.info("检查阿里云服务器环境...")
    logger.info("=" * 60)
    
    # SSH 命令
    ssh_cmd = f"ssh {SERVER_USER}@{SERVER_IP} -p {SERVER_PORT}"
    
    # 检查命令
    check_commands = [
        "python3 --version",
        "pip3 --version",
        "python3 -c 'import torch; print(f\"PyTorch: {torch.__version__}\")'",
        "nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo 'No GPU found'"
    ]
    
    logger.info(f"\n请手动执行以下命令检查服务器环境：\n")
    logger.info(f"ssh {SERVER_USER}@{SERVER_IP} -p {SERVER_PORT}\n")
    
    for cmd in check_commands:
        logger.info(f"  {cmd}")
    
    logger.info("\n" + "=" * 60)
    logger.info("或者使用以下一键检查脚本：\n")
    
    check_script = f"""
ssh {SERVER_USER}@{SERVER_IP} -p {SERVER_PORT} << 'EOF'
echo "=== Python 版本 ==="
python3 --version

echo "=== Pip 版本 ==="
pip3 --version

echo "=== PyTorch 检查 ==="
python3 -c "import torch; print(f'PyTorch: {{torch.__version__}}')" 2>/dev/null || echo "PyTorch 未安装"

echo "=== GPU 检查 ==="
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo "No GPU found"

echo "=== 磁盘空间 ==="
df -h {SERVER_WORK_DIR}
EOF
"""
    logger.info(check_script)
    logger.info("=" * 60)


def sync_code_to_server():
    """同步代码到服务器"""
    logger.info("\n" + "=" * 60)
    logger.info("同步代码到阿里云服务器...")
    logger.info("=" * 60)
    
    # 项目根目录
    project_root = Path(__file__).parent.parent
    
    # 需要同步的文件
    sync_files = [
        'code/dynamic_mtg nn_model.py',
        'code/test_model.py',
        'config/',
        'data/',
        '.env'
    ]
    
    logger.info(f"\n请手动执行以下命令同步代码：\n")
    
    for file in sync_files:
        src = project_root / file
        if src.exists():
            scp_cmd = f"scp -P {SERVER_PORT} -r {src} {SERVER_USER}@{SERVER_IP}:{SERVER_WORK_DIR}"
            logger.info(f"  {scp_cmd}")
    
    logger.info("\n或使用 rsync 全量同步：")
    rsync_cmd = f"rsync -avz -e 'ssh -p {SERVER_PORT}' {project_root}/ {SERVER_USER}@{SERVER_IP}:{SERVER_WORK_DIR}"
    logger.info(f"  {rsync_cmd}")
    
    logger.info("\n" + "=" * 60)


def install_server_deps():
    """服务器依赖安装"""
    logger.info("\n" + "=" * 60)
    logger.info("服务器依赖安装命令...")
    logger.info("=" * 60)
    
    install_script = f"""
ssh {SERVER_USER}@{SERVER_IP} -p {SERVER_PORT} << 'EOF'
cd {SERVER_WORK_DIR}

# 安装 Python 依赖
pip3 install torch numpy pandas matplotlib scikit-learn

# 验证安装
python3 -c "import torch; import numpy; import pandas; print('依赖安装成功')"
EOF
"""
    logger.info(install_script)
    logger.info("=" * 60)


def run_server_training():
    """服务器训练命令"""
    logger.info("\n" + "=" * 60)
    logger.info("服务器训练启动命令...")
    logger.info("=" * 60)
    
    train_script = f"""
ssh {SERVER_USER}@{SERVER_IP} -p {SERVER_PORT} << 'EOF'
cd {SERVER_WORK_DIR}

# 运行模型测试
python3 code/test_model.py

# 运行训练（示例）
# python3 code/train.py --model dynamic_mtg nn --epochs 50
EOF
"""
    logger.info(train_script)
    logger.info("=" * 60)


def main():
    """主函数"""
    logger.info("\n" + "=" * 70)
    logger.info("DARIS 环节 5：阿里云服务器自动化调优")
    logger.info("=" * 70)
    
    # 由于 Windows 限制，生成手动执行脚本
    check_server_env()
    sync_code_to_server()
    install_server_deps()
    run_server_training()
    
    logger.info("\n" + "=" * 70)
    logger.info("说明：")
    logger.info("1. 由于 Windows 限制，请手动复制上述命令执行")
    logger.info("2. 或使用 WSL/PowerShell 执行 SSH 命令")
    logger.info("3. 推荐使用 Xshell/PuTTY 等 SSH 客户端连接服务器")
    logger.info("=" * 70)


if __name__ == '__main__':
    main()