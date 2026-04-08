# OpenClaw 安装位置说明

## 📍 OpenClaw 安装在哪里？

### 实际安装位置

| 组件 | 位置 | 说明 |
|------|------|------|
| **OpenClaw CLI（命令行工具）** | `C:\Users\37813\AppData\Roaming\npm\node_modules\openclaw\` | 程序文件（在 C 盘） |
| **OpenClaw 配置和数据** | `E:\Openclaw\data\` | 配置文件、插件、日志等（已迁移到 E 盘） |
| **符号链接** | `C:\Users\37813\.openclaw` → `E:\Openclaw\data\` | C 盘是符号链接，实际数据在 E 盘 |

### 为什么要迁移到 E 盘？

1. **节省 C 盘空间**：OpenClaw 的插件和依赖文件较大（约 570MB）
2. **便于备份**：所有配置和数据集中在 E 盘，方便备份
3. **保持兼容**：使用符号链接，程序仍然认为数据在 C 盘，不影响功能

### 目录结构

```
E:\Openclaw\
└── data\                    # 实际数据目录（原 C:\Users\37813\.openclaw）
    ├── openclaw.json        # 主配置文件
    ├── mcp-servers.json     # MCP 服务器配置
    ├── gateway.cmd          # 网关启动脚本
    ├── canvas/              # 画布功能
    ├── cron/                # 定时任务
    ├── devices/             # 设备配对信息
    ├── extensions/          # 扩展插件
    │   └── openclaw-qqbot/  # QQ 机器人插件（约 570MB）
    ├── identity/            # 身份认证
    ├── logs/                # 日志文件
    ├── media/               # 媒体文件
    ├── qqbot/               # QQ 机器人数据
    └── ...
```

### 如何验证？

```bash
# 查看符号链接
dir C:\Users\37813\.openclaw

# 输出会显示：
# C:\Users\37813\.openclaw <<===>> E:\Openclaw\data
```

### 注意事项

1. **不要删除符号链接**：`C:\Users\37813\.openclaw` 是指向 E 盘的链接，删除会导致配置丢失
2. **修改配置时**：可以直接编辑 `E:\Openclaw\data\openclaw.json`
3. **查看日志时**：日志文件在 `E:\Openclaw\data\logs\` 或 `C:\Users\37813\AppData\Local\Temp\openclaw\`

---

## 科研项目位置

**项目根目录**：`D:\作业\大创_挑战杯_互联网\大学生创新创业计划\大创实现\总项目\`

```
总项目/
├── utils/              # 工具函数（文献检索、代码生成等）
├── models/             # 模型代码
├── notebooks/          # Jupyter 脚本
├── data/               # 数据集
├── results/            # 实验结果
├── docs/               # 文档
├── backup.py           # 备份脚本
├── requirements.txt    # Python 依赖
└── README.md           # 项目说明
```

---

## 其他相关路径

| 名称 | 路径 |
|------|------|
| Zotero 数据 | `D:\作业\science\zotero\数据存储` |
| Zotero 配置 | `D:\作业\science\zotero\系统文件\zotero-mcp-config.json` |
| Obsidian Vault | `D:\浏览器\Edge\科研\obsidian` |
| Obsidian 数据 | `D:\作业\science\obsidian` |
| 阿里云服务器 | 47.100.98.160 (SSH: root / Zlt20060313#) |

---

**总结**：OpenClaw 的程序在 C 盘（npm 全局安装），但配置和数据已迁移到 E 盘（`E:\Openclaw\data\`），通过符号链接保持功能正常。