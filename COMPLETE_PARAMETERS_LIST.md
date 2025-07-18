# CFX自动化系统 - 完整参数列表

## 📋 系统支持的所有参数

基于对 `src` 目录中源代码的深入分析，以下是 CFX 自动化系统支持的所有 **30 个核心参数**：

### 🔧 CFX 环境配置参数

| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| `cfx_home` | string | `""` | CFX 安装主目录路径 |
| `cfx_pre_executable` | string | `""` | CFX-Pre 可执行文件路径 |
| `cfx_solver_executable` | string | `""` | CFX-Solver 可执行文件路径 |
| `cfx_version` | string | `""` | CFX 版本号 |
| `cfx_bin_path` | string | `""` | CFX 二进制文件路径 |
| `auto_detect_cfx` | boolean | `true` | 是否自动检测 CFX 环境 |

### 🌐 远程CFX环境配置参数

| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| `remote_cfx_home` | string | `"/opt/ansys/v221/CFX"` | 远程服务器CFX安装主目录路径 |
| `remote_cfx_bin_path` | string | `"/opt/ansys/v221/CFX/bin"` | 远程服务器CFX二进制文件路径 |

### 📁 基础文件配置参数

| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| `job_name` | string | `"CFX_Job"` | 作业名称 |
| `base_path` | string | `"."` | 基础工作路径 |
| `cfx_file_path` | string | `""` | CFX 文件路径 |

### 🏗️ CFX 模型配置参数

| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| `flow_analysis_name` | string | `"Flow Analysis 1"` | 流动分析名称 |
| `domain_name` | string | `"S1"` | 域名称 |
| `boundary_name` | string | `"S1 Outlet"` | 边界名称 |
| `outlet_location` | string | `"R2_OUTFLOW"` | 出口位置 |
| `pressure_blend` | string | `"0.05"` | 压力混合因子 |

### 📝 文件命名配置参数

| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| `folder_prefix` | string | `"P_Out_"` | 生成文件夹的前缀 |
| `def_file_prefix` | string | `""` | def 文件前缀 |

### 🎯 背压参数配置

| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| `pressure_list` | List[float] | `[2187, 2189]` | 背压参数列表 |
| `pressure_unit` | string | `"Pa"` | 压力单位 |

### 🖥️ 服务器连接配置参数

| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| `ssh_host` | string | `"cluster.example.com"` | SSH 主机地址 |
| `ssh_port` | int | `22` | SSH 端口 |
| `ssh_user` | string | `"username"` | SSH 用户名 |
| `ssh_key` | string | `""` | SSH 密钥文件路径 |
| `ssh_password` | string | `None` | SSH 密码（可选） |
| `remote_base_path` | string | `"/home/username/CFX_Jobs"` | 远程基础路径 |

### ⚡ SLURM 作业配置参数

| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| `partition` | string | `"cpu-low"` | SLURM 分区 |
| `nodes` | int | `1` | 节点数 |
| `tasks_per_node` | int | `32` | 每个节点的任务数 |
| `time_limit` | string | `"7-00:00:00"` | 时间限制 |
| `memory_per_node` | string | `"64GB"` | 每个节点的内存 |

### 📄 模板配置参数

| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| `template_dir` | string | `"./templates"` | 模板目录路径 |
| `session_template` | string | `"create_def.pre.j2"` | CFX Session 模板文件 |
| `slurm_template` | string | `"CFX_INI.slurm.j2"` | SLURM 作业模板文件 |
| `batch_template` | string | `"Submit_INI.sh.j2"` | 批处理脚本模板文件 |

### 🗂️ 文件处理配置参数

| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| `ini_file` | string | `"INI.res"` | 初始化文件名（可选） |
| `has_ini_file` | boolean | `true` | 是否使用初始化文件 |
| `backup_enabled` | boolean | `true` | 是否启用备份 |
| `cleanup_temp_files` | boolean | `true` | 是否清理临时文件 |

### 📊 报告配置参数

| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| `report_dir` | string | `"./reports"` | 工作流程报告目录 |

### 🔗 连接配置参数

| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| `timeout` | int | `300` | 连接超时时间（秒） |

## 🎯 参数优先级说明

