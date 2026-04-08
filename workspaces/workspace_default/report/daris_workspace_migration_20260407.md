# DARIS 默认工作区完整迁移报告

## 1. 备份完成情况
- 备份目录: d:\computer learning\science_workflow\backup_20260407
- 备份项数量: 15

### 备份校验
- d:\computer learning\science_workflow\1_config -> d:\computer learning\science_workflow\backup_20260407\1_config | files=0 bytes=0 | 校验: files=False bytes=False
- d:\computer learning\science_workflow\2_agent_system -> d:\computer learning\science_workflow\backup_20260407\2_agent_system | files=0 bytes=0 | 校验: files=False bytes=False
- d:\computer learning\science_workflow\3_literature_workflow -> d:\computer learning\science_workflow\backup_20260407\3_literature_workflow | files=0 bytes=0 | 校验: files=False bytes=False
- d:\computer learning\science_workflow\4_research_hypothesis -> d:\computer learning\science_workflow\backup_20260407\4_research_hypothesis | files=0 bytes=0 | 校验: files=False bytes=False
- d:\computer learning\science_workflow\5_code_base -> d:\computer learning\science_workflow\backup_20260407\5_code_base | files=0 bytes=0 | 校验: files=False bytes=False
- d:\computer learning\science_workflow\6_experiment_execution -> d:\computer learning\science_workflow\backup_20260407\6_experiment_execution | files=0 bytes=0 | 校验: files=False bytes=False
- d:\computer learning\science_workflow\7_monitor_system -> d:\computer learning\science_workflow\backup_20260407\7_monitor_system | files=0 bytes=0 | 校验: files=False bytes=False
- d:\computer learning\science_workflow\8_knowledge_asset -> d:\computer learning\science_workflow\backup_20260407\8_knowledge_asset | files=0 bytes=0 | 校验: files=False bytes=False
- d:\computer learning\science_workflow\aliyun_connector.py -> d:\computer learning\science_workflow\backup_20260407\aliyun_connector.py | files=0 bytes=0 | 校验: files=False bytes=False
- d:\computer learning\science_workflow\dingtalk_callback.py -> d:\computer learning\science_workflow\backup_20260407\dingtalk_callback.py | files=0 bytes=0 | 校验: files=False bytes=False
- d:\computer learning\science_workflow\workspace_context.py -> d:\computer learning\science_workflow\backup_20260407\workspace_context.py | files=0 bytes=0 | 校验: files=False bytes=False
- d:\computer learning\science_workflow\openclaw_main.py -> d:\computer learning\science_workflow\backup_20260407\openclaw_main.py | files=0 bytes=0 | 校验: files=False bytes=False
- d:\computer learning\science_workflow\openclaw_requirements.txt -> d:\computer learning\science_workflow\backup_20260407\openclaw_requirements.txt | files=0 bytes=0 | 校验: files=False bytes=False
- d:\computer learning\science_workflow\工程化工作流.md -> d:\computer learning\science_workflow\backup_20260407\工程化工作流.md | files=0 bytes=0 | 校验: files=False bytes=False
- d:\computer learning\science_workflow\DARIS_V31.md -> d:\computer learning\science_workflow\backup_20260407\DARIS_V31.md | files=0 bytes=0 | 校验: files=False bytes=False

## 2. 迁移执行情况
- 默认工作区: d:\computer learning\science_workflow\workspaces\workspace_default
- 迁移项数量: 15

