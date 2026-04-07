# DARIS 项目技能文档

## SSH 免密登录（WSL + sshpass）

### 连接命令

```bash
# 基础连接
sshpass -p 'Zlt20060313#' ssh -o StrictHostKeyChecking=no -p 22 root@47.100.98.160

# 执行单条命令
sshpass -p 'Zlt20060313#' ssh -o StrictHostKeyChecking=no -p 22 root@47.100.98.160 "命令内容"

# 执行脚本
sshpass -p 'Zlt20060313#' ssh -o StrictHostKeyChecking=no -p 22 root@47.100.98.160 "bash -s" < 本地脚本.sh
```

### 服务器清理命令

```bash
# 清理代码目录中的临时文件（保留系统文件）
sshpass -p 'Zlt20060313#' ssh -o StrictHostKeyChecking=no -p 22 root@47.100.98.160 "
cd /home/workflow/DARIS/code &&
rm -f DEPLOY_GUIDE.md deploy_to_aliyun.sh sync_to_aliyun.py run_literature_download.py install_chromedriver.ps1 &&
rm -rf utils __pycache__ &&
echo '清理完成！'
"
```

### 内存清理命令

```bash
# 清理页面缓存和回收 slab
sshpass -p 'Zlt20060313#' ssh -o StrictHostKeyChecking=no -p 22 root@47.100.98.160 "
sync &&
echo 3 > /proc/sys/vm/drop_caches &&
free -h &&
echo '内存已清理！'
"
```

### 模型测试命令

```bash
# 运行模型测试（使用 python3.11）
sshpass -p 'Zlt20060313#' ssh -o StrictHostKeyChecking=no -p 22 root@47.100.98.160 "
cd /home/workflow/DARIS/code &&
python3.11 test_model.py
"
```

---

## 服务器信息

| 项目 | 值 |
|------|-----|
| IP 地址 | 47.100.98.160 |
| 端口 | 22 |
| 用户名 | root |
| 密码 | Zlt20060313# |
| 工作目录 | /home/workflow/DARIS |
| Python 版本 | 3.6.8 (系统默认), 3.11 (PyTorch 安装) |
| 内存 | 1.8GB |
| Swap | 2.0GB |

---

## 重要提示

1. **系统文件不要动**：
   - `.git/` 目录
   - `LICENSE`
   - 系统配置文件

2. **保留的核心文件**：
   - `code/dynamic_mtg nn_model.py`
   - `code/test_model.py`
   - `code/program.md`
   - `code/run_crawler.py`
   - `code/crawler/`
   - `config/`
   - `data/`

3. **可以删除的文件**：
   - 临时脚本（`*_setup.sh`, `deploy_*.sh`）
   - 重复功能的脚本
   - `__pycache__/` 缓存目录
   - Windows 专用脚本（`.ps1`）

---

## 常用命令速查

```bash
# 查看服务器文件
sshpass -p 'Zlt20060313#' ssh -o StrictHostKeyChecking=no -p 22 root@47.100.98.160 "ls -la /home/workflow/DARIS/"

# 查看内存状态
sshpass -p 'Zlt20060313#' ssh -o StrictHostKeyChecking=no -p 22 root@47.100.98.160 "free -h"

# 查看 Python 版本
sshpass -p 'Zlt20060313#' ssh -o StrictHostKeyChecking=no -p 22 root@47.100.98.160 "python3.11 --version"

# 检查 PyTorch 安装
sshpass -p 'Zlt20060313#' ssh -o StrictHostKeyChecking=no -p 22 root@47.100.98.160 "python3.11 -c 'import torch; print(torch.__version__)'"

# 运行模型测试
sshpass -p 'Zlt20060313#' ssh -o StrictHostKeyChecking=no -p 22 root@47.100.98.160 "cd /home/workflow/DARIS/code && python3.11 test_model.py"
```

---

## 已完成的部署

### PyTorch 安装

```bash
# 已安装 CPU 版 PyTorch
pip3 install --default-timeout=1000 -i https://pypi.tuna.tsinghua.edu.cn/simple torch==2.0.0+cpu torchvision==0.15.0+cpu torchaudio==2.0.0 --index-url https://download.pytorch.org/whl/cpu
```

**安装位置**：`/usr/local/lib64/python3.11/site-packages`

**使用命令**：`python3.11 -c "import torch; print(torch.__version__)"`

### 模型测试

```bash
# 测试成功
cd /home/workflow/DARIS/code && python3.11 test_model.py

# 预期输出：
# 测试 Dynamic MTGNN 模型...
# [OK] 测试通过！
#   输入形状：torch.Size([2, 12, 10, 1])
#   输出形状：torch.Size([2, 7, 10, 1])
#   模型参数量：4,913
```

---

## NumPy 版本警告处理

如果出现 `Failed to initialize NumPy: _ARRAY_API not found` 警告：

```bash
# 方案 1：降级 NumPy（推荐）
pip3 install 'numpy<2'

# 方案 2：忽略警告（可以正常运行）
# 警告不影响功能使用