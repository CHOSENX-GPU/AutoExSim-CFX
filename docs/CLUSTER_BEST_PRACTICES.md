# 集群配置最佳实践

## 🎯 概述

本文档提供CFX自动化系统在不同类型集群环境中的配置最佳实践，包括性能优化、资源管理、作业调度和故障排除等方面的建议。

## 📚 目录

1. [集群类型概述](#集群类型概述)
2. [学校集群配置](#学校集群配置)
3. [组内新集群配置](#组内新集群配置)
4. [组内老集群配置](#组内老集群配置)
5. [性能优化策略](#性能优化策略)
6. [资源管理](#资源管理)
7. [监控和调试](#监控和调试)
8. [故障排除](#故障排除)
9. [安全考虑](#安全考虑)

---

## 🏛️ 集群类型概述

### 集群分类

CFX自动化系统支持三种主要集群类型：

| 集群类型 | 调度系统 | 特点 | 适用场景 |
|---------|---------|------|----------|
| **university** | SLURM | 共享资源，标准化管理 | 学校公共集群 |
| **group_new** | SLURM | 专用资源，智能分配 | 新建课题组集群 |
| **group_old** | PBS | 传统管理，人工配置 | 传统集群环境 |

### 配置选择决策树

```
开始
  ├─ 是否为学校公共集群？
  │   └─ 是 → university配置
  └─ 否
      ├─ 使用SLURM调度器？
      │   └─ 是 → group_new配置
      └─ 否（PBS/其他）→ group_old配置
```

---

## 🏫 学校集群配置

### 特点分析

- **共享环境**: 多用户竞争资源
- **标准化配置**: 统一的软件环境
- **资源限制**: 作业数量和时间限制
- **队列管理**: 多个分区和QoS策略

### 推荐配置

```yaml
# 学校集群标准配置
cluster_type: "university"
scheduler_type: "SLURM"

# 关键设置
enable_node_detection: false        # 不启用节点检测
enable_node_allocation: false       # 不启用智能分配
enable_monitoring: true             # 启用监控

# SLURM作业设置
job_settings:
  partition: "cpu"                   # 使用CPU分区
  qos: "normal"                      # 正常优先级
  time_limit: "24:00:00"            # 24小时限制
  tasks_per_node: 32                # 标准节点配置
  memory_per_task: "2G"             # 保守内存设置
  
# 作业管理
max_concurrent_jobs: 5              # 限制并发作业数
job_submit_delay: 5                 # 增加提交间隔
max_queue_jobs: 20                  # 队列限制

# 监控配置
monitoring:
  check_interval_seconds: 120       # 较长监控间隔
  max_monitoring_duration_hours: 72 # 扩展监控时间
  
# 文件传输
transfer_retry_times: 5             # 增加重试次数
transfer_timeout: 1200              # 更长超时时间
```

### 分区选择策略

```yaml
# 常见学校集群分区配置
partition_strategies:
  cpu:
    description: "标准CPU计算分区"
    max_time: "24:00:00"
    max_nodes: 4
    typical_queue: "medium"
    
  cpu-long:
    description: "长时间CPU计算"
    max_time: "72:00:00" 
    max_nodes: 2
    typical_queue: "long"
    
  gpu:
    description: "GPU加速计算"
    max_time: "12:00:00"
    max_nodes: 1
    typical_queue: "short"
    
  debug:
    description: "调试和测试"
    max_time: "2:00:00"
    max_nodes: 1
    typical_queue: "immediate"

# 分区选择逻辑
partition_selection:
  - condition: "estimated_time < 2h"
    partition: "debug"
  - condition: "estimated_time < 24h"
    partition: "cpu"
  - condition: "estimated_time > 24h"
    partition: "cpu-long"
```

### QoS配置

```yaml
# 质量服务配置
qos_settings:
  debug:
    priority: 1000
    max_time: "2:00:00"
    max_submit_jobs: 5
    
  normal:
    priority: 100
    max_time: "24:00:00"
    max_submit_jobs: 50
    
  long:
    priority: 50
    max_time: "72:00:00"
    max_submit_jobs: 10
```

---

## 🔬 组内新集群配置

### 特点分析

- **专用资源**: 课题组专用节点
- **灵活配置**: 可自定义调度策略
- **智能分配**: 支持节点检测和分配
- **高性能**: 针对CFD优化的硬件

### 推荐配置

```yaml
# 组内新集群配置
cluster_type: "group_new"
scheduler_type: "SLURM"

# 智能功能
enable_node_detection: true         # 启用节点检测
enable_node_allocation: true        # 启用智能分配
allocation_strategy: "hybrid"       # 混合分配策略

# 节点查询配置
node_query:
  target_nodes: ["node001", "node002", "node003", "node004"]
  max_jobs_per_node: 2              # 每节点最大作业数
  min_memory_gb: 64                 # 最小内存要求
  min_cpu_cores: 32                 # 最小CPU核心数
  max_cpu_load: 0.8                 # 最大CPU负载

# 高性能设置
job_settings:
  partition: "compute"
  tasks_per_node: 64                # 高密度计算
  memory_per_task: "4G"             # 充足内存
  time_limit: "48:00:00"            # 长时间计算
  
# 并发控制
max_concurrent_jobs: 10             # 更多并发作业
job_submit_delay: 2                 # 短提交间隔
max_queue_jobs: 50                  # 大队列容量

# 优化监控
monitoring:
  check_interval_seconds: 60        # 频繁监控
  detailed_logging: true            # 详细日志
  performance_tracking: true       # 性能跟踪
```

### 智能分配策略

```yaml
# 分配策略详细配置
allocation_strategies:
  hybrid:
    description: "根据负载智能选择策略"
    conditions:
      - condition: "available_nodes >= total_jobs"
        strategy: "batch_allocation"
      - condition: "cpu_intensive_jobs > 0.7"
        strategy: "node_reuse"
      - default: "smart_queue"
        
  batch_allocation:
    description: "均匀分配到不同节点"
    max_jobs_per_node: 1
    prefer_idle_nodes: true
    
  node_reuse:
    description: "优先填满单个节点"
    fill_ratio: 0.9
    memory_threshold: 0.8
    
  smart_queue:
    description: "智能排队和负载均衡"
    load_balancing: true
    queue_prediction: true
```

### 性能调优

```yaml
# CFX专用优化
cfx_optimization:
  solver_settings:
    parallel_environment: "intel_mpi"
    memory_model: "distributed"
    interconnect: "infiniband"
    
  performance_tuning:
    partition_method: "metis"
    communication_optimization: true
    memory_allocation: "optimized"
    
# 网络配置
network_settings:
  mpi_implementation: "intel_mpi"
  fabric: "infiniband"
  bandwidth_optimization: true
  latency_reduction: true
```

---

## 🏗️ 组内老集群配置

### 特点分析

- **PBS调度**: 传统PBS作业管理系统
- **手动配置**: 需要人工指定节点
- **兼容性**: 支持较老的软件版本
- **稳定性**: 成熟稳定的环境

### 推荐配置

```yaml
# 组内老集群配置
cluster_type: "group_old"
scheduler_type: "PBS"

# PBS特有设置
enable_node_detection: true         # 仍可启用检测
enable_node_allocation: true        # 智能分配有效
allocation_strategy: "node_reuse"   # 适合PBS的策略

# PBS作业设置
job_settings:
  queue: "batch"                     # 批处理队列
  nodes: 1                           # 节点数量
  ppn: 32                           # 每节点进程数
  walltime: "24:00:00"              # 墙钟时间
  mem: "64gb"                       # 内存规格
  
# 节点配置
node_specification:
  node_list: ["node01", "node02", "node03"]
  node_properties: ["intel", "infiniband"]
  exclusive_access: false           # 非独占访问

# 兼容性设置
compatibility:
  pbs_version: "torque"             # PBS版本
  legacy_commands: true             # 支持传统命令
  shell_environment: "bash"        # Shell环境
```

### PBS作业脚本优化

```bash
# PBS作业脚本最佳实践
#!/bin/bash
#PBS -N CFX_Job
#PBS -q batch
#PBS -l nodes=2:ppn=32:intel
#PBS -l walltime=24:00:00
#PBS -l mem=128gb
#PBS -j oe
#PBS -m abe
#PBS -M user@domain.com

# 环境设置
module load ansys/22.1
module load intel-mpi/2019

# 工作目录
cd $PBS_O_WORKDIR

# CFX求解器执行
export MPI_ROOT=/opt/intel/mpi
export CFX_ROOTDIR=/opt/ansys_inc/v221/CFX

# 并行设置
export OMP_NUM_THREADS=1
export MPI_BUFFER_SIZE=20000000

# 执行CFX
cfx5solve -def input.def -par-local -partition $PBS_NP
```

---

## ⚡ 性能优化策略

### 1. CFX求解器优化

```yaml
# CFX性能调优
cfx_performance:
  parallel_settings:
    partition_method: "automatic"    # 自动分区
    partition_size_factor: 1.0      # 分区大小因子
    memory_allocation: "high"       # 高内存分配
    
  solver_optimization:
    advection_scheme: "high_resolution"
    turbulence_numerics: "first_order"  # 初始使用一阶
    convergence_acceleration: true
    
  numerical_settings:
    linear_solver: "multigrid"
    preconditioner: "ilu"
    convergence_criteria: "tight"
```

### 2. 内存优化

```yaml
# 内存使用优化
memory_optimization:
  estimation:
    base_memory_per_million_cells: 2.5  # GB
    safety_factor: 1.3
    parallel_overhead: 0.2
    
  allocation_strategy:
    distributed_memory: true
    shared_memory_regions: false
    memory_pool_size: "80%"
    
  monitoring:
    memory_usage_alerts: true
    swap_usage_threshold: 0.1
    oom_prevention: true
```

### 3. I/O优化

```yaml
# 输入输出优化
io_optimization:
  result_files:
    compression: true
    selective_output: true
    binary_format: true
    
  parallel_io:
    enable_parallel_io: true
    io_buffer_size: "64MB"
    stripe_count: 4
    
  temporary_files:
    tmp_directory: "/fast_storage/tmp"
    cleanup_policy: "aggressive"
    local_storage_preference: true
```

### 4. 网络优化

```yaml
# 网络和通信优化
network_optimization:
  mpi_settings:
    implementation: "intel_mpi"
    fabric: "infiniband"
    eager_threshold: 32768
    rendezvous_threshold: 131072
    
  bandwidth_optimization:
    message_aggregation: true
    compression: false  # 通常不推荐
    buffer_optimization: true
    
  latency_reduction:
    polling_mode: true
    interrupt_mode: false
    cpu_affinity: true
```

---

## 📊 资源管理

### 1. 资源监控

```yaml
# 资源监控配置
resource_monitoring:
  system_metrics:
    cpu_usage: true
    memory_usage: true
    disk_io: true
    network_io: true
    gpu_usage: true  # 如果适用
    
  cfx_specific_metrics:
    convergence_rate: true
    residual_trends: true
    mass_imbalance: true
    solver_performance: true
    
  alerting:
    high_cpu_threshold: 0.95
    high_memory_threshold: 0.9
    slow_convergence_alert: true
    stalled_job_detection: true
```

### 2. 负载均衡

```yaml
# 负载均衡策略
load_balancing:
  automatic_balancing: true
  
  balancing_criteria:
    cpu_load_weight: 0.4
    memory_usage_weight: 0.3
    io_activity_weight: 0.2
    queue_length_weight: 0.1
    
  rebalancing_triggers:
    load_imbalance_threshold: 0.3
    check_interval_minutes: 15
    minimum_rebalance_interval: 60
    
  migration_policy:
    allow_job_migration: false  # CFX通常不支持
    checkpoint_frequency: "1hour"
    migration_cost_threshold: 0.2
```

### 3. 容量规划

```yaml
# 容量规划
capacity_planning:
  resource_estimation:
    cpu_hours_per_case: 100      # 平均每案例CPU小时
    memory_gb_per_case: 64       # 平均每案例内存需求
    storage_gb_per_case: 10      # 平均每案例存储需求
    
  scaling_factors:
    mesh_density_factor: 1.5     # 网格密度影响
    physics_complexity_factor: 2.0  # 物理模型复杂度
    convergence_difficulty_factor: 1.3  # 收敛难度
    
  resource_allocation:
    reserved_capacity: 0.2       # 保留20%容量
    burst_capacity: 0.3          # 30%突发容量
    maintenance_window: "Sunday 02:00-06:00"
```

---

## 📈 监控和调试

### 1. 作业监控

```yaml
# 作业监控配置
job_monitoring:
  real_time_monitoring:
    enable: true
    update_interval: 30          # 秒
    metrics_collection: true
    
  convergence_monitoring:
    residual_tracking: true
    stagnation_detection: true
    divergence_alerts: true
    
  performance_monitoring:
    cpu_efficiency: true
    memory_utilization: true
    io_throughput: true
    solver_speed: true
    
  alerting_system:
    email_notifications: true
    webhook_notifications: false
    alert_thresholds:
      slow_progress: 0.1         # 进度缓慢阈值
      high_residuals: 1e-2       # 高残差阈值
      memory_leak: 0.1           # 内存泄漏阈值
```

### 2. 系统监控

```yaml
# 系统级监控
system_monitoring:
  infrastructure:
    node_health: true
    disk_space: true
    network_connectivity: true
    scheduler_status: true
    
  performance_metrics:
    cluster_utilization: true
    queue_statistics: true
    throughput_analysis: true
    efficiency_reports: true
    
  log_management:
    centralized_logging: true
    log_retention: "30days"
    log_analysis: true
    error_pattern_detection: true
```

### 3. 调试工具

```yaml
# 调试配置
debugging:
  verbose_logging: true
  debug_mode: false              # 生产环境关闭
  
  cfx_debugging:
    solver_debug_level: 1        # CFX调试级别
    memory_debugging: false      # 内存调试
    mpi_debugging: false         # MPI调试
    
  system_debugging:
    strace_enable: false         # 系统调用跟踪
    network_tracing: false       # 网络跟踪
    io_tracing: false           # I/O跟踪
    
  troubleshooting:
    auto_restart_failed_jobs: false
    collect_core_dumps: true
    preserve_failed_job_data: true
```

---

## 🚨 故障排除

### 1. 常见问题诊断

#### 作业提交失败

```bash
# 诊断步骤
# 1. 检查SLURM/PBS状态
sinfo  # SLURM
pbsnodes -a  # PBS

# 2. 检查资源可用性
squeue -u $USER  # SLURM
qstat -u $USER   # PBS

# 3. 验证作业脚本
sbatch --test-only job_script.sh  # SLURM
qsub -I job_script.pbs           # PBS交互测试

# 4. 检查权限和配额
sacctmgr show associations user=$USER  # SLURM
```

#### CFX求解器问题

```yaml
# CFX故障诊断清单
cfx_troubleshooting:
  license_issues:
    check_license_server: true
    verify_license_features: true
    monitor_license_usage: true
    
  memory_issues:
    check_available_memory: true
    verify_memory_limits: true
    monitor_memory_usage: true
    
  convergence_issues:
    analyze_residuals: true
    check_mesh_quality: true
    verify_boundary_conditions: true
    review_physics_models: true
    
  performance_issues:
    check_cpu_utilization: true
    verify_mpi_configuration: true
    analyze_load_balancing: true
    monitor_io_performance: true
```

### 2. 自动恢复机制

```yaml
# 自动恢复配置
auto_recovery:
  enable: true
  
  recovery_policies:
    transient_failures:
      max_retries: 3
      retry_delay: 300           # 5分钟
      exponential_backoff: true
      
    resource_failures:
      node_failure_handling: "reschedule"
      memory_overflow_handling: "increase_memory"
      timeout_handling: "extend_time"
      
    network_failures:
      connection_retry: 5
      timeout_extension: 1800    # 30分钟
      fallback_nodes: true
      
  notification:
    recovery_attempts: true
    recovery_success: true
    recovery_failure: true
```

### 3. 日志分析

```yaml
# 日志分析配置
log_analysis:
  collection:
    system_logs: true
    scheduler_logs: true
    cfx_logs: true
    application_logs: true
    
  analysis:
    error_pattern_detection: true
    performance_trend_analysis: true
    resource_usage_analysis: true
    failure_correlation_analysis: true
    
  reporting:
    daily_summary: true
    weekly_trends: true
    failure_reports: true
    performance_reports: true
```

---

## 🔒 安全考虑

### 1. 访问控制

```yaml
# 安全配置
security:
  authentication:
    ssh_key_authentication: true
    password_authentication: false
    multi_factor_authentication: false  # 根据需要
    
  authorization:
    user_based_access: true
    group_based_access: true
    role_based_access: false
    
  data_protection:
    file_encryption: false       # 根据需要
    data_transmission_encryption: true
    secure_deletion: true
```

### 2. 网络安全

```yaml
# 网络安全
network_security:
  firewall_configuration:
    enable_firewall: true
    allowed_ports: [22, 80, 443]
    ssh_port_change: false       # 根据政策
    
  vpn_requirements:
    vpn_access_required: false   # 根据环境
    vpn_protocols: ["openvpn", "ipsec"]
    
  monitoring:
    intrusion_detection: true
    traffic_analysis: true
    anomaly_detection: true
```

### 3. 数据安全

```yaml
# 数据安全
data_security:
  backup_strategy:
    regular_backups: true
    backup_frequency: "daily"
    backup_retention: "30days"
    offsite_backups: true
    
  data_classification:
    sensitive_data_handling: true
    data_retention_policy: true
    secure_disposal: true
    
  compliance:
    gdpr_compliance: false       # 根据需要
    industry_standards: ["iso27001"]
    audit_trail: true
```

---

## 📋 配置模板

### 学校集群模板

```yaml
# 学校集群标准配置模板
cluster_config_university:
  cluster_type: "university"
  scheduler_type: "SLURM"
  
  conservative_settings:
    enable_node_detection: false
    enable_node_allocation: false
    max_concurrent_jobs: 3
    job_submit_delay: 10
    
  resource_limits:
    max_walltime: "24:00:00"
    max_memory_per_job: "64GB"
    max_cpu_cores_per_job: 32
    
  queue_strategy:
    prefer_short_queue: true
    avoid_peak_hours: true
    weekend_scheduling: true
```

### 高性能集群模板

```yaml
# 高性能集群配置模板
cluster_config_hpc:
  cluster_type: "group_new"
  scheduler_type: "SLURM"
  
  aggressive_settings:
    enable_node_detection: true
    enable_node_allocation: true
    allocation_strategy: "hybrid"
    max_concurrent_jobs: 20
    
  performance_optimization:
    high_memory_nodes: true
    infiniband_network: true
    parallel_file_system: true
    gpu_acceleration: false
    
  monitoring:
    real_time_monitoring: true
    performance_profiling: true
    resource_utilization_tracking: true
```

通过遵循这些最佳实践，您可以在不同类型的集群环境中实现CFX自动化系统的最佳性能和可靠性。记住，配置需要根据具体的硬件环境、网络条件和使用模式进行调整。
