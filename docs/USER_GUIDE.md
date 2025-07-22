# CFX自动化系统用户指南 v2.0

## 🚀 快速开始

CFX自动化系统v2.0提供**智能节点分配**、**自动排队管理**和**多调度器支持**，让您的CFX计算任务更加高效。

### 一键安装

```bash
# 方法1: 使用安装脚本 (推荐)
git clone <repository_url>
cd cfx-automation
./install.sh    # Linux/macOS
install.bat     # Windows

# 方法2: 手动安装
pip install -r requirements.txt
```

### 快速配置

1. **选择配置模板**
```bash
# 大学集群 (SLURM + 智能分配)
cp config/local_cfx_university.yaml my_config.yaml

# 组内新集群 (SLURM + 队列管理)  
cp config/local_cfx_new_cluster.yaml my_config.yaml

# 组内老集群 (PBS + 智能分配)
cp config/local_cfx_old_cluster.yaml my_config.yaml
```

2. **配置集群连接**
```yaml
# SSH连接配置
ssh:
  host: "10.16.78.***"        # 集群地址
  username: "your_username"   # 用户名
  key_file: "~/.ssh/id_rsa"   # SSH密钥路径

# 🎯 智能分配配置 (新功能!)
node_allocation:
  enable_node_detection: true     # 启用智能节点检测
  enable_node_allocation: true    # 启用智能分配
  min_cores: 28                   # 最小核心数需求
  queue_strategy_preference: "auto"  # 自动选择队列策略

# CFX环境配置
cfx:
  version: "22.2"
  install_path: "/opt/ansys/cfx"  # 自动检测路径

# 调度器配置
scheduler_type: "SLURM"  # 或 "PBS"
cluster_type: "university"
```

3. **定义计算任务**
```yaml
jobs:
  - name: "optimization_run_1"
    def_file: "wing_optimization.def"
    cores: 28                    # 系统将智能分配最优节点
    memory: "64GB"
    parameters:
      inlet_velocity: 50
      angle_of_attack: 15
  
  - name: "validation_run"
    def_file: "validation.def" 
    cores: 56                    # 自动选择双核节点或单个56核节点
    parameters:
      mesh_density: "fine"
```

### 🎯 一键运行

```bash
# 标准运行 (推荐)
python cfx_automation.py -c my_config.yaml

# 启用详细输出
python cfx_automation.py -c my_config.yaml --verbose

# 仅生成脚本不提交
python cfx_automation.py -c my_config.yaml --dry-run

# 指定队列策略
python cfx_automation.py -c my_config.yaml --queue-strategy parallel
```

## 🔧 详细配置指南

### SSH连接配置

#### 基本SSH配置
```yaml
ssh:
  host: "cluster.university.edu"
  username: "your_username"
  port: 22
  
  # 方法1: SSH密钥认证 (推荐)
  key_file: "~/.ssh/id_rsa"
  
  # 方法2: 密码认证 (不推荐)
  password: "your_password"
  
  # 高级选项
  timeout: 30
  keepalive: 300
  compression: true
```

#### SSH密钥配置
```bash
# 生成SSH密钥对
ssh-keygen -t rsa -b 4096 -f ~/.ssh/cluster_key

# 复制公钥到集群
ssh-copy-id -i ~/.ssh/cluster_key.pub user@cluster.edu

# 在配置中使用
ssh:
  key_file: "~/.ssh/cluster_key"
```

### CFX环境配置

#### 自动检测CFX安装

```yaml
cfx:
  mode: "auto"          # 自动检测CFX安装
  preferred_version: "22.2"  # 首选版本
```

#### 手动指定CFX路径

```yaml
cfx:
  mode: "manual"
  version: "22.2"
  cfx_home: "/opt/ansys_inc/v222/CFX"
  cfx_pre: "/opt/ansys_inc/v222/CFX/bin/cfx5pre"
  cfx_solver: "/opt/ansys_inc/v222/CFX/bin/cfx5solve"
```

#### CFX许可证配置

```yaml
cfx:
  license_server: "license.university.edu"
  license_port: 1055
  license_feature: "cfx_solver"
```

### 作业配置详解

#### 基本作业定义

