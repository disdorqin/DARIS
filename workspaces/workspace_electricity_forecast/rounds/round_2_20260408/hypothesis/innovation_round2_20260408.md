# 多源异构数据融合 + 多特征工程优化策略

## 研究目标
充分利用多源异构数据中的多个特征，通过新增和优化特征工程、多源数据融合策略，提升电力预测精度与稳定性。

## 策略主线
1. 先做特征清洗与对齐，统一时间粒度与缺失补全。
2. 再做时间、天气、历史负荷、外部事件四类特征扩展。
3. 最后用注意力、门控或图结构把不同来源的特征融合为统一输入。

## 新增 / 优化特征清单
### 时间特征扩展
- 描述: 日/周/月周期的 sin-cos 编码、归一化时间索引、节假日/工作日标记。
- 文献依据主题: feature engineering, attention, multivariate time series forecasting
### 天气特征融合
- 描述: 温度、湿度、风速、降水、气压、体感温度等外部天气源按时间对齐后拼接。
- 文献依据主题: multimodal, fusion, heterogeneous
### 历史负荷特征交叉
- 描述: 目标负荷与滞后项、滑动均值、滑动标准差、差分项及相互乘积。
- 文献依据主题: feature interaction, selection, forecast
### 多尺度特征提取
- 描述: 6/24/168 小时多尺度滚动窗口、趋势-残差分解、短中长周期汇聚。
- 文献依据主题: decomposition, multiscale, transformer
### 多源融合门控
- 描述: 对负荷、天气、节假日、价格、事件等通道使用注意力/门控权重自动加权。
- 文献依据主题: attention, fusion, graph

## 文献依据摘记
- TIC-FusionNet: A multimodal deep learning framework with temporal decomposition and attention-based fusion for time series forecasting (2025) — https://doi.org/10.1371/journal.pone.0333379
- Spatial‐Temporal Feature Fusion Network for Short‐Term Photovoltaic Forecasting Utilising Multi‐Source Heterogeneous Data (2026) — https://doi.org/10.1049/rpg2.70209
- Exploring Causality in Feature Selection for Multivariate Time Series Forecasting (2024) — https://doi.org/10.2139/ssrn.4736990
- LAD-Net:Cross-channel linear attention with deep feature decomposition network for multivariate time series forecasting (2025) — https://doi.org/10.2139/ssrn.5451107
- Multi-source Data Fusion-based Grid-level Load Forecasting (2024) — https://doi.org/10.21203/rs.3.rs-5399298/v1
- Vttnet: Multi-Component Decomposition and Feature Fusion Network for Enhanced Short-Term Electricity Load Forecasting (2025) — https://doi.org/10.2139/ssrn.5189248
- Deep Learning Fusion Model Based Electricity Load Forecasting for Extreme Weather (2025) — https://doi.org/10.54097/njhzax84
- Feature Engineering in Time Series Forecasting (2025) — https://doi.org/10.14293/pr2199.002316.v1
- Statistical Forecasting of Short-term Electricity Load Using a Meteorological Feature-driven Deep Learning Fusion Framework (2025) — https://doi.org/10.1109/ceepe64987.2025.11034044
- Statistically Validated Multi-Horizon Electricity Load Forecasting with Weather-Augmented Machine Learning under Walk-Forward Evaluation (2026) — https://doi.org/10.21203/rs.3.rs-9285801/v1
- VTTnet: Multi-component decomposition and feature fusion network for enhanced short-term electricity load forecasting (2025) — https://doi.org/10.1016/j.epsr.2025.111876
- Empirical analysis of time series using feature selection algorithms (2021) — https://doi.org/10.5194/egusphere-egu21-6697

## 预期收益
- 缩短对单一原始特征的依赖。
- 通过多尺度与交叉特征补足短期波动和长期趋势。
- 通过外部多源数据增强极端峰值和异常时段的可预测性。

## 落地建议
- XGBoost 侧重显式特征工程和交叉项。
- TimesNet 侧重时序分解、周期特征和天气融合。
- MTGNN 侧重图相关辅助特征和多变量依赖。
- PatchTST 侧重多尺度 patch 编码与时序上下文特征。