### 迁移校验
- d:\computer learning\science_workflow\1_config -> d:\computer learning\science_workflow\workspaces\workspace_default\1_config | source_files=0 target_files=24 | source_bytes=0 target_bytes=74483 | 状态: PATCHED
- d:\computer learning\science_workflow\2_agent_system -> d:\computer learning\science_workflow\workspaces\workspace_default\2_agent_system | source_files=0 target_files=52 | source_bytes=0 target_bytes=197159 | 状态: PATCHED
- d:\computer learning\science_workflow\3_literature_workflow -> d:\computer learning\science_workflow\workspaces\workspace_default\3_literature_workflow | source_files=0 target_files=44 | source_bytes=0 target_bytes=176499249 | 状态: PATCHED
- d:\computer learning\science_workflow\4_research_hypothesis -> d:\computer learning\science_workflow\workspaces\workspace_default\hypothesis | source_files=0 target_files=11 | source_bytes=0 target_bytes=55389 | 状态: PATCHED
- d:\computer learning\science_workflow\5_code_base -> d:\computer learning\science_workflow\workspaces\workspace_default\code | source_files=0 target_files=19192 | source_bytes=0 target_bytes=543602835 | 状态: PATCHED
- d:\computer learning\science_workflow\6_experiment_execution -> d:\computer learning\science_workflow\workspaces\workspace_default\experiment | source_files=0 target_files=25 | source_bytes=0 target_bytes=14173603 | 状态: PATCHED
- d:\computer learning\science_workflow\7_monitor_system -> d:\computer learning\science_workflow\workspaces\workspace_default\7_monitor_system | source_files=0 target_files=8 | source_bytes=0 target_bytes=13726 | 状态: PATCHED
- d:\computer learning\science_workflow\8_knowledge_asset -> d:\computer learning\science_workflow\workspaces\workspace_default\knowledge_base | source_files=0 target_files=155 | source_bytes=0 target_bytes=1248248 | 状态: PATCHED
- d:\computer learning\science_workflow\aliyun_connector.py -> d:\computer learning\science_workflow\workspaces\workspace_default\code\utils\aliyun_connector.py | source_files=0 target_files=1 | source_bytes=0 target_bytes=593 | 状态: PATCHED
- d:\computer learning\science_workflow\dingtalk_callback.py -> d:\computer learning\science_workflow\workspaces\workspace_default\code\utils\dingtalk_callback.py | source_files=0 target_files=1 | source_bytes=0 target_bytes=771 | 状态: PATCHED
- d:\computer learning\science_workflow\workspace_context.py -> d:\computer learning\science_workflow\workspaces\workspace_default\code\utils\workspace_context.py | source_files=0 target_files=1 | source_bytes=0 target_bytes=199 | 状态: PATCHED
- d:\computer learning\science_workflow\openclaw_main.py -> d:\computer learning\science_workflow\workspaces\workspace_default\code\openclaw_main.py | source_files=0 target_files=1 | source_bytes=0 target_bytes=37903 | 状态: PATCHED
- d:\computer learning\science_workflow\openclaw_requirements.txt -> d:\computer learning\science_workflow\workspaces\workspace_default\code\openclaw_requirements.txt | source_files=0 target_files=1 | source_bytes=0 target_bytes=2149 | 状态: PATCHED
- d:\computer learning\science_workflow\工程化工作流.md -> d:\computer learning\science_workflow\workspaces\workspace_default\report\工程化工作流.md | source_files=0 target_files=1 | source_bytes=0 target_bytes=8737 | 状态: PATCHED
- d:\computer learning\science_workflow\DARIS_V31.md -> d:\computer learning\science_workflow\workspaces\workspace_default\report\DARIS_V31.md | source_files=0 target_files=1 | source_bytes=0 target_bytes=20172 | 状态: PATCHED

## 3. 根目录清理情况
- 已移除业务项数量: 7
- 已移除业务目录: d:\computer learning\science_workflow\5_code_base, d:\computer learning\science_workflow\6_experiment_execution, d:\computer learning\science_workflow\7_monitor_system, d:\computer learning\science_workflow\8_knowledge_asset
- 已移除临时文件: d:\computer learning\science_workflow\._migrate_default_workspace.py, d:\computer learning\science_workflow\.migrate_default_workspace.log, d:\computer learning\science_workflow\._migrate_default_workspace.log

## 4. 路径适配说明
- 迁移后的业务代码通过 core/utils/path_resolver.py 获取当前工作区路径。
- workspace_default/code/openclaw_main.py 已重写为从仓库根目录和 workspace utils 装载依赖。
- workspace_default/2_agent_system/1_research_manager/run.py 已重写为从仓库根目录装载 core。
- workspace_default/code/path_adaptation.md 已生成，用于说明入口修改方式。

## 5. 树文件位置
- 根目录树: d:\computer learning\science_workflow\workspaces\workspace_default\report\daris_root_tree_20260407.md
- workspace_default 树: d:\computer learning\science_workflow\workspaces\workspace_default\report\daris_workspace_default_tree_20260407.md
