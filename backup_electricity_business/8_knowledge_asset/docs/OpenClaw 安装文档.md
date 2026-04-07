# OpenClaw 安装文档

## 1. 安装目标
- 在本机提供 OpenClaw CLI 调度能力。
- 与 DARIS 的配置中心联动：1_config/base/openclaw_config.yaml。
- 仅使用环境变量读取密钥，不在文档中记录明文。

## 2. 推荐安装方式（Windows）
```powershell
npm.cmd config set registry https://registry.npmmirror.com
npm.cmd install -g openclaw --registry=https://registry.npmmirror.com
openclaw.cmd --version
```

## 3. 常见问题
### PowerShell 执行策略拦截 *.ps1
- 现象：npm/openclaw 命令报 Execution_Policies 错误。
- 处理：使用 npm.cmd 与 openclaw.cmd 调用。

### 网络受限
- 优先使用国内镜像源。
- 若镜像安装失败，保留配置框架，后续继续主流程。

## 4. 最小验证清单
- openclaw.cmd --version 可返回版本。
- 1_config/base/openclaw_config.yaml 存在且结构完整。
- report/stage2_openclaw_install.log 记录安装过程。

## 5. 安全约束
- 不在仓库写入 API_KEY 等敏感值。
- 仅允许使用 .env 中键名进行映射。