```yaml
jobs:
  - name: "pressure_study_1000Pa"
    def_file: "base_model.def"
    cores: 28
    memory: "64GB"
    walltime: "24:00:00"
    parameters:
      pressure: 1000
      temperature: 300
```

#### 参数化作业定义

```yaml
# 参数组合
parameter_combinations:
  pressure: [1000, 2000, 3000, 4000]
  velocity: [10, 20, 30]
  
# 自动生成12个作业 (4×3)
job_template:
  name: "study_{pressure}Pa_{velocity}ms"
  def_file: "parametric_model.def"
  cores: 28
  parameters:
    inlet_pressure: "{pressure}"
    inlet_velocity: "{velocity}"
```

### 🧠 智能节点分配配置

#### 基本智能分配设置

```yaml
node_allocation:
  # 启用智能功能
  enable_node_detection: true      # 启用实时节点检测
  enable_node_allocation: true     # 启用智能分配算法
  
  # 资源需求
  min_cores: 28                    # 最小核心数需求
  preferred_memory: "64GB"         # 首选内存大小
  
  # 分配策略
  queue_strategy_preference: "auto"  # auto/parallel/sequential/batch
  allow_overallocation: false       # 禁止过度分配
  
  # 节点选择偏好
  node_selection_strategy: "optimal"  # optimal/balanced/minimal
```

#### 高级分配设置

```yaml
node_allocation:
  # 智能优化选项
  core_efficiency_threshold: 0.8   # 核心利用率阈值
  memory_efficiency_threshold: 0.7  # 内存利用率阈值
  load_balancing: true             # 启用负载均衡
  
  # 节点过滤条件
  exclude_nodes: ["n01", "n02"]   # 排除特定节点
  prefer_nodes: ["n44-n60"]       # 优先使用节点范围
  
  # 故障恢复
  max_allocation_retries: 3        # 最大重试次数
  fallback_strategy: "best_effort" # 降级策略
```

### 📊 排队策略配置

#### 自动策略选择 (推荐)

```yaml
node_allocation:
  queue_strategy_preference: "auto"
  
  # 自动选择规则:
  # 可用节点 >= 作业数 → Parallel策略
  # 可用节点 < 作业数 AND 作业数 <= 8 → Sequential策略  
  # 作业数 > 8 → Batch策略
```

#### 强制指定策略

```yaml
# 强制并行策略
node_allocation:
  queue_strategy_preference: "parallel"
  parallel_settings:
    max_concurrent_jobs: 10
    job_submission_delay: 2  # 秒

# 强制顺序策略
node_allocation:
  queue_strategy_preference: "sequential"
  sequential_settings:
    batch_size: 4           # 每批作业数
    wait_timeout: 3600      # 等待超时(秒)

# 强制批次策略
node_allocation:
  queue_strategy_preference: "batch"
  batch_settings:
    batch_size: 6           # 每批作业数
    overlap_jobs: 1         # 重叠作业数
```

### 🖥️ 调度器配置

#### PBS配置

```yaml
scheduler_type: "PBS"
pbs_settings:
  queue: "batch"              # 队列名称
  priority: "high"            # 作业优先级
  resource_requirements:
    walltime: "24:00:00"      # 运行时间限制
    mem: "64gb"               # 内存需求
  
  # PBS特定选项
  job_array_support: true     # 支持作业数组
  qsub_options: ["-V", "-l nodes=1:ppn=28"]
```

#### SLURM配置

```yaml
scheduler_type: "SLURM"
slurm_settings:
  partition: "cpu"            # 分区名称
  qos: "normal"               # 服务质量
  account: "research_group"   # 账户
  
  # SLURM特定选项
  sbatch_options: ["--exclusive", "--job-name=CFX"]
  constraint: "intel"         # 节点约束
```

## 🎯 智能分配与排队策略详解

### 核心问题解决

#### 问题1: 过度分配问题

**问题描述**: 28核需求被分配44核（28+16双节点）

**解决方案**: 智能单节点优先分配

```text
传统分配:
28核需求 → n44(28核) + n55(16核) = 44核总计 ❌

智能分配:
28核需求 → n44(28核) = 28核精确匹配 ✅
```

#### 问题2: PBS核心数检测错误

