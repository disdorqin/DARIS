# 固定参数闭环执行报告

- 时间: 2026-04-03 12:08:40
- 数据: D:\computer learning\science_workflow\6_experiment_execution\data\shandong_pmos_hourly.csv
- 核心创新: FDP-LF: Feature Decoupling + Physics Constraint + Long-horizon Forecast
- 理论依据: 近三年时序研究普遍显示：趋势/残差解耦提升可预测性，物理边界约束增强稳健性，长窗口增强长时依赖建模。
- 实现逻辑: 输入特征做趋势-残差解耦；训练/推理施加物理约束（非负+坡度约束）；窗口长度从72提升到120。

## 阶段2 Demo指标
- MAE: 56.082336
- RMSE: 79.114660
- R2: 0.836117

## 三模型全量数据对比
| Model | Variant | MAE | RMSE | R2 |
|---|---:|---:|---:|---:|
| XGBoost | baseline | 35.546631 | 55.607320 | 0.901238 |
| XGBoost | optimized | 37.829319 | 56.513793 | 0.898027 |
| TimesNet | baseline | 74.907478 | 104.443003 | 0.651596 |
| TimesNet | optimized | 66.196976 | 91.532749 | 0.732697 |
| MTGNN | baseline | 78.487801 | 110.962158 | 0.606745 |
| MTGNN | optimized | 74.288582 | 98.366477 | 0.691293 |

## 优化收益
| Model | MAE improve % | RMSE improve % | R2 gain |
|---|---:|---:|---:|
| XGBoost | -6.42 | -1.63 | -0.003211 |
| TimesNet | 11.63 | 12.36 | 0.081101 |
| MTGNN | 5.35 | 11.35 | 0.084548 |

## 代码改动核心要点
- XGBoost: 5_code_base/optimized/power_models/xgboost_model.py: decouple特征 + 物理后处理 + 长窗口(96)
- TimesNet: 5_code_base/optimized/power_models/timesnet_model.py: TimesNetLite + decouple输入 + physics penalty + 长窗口(120)
- MTGNN: 5_code_base/optimized/power_models/mtgnn_model.py: 图相关邻接 + decouple输入 + physics penalty + 长窗口(120)

## 问题与修复复盘
- 每个训练任务均启用最多 3 次自动重试。
- 统一数据加载与编码回退，处理 NaN/零方差，避免训练中断。
- 统一物理约束后处理，缓解异常波动和无效预测值。

## 结论
本轮按固定流程完成单向闭环执行，已给出三模型 baseline 与优化版在 MAE、RMSE、R2 的可复现实验结果。
