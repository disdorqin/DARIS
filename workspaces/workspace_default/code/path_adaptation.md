# 路径适配说明

- 迁移后的业务入口统一通过 core/utils/path_resolver.py 获取当前工作区路径。
- workspace_default/code/openclaw_main.py 会把仓库根目录加入 sys.path，再加载 core 与 code/utils 下的本地包装模块。
- workspace_default/2_agent_system/1_research_manager/run.py 会把仓库根目录加入 sys.path，确保 core.utils.path_resolver 可导入。
- workspace_default/code/utils/aliyun_connector.py、dingtalk_callback.py、workspace_context.py 已按工作区路径重写。
