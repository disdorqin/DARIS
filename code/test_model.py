"""
Dynamic MTGNN 模型测试脚本
使用 importlib 导入带空格文件名的模块
"""

import torch
import sys
import importlib.util
from pathlib import Path

# 获取当前目录
current_dir = Path(__file__).parent

# 使用 importlib 导入带空格的模块
module_path = current_dir / "dynamic_mtg nn_model.py"
spec = importlib.util.spec_from_file_location("dynamic_mtg nn_model", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# 获取 DynamicMTGNN 类
DynamicMTGNN = module.DynamicMTGNN

def test_model():
    """测试 Dynamic MTGNN 模型"""
    print("测试 Dynamic MTGNN 模型...")
    
    # 创建模型（使用较小的参数以便快速测试）
    model = DynamicMTGNN(
        num_nodes=10,
        in_features=1,
        hidden_dim=16,
        num_blocks=2,
        pred_len=7,
        dropout=0.3
    )
    
    # 创建测试输入
    batch_size = 2
    seq_len = 12
    x = torch.randn(batch_size, seq_len, 10, 1)
    timestamps = torch.arange(seq_len).unsqueeze(0).expand(batch_size, -1).float()
    
    # 前向传播
    model.eval()
    with torch.no_grad():
        pred = model(x, timestamps)
    
    # 验证输出形状
    expected_shape = (batch_size, 7, 10, 1)
    assert pred.shape == expected_shape, f"期望形状 {expected_shape}, 得到 {pred.shape}"
    
    print("[OK] 测试通过！")
    print(f"  输入形状：{x.shape}")
    print(f"  输出形状：{pred.shape}")
    print(f"  模型参数量：{sum(p.numel() for p in model.parameters()):,}")
    
    return True

if __name__ == '__main__':
    test_model()