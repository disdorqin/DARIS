# 固定参数闭环执行报告

- 时间: 2026-04-02 21:56:25
- 数据: D:\computer learning\science_workflow\data\shandong_pmos_hourly.csv
- 核心创新: FDP-LF: Feature Decoupling + Physics Constraint + Long-horizon Forecast
- 理论依据: 近三年时序研究普遍显示：趋势/残差解耦提升可预测性，物理边界约束增强稳健性，长窗口增强长时依赖建模。
- 实现逻辑: 输入特征做趋势-残差解耦；训练/推理施加物理约束（非负+坡度约束）；窗口长度从72提升到120。

## 阶段2 Demo指标
- MAE: 51.683311
- RMSE: 72.663941
- R2: 0.861752

## 三模型全量数据对比
| Model | Variant | MAE | RMSE | R2 |
|---|---:|---:|---:|---:|
| XGBoost | baseline | 35.546631 | 55.607320 | 0.901238 |
| XGBoost | optimized | 37.335396 | 56.723444 | 0.897269 |
| TimesNet | baseline | 72.257195 | 108.536730 | 0.623749 |
| TimesNet | optimized | 71.933640 | 98.010328 | 0.693525 |
| MTGNN | baseline | 86.327293 | 123.084452 | 0.516128 |
| MTGNN | optimized | 86.038818 | 111.028035 | 0.606706 |

## 优化收益
| Model | MAE improve % | RMSE improve % | R2 gain |
|---|---:|---:|---:|
| XGBoost | -5.03 | -2.01 | -0.003969 |
| TimesNet | 0.45 | 9.70 | 0.069776 |
| MTGNN | 0.33 | 9.80 | 0.090579 |

## 代码改动核心要点
- XGBoost: code/power_models/xgboost_model.py: decouple特征 + 物理后处理 + 长窗口(96)
- TimesNet: code/power_models/timesnet_model.py: TimesNetLite + decouple输入 + physics penalty + 长窗口(120)
- MTGNN: code/power_models/mtgnn_model.py: 图相关邻接 + decouple输入 + physics penalty + 长窗口(120)

## 问题与修复复盘
- 每个训练任务均启用最多 3 次自动重试。
- 统一数据加载与编码回退，处理 NaN/零方差，避免训练中断。
- 统一物理约束后处理，缓解异常波动和无效预测值。

## 结论
本轮按固定流程完成单向闭环执行，已给出三模型 baseline 与优化版在 MAE、RMSE、R2 的可复现实验结果。
