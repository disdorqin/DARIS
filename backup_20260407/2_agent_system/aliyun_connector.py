#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
阿里云服务器连接器

支持自动重试、超时处理、保持连接
用于 DARIS 自动化脚本连接阿里云 GPU 服务器
"""

import paramiko
import time
import logging
from pathlib import Path
from typing import Optional, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AliyunConnector")


class AliyunConnector:
    """阿里云服务器连接器"""
    
    def __init__(
        self,
        host: str = "47.100.98.160",
        port: int = 22,
        user: str = "root",
        password: Optional[str] = None,
        key_file: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: int = 5
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.key_file = key_file
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.ssh = None
        self.connected = False
    
    def connect(self) -> bool:
        """
        连接阿里云服务器，支持自动重试
        
        Returns:
            bool: 连接是否成功
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"尝试连接 {self.user}@{self.host}:{self.port} (第 {attempt}/{self.max_retries} 次)")
                
                self.ssh = paramiko.SSHClient()
                self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                # 优先使用密钥认证，否则使用密码
                if self.key_file and Path(self.key_file).exists():
                    self.ssh.connect(
                        hostname=self.host,
                        port=self.port,
                        username=self.user,
                        key_filename=self.key_file,
                        timeout=self.timeout,
                        banner_timeout=self.timeout,
                        auth_timeout=self.timeout,
                        allow_agent=True,
                        look_for_keys=True
                    )
                elif self.password:
                    self.ssh.connect(
                        hostname=self.host,
                        port=self.port,
                        username=self.user,
                        password=self.password,
                        timeout=self.timeout,
                        banner_timeout=self.timeout,
                        auth_timeout=self.timeout,
                        allow_agent=False,
                        look_for_keys=False
                    )
                else:
                    logger.error("未提供密码或密钥文件")
                    return False
                
                # 测试连接
                stdin, stdout, stderr = self.ssh.exec_command("echo connected", timeout=10)
                result = stdout.read().decode().strip()
                
                if result == "connected":
                    logger.info("连接成功！")
                    self.connected = True
                    return True
                else:
                    logger.warning(f"连接测试失败：{result}")
                    
            except paramiko.AuthenticationException as e:
                logger.error(f"认证失败：{e}")
                return False  # 认证失败不重试
                
            except paramiko.SSHException as e:
                logger.warning(f"SSH 错误：{e}")
                
            except Exception as e:
                logger.warning(f"连接失败：{e}")
            
            if attempt < self.max_retries:
                logger.info(f"等待 {self.retry_delay} 秒后重试...")
                time.sleep(self.retry_delay)
        
        logger.error(f"连接失败，已重试 {self.max_retries} 次")
        return False
    
    def exec_command(self, command: str, timeout: int = 300) -> Tuple[Optional[str], Optional[str]]:
        """
        执行命令
        
        Args:
            command: 要执行的命令
            timeout: 超时时间（秒）
        
        Returns:
            (stdout, stderr) 或 (None, None)
        """
        if not self.ssh or not self.connected:
            logger.error("未连接到服务器")
            return None, None
        
        try:
            logger.info(f"执行命令：{command[:50]}...")
            stdin, stdout, stderr = self.ssh.exec_command(command, timeout=timeout)
            
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            return output, error
            
        except Exception as e:
            logger.error(f"命令执行失败：{e}")
            self.connected = False
            return None, None
    
    def check_gpu(self) -> bool:
        """检查 GPU 状态"""
        output, _ = self.exec_command("nvidia-smi --query-gpu=name,memory.total --format=csv,noheader")
        if output:
            logger.info(f"GPU 状态：{output.strip()}")
            return True
        return False
    
    def check_python(self) -> bool:
        """检查 Python 环境"""
        output, _ = self.exec_command("python --version && pip list | grep torch")
        if output:
            logger.info(f"Python 环境：{output.strip()}")
            return True
        return False
    
    def close(self):
        """关闭连接"""
        if self.ssh:
            try:
                self.ssh.close()
                logger.info("连接已关闭")
            except:
                pass
        self.connected = False
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


def create_connector_from_env() -> AliyunConnector:
    """从环境变量创建连接器"""
    import os
    
    # 从 .env 文件读取配置
    env_file = Path(__file__).resolve().parents[1] / ".env"
    env_config = {}
    
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env_config[key.strip()] = value.strip().strip('"').strip("'")
    
    return AliyunConnector(
        host=env_config.get("ALIYUN_SERVER_IP", "47.100.98.160"),
        port=int(env_config.get("ALIYUN_SERVER_PORT", "22")),
        user=env_config.get("ALIYUN_SERVER_USER", "root"),
        password=env_config.get("ALIYUN_SERVER_PASSWORD"),
        timeout=60,
        max_retries=3,
        retry_delay=10
    )


# ==================== 命令行使用 ====================

if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("阿里云服务器连接器")
    print("=" * 60)
    
    # 创建连接器
    connector = create_connector_from_env()
    
    # 连接
    if not connector.connect():
        print("\n连接失败，请检查：")
        print("1. 服务器是否运行")
        print("2. 安全组是否开放 22 端口")
        print("3. 密码是否正确")
        sys.exit(1)
    
    # 检查 GPU
    print("\n--- GPU 状态 ---")
    if connector.check_gpu():
        print("GPU 可用")
    else:
        print("GPU 不可用或未安装驱动")
    
    # 检查 Python
    print("\n--- Python 环境 ---")
    if connector.check_python():
        print("Python 环境正常")
    else:
        print("Python 未安装或 PyTorch 未安装")
    
    # 关闭连接
    connector.close()
    print("\n完成")