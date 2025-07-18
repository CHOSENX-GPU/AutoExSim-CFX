# 服务器CFX环境配置指南

## 📋 概述

服务器CFX环境配置允许您在服务器上完成所有CFX操作，包括def文件生成和计算运行。这种方式特别适合本地没有安装CFX软件的用户。

## 🔄 工作流程

### 完整服务器CFX流程
1. **上传CFX文件**: 将本地CFX文件上传到服务器
2. **服务器CFX Pre**: 在服务器上生成session文件
3. **生成def文件**: 服务器CFX Pre执行session生成def文件
4. **运行计算**: 服务器CFX Solver执行计算
5. **下载结果**: 自动下载计算结果到本地

### 🆕 独立步骤执行支持
系统现在支持独立执行任何工作流程步骤，无需依赖前一步完成：

```bash
# 执行特定步骤
python cfx_automation.py --step upload --config config/server_cfx_config.yaml  # 仅上传文件
python cfx_automation.py --step cfx --config config/server_cfx_config.yaml     # 仅生成def文件
python cfx_automation.py --step submit --config config/server_cfx_config.yaml  # 仅提交作业

# 从指定步骤开始执行
python cfx_automation.py --from-step cfx --config config/server_cfx_config.yaml # 从CFX步骤开始
```

## 🎯 适用场景

### 推荐使用情况
- 本地没有安装CFX软件
- 服务器计算资源充足
- 需要保持环境一致性
- 减少本地资源占用

### 不推荐使用情况
- 网络带宽有限（需要传输大量CFX文件）
- 服务器存储空间不足
- 本地CFX环境已配置完善

## 📁 配置文件选择

### 1. `server_cfx_simple.yaml` - 简化版（推荐）
```yaml
# 关键配置
cfx_mode: "server"
use_server_cfx: true
upload_cfx_file: true
cfx_home: "/opt/ansys/v221/CFX"
```

**特点**：
- 配置简单，易于上手
- 包含必要的服务器CFX配置
- 适合大多数用户

### 2. `server_cfx_config.yaml` - 完整版
```yaml
# 关键配置
cfx_mode: "server"
use_server_cfx: true
upload_cfx_file: true
cfx_home: "/opt/ansys/v221/CFX"

# 高级配置
server_env_vars:
  CFX_VERSION: "22.1"
  ANSYS_ROOT: "/opt/ansys/v221"

module_load_commands:
  - "module load ansys/22.1"
```

**特点**：
- 包含所有高级配置选项
- 支持环境变量和模块加载
- 适合复杂的服务器环境

## ⚙️ 关键配置项

### 服务器CFX路径配置
```yaml
# 服务器CFX环境路径（本地配置）
cfx_home: "/opt/ansys/v221/CFX"
cfx_pre_executable: "/opt/ansys/v221/CFX/bin/cfx5pre"
cfx_solver_executable: "/opt/ansys/v221/CFX/bin/cfx5solve"
cfx_bin_path: "/opt/ansys/v221/CFX/bin"

# 🆕 远程CFX路径配置（推荐）
remote_cfx_home: "/opt/ansys/v221/CFX"
remote_cfx_bin_path: "/opt/ansys/v221/CFX/bin"
```

### 工作模式配置
```yaml
# 服务器模式配置
cfx_mode: "server"          # 指定为服务器模式
use_server_cfx: true        # 使用服务器CFX
upload_cfx_file: true       # 上传CFX文件到服务器
auto_detect_cfx: false      # 禁用自动检测，使用指定路径
```

### 文件传输配置
```yaml
# 传输优化配置
upload_compression: true     # 上传时压缩
download_compression: true   # 下载时压缩
keep_server_files: false    # 完成后清理服务器文件
cleanup_server_temp: true   # 清理服务器临时文件
```

### 服务器环境配置
```yaml
# 环境变量设置
server_env_vars:
  CFX_VERSION: "22.1"
  ANSYS_ROOT: "/opt/ansys/v221"
  CFX_ROOT: "/opt/ansys/v221/CFX"

# 模块加载命令
module_load_commands:
  - "module load ansys/22.1"
  - "module load intel/2021.4"
  - "module load openmpi/4.1.1"
```

## 🚀 快速开始

### 步骤1: 选择配置文件
```bash
# 复制服务器CFX简化配置
cp config/server_cfx_simple.yaml config/my_server_config.yaml
```

### 步骤2: 修改配置
编辑 `config/my_server_config.yaml`：
```yaml
# 修改本地CFX文件路径
cfx_file_path: "您的CFX文件路径.cfx"

# 修改服务器信息
ssh_host: "您的服务器IP"
ssh_user: "您的用户名"
ssh_password: "您的密码"

# 修改压力参数
pressure_list: [2600, 2700, 2800]

# 🆕 配置远程CFX路径（推荐）
remote_cfx_home: "/opt/ansys/v221/CFX"
remote_cfx_bin_path: "/opt/ansys/v221/CFX/bin"
```

