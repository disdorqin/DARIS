# SSH 免密连接配置指南

## 问题说明

当前 SSH 连接阿里云服务器超时，需要配置 SSH 免密连接和保持连接。

---

## 解决方案

### 方案一：配置 SSH 免密连接（推荐）

#### 步骤 1: 生成本地 SSH 密钥

```bash
ssh-keygen -t rsa -b 4096
```

按回车接受默认设置（不需要密码）。

#### 步骤 2: 复制公钥到阿里云服务器

**方式 A: 使用 ssh-copy-id（如果有）**
```bash
ssh-copy-id root@47.100.98.160
```

**方式 B: 手动复制**

1. 查看公钥内容：
```bash
type $env:USERPROFILE\.ssh\id_rsa.pub
```

2. SSH 登录阿里云（输入密码）：
```bash
ssh root@47.100.98.160
```

3. 在阿里云服务器上执行：
```bash
mkdir -p ~/.ssh
echo "公钥内容" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
exit
```

#### 步骤 3: 测试免密连接

```bash
ssh -i ~/.ssh/id_rsa root@47.100.98.160 "echo connected"
```

---

### 方案二：使用 SSH 配置文件保持连接

#### 创建 SSH 配置文件

在 `C:\Users\你的用户名\.ssh\config` 创建文件：

```
Host aliyun
    HostName 47.100.98.160
    User root
    Port 22
    IdentityFile ~/.ssh/id_rsa
    ServerAliveInterval 60
    ServerAliveCountMax 3
    TCPKeepAlive yes
    ConnectTimeout 30
```

#### 使用方式

```bash
ssh aliyun "echo connected"
```

---

### 方案三：使用 paramiko 保持连接（Python 脚本）

创建 `2_agent_system/aliyun_connector.py`：

```python
import paramiko
import time

class AliyunConnector:
    def __init__(self, host, user, password):
        self.host = host
        self.user = user
        self.password = password
        self.ssh = None
        self.client = None
    
    def connect(self, max_retries=3):
        """连接阿里云服务器，支持重试"""
        for i in range(max_retries):
            try:
                self.ssh = paramiko.SSHClient()
                self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.ssh.connect(
                    self.host,
                    username=self.user,
                    password=self.password,
                    timeout=30,
                    banner_timeout=30,
                    auth_timeout=30
                )
                print(f"连接成功！")
                return True
            except Exception as e:
                print(f"连接失败 ({i+1}/{max_retries}): {e}")
                time.sleep(5)
        return False
    
    def exec_command(self, command):
        """执行命令"""
        if self.ssh:
            stdin, stdout, stderr = self.ssh.exec_command(command)
            return stdout.read().decode(), stderr.read().decode()
        return None, None
    
    def close(self):
        """关闭连接"""
        if self.ssh:
            self.ssh.close()

# 使用示例
if __name__ == "__main__":
    connector = AliyunConnector("47.100.98.160", "root", "你的密码")
    if connector.connect():
        output, error = connector.exec_command("nvidia-smi")
        print(output)
        connector.close()
```

---

### 方案四：使用 frp 内网穿透（高级）

如果阿里云服务器无法直接 SSH，可以在阿里云上部署 frp 服务端，本地部署 frpc 客户端。

---

## 自动化集成

### 在 openclaw_main.py 中添加 SSH 连接功能

```python
def check_aliyun_connection():
    """检查阿里云连接状态"""
    try:
        connector = AliyunConnector(...)
        if connector.connect():
            output, _ = connector.exec_command("nvidia-smi")
            connector.close()
            return "GPU 可用" in output
    except:
        pass
    return False
```

---

## 快速测试

### 测试连接

```bash
# 方式 1: 直接 SSH
ssh -o ConnectTimeout=10 -o ServerAliveInterval=30 root@47.100.98.160 "echo connected"

# 方式 2: 使用 paramiko
python -c "
import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('47.100.98.160', username='root', password='你的密码', timeout=10)
print('连接成功')
ssh.close()
"
```

---

## 常见问题

### Q1: 连接超时
- 检查服务器是否运行
- 检查安全组 22 端口是否开放
- 增加 ConnectTimeout 值

### Q2: 密码错误
- 确认密码正确
- 尝试重置服务器密码

### Q3: 公钥认证失败
- 检查 `~/.ssh/authorized_keys` 权限（应为 600）
- 检查 `~/.ssh` 目录权限（应为 700）

---

## 推荐配置流程

1. **先配置 SSH 免密连接**（方案一）
2. **配置 SSH 配置文件保持连接**（方案二）
3. **在 Python 脚本中使用 paramiko 连接**（方案三）

这样可以确保自动化脚本能够稳定连接阿里云服务器。