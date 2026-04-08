# DARIS v3 Skills Library

## 固定规则：冗余文件清理规则
- 每轮启动前必须先生成全目录预览，再执行清理。
- 仅允许自动删除：缓存目录（__pycache__/.pytest_cache/.mypy_cache/.ruff_cache/.ipynb_checkpoints）、Office 锁文件（~$*.docx|xlsx|pptx）、临时后缀文件（.tmp/.temp/.bak/.orig/.rej/.swp）、无效系统垃圾文件（Thumbs.db/.DS_Store）。
- 对失败/过期日志采用白名单路径和时间条件清理，默认保守跳过任何核心配置、有效代码、科研资产。
- 清理前必须记录清单和删除原因；清理后必须记录结果和回滚建议。

## 环节能力沉淀

## 每轮深度复盘

### [2026-04-07 23:15:03] 预清理阶段
- core_skills:
  - 全目录预览 + 安全白名单清理
  - 清理报告双格式落盘
- pitfalls:
  - 避免误删核心配置和科研资产
- optimizations:
  - 仅对显式冗余模式执行删除
- evidence:
  - report/cleanup_report_20260407_231503.md

### [2026-04-07 23:15:03] 标杆项目集成阶段
- core_skills:
  - 通过显式开关跳过高成本网络集成阶段
- pitfalls:
  - 外部仓库克隆过慢会拖慢主流程
- optimizations:
  - 在受限环境下优先保证主流程可交付
- evidence:
  - skip_benchmark=true
