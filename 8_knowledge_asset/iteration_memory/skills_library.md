# DARIS v3 Skills Library

## 固定规则：冗余文件清理规则
- 每轮工作流启动前，先生成全目录预览，不允许跳过。
- 自动清理仅允许处理以下对象：缓存目录（__pycache__/.pytest_cache/.mypy_cache/.ruff_cache/.ipynb_checkpoints）、Office 锁文件（~$*.docx|xlsx|pptx）、临时文件后缀（.tmp/.temp/.bak/.orig/.rej/.swp）、系统垃圾（Thumbs.db/.DS_Store）。
- 失败日志清理需同时满足：名称包含 failed 或 error，且超过 48 小时。
- 任何核心配置、有效代码、已沉淀科研资产一律不自动删除。
- 清理必须输出清单、原因、删除结果、跳过原因，并同步进入版本记录。

## 环节能力沉淀

## 每轮深度复盘

### [2026-04-03 10:24:12] 预清理阶段
- core_skills:
  - 全目录预览 + 安全白名单清理
  - 清理报告双格式落盘
- pitfalls:
  - 避免误删核心配置和科研资产
- optimizations:
  - 仅对显式冗余模式执行删除
- evidence:
  - 8_knowledge_asset/final_report/cleanup_report_20260403_102412.md

### [2026-04-03 10:26:03] 预清理阶段
- core_skills:
  - 全目录预览 + 安全白名单清理
  - 清理报告双格式落盘
- pitfalls:
  - 避免误删核心配置和科研资产
- optimizations:
  - 仅对显式冗余模式执行删除
- evidence:
  - 8_knowledge_asset/final_report/cleanup_report_20260403_102603.md

### [2026-04-03 10:26:37] 预清理阶段
- core_skills:
  - 全目录预览 + 安全白名单清理
  - 清理报告双格式落盘
- pitfalls:
  - 避免误删核心配置和科研资产
- optimizations:
  - 仅对显式冗余模式执行删除
- evidence:
  - 8_knowledge_asset/final_report/cleanup_report_20260403_102637.md

### [2026-04-03 10:27:25] 预清理阶段
- core_skills:
  - 全目录预览 + 安全白名单清理
  - 清理报告双格式落盘
- pitfalls:
  - 避免误删核心配置和科研资产
- optimizations:
  - 仅对显式冗余模式执行删除
- evidence:
  - 8_knowledge_asset/final_report/cleanup_report_20260403_102725.md

### [2026-04-03 10:29:49] 预清理阶段
- core_skills:
  - 全目录预览 + 安全白名单清理
  - 清理报告双格式落盘
- pitfalls:
  - 避免误删核心配置和科研资产
- optimizations:
  - 仅对显式冗余模式执行删除
- evidence:
  - 8_knowledge_asset/final_report/cleanup_report_20260403_102949.md

### [2026-04-03 10:30:43] 预清理阶段
- core_skills:
  - 全目录预览 + 安全白名单清理
  - 清理报告双格式落盘
- pitfalls:
  - 避免误删核心配置和科研资产
- optimizations:
  - 仅对显式冗余模式执行删除
- evidence:
  - 8_knowledge_asset/final_report/cleanup_report_20260403_103043.md

### [2026-04-03 10:31:32] 预清理阶段
- core_skills:
  - 全目录预览 + 安全白名单清理
  - 清理报告双格式落盘
- pitfalls:
  - 避免误删核心配置和科研资产
- optimizations:
  - 仅对显式冗余模式执行删除
- evidence:
  - 8_knowledge_asset/final_report/cleanup_report_20260403_103132.md

### [2026-04-03 10:36:52] 标杆项目集成阶段
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
  - 8_knowledge_asset/final_report/benchmark_integration_20260403_103652.md

### [2026-04-03 10:37:55] 轮次1执行阶段
- core_skills:
  - 文献抓取-创新生成-评审-代码改动-验证串行闭环
- pitfalls:
  - API 不可用时需降级且保持输出结构稳定
- optimizations:
  - 将全量测试日志固定重定向到 tuning_log
- evidence:
  - skipped_by_flag

### [2026-04-03 10:37:55] Round 1 深度复盘
- bottlenecks:
  - 标杆项目中存在 5 个非阻断失败项，影响能力完全落地率。
- root_causes:
  - 部分仓库地址不可用或网络不可达。
- optimization_paths:
  - 维护企业内部镜像仓库并在配置中优先使用镜像地址。
- reusable_capability_iterations:
  - 将仓库候选地址与探针文件写入配置并执行自动三次重试。

### [2026-04-03 10:38:47] 预清理阶段
- core_skills:
  - 全目录预览 + 安全白名单清理
  - 清理报告双格式落盘
- pitfalls:
  - 避免误删核心配置和科研资产
- optimizations:
  - 仅对显式冗余模式执行删除
- evidence:
  - 8_knowledge_asset/final_report/cleanup_report_20260403_103847.md

### [2026-04-03 10:52:25] 标杆项目集成阶段
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
  - 8_knowledge_asset/final_report/benchmark_integration_20260403_105225.md

### [2026-04-03 10:58:41] 轮次1执行阶段
- core_skills:
  - 文献抓取-创新生成-评审-代码改动-验证串行闭环
- pitfalls:
  - API 不可用时需降级且保持输出结构稳定
- optimizations:
  - 将全量测试日志固定重定向到 tuning_log
- evidence:
  - 6_experiment_execution\tuning_log\auto_full_pipeline_stdout.log

### [2026-04-03 10:58:41] Round 1 深度复盘
- bottlenecks:
  - 标杆项目中存在 9 个非阻断失败项，影响能力完全落地率。
