# CFX自动化配置文件说明

## 📁 配置文件概览

项目提供了多个配置文件模板，适用于不同的使用场景：

### 1. `production_config.yaml` - 生产环境配置
- **用途**: 完整的生产环境配置
- **特点**: 包含所有高级配置选项，支持远程CFX路径
- **CFX环境**: 使用本地CFX Pre生成def文件
- **适用场景**: 生产环境，需要完整功能

### 2. `simple_config.yaml` - 简化配置
- **用途**: 日常使用的简化配置
- **特点**: 去除复杂选项，保留核心功能
- **CFX环境**: 使用本地CFX Pre生成def文件
- **适用场景**: 快速上手，日常使用

### 3. `local_cfx_config.yaml` - 本地CFX配置
- **用途**: 专门用于本地CFX生成def文件的配置
- **特点**: 详细的工作流程说明，支持远程CFX路径
- **CFX环境**: 本地CFX Pre + 服务器CFX Solver
- **适用场景**: 混合环境，本地生成，服务器运行

### 4. `user_template.yaml` - 用户模板
- **用途**: 用户自定义配置模板
- **特点**: 包含详细的配置说明和示例，支持远程CFX路径
- **CFX环境**: 使用本地CFX Pre生成def文件
- **适用场景**: 新用户配置参考

### 5. `server_cfx_config.yaml` - 服务器CFX环境配置
- **用途**: 完全使用服务器CFX环境
- **特点**: 服务器上完成所有CFX操作，支持远程CFX路径
- **CFX环境**: 服务器CFX Pre + 服务器CFX Solver
- **适用场景**: 本地无CFX安装，服务器资源充足

### 6. `server_cfx_simple.yaml` - 服务器CFX简化配置
- **用途**: 服务器CFX环境的简化配置
- **特点**: 去除复杂选项，保留核心服务器功能，支持远程CFX路径
- **CFX环境**: 服务器CFX Pre + 服务器CFX Solver
- **适用场景**: 服务器CFX环境，快速上手

## 🔧 CFX环境配置说明

### 本地CFX配置 (推荐)
所有配置模板现在都使用本地CFX环境自动检测：

```yaml
# 本地CFX配置 - 启用自动检测
cfx_home: "C:/Program Files/ANSYS Inc/v221/CFX"  # 备选路径
cfx_pre_executable: "C:/Program Files/ANSYS Inc/v221/CFX/bin/cfx5pre.exe"  # 备选路径
cfx_solver_executable: "/opt/ansys/v221/CFX/bin/cfx5solve"  # 服务器路径
cfx_bin_path: "C:/Program Files/ANSYS Inc/v221/CFX/bin"  # 本地CFX二进制文件路径
auto_detect_cfx: true  # 启用自动检测本地CFX环境

# 🆕 远程CFX路径配置（推荐）
remote_cfx_home: "/opt/ansys/v221/CFX"  # 远程服务器CFX安装路径
remote_cfx_bin_path: "/opt/ansys/v221/CFX/bin"  # 远程服务器CFX二进制文件路径
```

**自动检测功能**：
- 系统会自动搜索本地CFX安装路径
- 支持多个ANSYS版本的自动识别
- 如果自动检测失败，会使用配置文件中的备选路径
- 优先检测最新版本的CFX

**远程CFX路径优势**：
- 支持本地和远程CFX路径不同的情况
- 在SLURM模板中自动使用远程CFX路径
- 提高跨平台兼容性（Windows本地 + Linux服务器）

### 服务器CFX配置
对于服务器CFX环境，完全在服务器上进行所有CFX操作：

```yaml
# 服务器CFX配置
cfx_mode: "server"  # 服务器模式
use_server_cfx: true  # 使用服务器CFX
upload_cfx_file: true  # 上传CFX文件到服务器
cfx_home: "/opt/ansys/v221/CFX"  # 服务器CFX路径
cfx_pre_executable: "/opt/ansys/v221/CFX/bin/cfx5pre"  # 服务器CFX Pre
cfx_solver_executable: "/opt/ansys/v221/CFX/bin/cfx5solve"  # 服务器CFX Solver
cfx_bin_path: "/opt/ansys/v221/CFX/bin"  # 服务器CFX二进制文件路径
auto_detect_cfx: false  # 使用指定的服务器CFX路径

# 🆕 远程CFX路径配置（与本地路径相同）
remote_cfx_home: "/opt/ansys/v221/CFX"
remote_cfx_bin_path: "/opt/ansys/v221/CFX/bin"
```

**服务器CFX特点**：
- 完全在服务器上进行CFX操作
- 需要上传CFX文件到服务器
- 服务器需要安装CFX环境
- 减少本地资源占用
- 支持远程CFX路径配置

### 工作流程
1. **本地生成**: 使用本地CFX Pre读取.cfx文件并生成def文件
2. **文件上传**: 上传def文件和相关文件到服务器
3. **服务器计算**: 服务器使用CFX Solver运行计算
4. **结果下载**: 自动下载计算结果

## 🚀 使用方法

### 快速开始
1. 选择合适的配置文件
2. 修改必要的配置项：
   - `cfx_file_path`: 您的CFX文件路径
   - `pressure_list`: 压力参数列表
   - `ssh_host`, `ssh_user`, `ssh_password`: 服务器信息
   - `remote_base_path`: 远程工作目录
   - `remote_cfx_home`, `remote_cfx_bin_path`: 远程CFX路径（推荐）

