#!/bin/bash
# CFX自动化系统安装脚本

echo "=== CFX自动化系统安装脚本 ==="
echo ""

# 检查Python版本
echo "检查Python版本..."
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "Python版本: $python_version"

# 检查pip是否存在
if ! command -v pip &> /dev/null; then
    echo "错误: pip未安装，请先安装pip"
    exit 1
fi

# 询问是否创建虚拟环境
echo ""
echo "是否创建虚拟环境?"
echo "1) 是 (推荐)"
echo "2) 否"
echo ""
read -p "请输入选择 (1-2): " venv_choice

if [ "$venv_choice" = "1" ]; then
    echo "创建虚拟环境..."
    
    # 创建虚拟环境
    python -m venv cfx-env
    
    # 激活虚拟环境
    source cfx-env/bin/activate
    
    echo "虚拟环境创建并激活成功!"
    echo "注意: 每次使用前需要激活虚拟环境: source cfx-env/bin/activate"
    echo ""
fi

# 询问安装类型
echo ""
echo "请选择安装类型:"
echo "1) 生产环境 (最小依赖)"
echo "2) 开发环境 (完整依赖)"
echo "3) 自定义安装"
echo ""
read -p "请输入选择 (1-3): " choice

case $choice in
    1)
        echo "安装生产环境依赖..."
        pip install -r requirements.txt
        echo "生产环境安装完成!"
        ;;
    2)
        echo "安装开发环境依赖..."
        pip install -r requirements-dev.txt
        echo "开发环境安装完成!"
        ;;
    3)
        echo "自定义安装选项:"
        echo "a) 基础依赖 (PyYAML, Jinja2, paramiko)"
        echo "b) 基础依赖 + 命令行工具 (click, rich, tqdm)"
        echo "c) 基础依赖 + 测试工具 (pytest, coverage)"
        echo "d) 基础依赖 + 代码质量工具 (black, flake8, mypy)"
        echo ""
        read -p "请输入选择 (a-d): " custom_choice
        
        case $custom_choice in
            a)
                pip install PyYAML>=6.0 Jinja2>=3.0.0 paramiko>=3.0.0
                if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
                    pip install pywin32>=304
                fi
                ;;
            b)
                pip install PyYAML>=6.0 Jinja2>=3.0.0 paramiko>=3.0.0 click>=8.0.0 rich>=13.0.0 tqdm>=4.65.0
                if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
                    pip install pywin32>=304
                fi
                ;;
            c)
                pip install PyYAML>=6.0 Jinja2>=3.0.0 paramiko>=3.0.0 pytest>=7.0.0 pytest-cov>=4.0.0 pytest-mock>=3.10.0
                if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
                    pip install pywin32>=304
                fi
                ;;
            d)
                pip install PyYAML>=6.0 Jinja2>=3.0.0 paramiko>=3.0.0 black>=23.0.0 flake8>=6.0.0 mypy>=1.0.0
                if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
                    pip install pywin32>=304
                fi
                ;;
            *)
                echo "无效选择，退出安装"
                exit 1
                ;;
        esac
        echo "自定义安装完成!"
        ;;
    *)
        echo "无效选择，退出安装"
        exit 1
        ;;
esac

echo ""
echo "=== 安装完成 ==="
echo ""

# 显示虚拟环境使用说明
if [ "$venv_choice" = "1" ]; then
    echo "虚拟环境使用说明:"
    echo "- 激活虚拟环境: source cfx-env/bin/activate"
    echo "- 退出虚拟环境: deactivate"
    echo ""
fi

echo "下一步:"
echo "1. 复制配置文件: cp config/simple_config.yaml config/my_config.yaml"
echo "2. 编辑配置文件: 根据您的环境修改配置参数"
echo "3. 运行测试: python cfx_automation.py --config config/my_config.yaml run --steps init --dry-run"
echo ""
echo "更多信息请查看 README.md 文件"
