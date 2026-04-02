# 阿里云服务器部署指南

## 方案：使用 /home/workflow 目录

### 步骤 1：在服务器上创建目录

在 SSH 会话中执行：
```bash
mkdir -p /home/workflow/DARIS
cd /home/workflow/DARIS
pwd
```

### 步骤 2：从本地上传文件

#### 方法 A：使用 scp 上传整个项目
在**本地终端**（不是 SSH 会话）执行：
```bash
scp -r -P 22 "d:\computer learning\science_workflow\code" root@47.100.98.160:/home/workflow/DARIS/
scp -P 22 "d:\computer learning\science_workflow\config" root@47.100.98.160:/home/workflow/DARIS/
scp -P 22 "d:\computer learning\science_workflow\data" root@47.100.98.160:/home/workflow/DARIS/
```

#### 方法 B：使用 git clone（推荐）
在**服务器 SSH 会话**中执行：
```bash
cd /home/workflow/DARIS
git clone https://github.com/disdorqin/DARIS.git .
```

### 步骤 3：安装依赖

在**服务器 SSH 会话**中执行：
```bash
cd /home/workflow/DARIS/code
pip3 install torch numpy pandas matplotlib scikit-learn
```

### 步骤 4：运行测试

在**服务器 SSH 会话**中执行：
```bash
cd /home/workflow/DARIS/code
python3 test_model.py
```

### 步骤 5：运行训练（可选）

```bash
cd /home/workflow/DARIS/code
python3 dynamic_mtg nn_model.py
```

---

## 快速部署命令（复制粘贴）

### 在服务器 SSH 会话中执行：
```bash
# 创建工作目录
mkdir -p /home/workflow/DARIS
cd /home/workflow/DARIS

# 使用 git clone 获取代码
git clone https://github.com/disdorqin/DARIS.git .

# 进入代码目录
cd code

# 安装依赖
pip3 install torch numpy pandas matplotlib scikit-learn

# 运行测试
python3 test_model.py
```

---

## 验证清单

- [ ] 工作目录创建：`/home/workflow/DARIS`
- [ ] 代码上传成功
- [ ] Python 依赖安装成功
- [ ] `test_model.py` 运行成功
- [ ] 输出形状正确：`[2, 7, 10, 1]`

---

## 常见问题

### Q1: scp 上传失败
**原因**：目标目录不存在或权限问题
**解决**：先执行 `mkdir -p /home/workflow/DARIS`

### Q2: git clone 失败
**原因**：网络问题或仓库不存在
**解决**：检查网络连接，或使用 scp 上传

### Q3: pip3 安装失败
**原因**：pip 版本过旧或网络问题
**解决**：`pip3 install --upgrade pip` 或使用国内镜像
```bash
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple torch numpy pandas matplotlib scikit-learn
```

### Q4: python3 找不到
**原因**：未安装 Python3
**解决**：
```bash
# Ubuntu/Debian
apt update && apt install python3 python3-pip

# CentOS/RHEL
yum install python3 python3-pip