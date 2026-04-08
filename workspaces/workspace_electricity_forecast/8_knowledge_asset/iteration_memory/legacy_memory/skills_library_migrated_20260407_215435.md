# DARIS v3 Skills Library

## 固定规则：冗余文件清理规则
- 每轮启动前必须先生成全目录预览，再执行清理。
- 仅允许自动删除：缓存目录（__pycache__/.pytest_cache/.mypy_cache/.ruff_cache/.ipynb_checkpoints）、Office 锁文件（~$*.docx|xlsx|pptx）、临时后缀文件（.tmp/.temp/.bak/.orig/.rej/.swp）、无效系统垃圾文件（Thumbs.db/.DS_Store）。
- 对失败/过期日志采用白名单路径和时间条件清理，默认保守跳过任何核心配置、有效代码、科研资产。
- 清理前必须记录清单和删除原因；清理后必须记录结果和回滚建议。

## 环节能力沉淀

## 每轮深度复盘

### [2026-04-07 21:51:01] 预清理阶段
- core_skills:
  - 全目录预览 + 安全白名单清理
  - 清理报告双格式落盘
- pitfalls:
  - 避免误删核心配置和科研资产
- optimizations:
  - 仅对显式冗余模式执行删除
- evidence:
  - report/cleanup_report_20260407_215101.md

### [2026-04-07 21:54:32] 标杆项目集成阶段
- core_skills:
  - 仓库三次重试克隆
  - 四步校验: 克隆/复现/适配/可用性
- pitfalls:
  - 仓库地址漂移导致克隆失败
  - 探针文件路径不稳定导致误判
- optimizations:
  - 配置化候选仓库地址
  - 统一适配文档模板自动生成
- evidence:
  - report/benchmark_integration_20260407_215432.md