- root_causes:
  - 部分仓库地址不可用或网络不可达。
- optimization_paths:
  - 维护企业内部镜像仓库并在配置中优先使用镜像地址。
- reusable_capability_iterations:
  - 将仓库候选地址与探针文件写入配置并执行自动三次重试。

### [2026-04-03 11:19:00] 预清理阶段
- core_skills:
  - 全目录预览 + 安全白名单清理
  - 清理报告双格式落盘
- pitfalls:
  - 避免误删核心配置和科研资产
- optimizations:
  - 仅对显式冗余模式执行删除
- evidence:
  - 8_knowledge_asset/final_report/cleanup_report_20260403_111900.md

### [2026-04-03 11:19:50] 预清理阶段
- core_skills:
  - 全目录预览 + 安全白名单清理
  - 清理报告双格式落盘
- pitfalls:
  - 避免误删核心配置和科研资产
- optimizations:
  - 仅对显式冗余模式执行删除
- evidence:
  - 8_knowledge_asset/final_report/cleanup_report_20260403_111950.md

### [2026-04-03 11:20:44] 标杆项目集成阶段
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
  - 8_knowledge_asset/final_report/benchmark_integration_20260403_112044.md

### [2026-04-03 11:22:15] 预清理阶段
- core_skills:
  - 全目录预览 + 安全白名单清理
  - 清理报告双格式落盘
- pitfalls:
  - 避免误删核心配置和科研资产
- optimizations:
  - 仅对显式冗余模式执行删除
- evidence:
  - 8_knowledge_asset/final_report/cleanup_report_20260403_112215.md

### [2026-04-03 11:22:30] 轮次1执行阶段
- core_skills:
  - 文献抓取-创新生成-评审-代码改动-验证串行闭环
- pitfalls:
  - API 不可用时需降级且保持输出结构稳定
- optimizations:
  - 将全量测试日志固定重定向到 tuning_log
- evidence:
  - skipped_by_flag

### [2026-04-03 11:22:30] Round 1 深度复盘
- bottlenecks:
  - 标杆项目中存在 5 个非阻断失败项，影响能力完全落地率。
- root_causes:
  - 部分仓库地址不可用或网络不可达。
- optimization_paths:
  - 维护企业内部镜像仓库并在配置中优先使用镜像地址。
- reusable_capability_iterations:
  - 将仓库候选地址与探针文件写入配置并执行自动三次重试。

### [2026-04-03 11:23:07] 标杆项目集成阶段
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
  - 8_knowledge_asset/final_report/benchmark_integration_20260403_112307.md

### [2026-04-03 11:24:44] 轮次1执行阶段
- core_skills:
  - 文献抓取-创新生成-评审-代码改动-验证串行闭环
- pitfalls:
  - API 不可用时需降级且保持输出结构稳定
- optimizations:
  - 将全量测试日志固定重定向到 tuning_log
- evidence:
  - skipped_by_flag

### [2026-04-03 11:24:44] Round 1 深度复盘
- bottlenecks:
  - 标杆项目中存在 5 个非阻断失败项，影响能力完全落地率。
- root_causes:
  - 部分仓库地址不可用或网络不可达。
- optimization_paths:
  - 维护企业内部镜像仓库并在配置中优先使用镜像地址。
- reusable_capability_iterations:
  - 将仓库候选地址与探针文件写入配置并执行自动三次重试。

### [2026-04-03 11:25:33] 预清理阶段
- core_skills:
  - 全目录预览 + 安全白名单清理
  - 清理报告双格式落盘
- pitfalls:
  - 避免误删核心配置和科研资产
- optimizations:
  - 仅对显式冗余模式执行删除
- evidence:
  - 8_knowledge_asset/final_report/cleanup_report_20260403_112533.md

### [2026-04-03 11:27:08] 预清理阶段
- core_skills:
  - 全目录预览 + 安全白名单清理
  - 清理报告双格式落盘
- pitfalls:
  - 避免误删核心配置和科研资产
- optimizations:
  - 仅对显式冗余模式执行删除
- evidence:
  - 8_knowledge_asset/final_report/cleanup_report_20260403_112708.md

### [2026-04-03 11:27:48] 预清理阶段
- core_skills:
  - 全目录预览 + 安全白名单清理
  - 清理报告双格式落盘
- pitfalls:
  - 避免误删核心配置和科研资产
- optimizations:
  - 仅对显式冗余模式执行删除
- evidence:
  - 8_knowledge_asset/final_report/cleanup_report_20260403_112748.md

### [2026-04-03 11:28:19] 标杆项目集成阶段
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
  - 8_knowledge_asset/final_report/benchmark_integration_20260403_112819.md

### [2026-04-03 11:29:17] 标杆项目集成阶段
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
  - 8_knowledge_asset/final_report/benchmark_integration_20260403_112917.md

### [2026-04-03 11:30:13] 轮次1执行阶段
- core_skills:
  - 文献抓取-创新生成-评审-代码改动-验证串行闭环
- pitfalls:
  - API 不可用时需降级且保持输出结构稳定
- optimizations:
  - 将全量测试日志固定重定向到 tuning_log
- evidence:
  - skipped_by_flag

### [2026-04-03 11:30:13] Round 1 深度复盘
- bottlenecks:
  - 本轮主流程执行顺畅，未出现显著阻断。
- root_causes:
  - 前置清理与重试机制降低了偶发错误率。
- optimization_paths:
  - 继续强化阶段内指标门禁，缩短无效迭代。
- reusable_capability_iterations:
  - 保持阶段日志与能力沉淀同步写入 skills 知识库。
