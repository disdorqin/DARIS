# 创新点技术路线拆解文档

**生成时间**: 2026-04-01  
**首选创新点**: 2.1 MTGNN+ 动态图学习  
**适配模型**: MTGNN

---

## 研究假说

**假说陈述**: 在 MTGNN 中引入动态图学习机制，使图结构能够随输入序列动态更新，可以显著提升时空序列预测的准确性，特别是在动态变化场景（如交通流量突变、电网负荷波动）中。

**可证伪性**: 若动态图学习后 val_MAE 未降低或降低<1%，则假说不成立。

---

## 原子技术模块拆解

### 模块 1：动态图学习层（DynamicGraphLayer）

**功能**: 根据输入序列动态生成图结构矩阵

**输入**:
- `x`: 输入张量 `[batch_size, seq_len, num_nodes, in_features]`
- `time_emb`: 时间编码 `[batch_size, seq_len, hidden_dim]`

**输出**:
- `adj_matrix`: 动态邻接矩阵 `[batch_size, seq_len, num_nodes, num_nodes]`

**核心逻辑**:
```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class DynamicGraphLayer(nn.Module):
    def __init__(self, num_nodes, hidden_dim, time_emb_dim):
        super().__init__()
        self.num_nodes = num_nodes
        # 节点嵌入
        self.node_emb = nn.Embedding(num_nodes, hidden_dim)
        # 时间投影
        self.time_proj = nn.Linear(time_emb_dim, hidden_dim)
        # 注意力权重
        self.attn_q = nn.Linear(hidden_dim, hidden_dim)
        self.attn_k = nn.Linear(hidden_dim, hidden_dim)
        
    def forward(self, x, time_emb):
        # 获取节点表示
        node_ids = torch.arange(self.num_nodes, device=x.device)
        node_repr = self.node_emb(node_ids)  # [num_nodes, hidden_dim]
        
        # 时间编码投影
        time_repr = self.time_proj(time_emb)  # [batch, seq_len, hidden_dim]
        
        # 计算注意力权重
        q = self.attn_q(node_repr)  # [num_nodes, hidden_dim]
        k = self.attn_k(time_repr.mean(dim=1))  # [batch, hidden_dim]
        
        # 动态图结构生成
        # 使用节点相似性计算邻接矩阵
        node_sim = torch.matmul(q, q.transpose(0, 1))  # [num_nodes, num_nodes]
        adj_matrix = F.relu(node_sim)  # 非负约束
        
        # 广播到 batch 和 seq_len
        adj_matrix = adj_matrix.unsqueeze(0).unsqueeze(0)
        adj_matrix = adj_matrix.expand(x.size(0), x.size(1), -1, -1)
        
        return adj_matrix
```

**数学公式**:
$$A_{t}^{(i,j)} = \text{ReLU}(q_i^T q_j + \phi(t))$$

其中 $q_i$ 是节点 i 的嵌入，$\phi(t)$ 是时间编码。

**对接方式**:
- 替换 MTGNN 原有的静态图学习层
- 输出传递给图卷积层

**单元测试规则**:
```python
def test_dynamic_graph_layer():
    layer = DynamicGraphLayer(num_nodes=207, hidden_dim=32, time_emb_dim=16)
    x = torch.randn(32, 12, 207, 1)
    time_emb = torch.randn(32, 12, 16)
    adj = layer(x, time_emb)
    
    # 检查输出形状
    assert adj.shape == (32, 12, 207, 207)
    # 检查非负性
    assert (adj >= 0).all()
    # 检查对称性（可选）
    assert torch.allclose(adj, adj.transpose(-1, -2), atol=1e-5)
```

---

### 模块 2：动态图卷积层（DynamicGraphConv）

**功能**: 在动态图结构上执行图卷积操作

**输入**:
- `x`: 输入特征 `[batch_size, seq_len, num_nodes, in_features]`
- `adj_matrix`: 动态邻接矩阵 `[batch_size, seq_len, num_nodes, num_nodes]`

**输出**:
- `out`: 图卷积输出 `[batch_size, seq_len, num_nodes, out_features]`

**核心逻辑**:
```python
class DynamicGraphConv(nn.Module):
    def __init__(self, in_features, out_features, bias=True):
        super().__init__()
        self.linear = nn.Linear(in_features, out_features, bias=bias)
        
    def forward(self, x, adj_matrix):
        # 图卷积：A * X * W
        # x: [batch, seq_len, num_nodes, in_features]
        # adj_matrix: [batch, seq_len, num_nodes, num_nodes]
        
        # 图消息传递
        graph_out = torch.matmul(adj_matrix, x)  # [batch, seq_len, num_nodes, in_features]
        
        # 线性变换
        out = self.linear(graph_out)
        
        return out
```

**数学公式**:
$$H^{(l+1)} = \sigma(\tilde{A}_t H^{(l)} W^{(l)})$$

其中 $\tilde{A}_t$ 是时间 t 的归一化邻接矩阵。

**对接方式**:
- 替换 MTGNN 中的 GraphConv 层
- 接收动态邻接矩阵作为额外输入

**单元测试规则**:
```python
def test_dynamic_graph_conv():
    conv = DynamicGraphConv(in_features=32, out_features=64)
    x = torch.randn(32, 12, 207, 32)
    adj = torch.rand(32, 12, 207, 207)
    out = conv(x, adj)
    
    assert out.shape == (32, 12, 207, 64)
```

---

### 模块 3：时间编码模块（TimeEncoding）

**功能**: 生成时间编码，捕捉时序位置信息