### 步骤3: 运行程序
```bash
# 完整工作流程
python cfx_automation.py --config config/my_server_config.yaml

# 🆕 独立步骤执行示例
python cfx_automation.py --step upload --config config/my_server_config.yaml  # 仅上传
python cfx_automation.py --step cfx --config config/my_server_config.yaml     # 仅生成def
python cfx_automation.py --step submit --config config/my_server_config.yaml  # 仅提交
```

## 🔧 服务器环境要求

### 必需软件
- ANSYS CFX 22.1或更高版本
- Python 3.8+（如果需要在服务器上运行脚本）
- SLURM作业调度系统

### 系统配置
- 足够的存储空间存储CFX文件
- 网络文件系统访问权限
- 正确的环境变量设置

### 许可证配置
```yaml
# 许可证服务器配置
license_server: "license.server.com"
license_port: 2325
license_feature: "cfx"
```

## 💡 优化建议

### 传输优化
```yaml
# 文件传输优化
transfer_chunk_size: 8192    # 8KB块大小
upload_compression: true     # 启用压缩
verify_transfer: true        # 验证传输完整性
```

### 存储优化
```yaml
# 存储管理
cleanup_server_temp: true    # 清理临时文件
keep_server_files: false     # 不保留服务器文件
backup_enabled: true         # 启用本地备份
```

### 性能优化
```yaml
# 性能配置
parallel_generation: true    # 并行生成
parallel_max_workers: 4      # 最大并行数
batch_size: 10              # 批处理大小
```

## 🛠️ 故障排除

### 常见问题

#### 1. 服务器CFX路径错误
**症状**: 找不到CFX可执行文件
**解决方案**:
```bash
# 在服务器上查找CFX路径
find /opt -name "cfx5pre" 2>/dev/null
which cfx5pre

# 🆕 配置远程CFX路径（推荐）
remote_cfx_home: "/opt/ansys/v221/CFX"
remote_cfx_bin_path: "/opt/ansys/v221/CFX/bin"
```

#### 2. 环境变量未加载
**症状**: CFX无法启动或许可证错误
**解决方案**:
```yaml
# 添加环境变量
server_env_vars:
  ANSYS_ROOT: "/opt/ansys/v221"
  CFX_ROOT: "/opt/ansys/v221/CFX"
```

#### 3. 文件上传失败
**症状**: 文件传输中断或失败
**解决方案**:
```yaml
# 调整传输参数
transfer_timeout: 3600  # 增加超时时间
retry_count: 5          # 增加重试次数
```

#### 4. 服务器存储空间不足
**症状**: 磁盘空间不足错误
**解决方案**:
```yaml
# 启用清理功能
cleanup_server_temp: true
keep_server_files: false
```

## 📊 监控和日志

### 启用详细日志
```yaml
# 日志配置
log_level: "DEBUG"
verbose_logging: true
save_logs: true
```

### 监控配置
```yaml
# 监控设置
monitor_interval: 30        # 30秒监控间隔
auto_download_results: true # 自动下载结果
```

## 🔒 安全考虑

### 文件权限
确保服务器上的工作目录有适当的权限：
```bash
# 设置工作目录权限
chmod 755 /path/to/your/workspace/CFX_Jobs
```

### 密码安全
建议使用SSH密钥认证：
```yaml
# 使用SSH密钥
ssh_key: "/path/to/private/key"
ssh_password: ""  # 留空
```

## 📋 配置检查清单

### 服务器端检查
- [ ] CFX软件已安装且可访问
- [ ] 环境变量正确设置
- [ ] 许可证服务器可访问
- [ ] 工作目录有写权限
- [ ] 存储空间充足
- [ ] 🆕 远程CFX路径配置正确

### 客户端检查
- [ ] 网络连接正常
- [ ] SSH认证配置正确
- [ ] 本地CFX文件路径正确
- [ ] 配置文件语法正确
- [ ] 🆕 远程CFX路径参数已设置

---

**使用服务器CFX环境，享受无需本地CFX安装的便捷体验！**

## 🔄 更新日志

- **2025-07-19**: 新增独立步骤执行功能支持
- **2025-07-19**: 新增远程CFX路径配置（`remote_cfx_home`, `remote_cfx_bin_path`）
- **2025-07-19**: 更新配置示例和故障排除指南
- **2025-07-19**: 升级到v2.0.0版本，支持更灵活的服务器CFX环境配置

---

**版本**: 1.0.2 
**环境**: 服务器CFX专用  
**最后更新**: 2025-07-19  
**新功能**: 独立步骤执行、远程CFX路径支持