**问题描述**: PBS节点显示56核实际只有28核

**解决方案**: np字段优先解析

```text
PBS输出解析:
np=28          ← 优先使用（真实物理核心）
ncpus=56       ← 次要参考（包含超线程）
结果: 准确识别28核 ✅
```

#### 问题3: 缺乏排队管理

**问题描述**: 节点不足时无法自动管理作业队列

**解决方案**: 3种智能排队策略

### 排队策略详细说明

#### Parallel策略（并行策略）

**适用场景**: 可用节点数 ≥ 作业数

**执行方式**: 每个作业独占一个节点，同时提交所有作业

**示例**:
```text
场景: 4个作业，6个可用节点
分配: 
  job1 → n44 (28核)
  job2 → n45 (28核)  
  job3 → n46 (28核)
  job4 → n48 (28核)

脚本生成:
  同时提交: qsub job1.pbs; qsub job2.pbs; qsub job3.pbs; qsub job4.pbs
```

#### Sequential策略（顺序策略）

**适用场景**: 可用节点数 < 作业数 且 作业数 ≤ 8

**执行方式**: 分批提交，前一批完成后自动提交下一批

**示例**:
```text
场景: 8个作业，4个可用节点
分配:
  批次1: job1-4 → 4个节点并行
  批次2: job5-8 → 等待批次1完成后执行

脚本生成:
  第一批: qsub job1.pbs; qsub job2.pbs; qsub job3.pbs; qsub job4.pbs
  监控等待批次1完成...
  第二批: qsub job5.pbs; qsub job6.pbs; qsub job7.pbs; qsub job8.pbs
```

#### Batch策略（批次策略）

**适用场景**: 作业数 > 8

**执行方式**: 智能分批，每批使用所有可用节点

**示例**:
```text
场景: 12个作业，6个可用节点
分配:
  批次1: job1-6  → 6个节点并行
  批次2: job7-12 → 等待批次1完成后执行

脚本生成:
  第一批: 6个作业同时提交
  监控等待批次1完成...
  第二批: 6个作业同时提交
```

## 🔧 命令行使用

### 基本命令

```bash
# 标准执行
python cfx_automation.py -c config.yaml

# 详细输出模式
python cfx_automation.py -c config.yaml --verbose

# 调试模式
python cfx_automation.py -c config.yaml --debug
```

### 智能分配相关命令

```bash
# 查看集群状态
python cfx_automation.py --cluster-status -c config.yaml

# 预览分配方案
python cfx_automation.py -c config.yaml --dry-run --show-allocation

# 强制指定排队策略
python cfx_automation.py -c config.yaml --queue-strategy parallel
python cfx_automation.py -c config.yaml --queue-strategy sequential
python cfx_automation.py -c config.yaml --queue-strategy batch

# 调试节点分配
python cfx_automation.py -c config.yaml --debug-allocation
```

### CFX环境管理命令

```bash
# 检测CFX安装
python cfx_automation.py --detect-cfx

# 验证配置文件
python cfx_automation.py --validate config.yaml

# 显示配置信息
python cfx_automation.py --info config.yaml

# 生成默认配置
python cfx_automation.py --create-config new_config.yaml
```

### 分步执行命令

```bash
# 仅生成脚本
python cfx_automation.py -c config.yaml --step generate

# 仅传输文件
python cfx_automation.py -c config.yaml --step transfer

# 仅提交作业
python cfx_automation.py -c config.yaml --step submit

# 仅监控作业
python cfx_automation.py -c config.yaml --step monitor
```

## 📋 工作流程详解

### 完整工作流程

```text
1. 配置加载与验证
   ├── YAML配置解析
   ├── SSH连接测试
   ├── CFX环境检测
   └── 参数验证

2. 集群状态查询 🆕
   ├── 调度器类型检测 (PBS/SLURM)
   ├── 节点状态查询
   ├── 资源信息解析
   └── 可用节点统计

3. 智能节点分配 🆕
   ├── 作业资源需求分析
   ├── 可用节点匹配
   ├── 分配策略选择 (Parallel/Sequential/Batch)
   ├── 节点分配执行
   └── 分配结果验证

4. CFX脚本生成
   ├── Pre脚本参数替换
   ├── Def文件生成
   ├── 作业脚本生成 (PBS/SLURM)
   └── Unix换行符转换 🆕

5. 文件传输
   ├── 远程目录创建
   ├── 文件上传
   ├── 权限设置
   └── 传输验证

6. 作业提交
   ├── 提交脚本执行
   ├── 作业ID收集
   ├── 排队状态监控 🆕
   └── 提交结果记录

7. 监控与下载
   ├── 作业状态跟踪
   ├── 完成检测
   ├── 结果文件下载
   └── 报告生成
```

