# Innovation Proposal (model=local-rescue)

[本地兜底生成]
输入片段: 基于文献阅读结论提出创新点，要求适配 MTGNN/TimesNet/XGBoost。  [本地兜底生成] 输入片段: 任务: 阅读以下文献条目并总结研究脉络、常见缺陷、可利用空白。  1. A Hybrid Method for Forecasting of Fuzzy Time Series    DOI: 10.2174/9781681085289117020012    URL: https://doi.org/10.2174/9781681085289117020012    Abstract:  2. R

创新点A: 动态图门控+自适应窗口，改动 MTGNN 优化分支。
创新点B: 趋势残差解耦+物理约束，改动 TimesNet 优化分支。
创新点C: 长窗特征+稳健树深调优，改动 XGBoost 优化分支。
评估指标: MAE/RMSE/R2 + 稳定性。