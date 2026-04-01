"""
Dynamic MTGNN - 动态图学习增强的 MTGNN 模型
创新点 2.1: MTGNN+ 动态图学习

作者：DARIS 团队
日期：2026-04-01
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np


class TimeEncoding(nn.Module):
    """时间编码模块 - 生成时间编码，捕捉时序位置信息"""
    
    def __init__(self, time_emb_dim, max_period=10000):
        super().__init__()
        self.time_emb_dim = time_emb_dim
        self.max_period = max_period
        
    def forward(self, timestamps):
        """
        生成时间编码
        
        Args:
            timestamps: 时间戳 [batch_size, seq_len]
            
        Returns:
            time_emb: 时间编码 [batch_size, seq_len, time_emb_dim]
        """
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


class DynamicGraphLayer(nn.Module):
    """动态图学习层 - 根据输入序列动态生成图结构矩阵"""
    
    def __init__(self, num_nodes, hidden_dim, time_emb_dim):
        super().__init__()
        self.num_nodes = num_nodes
        self.hidden_dim = hidden_dim
        
        # 节点嵌入
        self.node_emb = nn.Embedding(num_nodes, hidden_dim)
        
        # 时间投影
        self.time_proj = nn.Linear(time_emb_dim, hidden_dim)
        
        # 注意力权重
        self.attn_q = nn.Linear(hidden_dim, hidden_dim)
        self.attn_k = nn.Linear(hidden_dim, hidden_dim)
        
        # 图稀疏化参数
        self.sparse_threshold = 0.1
        
    def forward(self, x, time_emb):
        """
        生成动态图结构
        
        Args:
            x: 输入张量 [batch_size, seq_len, num_nodes, in_features]
            time_emb: 时间编码 [batch_size, seq_len, hidden_dim]
            
        Returns:
            adj_matrix: 动态邻接矩阵 [batch_size, seq_len, num_nodes, num_nodes]
        """
        batch_size, seq_len = x.shape[:2]
        device = x.device
        
        # 获取节点表示
        node_ids = torch.arange(self.num_nodes, device=device)
        node_repr = self.node_emb(node_ids)  # [num_nodes, hidden_dim]
        
        # 时间编码投影
        time_repr = self.time_proj(time_emb)  # [batch, seq_len, hidden_dim]
        time_repr_mean = time_repr.mean(dim=1)  # [batch, hidden_dim]
        
        # 计算节点间注意力权重
        q = self.attn_q(node_repr)  # [num_nodes, hidden_dim]
        
        # 对每个 batch 样本计算动态图
        adj_matrices = []
        for b in range(batch_size):
            k = self.attn_k(time_repr_mean[b])  # [hidden_dim]
            
            # 计算节点相似性矩阵
            node_sim = torch.matmul(q, q.transpose(0, 1))  # [num_nodes, num_nodes]
            
            # 加入时间因子
            time_factor = torch.sigmoid(k).unsqueeze(0) * torch.sigmoid(k).unsqueeze(1)
            adj_matrix = F.relu(node_sim) * time_factor
            
            # 稀疏化：保留前 k 个连接
            threshold = torch.quantile(adj_matrix, 1 - self.sparse_threshold)
            adj_matrix = torch.where(adj_matrix > threshold, adj_matrix, torch.zeros_like(adj_matrix))
            
            adj_matrices.append(adj_matrix)
        
        # 堆叠为 [batch_size, num_nodes, num_nodes]
        adj_matrix = torch.stack(adj_matrices, dim=0)  # [batch_size, num_nodes, num_nodes]
        
        # 广播到 seq_len
        adj_matrix = adj_matrix.unsqueeze(1).expand(-1, seq_len, -1, -1)
        
        return adj_matrix


class DynamicGraphConv(nn.Module):
    """动态图卷积层 - 在动态图结构上执行图卷积操作"""
    
    def __init__(self, in_features, out_features, bias=True):
        super().__init__()
        self.linear = nn.Linear(in_features, out_features, bias=bias)
        
    def forward(self, x, adj_matrix):
        """
        动态图卷积
        
        Args:
            x: 输入特征 [batch_size, seq_len, num_nodes, in_features]
            adj_matrix: 动态邻接矩阵 [batch_size, seq_len, num_nodes, num_nodes]
            
        Returns:
            out: 图卷积输出 [batch_size, seq_len, num_nodes, out_features]
        """
        # 图消息传递：A * X
        graph_out = torch.matmul(adj_matrix, x)  # [batch, seq_len, num_nodes, in_features]
        
        # 线性变换
        out = self.linear(graph_out)
        
        return out


class MTGNNBlock(nn.Module):
    """MTGNN 基础模块 - 图卷积 + 时间卷积"""
    
    def __init__(self, hidden_dim, num_nodes, dropout=0.3):
        super().__init__()
        self.num_nodes = num_nodes
        self.hidden_dim = hidden_dim
        
        # 动态图学习
        self.dynamic_graph = DynamicGraphLayer(num_nodes, hidden_dim, hidden_dim)
        
        # 图卷积
        self.graph_conv1 = DynamicGraphConv(hidden_dim, hidden_dim)
        self.graph_conv2 = DynamicGraphConv(hidden_dim, hidden_dim)
        
        # 时间卷积
        self.temporal_conv = nn.Conv2d(hidden_dim, hidden_dim, kernel_size=(1, 3), padding=(0, 1))
        
        # 归一化
        self.norm1 = nn.LayerNorm(hidden_dim)
        self.norm2 = nn.LayerNorm(hidden_dim)
        
        # Dropout
        self.dropout = nn.Dropout(dropout)
        
    def forward(self, x, time_emb):
        """
        MTGNN 块前向传播
        
        Args:
            x: 输入 [batch_size, seq_len, num_nodes, hidden_dim]
            time_emb: 时间编码 [batch_size, seq_len, hidden_dim]
            
        Returns:
            out: 输出 [batch_size, seq_len, num_nodes, hidden_dim]
        """
        # 动态图结构
        adj_matrix = self.dynamic_graph(x, time_emb)
        
        # 图卷积 + 残差
        h = self.graph_conv1(x, adj_matrix)
        h = F.relu(h)
        h = self.dropout(h)
        h = self.graph_conv2(h, adj_matrix)
        h = h + x  # 残差连接
        h = self.norm1(h)
        
        # 时间卷积
        h = h.permute(0, 3, 1, 2)  # [batch, hidden, seq_len, num_nodes]
        h = self.temporal_conv(h)
        h = h.permute(0, 2, 3, 1)  # [batch, seq_len, num_nodes, hidden]
        h = F.relu(h)
        
        # 残差 + 归一化
        h = h + x[:, :h.size(1), :, :]
        h = self.norm2(h)
        
        return h


class DynamicMTGNN(nn.Module):
    """Dynamic MTGNN - 动态图学习增强的 MTGNN 模型"""
    
    def __init__(
        self,
        num_nodes,
        in_features=1,
        hidden_dim=32,
        num_blocks=4,
        pred_len=7,
        dropout=0.3
    ):
        super().__init__()
        self.num_nodes = num_nodes
        self.hidden_dim = hidden_dim
        self.pred_len = pred_len
        
        # 输入嵌入
        self.input_embedding = nn.Linear(in_features, hidden_dim)
        
        # 时间编码
        self.time_encoding = TimeEncoding(time_emb_dim=hidden_dim)
        
        # MTGNN 块堆叠
        self.blocks = nn.ModuleList([
            MTGNNBlock(hidden_dim, num_nodes, dropout)
            for _ in range(num_blocks)
        ])
        
        # 输出层
        self.output_layer = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 1)
        )
        
    def forward(self, x, timestamps=None):
        """
        Dynamic MTGNN 前向传播
        
        Args:
            x: 输入序列 [batch_size, seq_len, num_nodes, in_features]
            timestamps: 时间戳 [batch_size, seq_len], 可选
            
        Returns:
            prediction: 预测结果 [batch_size, pred_len, num_nodes, 1]
        """
        batch_size, seq_len = x.shape[:2]
        device = x.device
        
        # 输入嵌入
        h = self.input_embedding(x)  # [batch, seq_len, num_nodes, hidden]
        
        # 时间编码
        if timestamps is None:
            timestamps = torch.arange(seq_len).unsqueeze(0).expand(batch_size, -1).float().to(device)
        time_emb = self.time_encoding(timestamps)
        
        # 通过 MTGNN 块
        for block in self.blocks:
            h = block(h, time_emb)
        
        # 输出层（使用最后几个时间步预测未来）
        h_last = h[:, -self.pred_len:, :, :]  # [batch, pred_len, num_nodes, hidden]
        prediction = self.output_layer(h_last)  # [batch, pred_len, num_nodes, 1]
        
        return prediction


def test_dynamic_mtg nn():
    """测试 Dynamic MTGNN 模型"""
    print("测试 Dynamic MTGNN 模型...")
    
    # 创建模型
    model = DynamicMTGNN(
        num_nodes=207,
        in_features=1,
        hidden_dim=32,
        num_blocks=2,
        pred_len=7,
        dropout=0.3
    )
    
    # 创建测试输入
    batch_size = 4
    seq_len = 12
    x = torch.randn(batch_size, seq_len, 207, 1)
    timestamps = torch.arange(seq_len).unsqueeze(0).expand(batch_size, -1).float()
    
    # 前向传播
    model.eval()
    with torch.no_grad():
        pred = model(x, timestamps)
    
    # 验证输出形状
    assert pred.shape == (batch_size, 7, 207, 1), f"期望形状 {(batch_size, 7, 207, 1)}, 得到 {pred.shape}"
    
    print(f"✓ 测试通过！输入形状：{x.shape}, 输出形状：{pred.shape}")
    print(f"✓ 模型参数量：{sum(p.numel() for p in model.parameters()):,}")
    
    return model


if __name__ == '__main__':
    test_dynamic_mtg nn()