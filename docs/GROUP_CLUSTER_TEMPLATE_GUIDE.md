# 组内新集群CFX模板使用说明

## 📋 概述

我们为组内新集群创建了一个统一的CFX作业脚本模板，该模板：

- ✅ **统一处理**：自动处理带/不带初始文件的计算任务
- ✅ **节点适配**：自动适配单节点和多节点并行计算
- ✅ **符合习惯**：使用`.sbatch`扩展名，符合集群使用习惯
- ✅ **基于实际**：基于组内集群的真实配置和脚本优化

## 🎯 模板特点

### 1. 统一模板设计
不再需要选择不同的模板类型，一个模板处理所有情况：
- 标准CFX计算（无初始文件）
- 带初始文件的CFX计算
- 单节点并行计算
- 多节点并行计算

### 2. 智能条件处理
模板内部使用Jinja2条件语句自动处理：
```jinja
{% if initial_file %}
# 带初始文件的计算命令
$CFX -def $INPUT -ini-file $INITIAL -par-dist $HLIST -start-method "Platform MPI Distributed Parallel"
{% else %}
# 标准计算命令  
$CFX -def $INPUT -par-dist $HLIST -start-method "Platform MPI Distributed Parallel"
{% endif %}
```

### 3. 节点分配策略
```bash
{% if nodes > 1 %}
# 多节点：动态构建主机分布列表
# 自动生成类似 "node1*32,node2*32" 的分布
{% else %}
# 单节点：直接使用当前节点
HLIST="$(hostname)*32"
{% endif %}
```

## 📁 文件结构

```
templates/
├── CFX_Group_Cluster.sbatch.j2    # 组内新集群统一模板
├── CFX_University.slurm.j2        # 学校集群模板
├── CFX_Group_PBS.pbs.j2           # 组内老集群PBS模板
└── create_def_*.pre.j2             # CFX前处理模板
```

## ⚙️ 配置更新

配置文件 `config/local_cfx_new_cluster.yaml` 中的关键配置：

```yaml
# 集群配置
cluster_type: "group_new"
scheduler_type: "SLURM"

# 模板配置 - 统一使用一个模板
sbatch_template: "CFX_Group_Cluster.sbatch.j2"

# CFX环境配置（基于实际集群路径）
remote_cfx_bin_path: "/home/opt/ansys/ansys2022r1/v221/CFX/bin/"

# SLURM作业配置
partition: "batch"                   # 组内集群使用batch分区
tasks_per_node: 32                   # 每节点32核
exclude_nodes: "master"              # 排除master节点
```

## 🔄 模板对比

### 之前（多个模板）：
- `CFX_Group_Cluster.slurm.j2` - 标准计算
- `CFX_Group_Cluster_Initial.slurm.j2` - 带初始文件
- `CFX_Group_Cluster_Single.slurm.j2` - 单节点
- `CFX_Group_Cluster_Simple.slurm.j2` - 简化版

### 现在（统一模板）：
- `CFX_Group_Cluster.sbatch.j2` - 处理所有情况

## 🚀 使用示例

### 1. 标准CFX计算
```python
job = {
    "name": "CFX_Standard",
    "def_file": "model.def",
    "nodes": 1,
    "allocated_cpus": 32
}
```

生成的脚本会自动执行：
```bash
cfx5solve -def model.def -par-dist $(hostname)*32 -start-method "Platform MPI Distributed Parallel"
```

### 2. 带初始文件计算
```python
job = {
    "name": "CFX_With_Initial", 
    "def_file": "model.def",
    "initial_file": "restart.res",
    "nodes": 1,
    "allocated_cpus": 32
}
```

生成的脚本会自动执行：
```bash
cfx5solve -def model.def -ini-file restart.res -par-dist $(hostname)*32 -start-method "Platform MPI Distributed Parallel"
```

### 3. 多节点并行计算
```python
job = {
    "name": "CFX_Multi_Node",
    "def_file": "model.def", 
    "nodes": 2,
    "allocated_cpus": 32
}
```

生成的脚本会自动构建主机列表：
```bash
# 自动生成类似 "node1*32,node2*32" 的分布
cfx5solve -def model.def -par-dist $HLIST -start-method "Platform MPI Distributed Parallel"
```

## 🎨 模板优势

### 1. 简化维护
- 只需维护一个模板文件
- 减少代码重复和不一致性
- 更容易进行版本控制

### 2. 用户友好
- 不需要选择模板类型
- 自动适配不同计算场景
- 统一的错误处理和日志记录

### 3. 基于实际
- 基于组内集群真实的CFX脚本
- 遵循集群的实际使用习惯
- 使用`.sbatch`扩展名符合规范

### 4. 智能处理
- 自动检测文件存在性
- 智能选择并行分布策略
- 详细的计算结果检查

## 🔧 技术细节

### SLURM vs SBATCH
- **功能**: `.slurm`和`.sbatch`文件功能完全相同
- **习惯**: 组内集群更常用`.sbatch`扩展名
- **提交**: 都使用`sbatch`命令提交作业

### 模板引擎
- 使用Jinja2模板引擎
- 支持条件语句和循环
- 变量替换和过滤器功能

### 错误处理
- 文件存在性检查
- CFX执行结果验证
- 详细的错误日志记录

## 📈 后续优化

1. **性能监控**: 添加作业性能监控功能
2. **自动重启**: 失败作业的自动重启机制
3. **结果分析**: 集成结果文件自动分析
4. **通知系统**: 作业完成的邮件通知

---

*最后更新: 2025年7月22日*
