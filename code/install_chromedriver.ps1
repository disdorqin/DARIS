# PowerShell 脚本：自动安装 ChromeDriver
# 解决无法访问 Google 服务器的问题

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ChromeDriver 自动安装脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 获取 Chrome 版本
$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
if (Test-Path $chromePath) {
    $chromeVersion = (Get-Item $chromePath).VersionInfo.ProductVersion.Split('.')[0]
    Write-Host "检测到 Chrome 版本：$chromeVersion" -ForegroundColor Green
} else {
    $chromePath = "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    if (Test-Path $chromePath) {
        $chromeVersion = (Get-Item $chromePath).VersionInfo.ProductVersion.Split('.')[0]
        Write-Host "检测到 Chrome 版本：$chromeVersion" -ForegroundColor Green
    } else {
        Write-Host "未找到 Chrome 浏览器，请安装 Chrome" -ForegroundColor Red
        exit 1
    }
}

# 使用国内镜像下载
$mirrorUrl = "https://npmmirror.com/mirrors/chromedriver"
Write-Host "使用国内镜像：$mirrorUrl" -ForegroundColor Yellow

# 下载 ChromeDriver
$downloadUrl = "$mirrorUrl/${chromeVersion}.0.7390.122/chromedriver_win32.zip"
$downloadPath = "$env:TEMP\chromedriver.zip"
$installPath = "C:\chromedriver"

Write-Host "`n正在下载 ChromeDriver..." -ForegroundColor Yellow
try {
    Invoke-WebRequest -Uri $downloadUrl -OutFile $downloadPath
    Write-Host "下载完成" -ForegroundColor Green
} catch {
    Write-Host "下载失败，尝试其他版本..." -ForegroundColor Red
    
    # 尝试使用最新兼容版本
    $downloadUrl = "$mirrorUrl/LATEST_RELEASE/chromedriver_win32.zip"
    try {
        Invoke-WebRequest -Uri $downloadUrl -OutFile $downloadPath
        Write-Host "下载完成" -ForegroundColor Green
    } catch {
        Write-Host "无法下载，请手动安装" -ForegroundColor Red
        Write-Host "手动安装步骤:" -ForegroundColor Yellow
        Write-Host "1. 访问：https://npmmirror.com/mirrors/chromedriver" -ForegroundColor White
        Write-Host "2. 下载对应版本的 chromedriver_win32.zip" -ForegroundColor White
        Write-Host "3. 解压到 C:\chromedriver 或添加到 PATH" -ForegroundColor White
        exit 1
    }
}

# 解压
Write-Host "`n正在解压..." -ForegroundColor Yellow
if (!(Test-Path $installPath)) {
    New-Item -ItemType Directory -Path $installPath | Out-Null
}
Expand-Archive -Path $downloadPath -DestinationPath $installPath -Force

# 添加到 PATH
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($currentPath -notlike "*$installPath*") {
    [Environment]::SetEnvironmentVariable("Path", "$currentPath;$installPath", "User")
    Write-Host "已添加到 PATH" -ForegroundColor Green
}

# 清理
Remove-Item $downloadPath -Force

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "ChromeDriver 安装完成！" -ForegroundColor Green
Write-Host "安装路径：$installPath" -ForegroundColor Yellow
Write-Host "`n请重新运行爬取命令:" -ForegroundColor Cyan
Write-Host "python run_crawler.py --keywords `"尖峰预测`" --max-results 3" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan