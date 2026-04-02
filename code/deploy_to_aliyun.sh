#!/bin/bash
# DARIS 项目阿里云服务器部署脚本
# 使用方法：
# 1. 先 SSH 登录服务器：ssh root@47.100.98.160
# 2. 在服务器上执行此脚本

echo "========================================"
echo "DARIS 项目部署脚本"
echo "========================================"

# 设置工作目录
WORK_DIR="/home/root/DARIS"
mkdir -p $WORK_DIR
cd $WORK_DIR
echo "工作目录：$WORK_DIR"

# 检查 Python 环境
echo ""
echo "=== 检查 Python 环境 ==="
python3 --version
if [ $? -ne 0 ]; then
    echo "错误：未找到 Python3，请先安装"
    exit 1
fi

# 安装依赖
echo ""
echo "=== 安装 Python 依赖 ==="
pip3 install torch numpy pandas matplotlib scikit-learn

# 验证安装
echo ""
echo "=== 验证依赖安装 ==="
python3 -c "import torch; import numpy; import pandas; print('PyTorch 版本:', torch.__version__); print('依赖安装成功！')"

# 创建测试脚本
echo ""
echo "=== 创建测试脚本 ==="
cat > test_dynamic_mtg nn.py << 'PYTHON_EOF'
"""
Dynamic MTGNN 模型测试脚本
"""
import torch
import torch.nn as nn
import torch.nn.functional as F

class TimeEncoding(nn.Module):
    def __init__(self, time_emb_dim, max_period=10000):
        super().__init__()
        self.time_emb_dim = time_emb_dim
        self.max_period = max_period
        
    def forward(self, timestamps):
        batch_size, seq_len = timestamps.shape
        periods = torch.pow(
            self.max_period,
            torch.arange(0, self.time_emb_dim, 2).float() / self.time_emb_dim
        ).to(timestamps.device)
        time_emb = torch.zeros(batch_size, seq_len, self.time_emb_dim).to(timestamps.device)
        time_emb[:, :, 0::2] = torch.sin(timestamps.unsqueeze(-1) / periods)
        time_emb[:, :, 1::2] = torch.cos(timestamps.unsqueeze(-1) / periods)
        return time_emb

class DynamicGraphLayer(nn.Module):
    def __init__(self, num_nodes, hidden_dim, time_emb_dim):
        super().__init__()
        self.num_nodes = num_nodes
        self.hidden_dim = hidden_dim
        self.node_emb = nn.Embedding(num_nodes, hidden_dim)
        self.time_proj = nn.Linear(time_emb_dim, hidden_dim)
        self.attn_q = nn.Linear(hidden_dim, hidden_dim)
        self.attn_k = nn.Linear(hidden_dim, hidden_dim)
        self.sparse_threshold = 0.1
        
    def forward(self, x, time_emb):
        batch_size, seq_len = x.shape[:2]
        device = x.device
        node_ids = torch.arange(self.num_nodes, device=device)
        node_repr = self.node_emb(node_ids)
        time_repr = self.time_proj(time_emb)
        time_repr_mean = time_repr.mean(dim=1)
        q = self.attn_q(node_repr)
        adj_matrices = []
        for b in range(batch_size):
            k = self.attn_k(time_repr_mean[b])
            node_sim = torch.matmul(q, q.transpose(0, 1))
            time_factor = torch.sigmoid(k).mean()
            adj_matrix = F.relu(node_sim) * time_factor
            threshold = torch.quantile(adj_matrix, 1 - self.sparse_threshold)
            adj_matrix = torch.where(adj_matrix > threshold, adj_matrix, torch.zeros_like(adj_matrix))
            adj_matrices.append(adj_matrix)
        adj_matrix = torch.stack(adj_matrices, dim=0).unsqueeze(1).expand(-1, seq_len, -1, -1)
        return adj_matrix

class DynamicMTGNN(nn.Module):
    def __init__(self, num_nodes, in_features=1, hidden_dim=32, num_blocks=2, pred_len=7, dropout=0.3):
        super().__init__()
        self.num_nodes = num_nodes
        self.hidden_dim = hidden_dim
        self.pred_len = pred_len
        self.input_embedding = nn.Linear(in_features, hidden_dim)
        self.time_encoding = TimeEncoding(time_emb_dim=hidden_dim)
        self.blocks = nn.ModuleList([
            nn.ModuleList([
                DynamicGraphLayer(num_nodes, hidden_dim, hidden_dim),
                nn.Linear(hidden_dim, hidden_dim),
                nn.Linear(hidden_dim, hidden_dim)
            ])
            for _ in range(num_blocks)
        ])
        self.output_layer = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 1)
        )
        
    def forward(self, x, timestamps=None):
        batch_size, seq_len, num_nodes, _ = x.shape
        device = x.device
        h = self.input_embedding(x)
        if timestamps is None:
            timestamps = torch.arange(seq_len).unsqueeze(0).expand(batch_size, -1).float().to(device)
        time_emb = self.time_encoding(timestamps)
        for block in self.blocks:
            adj_matrix = block[0](h, time_emb)
            h = block[1](h)
            h = F.relu(h)
            h = block[2](h)
            h = F.relu(h)
        h_last = h[:, -self.pred_len:, :, :]
        prediction = self.output_layer(h_last)
        return prediction

if __name__ == "__main__":
    print("Dynamic MTGNN 模型测试...")
    model = DynamicMTGNN(num_nodes=10, in_features=1, hidden_dim=16, num_blocks=2, pred_len=7)
    x = torch.randn(2, 12, 10, 1)
    timestamps = torch.arange(12).unsqueeze(0).expand(2, -1).float()
    model.eval()
    with torch.no_grad():
        pred = model(x, timestamps)
    print(f"输入形状：{x.shape}")
    print(f"输出形状：{pred.shape}")
    print(f"模型参数量：{sum(p.numel() for p in model.parameters()):,}")
    print("测试成功！")
PYTHON_EOF

# 运行测试
echo ""
echo "=== 运行模型测试 ==="
python3 test_dynamic_mtg nn.py

echo ""
echo "========================================"
echo "部署完成！"
echo "========================================"
echo "工作目录：$WORK_DIR"
echo "测试文件：$WORK_DIR/test_dynamic_mtg nn.py"