### 各步骤详细说明

#### 步骤1: 配置加载与验证

**功能**: 加载和验证配置文件，检查必要参数

**输出示例**:
```text
=== 配置验证 ===
✓ SSH连接配置完整
✓ CFX环境配置有效
✓ 作业参数验证通过
✓ 智能分配配置正确
```

#### 步骤2: 集群状态查询 🆕

**功能**: 实时查询集群状态，为智能分配提供数据

**输出示例**:
```text
=== 集群状态查询 ===
调度器类型: PBS
总节点数: 20
可用节点数: 8
节点详情:
  n44: 28核/64GB 可用
  n45: 28核/64GB 可用
  n46: 28核/64GB 可用
  n48: 28核/64GB 可用
  ...
```

#### 步骤3: 智能节点分配 🆕

**功能**: 根据作业需求和集群状态执行智能分配

**输出示例**:
```text
=== 智能节点分配 ===
作业总数: 6
可用节点数: 8
选择策略: Parallel (并行策略)

分配结果:
  CFX_Job_1000Pa → n44 (28核/64GB)
  CFX_Job_2000Pa → n45 (28核/64GB)
  CFX_Job_3000Pa → n46 (28核/64GB)
  CFX_Job_4000Pa → n48 (28核/64GB)
  CFX_Job_5000Pa → n49 (28核/64GB)
  CFX_Job_6000Pa → n50 (28核/64GB)

✓ 所有作业成功分配节点
```

#### 步骤4: CFX脚本生成

**功能**: 生成CFX Pre脚本、Def文件和调度器脚本

**输出示例**:
```text
=== 脚本生成 ===
✓ Pre脚本: create_def_CFX_Job_1000Pa.pre
✓ Def文件: CFX_Job_1000Pa.def
✓ PBS脚本: CFX_Job_1000Pa.pbs (Unix格式)
✓ 提交脚本: Submit_All.sh
```

#### 步骤5: 文件传输

**功能**: 将所有必要文件传输到集群

**输出示例**:
```text
=== 文件传输 ===
创建远程目录: /home/user/CFX_Project_20240122_143022
上传文件:
  ✓ base_model.cfx (15.2 MB)
  ✓ create_def_CFX_Job_1000Pa.pre (2.1 KB)
  ✓ CFX_Job_1000Pa.pbs (1.5 KB)
  ✓ Submit_All.sh (3.2 KB)
设置权限: 755
```

#### 步骤6: 作业提交

**功能**: 根据排队策略提交作业

**输出示例**:
```text
=== 作业提交 (Parallel策略) ===
提交作业: CFX_Job_1000Pa → 作业ID: 12345
提交作业: CFX_Job_2000Pa → 作业ID: 12346
提交作业: CFX_Job_3000Pa → 作业ID: 12347
提交作业: CFX_Job_4000Pa → 作业ID: 12348
提交作业: CFX_Job_5000Pa → 作业ID: 12349
提交作业: CFX_Job_6000Pa → 作业ID: 12350

✓ 成功提交6个作业
```

#### 步骤7: 监控与下载

**功能**: 监控作业状态并下载结果

**输出示例**:
```text
=== 作业监控 ===
12345: CFX_Job_1000Pa [运行中] n44
12346: CFX_Job_2000Pa [排队中] -
12347: CFX_Job_3000Pa [排队中] -
...

=== 结果下载 ===
✓ CFX_Job_1000Pa_001.res (45.2 MB)
✓ CFX_Job_1000Pa.out (1.2 MB)
```

## 📊 实际使用示例

### 示例1: 压力参数研究

**场景**: 研究4个不同压力值对流场的影响，使用大学SLURM集群

