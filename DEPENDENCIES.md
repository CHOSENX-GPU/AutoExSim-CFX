# CFX自动化系统依赖说明

## 依赖包分类

### 核心依赖 (必需)
这些是系统运行所必需的包：

1. **PyYAML>=6.0**
   - 用途: 解析和生成YAML配置文件
   - 重要性: 核心配置管理

2. **Jinja2>=3.0.0**
   - 用途: 模板引擎，生成SLURM脚本和CFX Session文件
   - 重要性: 核心功能

3. **paramiko>=3.0.0**
   - 用途: SSH连接和SFTP文件传输
   - 重要性: 服务器通信

4. **pywin32>=304 (仅Windows)**
   - 用途: Windows注册表访问，自动检测CFX安装路径
   - 重要性: CFX路径自动检测

### 标准库依赖
这些是Python标准库的一部分，无需额外安装：

- `os` - 操作系统接口
- `sys` - 系统相关参数和函数
- `logging` - 日志记录
- `pathlib` - 面向对象的路径操作
- `subprocess` - 子进程管理
- `argparse` - 命令行参数解析
- `dataclasses` - 数据类
- `datetime` - 日期和时间处理
- `typing` - 类型提示
- `stat` - 文件状态
- `shutil` - 高级文件操作
- `platform` - 平台识别
- `winreg` - Windows注册表 (仅Windows)

### 可选依赖
这些包可以提供额外功能，但不是必需的：

#### 用户界面增强
- `click>=8.0.0` - 更好的命令行界面
- `rich>=13.0.0` - 彩色终端输出
- `tqdm>=4.65.0` - 进度条显示

#### 开发工具
- `pytest>=7.0.0` - 单元测试框架
- `pytest-cov>=4.0.0` - 测试覆盖率
- `pytest-mock>=3.10.0` - 模拟测试
- `black>=23.0.0` - 代码格式化
- `flake8>=6.0.0` - 代码检查
- `mypy>=1.0.0` - 类型检查

#### 数据分析
- `pandas>=2.0.0` - 数据分析
- `numpy>=1.24.0` - 数值计算
- `matplotlib>=3.7.0` - 数据可视化
- `seaborn>=0.12.0` - 统计数据可视化

#### 高级功能
- `watchdog>=3.0.0` - 文件系统监控
- `schedule>=1.2.0` - 任务调度
- `APScheduler>=3.10.0` - 高级任务调度
- `requests>=2.28.0` - HTTP请求
- `SQLAlchemy>=2.0.0` - 数据库ORM
- `psutil>=5.9.0` - 系统监控
- `fabric>=3.0.0` - 远程服务器管理
- `scp>=0.14.0` - SCP文件传输
- `pydantic>=2.0.0` - 数据验证

## 安装方式

### 最小安装 (推荐用户)
```bash
pip install -r requirements.txt
```

### 开发环境安装
```bash
pip install -r requirements-dev.txt
```

### 自定义安装
```bash
# 只安装核心依赖
pip install PyYAML>=6.0 Jinja2>=3.0.0 paramiko>=3.0.0

# Windows用户还需要
pip install pywin32>=304

# 添加命令行工具
pip install click>=8.0.0 rich>=13.0.0 tqdm>=4.65.0
```

### 使用安装脚本
```bash
# Linux/Mac
./install.sh

# Windows
install.bat
```

## 依赖检查

运行以下命令检查依赖是否正确安装：

```bash
python -c "import yaml, jinja2, paramiko; print('核心依赖检查通过')"
```

Windows用户还需要检查：
```bash
python -c "import win32api; print('Windows依赖检查通过')"
```

## 故障排除

### 常见安装问题

1. **paramiko安装失败**
   - 确保安装了C编译器 (Windows: Visual Studio Build Tools)
   - 或使用预编译版本: `pip install paramiko --only-binary=all`

2. **pywin32安装失败**
   - 确保使用管理员权限运行
   - 安装后运行: `python Scripts/pywin32_postinstall.py -install`

3. **依赖冲突**
   - 使用虚拟环境: `python -m venv cfx_env`
   - 激活环境: `cfx_env\Scripts\activate` (Windows) 或 `source cfx_env/bin/activate` (Linux/Mac)

### 版本兼容性

- Python 3.8+ (推荐 3.9+)
- 所有依赖都支持当前的Python版本
- 建议使用最新的稳定版本

## 许可证

所有依赖包都使用开源许可证，与本项目兼容。详细信息请查看各包的许可证文件。
