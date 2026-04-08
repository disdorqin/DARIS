# SSH 免密登录完整配置指南

## 问题诊断

如果添加公钥后仍然需要密码，可能是以下原因：

1. 公钥未正确添加到 `authorized_keys`
2. 权限设置不正确
3. SSH 配置问题

---

## 完整步骤（在服务器上执行）

### 步骤 1：SSH 登录服务器

```bash
ssh root@47.100.98.160 -p 22
# 输入密码：Zlt20060313#
```

### 步骤 2：检查并创建 authorized_keys

```bash
# 查看当前 authorized_keys 内容
cat ~/.ssh/authorized_keys

# 如果没有内容或不存在，重新创建
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# 添加公钥（复制下面完整一行）
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJV6NyHSQq9DjJAMy9bJfIi0/D+djSL6YEAeJpq1G5gz 37813@DESKTOP" > ~/.ssh/authorized_keys

# 设置正确权限
chmod 600 ~/.ssh/authorized_keys

# 验证
cat ~/.ssh/authorized_keys
```

### 步骤 3：检查 SSH 配置

```bash
# 查看 SSH 配置
cat /etc/ssh/sshd_config | grep -E "(PubkeyAuthentication|AuthorizedKeysFile)"

# 确保以下配置存在且正确：
# PubkeyAuthentication yes
# AuthorizedKeysFile .ssh/authorized_keys
```

### 步骤 4：重启 SSH 服务

```bash
# CentOS/RHEL
systemctl restart sshd

# 或
service sshd restart
```

### 步骤 5：测试免密连接

**在本地执行**：
```bash
ssh root@47.100.98.160 -p 22
```

---

## 如果还是不行，使用以下命令诊断

### 在本地执行详细诊断

```bash
ssh -v root@47.100.98.160 -p 22
```

查看输出中的：
- `Offering public key` - 表示正在尝试公钥认证
- `Authentication succeeded` - 表示成功
- `Authentication failed` - 表示失败，查看具体原因

---

## 常见问题解决

### 问题 1：authorized_keys 权限错误

```bash
# 在服务器上执行
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chown -R root:root ~/.ssh
```

### 问题 2：SELinux 阻止

```bash
# 检查 SELinux 状态
getenforce

# 如果返回 Enforcing，临时禁用测试
setenforce 0

# 或修复 SELinux 上下文
restorecon -R -v ~/.ssh
```

### 问题 3：SSH 配置禁止公钥认证

```bash
# 编辑 SSH 配置
vi /etc/ssh/sshd_config

# 确保以下配置存在：
PubkeyAuthentication yes
PasswordAuthentication yes  # 保留密码认证作为备用

# 然后重启 SSH
systemctl restart sshd
```

---

## 快速解决方案（使用 ssh-copy-id 替代方案）

如果上述都不行，使用以下命令直接复制公钥：

```bash
# 在本地 PowerShell 执行
type C:\Users\37813\.ssh\id_ed25519.pub | ssh root@47.100.98.160 -p 22 "cat >> ~/.ssh/authorized_keys"
```

这会通过 SSH 连接将公钥追加到服务器的 authorized_keys 文件中。

---

## 最终测试

```bash
# 测试连接（应该不需要密码）
ssh root@47.100.98.160 -p 22 "echo 连接成功！"
```

如果成功，会输出"连接成功！"而不需要输入密码。