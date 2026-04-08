# 上下文压缩快照（核心态）

## 当前状态
- 固定参数闭环已完成，阶段1-5均已跑通。

## 核心创新
- FDP-LF：特征解耦 + 物理约束 + 长时序窗口优化。

## 关键代码
- `code/power_models/common.py`
- `code/power_models/xgboost_model.py`
- `code/power_models/timesnet_model.py`
- `code/power_models/mtgnn_model.py`
- `code/run_round_fixed_pipeline.py`

## 核心指标（全量 /data）
- XGBoost: baseline(35.5466, 55.6073, 0.9012) -> optimized(37.3354, 56.7234, 0.8973)
- TimesNet: baseline(89.6594, 127.3486, 0.4820) -> optimized(66.8901, 94.0527, 0.7178)
- MTGNN: baseline(81.1774, 112.8659, 0.5931) -> optimized(71.8979, 95.6368, 0.7082)

## 核心文档
- 主日志：`report/AUTO_EXECUTION_LOG.md`
- 固定轮次报告：`report/FINAL_RESEARCH_REPORT_FIXED_ROUND.md`
- 指标JSON：`report/round_fixed_metrics.json`

## 快速续跑口令
- “读取 `report/CONTEXT_SNAPSHOT.md` 与 `report/round_fixed_metrics.json`，在保留 FDP-LF 前提下继续优化 XGBoost 退化问题。”