**输入**:
- `timestamps`: 时间戳 `[batch_size, seq_len]`

**输出**:
- `time_emb`: 时间编码 `[batch_size, seq_len, time_emb_dim]`

**核心逻辑**:
```python
class TimeEncoding(nn.Module):
    def __init__(self, time_emb_dim, max_period=10000):
        super().__init__()
        self.time_emb_dim = time_emb_dim
        self.max_period = max_period
        
    def forward(self, timestamps):
        # 位置编码风格的时间编码
        batch_size, seq_len = timestamps.shape
        
        # 生成周期项
        periods = torch.pow(
            self.max_period,
            torch.arange(0, self.time_emb_dim, 2).float() / self.time_emb_dim
        ).to(timestamps.device)
        
        # 计算编码
        time_emb = torch.zeros(batch_size, seq_len, self.time_emb_dim).to(timestamps.device)
        time_emb[:, :, 0::2] = torch.sin(timestamps.unsqueeze(-1) / periods)
        time_emb[:, :, 1::2] = torch.cos(timestamps.unsqueeze(-1) / periods)
        
        return time_emb
```

**数学公式**:
$$\text{TE}(t, 2i) = \sin\left(\frac{t}{10000^{2i/d}}\right)$$
$$\text{TE}(t, 2i+1) = \cos\left(\frac{t}{10000^{2i/d}}\right)$$

**对接方式**:
- 作为动态图学习层的辅助输入
- 可复用时序预测中的标准位置编码

**单元测试规则**:
```python
def test_time_encoding():
    encoding = TimeEncoding(time_emb_dim=16)
    timestamps = torch.arange(0, 12).unsqueeze(0).expand(32, -1)
    time_emb = encoding(timestamps)
    
    assert time_emb.shape == (32, 12, 16)
    # 检查周期性
    assert torch.allclose(time_emb[:, 0, :], time_emb[:, 12, :], atol=1e-5)
```

---

### 模块 4：动态 MTGNN 模型（DynamicMTGNN）

**功能**: 整合上述模块，形成完整的动态 MTGNN 模型

**输入**:
- `x`: 输入序列 `[batch_size, seq_len, num_nodes, in_features]`
- `timestamps`: 时间戳 `[batch_size, seq_len]`

**输出**:
- `prediction`: 预测结果 `[batch_size, pred_len, num_nodes, out_features]`

**核心逻辑**:
```python
class DynamicMTGNN(nn.Module):
    def __init__(self, num_nodes, in_features, hidden_dim, pred_len):
        super().__init__()
        self.num_nodes = num_nodes
        self.hidden_dim = hidden_dim
        self.pred_len = pred_len
        
        # 时间编码
        self.time_encoding = TimeEncoding(time_emb_dim=hidden_dim)
        
        # 动态图学习
        self.dynamic_graph = DynamicGraphLayer(num_nodes, hidden_dim, hidden_dim)
        
        # 图卷积堆叠
        self.graph_conv1 = DynamicGraphConv(in_features, hidden_dim)
        self.graph_conv2 = DynamicGraphConv(hidden_dim, hidden_dim)
        
        # 时间卷积
        self.temporal_conv = nn.Conv1d(hidden_dim, hidden_dim, kernel_size=3, padding=1)
        
        # 输出层
        self.output_layer = nn.Linear(hidden_dim, 1)
        
    def forward(self, x, timestamps):
        batch_size, seq_len, num_nodes, _ = x.shape
        
        # 时间编码
        time_emb = self.time_encoding(timestamps)
        
        # 动态图结构
        adj_matrix = self.dynamic_graph(x, time_emb)
        
        # 图卷积
        h = self.graph_conv1(x, adj_matrix)
        h = F.relu(h)
        h = self.graph_conv2(h, adj_matrix)
        h = F.relu(h)
        
        # 时间卷积
        h = h.permute(0, 2, 3, 1).reshape(batch_size * num_nodes, -1, seq_len)
        h = self.temporal_conv(h)
        h = h.reshape(batch_size, num_nodes, -1, seq_len).permute(0, 3, 1, 2)
        
        # 输出
        prediction = self.output_layer(h[:, -self.pred_len:, :, :])
        
        return prediction
```

**对接方式**:
- 继承自 MTGNN 官方代码结构
- 保持相同的数据接口

**单元测试规则**:
```python
def test_dynamic_mtg nn():
    model = DynamicMTGNN(num_nodes=207, in_features=1, hidden_dim=32, pred_len=7)
    x = torch.randn(32, 12, 207, 1)
    timestamps = torch.arange(0, 12).unsqueeze(0).expand(32, -1)
    pred = model(x, timestamps)
    
    assert pred.shape == (32, 7, 207, 1)
```

---

## 整合与测试计划

### 第 1 周：基础模块实现
- [ ] 实现 DynamicGraphLayer
- [ ] 实现 DynamicGraphConv
- [ ] 实现 TimeEncoding
- [ ] 完成单元测试

### 第 2 周：模型整合
- [ ] 实现 DynamicMTGNN
- [ ] 整合到 MTGNN 训练流程
- [ ] 完成集成测试

### 第 3 周：实验验证
- [ ] 在 METR-LA 数据集上训练
- [ ] 对比 MTGNN 基线
- [ ] 消融实验验证各模块贡献

### 第 4 周：论文撰写
- [ ] 整理实验结果
- [ ] 撰写论文初稿
- [ ] 准备投稿

---

## Obsidian 双向链接
- [[DARIS 工作流]]
- [[分级创新点清单]]
- [[MTGNN 基线代码]]
- [[实验设计与结果]]