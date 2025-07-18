# CFX自动化批量提交系统

一个完整的Python CFX自动化解决方案，用于自动化ANSYS CFX计算流体力学(CFD)批量提交工作流程。该系统支持本地CFX环境和服务器CFX环境，集成了CFX-Pre预处理、SLURM作业调度、文件传输和完整的工作流程管理功能。

## 🚀 核心功能

### 主要特性

- **智能CFX环境检测**: 自动检测本地或服务器CFX安装
- **双环境支持**: 支持本地CFX生成def文件或完全服务器CFX环境
- **参数化批量处理**: 基于压力参数自动生成多个CFX算例
- **SLURM作业管理**: 自动生成和提交集群作业脚本
- **文件传输管理**: 智能文件上传/下载和传输验证
- **工作流程编排**: 端到端自动化流程管理，支持独立步骤执行
- **配置模板系统**: 多种预配置模板适用不同使用场景

### 技术特点

- **模块化架构**: 清晰的代码结构，易于维护和扩展
- **配置驱动**: 灵活的YAML配置系统，支持多种环境配置
- **模板引擎**: 基于Jinja2的模板系统，支持自定义脚本生成
- **智能检测**: 自动检测CFX版本和环境配置
- **错误处理**: 全面的异常处理和重试机制
- **日志记录**: 详细的操作日志和状态跟踪
- **独立执行**: 每个工作流程步骤可以独立执行，无需依赖前一步完成

## 📋 系统要求

### 软件要求
- Python 3.8+
- ANSYS CFX (支持v18.0+) - 本地环境或服务器环境
- Windows (本地) + Linux (服务器) 环境

### Python依赖

**最小依赖（生产环境）**：
- PyYAML>=6.0 - YAML配置文件处理
- Jinja2>=3.0 - 模板引擎
- paramiko>=3.0.0 - SSH连接和文件传输
- pywin32>=304 - Windows注册表访问（仅Windows）

**完整依赖（开发环境）**：
- 包含所有测试、代码质量工具、文档生成工具等

## 🛠️ 快速开始

### 0.克隆项目
```bash
git clone https://github.com/CHOSENX-GPU/AutoExSim-CFX.git
```

### 1. 安装依赖

**推荐使用虚拟环境**：

```bash
# 创建虚拟环境
python -m venv cfx-env

# 激活虚拟环境
# Windows PowerShell
cfx-env\Scripts\Activate.ps1
# Windows CMD
cfx-env\Scripts\activate.bat
# Linux/Mac
source cfx-env/bin/activate
```

**生产环境（最小依赖）**：

```bash
pip install -r requirements.txt
```

**开发环境（完整依赖）**：

```bash
pip install -r requirements-dev.txt
```

**退出虚拟环境**：

```bash
deactivate
```

### 2. 配置设置

选择适合您环境的配置文件：

#### 新用户（推荐）
```bash
# 复制用户模板
cp config/user_template.yaml config/my_config.yaml
# 编辑配置文件中的关键参数
```

#### 本地CFX环境
```bash
# 使用简化配置
python cfx_automation.py --config config/simple_config.yaml

# 使用完整配置
python cfx_automation.py --config config/production_config.yaml
```

#### 服务器CFX环境
```bash
# 使用服务器CFX简化配置
python cfx_automation.py --config config/server_cfx_simple.yaml

# 使用服务器CFX完整配置
python cfx_automation.py --config config/server_cfx_config.yaml
```

### 3. 基本使用

```bash
# 使用指定配置文件运行
python cfx_automation.py --config config/my_config.yaml

# 使用默认配置运行
python cfx_automation.py
```

## 📁 项目结构

