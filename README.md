# CFX自动化计算系统

一个完整的Python CFX自动化解决方案，专为ANSYS CFX计算流体力学(CFD)集群作业管理而设计。该系统集成了**智能节点分配策略**、**实时集群状态查询**、**自动脚本生成**、**排队策略管理**、**作业监控**和**结果自动下载**等功能，全面支持PBS和SLURM调度系统。

## 🎯 主要功能

### 🔥 核心特性

- **🧠 智能节点分配**: 单节点优先分配，避免资源浪费（解决28核需求被分配44核问题）
- **🔍 实时集群查询**: 准确解析PBS节点信息（np字段优先，修复核心数错误问题）
- **📊 智能排队策略**: 3种排队策略（parallel/sequential/batch）自动适应节点资源
- **📄 多调度器支持**: 完整支持PBS/SLURM，自动生成正确的提交脚本
- **🚀 一键式工作流程**: 连接→查询→分配→生成→提交→监控
- **💻 用户友好界面**: 命令行工具和YAML配置文件管理
- **🔧 Unix兼容性**: PBS脚本使用Unix换行符，解决DOS/Windows格式问题

### 🎯 排队策略智能管理

- **📋 Parallel策略**: 节点充足时，每个作业分配独立节点
- **⚡ Sequential策略**: 节点不足时，作业依次执行避免冲突
- **📦 Batch策略**: 大量作业时，分批处理优化资源利用
- **🤖 自动策略选择**: 根据可用节点数和作业数量智能选择最优策略
- **🔄 动态节点追踪**: 实时更新已分配节点，避免重复分配
- **⚖️ 负载均衡**: 智能分散作业到不同节点，提高并行效率

### 🔄 作业监控与结果管理

- **🎯 智能作业监控**: 自动检测作业完成状态，支持PBS/SLURM双调度系统
- **📦 自动结果下载**: 计算完成后自动下载.res、.out、.log等结果文件
- **🕒 灵活监控策略**: 可配置监控间隔、超时时间和文件类型
- **📍 本地目录映射**: 结果文件自动下载到对应的本地目录
- **📋 监控报告生成**: 生成详细的监控日志和执行报告

### 🛠️ CFX环境管理

- **智能CFX环境检测**: 自动检测本地和服务器CFX安装
- **双环境支持**: 支持本地CFX生成def文件或完全服务器CFX环境
- **参数化批量处理**: 基于压力参数自动生成多个CFX算例
- **文件传输管理**: 智能文件上传/下载和传输验证
- **跨平台兼容**: 处理Windows（本地）与Linux（服务器）路径差异

## 📁 项目结构

```text
CFX_Automation/
├── src/                          # 源代码
│   ├── __init__.py
│   ├── config.py                 # 配置管理
│   ├── cfx.py                    # CFX核心功能
│   ├── cluster_query.py          # 集群查询与节点分配
│   ├── script_generator.py       # 智能脚本生成
│   ├── transfer.py               # 文件传输管理
│   ├── job_monitor.py            # 作业监控
│   ├── workflow_orchestrator.py  # 工作流编排
│   ├── slurm.py                  # SLURM调度器支持
│   └── utils/                    # 工具模块
│       └── cfx_detector.py       # CFX环境检测
├── templates/                    # 模板文件
│   ├── create_def.pre.j2         # CFX Pre脚本模板
│   ├── CFX_Group_Cluster.slurm.j2 # SLURM作业模板
│   ├── CFX_Group_PBS.pbs.j2      # PBS作业模板
│   ├── Submit_All.sh.j2          # 批量提交脚本模板
│   └── Submit_INI.sh.j2          # 初始化提交模板
├── config/                       # 配置文件
│   ├── local_cfx_university.yaml # 学校集群配置（PBS）
│   ├── local_cfx_new_cluster.yaml # 组内新集群配置（SLURM）
│   ├── local_cfx_old_cluster.yaml # 组内老集群配置（PBS）
│   └── queue_test_config.yaml    # 排队策略测试配置
├── docs/                         # 完整文档
│   ├── USER_GUIDE.md            # 用户指南
│   ├── FEATURES.md              # 功能特性
│   ├── INSTALLATION.md          # 安装指南
│   ├── ARCHITECTURE.md          # 系统架构
│   └── ...                     # 更多文档
├── tests/                        # 测试文件
├── report/                       # 执行报告
├── main.py                       # 主程序入口
├── requirements.txt              # 依赖包
└── README.md                     # 项目说明
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository_url>
cd CFX_Automation

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置设置

运行程序创建示例配置：

```bash
python main.py
```

选择 `y` 创建示例配置文件，然后编辑 `config/` 目录下的配置文件：

- `local_cfx_university.yaml` - 学校集群配置（PBS调度器）
- `local_cfx_new_cluster.yaml` - 组内新集群配置（SLURM调度器）
- `local_cfx_old_cluster.yaml` - 组内老集群配置（PBS调度器）
- `queue_test_config.yaml` - 排队策略测试配置

### 3. 核心功能演示

#### 🔧 智能节点分配与排队策略

```bash
# 测试智能排队策略（自动选择最优策略）
python main.py --run config/queue_test_config.yaml --steps connect_server query_cluster generate_scripts

