@echo off
setlocal
set PYTHONUNBUFFERED=1
cd /d "d:\computer learning\science_workflow\workspaces\workspace_electricity_forecast"
"C:\ProgramData\anaconda3\envs\daris-research\python.exe" "2_agent_system\1_research_manager\run.py" --request "多源异构数据预测、多特征时序预测、多变量特征工程、多源数据融合、电力预测多特征利用，重点抓取当前可公开检索到的相关文献，提炼多特征利用与多源融合方法，提出多源异构数据融合+多特征工程优化策略，并修改XGBoost、TimesNet、MTGNN、PatchTST四模型代码完成全量测试" --rounds 1 --skip-migrate --skip-benchmark --skip-git > "d:\computer learning\science_workflow\workspaces\workspace_electricity_forecast\report\round2_run.log" 2>&1
endlocal
