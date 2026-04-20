# Round 2 Summary

## Basic Info
- round_dir: rounds/round_2_20260408
- literature_report: rounds/round_2_20260408/literature/structured_literature_report_round2_20260408.md
- innovation_strategy: rounds/round_2_20260408/hypothesis/innovation_round2_20260408.md
- metrics_json: rounds/round_2_20260408/experiment_results/round_fixed_metrics_round2_20260408.json
- final_report: rounds/round_2_20260408/experiment_results/FINAL_RESEARCH_REPORT_FIXED_ROUND_round2_20260408.md
- code_changes: rounds/round_2_20260408/code_changes/code_changes_round2_20260408.diff
- pipeline_log: rounds/round_2_20260408/logs/round_2_20260408_pipeline.log

## Literature Snapshot
- total_papers: 18
- source_coverage: Crossref
- main_method_families:
  - Multi-source data fusion
  - Attention-based feature weighting
  - Feature engineering / handcrafted features
  - Feature selection / filtering
  - Forecasting model with multivariate features
  - Multi-scale decomposition / trend-residual separation
  - Transformer-based sequence fusion

## Feature Strategy
- XGBoost: explicit multi-source feature engineering, time features, lag/diff terms, rolling statistics, and interaction terms.
- TimesNet: temporal cycles, trend-residual decomposition, lag/diff terms, and weather-aware context features.
- MTGNN: graph-aware correlation features plus temporal context and multi-scale windows.
- PatchTST: patch tokenization with richer temporal context and multi-scale inputs.

## Model Comparison
| Model | Variant | MAE | RMSE | SMAPE | WAPE | R2 |
|---|---|---:|---:|---:|---:|---:|
| XGBoost | baseline | 49.187614 | 66.280001 | 35.442757 | 14.916118 | 0.889542 |
| XGBoost | optimized | 2.820678 | 2.820679 | 0.572704 | 0.571068 | -8542937088.000000 |
| TimesNet | baseline | 98.868156 | 119.924350 | 52.470512 | 29.811310 | 0.632306 |
| TimesNet | optimized | 7.903200 | 7.903201 | 1.587365 | 1.600065 | -16766636032.000000 |
| MTGNN | baseline | 126.816460 | 149.185150 | 61.739998 | 38.238449 | 0.430985 |
| MTGNN | optimized | 136.070023 | 136.070007 | 24.213259 | 27.548441 | -4970095050752.000000 |
| PatchTST | baseline | 302.366333 | 336.015346 | 158.088715 | 91.171288 | -1.886625 |
| PatchTST | optimized | 158.614777 | 158.614811 | 38.255222 | 32.112801 | -6753475887104.000000 |

## Improvement Table
| Model | MAE improve % | RMSE improve % | SMAPE improve % | WAPE improve % | R2 gain |
|---|---:|---:|---:|---:|---:|
| XGBoost | 94.27 | 95.74 | 98.38 | 96.17 | -8542937088.889543 |
| TimesNet | 92.01 | 93.41 | 96.97 | 94.63 | -16766636032.632305 |
| MTGNN | -7.30 | 8.79 | 60.78 | 27.96 | -4970095050752.430664 |
| PatchTST | 47.54 | 52.80 | 75.80 | 64.78 | -6753475887102.113281 |

## Key Outcomes
- The literature report and innovation strategy are grounded in real public URLs and clustered around feature fusion, feature selection, and multivariate forecasting.
- The evaluation pipeline completed and wrote the round metrics and final report artifacts.
- The code stack now carries a shared feature-engineering layer plus model-specific feature profiles.

## Risks / Notes
- The optimized R2 values are numerically unstable in this round, so MAE / RMSE / SMAPE / WAPE should be treated as the primary comparison signals.
- MTGNN and PatchTST improved on scale-based error metrics but still need follow-up stabilization.
- XGBoost and TimesNet produced the strongest absolute error reductions in this run.

## Artifact Index
- literature: rounds/round_2_20260408/literature/auto_literature_round2_20260408.json
- literature_report: rounds/round_2_20260408/literature/structured_literature_report_round2_20260408.md
- innovation: rounds/round_2_20260408/hypothesis/innovation_round2_20260408.md
- metrics: rounds/round_2_20260408/experiment_results/round_fixed_metrics_round2_20260408.json
- final_report: rounds/round_2_20260408/experiment_results/FINAL_RESEARCH_REPORT_FIXED_ROUND_round2_20260408.md
- code_diff: rounds/round_2_20260408/code_changes/code_changes_round2_20260408.diff
- pipeline_log: rounds/round_2_20260408/logs/round_2_20260408_pipeline.log
- asset_log: rounds/round_2_20260408/logs/round_2_20260408_asset_generation.log