# 仅查询集群状态（验证节点信息）
python main.py --run config/queue_test_config.yaml --steps connect_server query_cluster

# 单独生成脚本（测试排队策略）
python main.py --run config/queue_test_config.yaml --steps generate_scripts
```

**系统自动解决的问题：**

- ✅ **28核需求被分配44核问题** → 智能单节点优先分配
- ✅ **节点核心数检测错误** → np字段优先，避免status中ncpus覆盖
- ✅ **节点不足时的排队管理** → 3种策略自动适应（parallel/sequential/batch）
- ✅ **PBS脚本DOS格式问题** → 强制Unix换行符，避免提交错误

#### 📊 排队策略详解

- **Parallel策略**: 节点充足时，每个作业独立节点
- **Sequential策略**: 节点不足时，作业依次执行
- **Batch策略**: 大量作业时，分批处理（如4作业分2批）

### 4. 基本使用

```bash
# 使用压力参数列表运行
python main.py --config config/local_cfx_university.yaml --pressures 2187 2189 2191

# 使用作业配置文件运行
python main.py --config config/local_cfx_new_cluster.yaml --jobs example_jobs.json

# 单步执行（调试用）
python main.py --config config.yaml --mode step --step query_cluster

# 干运行（仅生成脚本不执行）
python main.py --config config.yaml --pressures 2187 2189 --dry-run
```

## ⚙️ 配置说明

### 主要配置项

```yaml
# CFX环境配置
cfx_mode: "local"                    # local/server - CFX运行模式
auto_detect_cfx: true                # 自动检测CFX路径
remote_cfx_home: "/opt/ansys_inc/v231/CFX"

# 集群配置
cluster_type: "university"           # university/group_new/group_old
scheduler_type: "PBS"                # SLURM/PBS
enable_node_detection: true          # 是否启用节点检测
enable_node_allocation: true         # 是否启用智能分配

# 服务器连接
ssh_host: "cluster.university.edu"
ssh_user: "your_username"
remote_base_path: "/home/your_username/CFX_Jobs"

# 作业参数
pressure_list: [2187, 2189, 2191]   # 压力参数
partition: "cpu-low"                 # SLURM分区
tasks_per_node: 28                   # 每节点任务数（推荐28）
min_cores: 28                        # 最小核心数要求

# 排队策略配置
queue_strategy_preference: "auto"    # auto/parallel/sequential/batch
force_queue_strategy: null           # 强制使用特定策略（可选）
```

## 💡 核心特性详解

### 🧠 智能节点分配

系统会根据集群实际状态和作业需求，智能选择最优的节点分配策略：

#### 分配优先级

1. **单节点优先**: 优先选择满足需求的单节点（如28核→选择28核节点）
2. **避免浪费**: 避免过度分配（28核需求不会分配到44核）
3. **负载均衡**: 智能分散作业到不同节点
4. **实时更新**: 动态追踪已分配节点，避免重复分配

#### 排队策略自动选择

```text
可用节点数 >= 作业数  →  Parallel策略（每作业独立节点）
可用节点数 < 作业数   →  Sequential策略（依次执行）
作业数 > 8个         →  Batch策略（分批处理）
```

### 🔍 实时集群查询

#### PBS节点信息准确解析

```bash
# 修复前：错误使用status中的ncpus（可能是56）
# 修复后：优先使用np字段（正确的28）

节点信息：
  name: n54
  np: 28          ← 正确的核心数（优先使用）
  status: ncpus=56 ← 错误的核心数（忽略）
  state: free
```

#### 集群状态实时同步

- 实时查询节点状态（free/allocated/down）
- 准确获取可用节点列表
- 智能过滤不可用节点
- 支持PBS和SLURM双调度系统

### 📄 多调度器脚本生成

#### PBS调度器支持

```bash
# 生成PBS脚本（.pbs）
qsub job_2300.pbs

# 查看队列状态
qstat -u $USER

# 取消作业
qdel <JOB_ID>
```

#### SLURM调度器支持

```bash
# 生成SLURM脚本（.slurm）
sbatch job_2300.slurm

# 查看队列状态
squeue -u $USER