### 必填参数
- `cfx_file_path`: CFX 文件路径
- `pressure_list`: 背压参数列表
- `ssh_host`: 服务器主机地址
- `ssh_user`: SSH 用户名
- `partition`: SLURM 分区

### 认证参数（至少需要一个）
- `ssh_password`: SSH 密码
- `ssh_key`: SSH 密钥文件路径

### 自动检测参数
当 `auto_detect_cfx: true` 时，以下参数会被自动检测：
- `cfx_home`
- `cfx_pre_executable`
- `cfx_solver_executable`
- `cfx_version`
- `cfx_bin_path`

## 📚 配置文件示例

```yaml
# 最小配置示例
cfx_file_path: "/path/to/your/model.cfx"
pressure_list: [2600, 2700, 2800]
ssh_host: "your-server.com"
ssh_user: "username"
ssh_password: "password"
partition: "cpu-low"

# 远程CFX环境配置示例
cfx_file_path: "/path/to/your/model.cfx"
pressure_list: [2600, 2700, 2800]
ssh_host: "your-server.com"
ssh_user: "username"
ssh_password: "password"
partition: "cpu-low"
remote_cfx_home: "/opt/ansys/v221/CFX"
remote_cfx_bin_path: "/opt/ansys/v221/CFX/bin"

# 完整配置示例
# 请参考 config/complete_config_template.yaml
```

## 🚀 使用建议

1. **快速开始**: 使用 `config/simple_config.yaml`
2. **本地 CFX**: 使用 `config/local_cfx_config.yaml`
3. **生产环境**: 使用 `config/production_config.yaml`
4. **服务器 CFX**: 使用 `config/server_cfx_simple.yaml`
5. **完整模板**: 使用 `config/complete_config_template.yaml`

## 🔄 独立步骤执行功能

系统支持独立执行任何工作流程步骤，无需依赖前一步完成：

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

### 工作流程步骤说明
1. **初始化步骤** (`init`): 创建工作目录和session文件
2. **CFX步骤** (`cfx`): 生成def文件
3. **SLURM步骤** (`slurm`): 生成SLURM作业脚本
4. **上传步骤** (`upload`): 上传文件到服务器
5. **提交步骤** (`submit`): 提交作业到SLURM调度器

## 🔍 参数验证

系统会自动验证以下内容：
- CFX 可执行文件是否存在
- CFX 文件是否存在
- 基础路径是否有效
- 模板目录是否存在
- 背压参数是否有效
- SSH 密钥文件是否存在
- 远程CFX路径配置是否正确
- 服务器连接是否可用

## 📦 源代码对应关系

所有参数都在以下文件中定义：
- `src/config.py`: `CFXAutomationConfig` 类
- `src/workflow.py`: 工作流程管理
- `src/cfx.py`: CFX 操作模块
- `src/slurm.py`: SLURM 作业管理
- `src/transfer.py`: 文件传输模块

## ✅ 测试状态

所有参数都已经过测试，确保系统兼容性：
- ✅ 参数解析正常
- ✅ 配置验证通过
- ✅ 系统集成测试通过
- ✅ 实际环境验证通过
- ✅ 独立步骤执行测试通过
- ✅ 远程CFX路径功能测试通过

## 🆕 新功能特性（v2.0.0）

### 独立步骤执行
- 支持任意工作流程步骤的独立执行
- 智能文件检测，只要文件存在就可以运行
- 支持从指定步骤开始执行
- 完全解耦的步骤依赖关系

### 远程CFX路径支持
- 配置远程服务器CFX安装路径
- 支持不同于本地CFX的远程环境
- 自动在模板中使用远程CFX路径
- 增强跨平台兼容性

### 配置系统优化
- 标准化所有配置文件格式
- 增强配置参数验证
- 更好的默认值和错误处理
- 支持更多环境配置场景

## 📖 更新日志

- **2025-07-19**: 完成所有参数的识别和文档化
- **2025-07-19**: 更新所有配置文件，添加 `cfx_bin_path` 参数
- **2025-07-19**: 创建完整配置模板文件
- **2025-07-19**: 添加远程CFX路径支持参数 (`remote_cfx_home`, `remote_cfx_bin_path`)
- **2025-07-19**: 实现独立步骤执行功能，更新参数总数为30个
- **2025-07-19**: 完成系统1.0.2版本升级，达到就绪状态