**配置文件** (`pressure_study.yaml`):
```yaml
# 项目信息
project:
  name: "Pressure_Study"
  description: "压力参数对流场影响研究"

# SSH连接
ssh:
  host: "cluster.university.edu"
  username: "student123"
  key_file: "~/.ssh/university_key"

# CFX环境
cfx:
  mode: "auto"
  preferred_version: "22.2"

# 调度器配置
scheduler_type: "SLURM"
slurm_settings:
  partition: "cpu"
  account: "research_group"

# 🎯 智能分配配置
node_allocation:
  enable_node_detection: true
  enable_node_allocation: true
  min_cores: 28
  queue_strategy_preference: "auto"

# 参数化作业
parameter_combinations:
  pressure: [1000, 2000, 3000, 4000]

job_template:
  name: "pressure_{pressure}Pa"
  def_file: "base_model.def"
  cores: 28
  memory: "64GB"
  walltime: "12:00:00"
  parameters:
    inlet_pressure: "{pressure}"
```

**执行命令**:
```bash
python cfx_automation.py -c pressure_study.yaml --verbose
```

**预期输出**:
```text
=== CFX自动化系统v2.0 ===
加载配置: pressure_study.yaml
检测到4个参数化作业

=== 集群状态查询 ===
调度器: SLURM
可用节点: 12个
选择策略: Parallel (并行策略)

=== 智能节点分配 ===
pressure_1000Pa → node-001 (28核)
pressure_2000Pa → node-002 (28核)
pressure_3000Pa → node-003 (28核)
pressure_4000Pa → node-004 (28核)

=== 作业提交 ===
✓ 成功提交4个作业，作业ID: 54321-54324
```

### 示例2: 大量优化研究

**场景**: 12个优化变量组合，使用组内PBS集群，节点资源有限

**配置文件** (`optimization_study.yaml`):
```yaml
project:
  name: "Optimization_Study"

ssh:
  host: "10.16.78.100"
  username: "researcher"
  key_file: "~/.ssh/cluster_key"

# PBS调度器
scheduler_type: "PBS"
pbs_settings:
  queue: "batch"
  walltime: "24:00:00"

# 智能分配 - 强制Sequential策略
node_allocation:
  enable_node_detection: true
  enable_node_allocation: true
  min_cores: 28
  queue_strategy_preference: "sequential"  # 强制顺序策略

# 12个优化作业
parameter_combinations:
  angle: [0, 5, 10, 15]
  velocity: [20, 30, 40]

job_template:
  name: "opt_a{angle}_v{velocity}"
  def_file: "optimization_model.def"
  cores: 28
  parameters:
    angle_of_attack: "{angle}"
    inlet_velocity: "{velocity}"
```

**执行和监控**:
```bash
# 提交作业
python cfx_automation.py -c optimization_study.yaml

# 监控作业状态
python cfx_automation.py -c optimization_study.yaml --step monitor
```

**预期行为**:
```text
=== 集群状态查询 ===
可用节点: 4个 (n44, n45, n46, n48)
作业总数: 12个
选择策略: Sequential (顺序策略)

=== 分批提交 ===
批次1 (4个作业): 立即提交
  opt_a0_v20  → n44
  opt_a5_v20  → n45
  opt_a10_v20 → n46
  opt_a15_v20 → n48

批次2 (4个作业): 等待批次1完成
批次3 (4个作业): 等待批次2完成

监控系统将自动管理后续批次的提交...
```

### 示例3: 混合配置研究

**场景**: 不同核心数需求的混合作业，测试智能分配的适应性

**配置文件** (`mixed_study.yaml`):
```yaml
project:
  name: "Mixed_Core_Study"

# ... SSH和调度器配置 ...

# 智能分配 - 自适应策略
node_allocation:
  enable_node_detection: true
  enable_node_allocation: true
  min_cores: 28
  queue_strategy_preference: "auto"
  node_selection_strategy: "optimal"

# 混合作业定义
jobs:
  - name: "small_model_28c"
    def_file: "small.def"
    cores: 28
    memory: "32GB"
  
  - name: "medium_model_56c" 
    def_file: "medium.def"
    cores: 56
    memory: "64GB"
    
  - name: "large_model_112c"
    def_file: "large.def"
    cores: 112
    memory: "128GB"
```

