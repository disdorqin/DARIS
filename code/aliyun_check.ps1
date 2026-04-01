# PowerShell 脚本：检查阿里云服务器环境并同步代码
# 环节 5：阿里云服务器自动化调优

$serverIp = "47.100.98.160"
$serverUser = "root"
$serverPort = "22"
$serverWorkDir = "/home/root/DARIS/"
$projectRoot = "d:\computer learning\science_workflow"

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "DARIS 环节 5：阿里云服务器自动化调优" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

# 提示输入密码
$securePassword = Read-Host "请输入服务器密码" -AsSecureString
$credential = New-Object System.Management.Automation.PSCredential($serverUser, $securePassword)

Write-Host "`n[1/4] 检查服务器环境..." -ForegroundColor Yellow

# SSH 检查命令
$sshCheckCommand = @"
echo "=== Python 版本 ==="
python3 --version

echo "=== Pip 版本 ==="
pip3 --version

echo "=== PyTorch 检查 ==="
python3 -c "import torch; print(f'PyTorch: {torch.__version__}')" 2>&1 || echo "PyTorch 未安装"

echo "=== GPU 检查 ==="
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo "No GPU found"

echo "=== 磁盘空间 ==="
df -h $serverWorkDir
"@

Write-Host "请手动执行以下命令（使用 Xshell/PuTTY 或 WSL）：`n" -ForegroundColor Yellow
Write-Host "ssh $serverUser@$serverIp -p $serverPort" -ForegroundColor White
Write-Host "密码：(已填写)" -ForegroundColor White
Write-Host "`n然后执行：`n$sshCheckCommand" -ForegroundColor White

Write-Host "`n`n[2/4] 同步代码到服务器..." -ForegroundColor Yellow

# SCP 同步命令
$syncCommands = @(
    "scp -P $serverPort -r '$projectRoot\code' $serverUser@$serverIp`:$serverWorkDir",
    "scp -P $serverPort -r '$projectRoot\config' $serverUser@$serverIp`:$serverWorkDir",
    "scp -P $serverPort -r '$projectRoot\data' $serverUser@$serverIp`:$serverWorkDir"
)

Write-Host "`n同步命令（在 PowerShell 或 CMD 中执行）：`n" -ForegroundColor Yellow
foreach ($cmd in $syncCommands) {
    Write-Host "  $cmd" -ForegroundColor White
}

Write-Host "`n或使用 rsync（推荐）：`n" -ForegroundColor Yellow
Write-Host "  rsync -avz -e 'ssh -p $serverPort' '$projectRoot/' $serverUser@$serverIp`:$serverWorkDir" -ForegroundColor White

Write-Host "`n`n[3/4] 安装服务器依赖..." -ForegroundColor Yellow

$installCommand = @"
ssh $serverUser@$serverIp -p $serverPort << 'EOF'
cd $serverWorkDir
pip3 install torch numpy pandas matplotlib scikit-learn
python3 -c "import torch; import numpy; import pandas; print('依赖安装成功')"
EOF
"@

Write-Host "`n执行命令：`n$installCommand" -ForegroundColor Yellow

Write-Host "`n`n[4/4] 运行模型测试..." -ForegroundColor Yellow

$trainCommand = @"
ssh $serverUser@$serverIp -p $serverPort << 'EOF'
cd $serverWorkDir
python3 code/test_model.py
EOF
"@

Write-Host "`n执行命令：`n$trainCommand" -ForegroundColor Yellow

Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host "说明：" -ForegroundColor Cyan
Write-Host "1. 推荐使用 Xshell、PuTTY 或 Windows Terminal 连接服务器" -ForegroundColor Cyan
Write-Host "2. 复制上述命令逐行执行" -ForegroundColor Cyan
Write-Host "3. 服务器密码：已在上方输入" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan