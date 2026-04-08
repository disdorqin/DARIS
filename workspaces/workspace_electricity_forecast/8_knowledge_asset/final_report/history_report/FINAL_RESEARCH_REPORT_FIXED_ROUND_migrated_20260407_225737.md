# 固定参数闭环执行报告

- 时间: 2026-04-07 22:04:55
- 数据: D:\computer learning\science_workflow\workspaces\workspace_electricity_forecast\6_experiment_execution\data\shandong_pmos_hourly.csv
- 核心创新: FDP-LF: Feature Decoupling + Physics Constraint + Long-horizon Forecast
- 理论依据: 近三年时序研究普遍显示：趋势/残差解耦提升可预测性，物理边界约束增强稳健性，长窗口增强长时依赖建模。
- 实现逻辑: 输入特征做趋势-残差解耦；训练/推理施加物理约束（非负+坡度约束）；窗口长度从72提升到120，并扩展到 PatchTST 轻量补充分支。

## 阶段2 Demo指标
- XGBoost MAE: 56.082336
- XGBoost RMSE: 79.114660
- XGBoost SMAPE: 51.730125
- XGBoost WAPE: 18.627249
- PatchTST MAE: 141.381393
- PatchTST RMSE: 175.262242
- PatchTST SMAPE: 64.694466
- PatchTST WAPE: 46.723038

## 四模型全量数据对比
| Model | Variant | MAE | RMSE | SMAPE | WAPE | R2 |
|---|---:|---:|---:|---:|---:|---:|
| XGBoost | baseline | 35.546631 | 55.607320 | 25.373453 | 11.096836 | 0.901238 |
| XGBoost | optimized | 37.829319 | 56.513793 | 35.150738 | 11.809752 | 0.898027 |
| TimesNet | baseline | 79.951813 | 116.359647 | 41.159519 | 24.959106 | 0.567557 |
| TimesNet | optimized | 77.544563 | 99.374258 | 46.865780 | 24.212175 | 0.684936 |
| MTGNN | baseline | 93.677643 | 128.726530 | 47.893883 | 29.243994 | 0.470750 |
| MTGNN | optimized | 78.136688 | 100.307530 | 51.491512 | 24.397058 | 0.678990 |
| PatchTST | baseline | 125.956375 | 164.056607 | 53.125614 | 39.320667 | 0.140369 |
| PatchTST | optimized | 114.693817 | 160.746312 | 47.386967 | 35.811497 | 0.175608 |

## 优化收益
| Model | MAE improve % | RMSE improve % | SMAPE improve % | WAPE improve % | R2 gain |
|---|---:|---:|---:|---:|---:|
| XGBoost | -6.42 | -1.63 | -38.53 | -6.42 | -0.003211 |
| TimesNet | 3.01 | 14.60 | -13.86 | 2.99 | 0.117379 |
| MTGNN | 16.59 | 22.08 | -7.51 | 16.57 | 0.208240 |
| PatchTST | 8.94 | 2.02 | 10.80 | 8.92 | 0.035239 |

## 代码改动核心要点
- XGBoost: 5_code_base/optimized/power_models/xgboost_model.py: decouple特征 + 物理后处理 + 长窗口(96)
- TimesNet: 5_code_base/optimized/power_models/timesnet_model.py: TimesNetLite + decouple输入 + physics penalty + 长窗口(120)
- MTGNN: 5_code_base/optimized/power_models/mtgnn_model.py: 图相关邻接 + decouple输入 + physics penalty + 长窗口(120)

## 问题与修复复盘
- 每个训练任务均启用最多 3 次自动重试。
- 统一数据加载与编码回退，处理 NaN/零方差，避免训练中断。
- 统一物理约束后处理，缓解异常波动和无效预测值。

## 结论
本轮按固定流程完成单向闭环执行，已给出四模型 baseline 与优化版在 MAE、RMSE、SMAPE、WAPE、R2 的可复现实验结果。
