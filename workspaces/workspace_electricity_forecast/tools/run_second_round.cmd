@echo off
setlocal
cd /d "d:\computer learning\science_workflow\workspaces\workspace_electricity_forecast"
set CUDA_VISIBLE_DEVICES=0
C:\ProgramData\anaconda3\envs\daris-research\python.exe -u openclaw_main.py --request "尖峰电价预测" --rounds 1 --gpu --no-callback --skip-git > report\second_round_run_20260407.log 2>&1