**智能分配结果**:
```text
=== 智能节点分配 ===
small_model_28c  → n44 (28核精确匹配)
medium_model_56c → n55 (56核精确匹配)
large_model_112c → n01+n02 (56+56核组合)

优化结果:
- 避免了28核→44核的过度分配
- 实现了各作业的最优资源匹配
- 提升整体集群资源利用率
```

## 📊 监控和报告

### 实时监控

#### 作业状态监控

```bash
# 启动监控模式
python cfx_automation.py -c config.yaml --step monitor

# 持续监控直到完成
python cfx_automation.py -c config.yaml --monitor-continuous
```

**监控输出示例**:
```text
=== 作业监控报告 ===
时间: 2024-01-22 14:30:22
总作业数: 6

作业状态统计:
  运行中: 4个
  排队中: 2个
  已完成: 0个
  失败: 0个

详细状态:
┌─────────────────┬────────┬────────┬──────────┬─────────────────┐
│ 作业名称        │ 作业ID │ 状态   │ 节点     │ 运行时间        │
├─────────────────┼────────┼────────┼──────────┼─────────────────┤
│ pressure_1000Pa │ 12345  │ 运行中 │ n44      │ 02:15:30        │
│ pressure_2000Pa │ 12346  │ 运行中 │ n45      │ 02:15:28        │
│ pressure_3000Pa │ 12347  │ 运行中 │ n46      │ 02:15:25        │
│ pressure_4000Pa │ 12348  │ 运行中 │ n48      │ 02:15:22        │
│ pressure_5000Pa │ 12349  │ 排队中 │ -        │ -               │
│ pressure_6000Pa │ 12350  │ 排队中 │ -        │ -               │
└─────────────────┴────────┴────────┴──────────┴─────────────────┘

下次检查: 60秒后
```

#### 集群资源监控

```bash
# 查看集群状态
python cfx_automation.py --cluster-status -c config.yaml
```

**输出示例**:
```text
=== 集群资源状态 ===
调度器: PBS
集群总览:
  总节点数: 20
  可用节点: 8
  忙碌节点: 12
  离线节点: 0

节点详情:
┌──────┬────────┬────────┬──────────┬─────────────────┐
│ 节点 │ 状态   │ 核心数 │ 内存     │ 当前作业        │
├──────┼────────┼────────┼──────────┼─────────────────┤
│ n44  │ 运行中 │ 28     │ 64GB     │ pressure_1000Pa │
│ n45  │ 运行中 │ 28     │ 64GB     │ pressure_2000Pa │
│ n46  │ 可用   │ 28     │ 64GB     │ -               │
│ n48  │ 可用   │ 28     │ 64GB     │ -               │
│ n49  │ 可用   │ 28     │ 64GB     │ -               │
│ n50  │ 可用   │ 28     │ 64GB     │ -               │
└──────┴────────┴────────┴──────────┴─────────────────┘
```

### 详细报告

#### 执行报告

**系统自动生成的报告包括**:

1. **配置报告** (`config_report.json`)
```json
{
  "project_name": "Pressure_Study",
  "execution_time": "2024-01-22T14:30:22",
  "ssh_connection": {
    "host": "cluster.university.edu",
    "connection_status": "success"
  },
  "cfx_environment": {
    "version": "22.2",
    "path": "/opt/ansys_inc/v222/CFX"
  },
  "intelligent_allocation": {
    "enabled": true,
    "strategy_used": "parallel",
    "nodes_allocated": 4,
    "efficiency": 0.95
  }
}
```

2. **分配报告** (`allocation_report.json`)
```json
{
  "allocation_summary": {
    "total_jobs": 4,
    "available_nodes": 12,
    "strategy_selected": "parallel",
    "allocation_time": "2.3s"
  },
  "job_allocations": [
    {
      "job_name": "pressure_1000Pa",
      "allocated_node": "n44",
      "cores_requested": 28,
      "cores_allocated": 28,
      "efficiency": 1.0
    }
  ],
  "cluster_state": {
    "query_time": "2024-01-22T14:30:20",
    "total_nodes": 20,
    "available_nodes": 12,
    "node_details": [...]
  }
}
```

