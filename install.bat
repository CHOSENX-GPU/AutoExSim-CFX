@echo off
REM CFX自动化系统安装脚本 (Windows版)

echo === CFX自动化系统安装脚本 ===
echo.

REM 检查Python版本
echo 检查Python版本...
python --version 2>NUL
if errorlevel 1 (
    echo 错误: Python未安装或不在PATH中
    pause
    exit /b 1
)

REM 检查pip是否存在
pip --version 2>NUL
if errorlevel 1 (
    echo 错误: pip未安装，请先安装pip
    pause
    exit /b 1
)

echo.
echo 请选择安装类型:
echo 1) 生产环境 (最小依赖)
echo 2) 开发环境 (完整依赖)  
echo 3) 自定义安装
echo.
set /p choice=请输入选择 (1-3): 

if "%choice%"=="1" (
    echo 安装生产环境依赖...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 安装失败!
        pause
        exit /b 1
    )
    echo 生产环境安装完成!
) else if "%choice%"=="2" (
    echo 安装开发环境依赖...
    pip install -r requirements-dev.txt
    if errorlevel 1 (
        echo 安装失败!
        pause
        exit /b 1
    )
    echo 开发环境安装完成!
) else if "%choice%"=="3" (
    echo 自定义安装选项:
    echo a) 基础依赖 (PyYAML, Jinja2, paramiko)
    echo b) 基础依赖 + 命令行工具 (click, rich, tqdm)
    echo c) 基础依赖 + 测试工具 (pytest, coverage)
    echo d) 基础依赖 + 代码质量工具 (black, flake8, mypy)
    echo.
    set /p custom_choice=请输入选择 (a-d): 
    
    if "%custom_choice%"=="a" (
        pip install "PyYAML>=6.0" "Jinja2>=3.0.0" "paramiko>=3.0.0" "pywin32>=304"
    ) else if "%custom_choice%"=="b" (
        pip install "PyYAML>=6.0" "Jinja2>=3.0.0" "paramiko>=3.0.0" "pywin32>=304" "click>=8.0.0" "rich>=13.0.0" "tqdm>=4.65.0"
    ) else if "%custom_choice%"=="c" (
        pip install "PyYAML>=6.0" "Jinja2>=3.0.0" "paramiko>=3.0.0" "pywin32>=304" "pytest>=7.0.0" "pytest-cov>=4.0.0" "pytest-mock>=3.10.0"
    ) else if "%custom_choice%"=="d" (
        pip install "PyYAML>=6.0" "Jinja2>=3.0.0" "paramiko>=3.0.0" "pywin32>=304" "black>=23.0.0" "flake8>=6.0.0" "mypy>=1.0.0"
    ) else (
        echo 无效选择，退出安装
        pause
        exit /b 1
    )
    if errorlevel 1 (
        echo 安装失败!
        pause
        exit /b 1
    )
    echo 自定义安装完成!
) else (
    echo 无效选择，退出安装
    pause
    exit /b 1
)

echo.
echo === 安装完成 ===
echo.
echo 下一步:
echo 1. 复制配置文件: copy config\simple_config.yaml config\my_config.yaml
echo 2. 编辑配置文件: 根据您的环境修改配置参数
echo 3. 运行测试: python cfx_automation.py --config config\my_config.yaml run --steps init --dry-run
echo.
echo 更多信息请查看 README.md 文件
pause
