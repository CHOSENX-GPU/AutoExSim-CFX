# CFX 自动化系统 - 分步执行指南

## 📋 系统概述

CFX 自动化系统包含以下主要步骤：
1. **init** - 初始化工作流程
2. **cfx** - 生成 CFX def 文件
3. **slurm** - 生成 SLURM 作业脚本
4. **upload** - 上传文件到服务器
5. **submit** - 提交作业到 SLURM 队列

## 🚀 分步执行指南

### 前提条件检查

在开始之前，请确保：
- [x] CFX 软件已安装并可访问
- [x] 配置文件已正确设置
- [x] 网络连接正常（如需服务器操作）

### 步骤 1: 初始化工作流程

```bash
# 只执行初始化步骤
python cfx_automation.py --config config/simple_config.yaml run --steps init

# 或者指定特定的背压值
python cfx_automation.py --config config/simple_config.yaml run --steps init --pressure-list 2600 2700 2800
```

**功能说明**：
- 验证配置文件的正确性
- 检查 CFX 文件路径
- 验证服务器连接参数
- 初始化工作流程状态

**预期输出**：
```
运行CFX自动化工作流程: config/simple_config.yaml
初始化CFX自动化工作流程...
工作流程初始化成功
```

### 步骤 2: 生成 CFX def 文件

```bash
# 生成 CFX def 文件（包含初始化）
python cfx_automation.py --config config/simple_config.yaml run --steps init cfx

# 或者指定特定的背压值
python cfx_automation.py --config config/simple_config.yaml run --steps init cfx --pressure-list 2600 2700
```

**功能说明**：
- 生成 CFX Session 文件
- 执行 CFX-Pre 批量生成 def 文件
- 验证生成的 def 文件

**预期输出**：
```
生成CFX算例...
生成参数化算例，背压列表: [2600.0, 2700.0]
生成CFX Session文件: /path/to/create_def.pre
执行CFX-Pre Session: /path/to/create_def.pre
CFX-Pre Session执行成功
def文件生成成功: /path/to/P_Out_2600/2600.def
def文件生成成功: /path/to/P_Out_2700/2700.def
总共生成了 2 个def文件
```

**生成的文件**：
- `P_Out_2600/2600.def`
- `P_Out_2700/2700.def`
- `create_def.pre` (Session 文件)

### 步骤 3: 生成 SLURM 作业脚本

```bash
# 生成 SLURM 脚本（包含前面的步骤）
python cfx_automation.py --config config/simple_config.yaml run --steps init cfx slurm

# 或者只生成 SLURM 脚本（如果 CFX 文件已存在）
python cfx_automation.py --config config/simple_config.yaml run --steps init slurm --pressure-list 2600 2700
```

**功能说明**：
- 为每个背压值生成 SLURM 作业脚本
- 生成批处理提交脚本
- 验证脚本的正确性

**预期输出**：
```
生成Slurm作业脚本...
生成所有Slurm作业脚本，背压列表: [2600.0, 2700.0]
生成Slurm作业脚本: 背压 2600.0
生成Slurm作业脚本: 背压 2700.0
Slurm作业脚本生成成功: 2 个脚本
```

**生成的文件**：
- `P_Out_2600/CFX_INI.slurm`
- `P_Out_2700/CFX_INI.slurm`
- `Submit_INI.sh` (批处理提交脚本)

### 步骤 4: 上传文件到服务器

```bash
# 上传文件到服务器（包含前面的步骤）
python cfx_automation.py --config config/simple_config.yaml run --steps init cfx slurm upload

# 或者只上传文件（如果其他文件已准备好）
python cfx_automation.py --config config/simple_config.yaml run --steps init upload --pressure-list 2600 2700
```

**功能说明**：
- 通过 SSH/SFTP 连接到服务器
- 上传 def 文件到服务器
- 上传 SLURM 脚本到服务器
- 验证上传的文件完整性

**预期输出**：
```
上传文件到服务器...
连接服务器: your.server.com:22
上传文件: P_Out_2600/2600.def -> /remote/path/P_Out_2600/2600.def
上传文件: P_Out_2700/2700.def -> /remote/path/P_Out_2700/2700.def
上传文件: P_Out_2600/CFX_INI.slurm -> /remote/path/P_Out_2600/CFX_INI.slurm
上传文件: P_Out_2700/CFX_INI.slurm -> /remote/path/P_Out_2700/CFX_INI.slurm
文件上传成功: 4 个文件
```