3. **提交报告** (`submission_report.json`)
```json
{
  "submission_summary": {
    "total_jobs_submitted": 4,
    "successful_submissions": 4,
    "failed_submissions": 0,
    "submission_time": "2024-01-22T14:30:25"
  },
  "job_submissions": [
    {
      "job_name": "pressure_1000Pa",
      "job_id": "12345",
      "submission_status": "success",
      "allocated_node": "n44"
    }
  ]
}
```

4. **监控报告** (`monitoring_report.json`)
```json
{
  "monitoring_summary": {
    "start_time": "2024-01-22T14:30:25",
    "end_time": "2024-01-22T18:45:12",
    "total_monitoring_time": "4h 14m 47s",
    "completed_jobs": 4,
    "failed_jobs": 0
  },
  "job_timelines": [
    {
      "job_name": "pressure_1000Pa",
      "job_id": "12345",
      "submitted": "2024-01-22T14:30:25",
      "started": "2024-01-22T14:32:10",
      "completed": "2024-01-22T18:15:33",
      "runtime": "3h 43m 23s",
      "status": "completed"
    }
  ]
}
```

#### 报告查看和分析

```bash
# 查看最新执行报告
python cfx_automation.py --show-reports

# 查看特定类型报告
python cfx_automation.py --show-report allocation

# 生成汇总报告
python cfx_automation.py --generate-summary config.yaml
```

## 🛠️ 故障排除

### 智能分配问题

#### 问题1: 仍然出现过度分配

**现象**: 28核需求仍被分配44核

**可能原因**:
- 智能分配未启用
- 配置文件错误
- 集群状态查询失败

**解决方案**:
```bash
# 1. 检查配置
node_allocation:
  enable_node_allocation: true  # 确保已启用
  allow_overallocation: false  # 确保禁止过度分配

# 2. 验证集群查询
python cfx_automation.py --cluster-status -c config.yaml

# 3. 调试分配过程
python cfx_automation.py -c config.yaml --debug-allocation
```

#### 问题2: PBS核心数检测错误

**现象**: 节点显示错误的核心数（如28核显示为56核）

**解决方案**:
```bash
# 手动验证节点信息
ssh user@cluster.edu "pbsnodes -a | grep -A 10 n44"

# 检查np字段优先级
# 系统应该优先使用np=28而不是ncpus=56
```

#### 问题3: 策略选择不当

**现象**: 系统选择的排队策略不符合预期

**解决方案**:
```yaml
# 强制指定策略
node_allocation:
  queue_strategy_preference: "parallel"  # 或 sequential/batch

# 或使用命令行
python cfx_automation.py -c config.yaml --queue-strategy sequential
```

### PBS脚本格式问题

#### 问题: "DOS/Windows text format"错误

**现象**: `qsub: script is written in DOS/Windows text format`

**解决方案**: 系统已自动修复，如仍有问题可手动转换:
```bash
# 手动转换换行符
dos2unix *.pbs

# 验证文件格式
file script.pbs  # 应显示: script.pbs: ASCII text
```

### 连接和权限问题

#### SSH连接问题

**常见错误**:
```text
ssh: connect to host cluster.edu port 22: Connection refused
Permission denied (publickey)
```

**解决方案**:
```bash
# 1. 测试SSH连接
ssh -i ~/.ssh/cluster_key user@cluster.edu

# 2. 检查密钥权限
chmod 600 ~/.ssh/cluster_key

# 3. 验证公钥是否在服务器上
ssh-copy-id -i ~/.ssh/cluster_key.pub user@cluster.edu
```

#### CFX许可证问题

**常见错误**:
```text
CFX: License checkout failed
```

**解决方案**:
```yaml
# 配置许可证服务器
cfx:
  license_server: "license.university.edu"
  license_port: 1055
  
# 或设置环境变量
environment_variables:
  ANSYSLMD_LICENSE_FILE: "1055@license.university.edu"
```

### 调试和诊断工具

#### 详细调试模式

```bash
# 启用详细调试
python cfx_automation.py -c config.yaml --debug --verbose

# 分步调试
python cfx_automation.py -c config.yaml --step generate --debug
python cfx_automation.py -c config.yaml --step transfer --debug
```