# 取消作业
scancel <JOB_ID>
```

#### Unix兼容性

- 所有脚本使用Unix换行符（LF）
- 避免"DOS/Windows text format"错误
- 确保PBS/SLURM正确识别脚本格式

## 📊 监控与报告

### 执行报告

系统会生成详细的执行报告，包含：

```json
{
  "execution_summary": {
    "total_jobs": 4,
    "successful_submissions": 4,
    "execution_duration_seconds": 45,
    "queue_strategy_used": "parallel",
    "nodes_allocated": ["n44", "n45", "n46", "n48"]
  },
  "cluster_status": {
    "total_nodes": 23,
    "available_nodes": 16,
    "node_allocation_efficiency": "100%"
  }
}
```

### 监控报告

作业监控过程中生成的报告：

```json
{
  "monitoring_summary": {
    "total_monitored_jobs": 4,
    "completed_jobs": 4,
    "failed_jobs": 0,
    "monitoring_duration": "2h 15m",
    "average_job_time": "32m"
  },
  "job_details": [
    {
      "job_id": "50198.hn",
      "pressure": 2300,
      "status": "completed",
      "runtime": "35m 12s",
      "node": "n44"
    }
  ]
}
```

## 🔧 模板系统

### 模板特性

系统使用Jinja2模板引擎，支持：

- 动态参数替换
- 条件逻辑（if/else）
- 循环结构（for loops）
- 模板继承
- 自定义过滤器

#### 可用模板

- `create_def.pre.j2` - CFX Pre脚本模板
- `CFX_Group_Cluster.slurm.j2` - SLURM作业模板
- `CFX_Group_PBS.pbs.j2` - PBS作业模板
- `Submit_All.sh.j2` - 批量提交脚本模板

#### 创建自定义模板

```bash
# 复制现有模板
cp templates/CFX_Group_PBS.pbs.j2 templates/my_custom.pbs.j2

# 编辑模板
nano templates/my_custom.pbs.j2

# 在配置中指定自定义模板
template_file: "my_custom.pbs.j2"
```

#### 模板参数示例

```yaml
template_vars:
  pressure: 2300
  job_name: "CFX_Job_2300"
  walltime: "24:00:00"
  nodes: "n44:ppn=28"
  cfx_solver_path: "/opt/ansys_inc/v231/CFX/bin/cfx5solve"
  mpi_type: "Intel MPI Distributed Parallel"
```

## 📚 文档

完整文档位于 `docs/` 目录：

- [用户指南](./docs/USER_GUIDE.md)
- [功能特性](./docs/FEATURES.md)
- [安装指南](./docs/INSTALLATION.md)
- [系统架构](./docs/ARCHITECTURE.md)
- [模板指南](./docs/TEMPLATE_GUIDE.md)
- [故障排除](./docs/TROUBLESHOOTING.md)

## 🛠️ 开发指南

### 项目依赖

```bash
pip install -r requirements.txt
```

主要依赖包：

- `paramiko` - SSH连接和文件传输
- `jinja2` - 模板引擎
- `pyyaml` - YAML配置文件解析
- `requests` - HTTP请求（可选）

### 代码结构

- `src/config.py` - 配置管理和验证
- `src/cluster_query.py` - 集群状态查询和节点分配
- `src/script_generator.py` - 智能脚本生成
- `src/workflow_orchestrator.py` - 工作流程编排

### 扩展开发

要添加新的调度器支持：

1. 在 `cluster_query.py` 中添加新的查询方法
2. 在 `script_generator.py` 中添加对应的脚本生成逻辑
3. 创建相应的模板文件
4. 更新配置文件schema

## 🐛 故障排除

### 常见问题

#### 1. 节点分配问题

**问题**: "28核需求被分配44核"

**解决**: 
- 启用智能分配: `enable_node_allocation: true`
- 设置最小核心数: `min_cores: 28`
- 系统会自动选择单节点分配

#### 2. PBS脚本格式错误

**问题**: "qsub: script is written in DOS/Windows text format"

**解决**: 
- 系统已自动修复，使用Unix换行符
- 确保使用最新版本的脚本生成器

#### 3. 排队策略选择

**问题**: 不知道选择哪种排队策略

**解决**:
- 使用 `queue_strategy_preference: "auto"`
- 系统会根据集群状态自动选择最优策略

#### 4. 集群连接问题

**问题**: SSH连接失败

**解决**:
```yaml
# 检查配置
ssh_host: "正确的集群地址"
ssh_user: "正确的用户名"
ssh_password: "密码或留空使用密钥"
ssh_key: "密钥文件路径（可选）"
```

### 调试模式

```bash
# 单步执行
python main.py --config config.yaml --steps connect_server
python main.py --config config.yaml --steps query_cluster
python main.py --config config.yaml --steps generate_scripts

# 查看详细日志
python main.py --config config.yaml --verbose
```

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

---

**CFX自动化计算系统** - 让CFX集群计算更简单、更智能！🚀