```
cfx-automation/
├── cfx_automation.py          # 主程序入口
├── src/                       # 核心模块
│   ├── config.py             # 配置管理
│   ├── workflow.py           # 工作流程编排
│   ├── transfer.py           # 文件传输
│   ├── cfx.py               # CFX处理
│   ├── slurm.py             # SLURM集成
│   └── utils/
│       └── cfx_detector.py   # CFX环境检测
├── config/                   # 配置文件
│   ├── production_config.yaml    # 生产环境配置
│   ├── simple_config.yaml        # 简化配置
│   ├── local_cfx_config.yaml     # 本地CFX配置
│   ├── user_template.yaml        # 用户模板
│   ├── server_cfx_config.yaml    # 服务器CFX配置
│   └── server_cfx_simple.yaml    # 服务器CFX简化配置
├── templates/                # 模板文件
│   ├── CFX_INI.slurm.j2     # SLURM作业脚本模板
│   ├── create_def.pre.j2    # CFX Session文件模板
│   └── Submit_INI.sh.j2     # 批处理提交脚本模板
├── requirements.txt         # 依赖列表
├── README.md               # 项目说明
├── LICENSE                 # 许可证
├── CONFIG_GUIDE.md         # 配置指南
├── CFX_AUTO_DETECT_GUIDE.md # CFX自动检测指南
├── SERVER_CFX_GUIDE.md     # 服务器CFX指南
└── PROJECT_COMPLETION_SUMMARY.md # 项目完成总结
```

## ⚙️ 配置说明

### 配置文件选择

系统提供6种配置文件模板：

| 配置文件 | 适用场景 | CFX环境 | 特点 |
|---------|---------|---------|------|
| `production_config.yaml` | 生产环境 | 本地CFX | 完整功能配置 |
| `simple_config.yaml` | 日常使用 | 本地CFX | 简化配置 |
| `local_cfx_config.yaml` | 本地CFX专用 | 本地CFX | 详细工作流程 |
| `user_template.yaml` | 新用户 | 本地CFX | 配置模板 |
| `server_cfx_config.yaml` | 服务器CFX | 服务器CFX | 完整服务器功能 |
| `server_cfx_simple.yaml` | 服务器CFX | 服务器CFX | 简化服务器配置 |

### 关键配置项

```yaml
# 基本配置
cfx_file_path: "您的CFX文件路径.cfx"
pressure_list: [2600, 2700, 2800]  # 背压参数列表
job_name: "您的作业名称"

# 服务器配置
ssh_host: "服务器IP地址"
ssh_user: "用户名"
ssh_password: "密码"
remote_base_path: "远程工作目录"

# CFX环境配置
auto_detect_cfx: true  # 启用自动检测
cfx_home: "CFX安装路径"  # 备选路径
```

## 🔧 CFX环境支持

### 本地CFX环境（推荐）

**工作流程**：
1. 本地CFX Pre读取.cfx文件
2. 生成def文件
3. 上传def文件到服务器
4. 服务器CFX Solver运行计算
5. 下载计算结果

**配置示例**：
```yaml
cfx_mode: "local"  # 或省略此项
auto_detect_cfx: true
cfx_home: "C:/Program Files/ANSYS Inc/v221/CFX"
```

### 服务器CFX环境

**工作流程**：
1. 上传CFX文件到服务器
2. 服务器CFX Pre生成def文件
3. 服务器CFX Solver运行计算
4. 下载计算结果

**配置示例**：
```yaml
cfx_mode: "server"
use_server_cfx: true
upload_cfx_file: true
cfx_home: "/opt/ansys/v221/CFX"
```

## 🔄 独立步骤执行

系统支持独立执行任何工作流程步骤，无需依赖前一步完成。每个步骤都会检查所需文件是否存在，只要文件存在就可以运行。

### 工作流程步骤

1. **初始化步骤** (`init`): 创建工作目录和session文件
2. **CFX步骤** (`cfx`): 生成def文件
3. **SLURM步骤** (`slurm`): 生成SLURM作业脚本
4. **上传步骤** (`upload`): 上传文件到服务器
5. **提交步骤** (`submit`): 提交作业到SLURM调度器

### 独立执行命令

```bash
# 执行特定步骤
python cfx_automation.py --step init       # 仅初始化
python cfx_automation.py --step cfx        # 仅生成def文件
python cfx_automation.py --step slurm      # 仅生成SLURM脚本
python cfx_automation.py --step upload     # 仅上传文件
python cfx_automation.py --step submit     # 仅提交作业

# 从指定步骤开始执行
python cfx_automation.py --from-step cfx   # 从CFX步骤开始
python cfx_automation.py --from-step upload # 从上传步骤开始
```