#### 配置验证工具

```bash
# 验证配置完整性
python cfx_automation.py --validate config.yaml

# 检查CFX环境
python cfx_automation.py --detect-cfx --verbose

# 测试集群连接
python cfx_automation.py --test-connection config.yaml
```

#### 日志文件分析

**系统日志位置**:
```text
logs/
├── cfx_automation.log      # 主日志
├── allocation_debug.log    # 分配调试日志
├── ssh_operations.log      # SSH操作日志
└── error_traceback.log     # 错误追踪日志
```

**查看关键日志**:
```bash
# 查看分配日志
tail -f logs/allocation_debug.log

# 查看错误日志
grep "ERROR" logs/cfx_automation.log

# 查看SSH连接日志
grep "SSH" logs/ssh_operations.log
```

## 🎯 最佳实践

### 配置优化建议

#### 1. SSH连接优化

```yaml
ssh:
  # 使用SSH密钥而非密码
  key_file: "~/.ssh/cluster_key"
  
  # 启用连接复用
  keepalive: 300
  compression: true
  
  # 设置合理超时
  timeout: 30
```

#### 2. 智能分配优化

```yaml
node_allocation:
  # 启用所有智能功能
  enable_node_detection: true
  enable_node_allocation: true
  
  # 使用自动策略选择
  queue_strategy_preference: "auto"
  
  # 禁止过度分配
  allow_overallocation: false
  
  # 设置资源利用率阈值
  core_efficiency_threshold: 0.8
```

#### 3. 作业配置优化

```yaml
# 使用参数化作业而非重复定义
parameter_combinations:
  pressure: [1000, 2000, 3000]
  velocity: [10, 20, 30]

job_template:
  name: "study_p{pressure}_v{velocity}"
  def_file: "template.def"
  cores: 28
  
# 设置合理的资源需求
resources:
  cores: 28              # 匹配实际需求
  memory: "64GB"         # 避免内存不足
  walltime: "12:00:00"   # 设置合理时间限制
```

### 性能优化建议

#### 1. 大量作业处理

**对于大量作业（>50个）**:
```yaml
node_allocation:
  queue_strategy_preference: "batch"
  batch_settings:
    batch_size: 10        # 合理的批次大小
    overlap_jobs: 2       # 允许作业重叠
```

#### 2. 网络传输优化

```yaml
transfer_settings:
  compression: true       # 启用传输压缩
  parallel_transfers: 4   # 并行传输数
  retry_attempts: 3       # 重试次数
```

#### 3. 监控频率优化

```yaml
monitoring:
  check_interval: 300     # 5分钟检查一次
  parallel_monitoring: true
  max_monitoring_time: 86400  # 24小时最大监控时间
```

### 安全性建议

#### 1. 认证安全

```bash
# 使用专门的集群密钥
ssh-keygen -t rsa -b 4096 -f ~/.ssh/cluster_key

# 设置严格权限
chmod 600 ~/.ssh/cluster_key
chmod 644 ~/.ssh/cluster_key.pub

# 定期更新密钥
```

#### 2. 配置安全

```yaml
# 避免在配置文件中存储密码
ssh:
  password: null          # 不使用密码认证
  key_file: "~/.ssh/cluster_key"

# 使用环境变量存储敏感信息
environment_variables:
  CLUSTER_USERNAME: "${USER}"
  LICENSE_SERVER: "${ANSYS_LICENSE_SERVER}"
```

### 维护和监控建议

#### 1. 定期检查

```bash
# 每周检查集群状态
python cfx_automation.py --cluster-status -c config.yaml

# 验证配置文件
python cfx_automation.py --validate config.yaml

# 清理旧文件
python cfx_automation.py --cleanup --days 30
```

#### 2. 日志管理

```bash
# 定期清理日志
find logs/ -name "*.log" -mtime +30 -delete

# 监控错误日志
grep "ERROR\|CRITICAL" logs/cfx_automation.log | tail -20
```

#### 3. 性能监控

```python
# 在配置中启用性能指标
performance:
  enable_metrics: true
  save_timings: true
  generate_reports: true
```

---

**CFX自动化系统v2.0 - 智能、高效、可靠的CFX集群计算解决方案** 🚀
