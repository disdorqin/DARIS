# Iteration-3 计划（回退后新一轮）

## 锚点阶段
文献深度挖掘与创新点生成（阶段1）

## 新候选创新点（按优先级）
1. 多尺度分解增强 + MTGNN 图学习耦合
- 理由：前两轮仅改图融合策略，时序分解能力仍不足。
- 改动方向：在输入端增加可学习多尺度分解分支（短期/中期/长期），再送入图卷积。

2. 稀疏子图自适应阈值（动态 k）
- 理由：固定 subgraph_size 可能限制图结构表达。
- 改动方向：让阈值随批次统计量变化（波动大时放宽连接，平稳时收紧）。

3. 稳健损失函数（Huber）替代 L1
- 理由：电力数据含异常尖峰，纯 L1 对极值梯度行为不稳定。
- 改动方向：在训练脚本新增损失选项并进行对照。

## 阶段2执行入口（下一步直接做）
- 目标模型文件：MTGNN/layer.py, MTGNN/net.py, MTGNN/train_single_step.py
- 对照标准：Baseline vs 新创新组（同数据、同 epoch、同 batch）
- 核心指标：test_rse, test_rae, test_corr（后续扩展 MAE/RMSE/R2）

## 一键复跑命令（当前环境）
- python: C:/ProgramData/anaconda3/envs/daris-research/python.exe
- 数据准备: code/prepare_mtg_data.py
- 快速实验日志目录: experiment/
