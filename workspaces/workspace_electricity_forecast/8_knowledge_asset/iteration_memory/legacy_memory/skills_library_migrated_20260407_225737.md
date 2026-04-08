# DARIS v3 Skills Library

## 固定规则：冗余文件清理规则
- 每轮启动前必须先生成全目录预览，再执行清理。
- 仅允许自动删除：缓存目录（__pycache__/.pytest_cache/.mypy_cache/.ruff_cache/.ipynb_checkpoints）、Office 锁文件（~$*.docx|xlsx|pptx）、临时后缀文件（.tmp/.temp/.bak/.orig/.rej/.swp）、无效系统垃圾文件（Thumbs.db/.DS_Store）。
- 对失败/过期日志采用白名单路径和时间条件清理，默认保守跳过任何核心配置、有效代码、科研资产。
- 清理前必须记录清单和删除原因；清理后必须记录结果和回滚建议。

## 环节能力沉淀

## 每轮深度复盘

### [2026-04-07 22:04:55] 轮次1执行阶段
- core_skills:
  - 文献抓取-创新生成-评审-代码改动-验证串行闭环
- pitfalls:
  - API 不可用时需降级且保持输出结构稳定
- optimizations:
  - 将全量测试日志固定重定向到 tuning_log
- evidence:
  - logs\auto_full_pipeline_stdout.log

### [2026-04-07 22:04:55] Round 1 深度复盘
- bottlenecks:
  - 标杆项目中存在 1 个非阻断失败项，影响能力完全落地率。
- root_causes:
  - 部分仓库地址不可用或网络不可达。
- optimization_paths:
  - 维护企业内部镜像仓库并在配置中优先使用镜像地址。
- reusable_capability_iterations:
  - 将仓库候选地址与探针文件写入配置并执行自动三次重试。

### [2026-04-07 22:49:38] 预清理阶段
- core_skills:
  - 全目录预览 + 安全白名单清理
  - 清理报告双格式落盘
- pitfalls:
  - 避免误删核心配置和科研资产
- optimizations:
  - 仅对显式冗余模式执行删除
- evidence:
  - report/cleanup_report_20260407_224938.md

### [2026-04-07 22:54:59] 预清理阶段
- core_skills:
  - 全目录预览 + 安全白名单清理
  - 清理报告双格式落盘
- pitfalls:
  - 避免误删核心配置和科研资产
- optimizations:
  - 仅对显式冗余模式执行删除
- evidence:
  - report/cleanup_report_20260407_225459.md

### [2026-04-07 22:57:37] 标杆项目集成阶段
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
  - report/benchmark_integration_20260407_225737.md