### 🆕 独立步骤执行功能
所有配置文件都支持独立步骤执行，无需依赖前一步完成：

```bash
# 完整工作流程
python cfx_automation.py --config config/my_config.yaml

# 独立步骤执行
python cfx_automation.py --step init --config config/my_config.yaml      # 仅初始化
python cfx_automation.py --step cfx --config config/my_config.yaml       # 仅生成def文件
python cfx_automation.py --step slurm --config config/my_config.yaml     # 仅生成SLURM脚本
python cfx_automation.py --step upload --config config/my_config.yaml    # 仅上传文件
python cfx_automation.py --step submit --config config/my_config.yaml    # 仅提交作业

# 从指定步骤开始执行
python cfx_automation.py --from-step cfx --config config/my_config.yaml  # 从CFX步骤开始
```

### 推荐配置选择

#### 新用户
使用 `user_template.yaml` 作为起点：
```bash
cp config/user_template.yaml config/my_config.yaml
# 编辑 my_config.yaml 中的配置
python cfx_automation.py --config config/my_config.yaml
```

#### 日常使用
使用 `simple_config.yaml`：
```bash
python cfx_automation.py --config config/simple_config.yaml
```

#### 生产环境
使用 `production_config.yaml`：
```bash
python cfx_automation.py --config config/production_config.yaml
```

#### 服务器CFX环境
使用 `server_cfx_simple.yaml`：
```bash
python cfx_automation.py --config config/server_cfx_simple.yaml
```

#### 完整服务器CFX功能
使用 `server_cfx_config.yaml`：
```bash
python cfx_automation.py --config config/server_cfx_config.yaml
```

## 📝 重要配置项说明

### 必须配置的项目
- `cfx_file_path`: 本地CFX文件路径
- `pressure_list`: 压力参数列表
- `ssh_host`, `ssh_user`, `ssh_password`: 服务器连接信息
- `remote_base_path`: 远程工作目录

### 可选配置项目
- `job_name`: 作业名称
- `partition`: SLURM分区
- `nodes`, `tasks_per_node`: 计算资源
- `time_limit`: 时间限制

### CFX模型配置
- `flow_analysis_name`: 流动分析名称
- `domain_name`: 域名称
- `boundary_name`: 边界名称
- `outlet_location`: 出口位置

## 💡 配置建议

### 本地CFX路径设置
启用自动检测后，系统会自动搜索CFX安装路径：
```yaml
cfx_home: "C:/Program Files/ANSYS Inc/v221/CFX"  # 备选路径
cfx_pre_executable: "C:/Program Files/ANSYS Inc/v221/CFX/bin/cfx5pre.exe"  # 备选路径
auto_detect_cfx: true  # 启用自动检测
```

**自动检测逻辑**：
- 搜索常见的ANSYS安装路径
- 检测多个版本（v221, v222, v231等）
- 优先选择最新版本
- 如果检测失败，使用配置文件中的备选路径

### 服务器路径设置
确保服务器CFX Solver路径正确：
```yaml
cfx_solver_executable: "/opt/ansys/v221/CFX/bin/cfx5solve"
```

### 压力参数设置
根据需要设置压力列表：
```yaml
pressure_list: [2600, 2700, 2800, 2900, 3000]
```

## 🔒 安全建议

### 密码安全
- 生产环境建议使用SSH密钥认证
- 避免在配置文件中明文存储密码
- 使用环境变量或密钥文件

### 文件权限
- 确保配置文件权限适当（600或644）
- 避免在版本控制中提交含有敏感信息的配置

## 🔄 更新日志

- **2025-07-19**: 新增独立步骤执行功能支持
- **2025-07-19**: 新增远程CFX路径配置（`remote_cfx_home`, `remote_cfx_bin_path`）
- **2025-07-19**: 更新所有配置文件支持远程CFX路径
- **2025-07-19**: 添加独立步骤执行使用示例
- **2025-07-19**: 升级到v2.0.0版本，增强配置灵活性

## 📋 配置文件对比表

| 配置文件 | 使用场景 | CFX环境 | 远程CFX路径 | 独立步骤 |
|----------|----------|---------|-------------|----------|
| `production_config.yaml` | 生产环境 | 本地CFX | ✅ | ✅ |
| `simple_config.yaml` | 日常使用 | 本地CFX | ✅ | ✅ |
| `local_cfx_config.yaml` | 本地CFX专用 | 本地CFX | ✅ | ✅ |
| `user_template.yaml` | 新用户 | 本地CFX | ✅ | ✅ |
| `server_cfx_config.yaml` | 服务器CFX | 服务器CFX | ✅ | ✅ |
| `server_cfx_simple.yaml` | 服务器CFX | 服务器CFX | ✅ | ✅ |
| `complete_config_template.yaml` | 完整模板 | 混合 | ✅ | ✅ |

---

**版本**: 1.0.2  
**状态**: 就绪  
**最后更新**: 2025-07-19  
**新功能**: 独立步骤执行、远程CFX路径支持、优化配置系统

## 🛠️ 故障排除

### 常见问题
1. **CFX路径错误**: 检查本地CFX安装路径
2. **服务器连接失败**: 检查网络连接和认证信息
3. **路径权限问题**: 确保远程路径有写权限

### 调试模式
启用调试模式获取更多信息：
```yaml
debug:
  enabled: true
  verbose_logging: true
```

---

**选择适合您需求的配置文件，开始使用CFX自动化系统！**