### 步骤 5: 提交作业到 SLURM 队列

```bash
# 提交作业（包含所有步骤）
python cfx_automation.py --config config/simple_config.yaml run --steps init cfx slurm upload submit

# 或者只提交作业（如果文件已上传）
python cfx_automation.py --config config/simple_config.yaml run --steps init submit --pressure-list 2600 2700
```

**功能说明**：
- 连接到服务器
- 提交 SLURM 作业到队列
- 获取作业 ID
- 监控作业状态

**预期输出**：
```
提交作业到SLURM队列...
连接服务器: your.server.com:22
提交作业: P_Out_2600/CFX_INI.slurm
作业ID: 12345
提交作业: P_Out_2700/CFX_INI.slurm
作业ID: 12346
作业提交成功: 2 个作业
```

## 🎯 完整流程执行

### 一次性执行所有步骤
```bash
# 使用配置文件中的默认背压值
python cfx_automation.py --config config/simple_config.yaml run

# 指定特定的背压值
python cfx_automation.py --config config/simple_config.yaml run --pressure-list 2600 2700 2800
```

### 模拟运行（调试模式）
```bash
# 模拟运行，不实际执行操作
python cfx_automation.py --config config/simple_config.yaml run --dry-run
```

## 🔧 常用组合

### 1. 本地生成文件（不上传）
```bash
# 只生成 CFX def 文件和 SLURM 脚本
python cfx_automation.py --config config/simple_config.yaml run --steps init cfx slurm
```

### 2. 快速测试（单个背压值）
```bash
# 测试单个背压值的完整流程
python cfx_automation.py --config config/simple_config.yaml run --pressure-list 2600 --steps init cfx
```

### 3. 重新上传和提交
```bash
# 如果本地文件已存在，只需上传和提交
python cfx_automation.py --config config/simple_config.yaml run --steps init upload submit
```

## 📊 执行状态监控

每个步骤执行后，系统会显示工作流程状态：

```
=== CFX自动化工作流程状态 ===
初始化             ✓
CFX算例生成         ✓
Slurm脚本生成       ✓
文件上传            ✓
作业提交            ✓
工作流程完成          ✓

=== 执行摘要 ===
CFX算例: 3/3 成功
SLURM脚本: 3/3 成功
文件上传: 6/6 成功
作业提交: 3/3 成功
```

## 🛠️ 故障排除

### 如果某个步骤失败：

1. **查看详细日志**：
   ```bash
   python cfx_automation.py --config config/simple_config.yaml run --log-level DEBUG
   ```

2. **检查工作流程报告**：
   ```bash
   # 查看最新的报告文件
   ls -la reports/
   ```

3. **重新执行失败的步骤**：
   ```bash
   # 例如，如果 CFX 生成失败，重新执行
   python cfx_automation.py --config config/simple_config.yaml run --steps init cfx
   ```

### 常见问题：

1. **CFX-Pre 执行失败**：
   - 检查 CFX 文件路径是否正确
   - 确保 CFX 软件已正确安装
   - 删除旧的错误日志文件

2. **服务器连接失败**：
   - 检查 SSH 连接参数
   - 验证用户名和密码
   - 确认服务器可达性

3. **文件上传失败**：
   - 检查远程路径权限
   - 确认磁盘空间充足
   - 验证网络连接稳定性

## 📝 配置文件示例

确保您的 `config/simple_config.yaml` 包含所有必要的配置：

```yaml
# 基本配置
cfx_file_path: "D:/Desktop/TA29_radial_load/Pre/Grid Independence Gap/TA29_75/TA29_75.cfx"
pressure_list: [2600, 2700, 2800]
base_path: "D:/Desktop/TA29_radial_load/Pre/Grid Independence Gap/TA29_75/"

# 服务器配置
ssh_host: "your.server.com"
ssh_user: "your_username"
ssh_password: "your_password"
remote_base_path: "/path/to/your/workspace/TA29_Radial_loading/test"

# CFX 环境配置
cfx_pre_executable: "D:/ANSYS Inc/v221/CFX/bin/cfx5pre.exe"
cfx_version: "22.1"
```

## 🎉 总结

通过分步执行，您可以：
- 逐步验证每个阶段的结果
- 快速定位和解决问题
- 根据需要选择性执行特定步骤
- 提高工作流程的可控性和可靠性

选择适合您需求的执行方式，享受高效的 CFX 自动化体验！