### 使用场景

- **调试**: 单独测试某个步骤
- **恢复**: 从失败的步骤继续执行
- **分阶段**: 分时段执行不同步骤
- **自定义**: 根据需要组合不同步骤

## 🚀 使用示例

### 1. 简单使用

```bash
# 使用默认配置
python cfx_automation.py

# 使用指定配置
python cfx_automation.py --config config/simple_config.yaml
```

### 2. 新用户配置

```bash
# 1. 复制用户模板
cp config/user_template.yaml config/my_config.yaml

# 2. 编辑配置文件
# 修改 cfx_file_path, pressure_list, 服务器信息等

# 3. 运行程序
python cfx_automation.py --config config/my_config.yaml
```

### 3. 批量处理

```python
# 自定义压力参数列表
pressure_list = [2600, 2700, 2800, 2900, 3000]

# 系统会自动为每个压力值生成对应的CFX算例
# 并提交到服务器进行计算
```

## � 功能特性

### 1. 智能CFX检测

- 自动搜索常见ANSYS安装路径
- 支持多版本CFX检测（v221, v222, v231等）
- 优先选择最新版本
- 备选路径机制

### 2. 文件传输管理

- 智能文件上传/下载
- 传输完整性验证
- 压缩传输支持
- 自动重试机制

### 3. 作业调度

- 自动生成SLURM脚本
- 智能资源分配
- 作业状态监控
- 错误恢复机制

### 4. 配置灵活性

- 多种配置模板
- 环境自适应
- 参数化配置
- 自定义扩展

## 📊 项目完成度

### 已完成功能 ✅

- [x] 核心工作流程实现
- [x] 本地CFX环境支持
- [x] 服务器CFX环境支持
- [x] 智能CFX检测
- [x] 文件传输管理
- [x] SLURM作业调度
- [x] 配置管理系统
- [x] 模板引擎
- [x] 错误处理和日志
- [x] 多种配置模板
- [x] 文档系统
- [x] 独立步骤执行功能
- [x] 远程CFX路径支持

### 测试验证 ✅

- [x] 真实服务器环境测试
- [x] 28MB CFX文件处理测试
- [x] 批量作业提交测试
- [x] 文件传输完整性测试
- [x] 错误恢复机制测试
- [x] 独立步骤执行测试
- [x] 远程CFX路径功能测试

## �️ 故障排除

### 常见问题

#### 1. CFX检测失败
```bash
# 检查CFX安装路径
# 在配置文件中手动指定CFX路径
cfx_home: "C:/Program Files/ANSYS Inc/v221/CFX"
auto_detect_cfx: false
```

#### 2. 服务器连接失败
```bash
# 检查网络连接
ping 服务器IP
# 检查SSH配置
ssh 用户名@服务器IP
```

#### 3. 文件传输失败
```yaml
# 增加重试次数和超时时间
retry_count: 5
transfer_timeout: 3600
```

### 调试模式

```yaml
# 启用详细日志
log_level: "DEBUG"
verbose_logging: true
```

## 📚 文档

- [CONFIG_GUIDE.md](CONFIG_GUIDE.md) - 配置文件使用指南
- [STEP_BY_STEP_GUIDE.md](STEP_BY_STEP_GUIDE.md) - 逐步运行使用指南
- [SERVER_CFX_GUIDE.md](SERVER_CFX_GUIDE.md) - 服务器CFX环境指南
- [COMPLETE_PARAMETERS_LIST.md](COMPLETE_PARAMETERS_LIST.md) - 完整配置文件说明

## 🤝 贡献

欢迎贡献代码、报告问题或提出改进建议！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🆘 支持

如有问题或建议，请：
- 查看 [文档](CONFIG_GUIDE.md) 获取详细信息
- 检查 [故障排除](#🛠️-故障排除) 部分
- 创建 Issue 报告问题

---

**版本**: 1.0.2  
**状态**: 就绪  
**最后更新**: 2025-07-19  
**环境**: 本地CFX + 服务器CFX双环境支持  
