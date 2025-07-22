# CFX自动化系统架构文档 v2.0

## 系统概述

CFX自动化系统v2.0采用智能化模块设计，集成了**智能节点分配**、**排队策略管理**和**多调度器支持**等核心功能。系统架构经过重构优化，提供高效、可靠的CFX集群计算解决方案。

## 🏗️ 系统架构

### 总体架构

```text
CFX自动化系统 v2.0 架构图

┌─────────────────────────────────────────────────────────────────┐
│                    用户接口层 (CLI/Config)                        │
├─────────────────────────────────────────────────────────────────┤
│                工作流编排层 (WorkflowOrchestrator)                 │
├─────────────────────────────────────────────────────────────────┤
│  智能分配层   │  CFX管理层   │  集群管理层   │  传输监控层           │
│  ┌─────────── │ ───────────  │ ─────────── │ ──────────────────── │
│  │智能节点分配 │ CFX环境检测  │ 集群状态查询  │ 文件传输管理         │
│  │排队策略管理 │ 参数化建模   │ 调度器适配   │ 作业监控             │
│  │动态节点追踪 │ 脚本生成     │ Unix兼容性   │ 结果下载             │
│  └─────────── │ ───────────  │ ─────────── │ ──────────────────── │
├─────────────────────────────────────────────────────────────────┤
│                基础设施层 (SSH/SFTP/Jinja2)                       │
└─────────────────────────────────────────────────────────────────┘
```

### 核心模块架构

#### 1. 智能分配模块 (cluster_query.py)

```text
智能分配模块架构
├── ClusterQueryManager
│   ├── PBS节点信息解析器
│   │   ├── np字段优先解析
│   │   ├── 状态信息标准化
│   │   └── 内存信息提取
│   ├── SLURM节点信息解析器
│   │   ├── sinfo命令解析
│   │   ├── 节点状态映射
│   │   └── 资源信息获取
│   └── 智能分配算法
│       ├── 单节点优先策略
│       ├── 资源精确匹配
│       └── 负载均衡分配
```

**核心功能**：
- **PBS节点信息准确解析**: 优先使用np字段，修复核心数错误问题
- **智能单节点分配**: 避免28核需求被分配44核的资源浪费
- **实时集群状态同步**: 动态获取节点可用性和资源状态

#### 2. 排队策略管理 (script_generator.py)

```text
排队策略管理模块
├── ScriptGenerator
│   ├── 策略选择器
│   │   ├── Parallel策略 (节点充足)
│   │   ├── Sequential策略 (节点不足)
│   │   ├── Batch策略 (大量作业)
│   │   └── 自动策略选择
│   ├── 脚本生成器
│   │   ├── PBS脚本生成 (.pbs)
│   │   ├── SLURM脚本生成 (.slurm)
│   │   ├── 提交脚本生成 (qsub/sbatch)
│   │   └── Unix兼容性保证
│   └── 节点分配器
│       ├── 动态节点追踪
│       ├── 已分配节点记录
│       └── 智能节点复用
```

**核心功能**：
- **3种排队策略**: 根据资源状况自动选择最优策略
- **Unix格式脚本**: 强制Unix换行符，解决PBS DOS格式问题
- **多调度器支持**: 同时支持PBS和SLURM调度系统

#### 3. CFX环境管理 (cfx.py)

```text
CFX环境管理模块
├── CFXManager
│   ├── 环境检测器
│   │   ├── 自动路径扫描
│   │   ├── 版本兼容性检查
│   │   └── 可执行文件验证
│   ├── 参数化建模器
│   │   ├── 模板参数替换
│   │   ├── Pre脚本生成
│   │   └── Def文件生成
│   └── 跨平台适配器
│       ├── Windows路径处理
│       ├── Linux路径映射
│       └── 文件格式转换
```

#### 4. 工作流编排 (workflow_orchestrator.py)

```text
工作流编排模块
├── WorkflowOrchestrator
│   ├── 步骤管理器
│   │   ├── 单步执行支持
│   │   ├── 错误处理机制
│   │   └── 状态追踪
│   ├── 资源管理器
│   │   ├── SSH连接池
│   │   ├── 文件传输队列
│   │   └── 内存管理
│   └── 报告生成器
│       ├── 执行报告
│       ├── 监控报告
│       └── 诊断信息
```

## 🔧 技术实现细节

### 智能节点分配算法

#### 核心问题解决

**问题1: PBS节点核心数错误**

```python
# 修复前的错误逻辑
if key == "ncpus":
    node_info["cpus"] = ncpus  # 可能是错误的超线程数

# 修复后的正确逻辑
if key == "np":
    current_node["cpus"] = self._parse_cpu_count(value)  # 优先使用np字段
elif key == "ncpus":
    if node_info.get("cpus", 0) == 0:  # 只有np未设置时才使用ncpus
        node_info["cpus"] = ncpus
```

**问题2: 过度分配问题**

```python
# 智能单节点优先分配
def _allocate_single_node_priority(self, required_cores, available_nodes):
    # 1. 寻找精确匹配的节点
    exact_match = [n for n in available_nodes if n['cpus'] == required_cores]
    if exact_match:
        return exact_match[0]
    
    # 2. 寻找略大于需求的节点
    suitable = [n for n in available_nodes if n['cpus'] >= required_cores]
    if suitable:
        return min(suitable, key=lambda x: x['cpus'])  # 选择最小的满足需求的节点
    
    return None
```

### 排队策略自动选择

```python
def _determine_queue_strategy(self, available_nodes, job_count):
    """智能选择排队策略"""
    if available_nodes >= job_count:
        return "parallel"    # 每个作业独立节点
    elif job_count > 8:
        return "batch"       # 分批处理
    else:
        return "sequential"  # 依次执行
```

### Unix兼容性保证

```python
def _write_script_file(self, filepath, content):
    """确保生成Unix格式脚本"""
    with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)  # 强制使用Unix换行符
```

## 📊 数据流架构

### 典型工作流数据流

```text
1. 配置加载
   ├── YAML解析
   ├── 参数验证
   └── 环境变量解析

2. 集群连接
   ├── SSH密钥认证
   ├── 连接池建立
   └── 权限验证

3. 集群状态查询
   ├── 调度器检测 (PBS/SLURM)
   ├── 节点信息解析
   └── 资源状态映射

4. 智能节点分配
   ├── 需求分析
   ├── 可用节点筛选
   ├── 分配算法执行
   └── 分配结果验证

5. 排队策略选择
   ├── 资源评估
   ├── 策略匹配
   ├── 作业分组
   └── 执行计划生成

6. 脚本生成
   ├── 模板参数替换
   ├── Unix格式转换
   ├── 调度器适配
   └── 文件输出

7. 文件传输
   ├── 目录结构创建
   ├── 文件上传
   ├── 权限设置
   └── 传输验证

8. 作业提交
   ├── 提交脚本执行
   ├── 作业ID获取
   ├── 状态监控
   └── 结果收集
```

## 🔌 接口设计

### 配置接口

```python
class CFXAutomationConfig:
    """统一配置管理接口"""
    
    # 智能分配配置
    enable_node_detection: bool = True
    enable_node_allocation: bool = True
    min_cores: int = 28
    queue_strategy_preference: str = "auto"
    
    # 调度器配置
    scheduler_type: str = "PBS"  # PBS | SLURM
    cluster_type: str = "university"
    
    # SSH连接配置
    ssh_host: str
    ssh_user: str
    ssh_key: Optional[str] = None
```

### 核心API接口

```python
class ClusterQueryManager:
    """集群查询管理器"""
    
    def query_cluster_nodes(self, ssh_client) -> List[Dict]:
        """查询集群节点状态"""
        
    def allocate_nodes_intelligent(self, jobs, cluster_status) -> List[Dict]:
        """智能节点分配"""

class ScriptGenerator:
    """脚本生成器"""
    
    def generate_job_scripts(self, job_configs, cluster_status) -> Dict:
        """生成作业脚本"""
        
    def _determine_queue_strategy(self, available_nodes, job_count) -> str:
        """确定排队策略"""
```

## 🧪 测试架构

### 单元测试

```text
tests/
├── test_cluster_query.py      # 集群查询测试
├── test_script_generator.py   # 脚本生成测试
├── test_intelligent_allocation.py  # 智能分配测试
├── test_queue_strategies.py   # 排队策略测试
└── test_unix_compatibility.py # Unix兼容性测试
```

### 集成测试

```text
integration_tests/
├── test_full_workflow.py      # 完整工作流测试
├── test_pbs_integration.py    # PBS集成测试
├── test_slurm_integration.py  # SLURM集成测试
└── test_error_recovery.py     # 错误恢复测试
```

## 📈 性能优化

### 关键优化点

1. **节点查询缓存**: 避免重复查询集群状态
2. **连接复用**: SSH连接池管理
3. **并行文件传输**: 多线程文件上传
4. **智能批处理**: 大量作业的批次优化

### 内存优化

```python
# 大数据量处理优化
def process_large_job_list(self, jobs):
    """批量处理大量作业"""
    batch_size = 50
    for batch in self._batch_jobs(jobs, batch_size):
        yield self._process_job_batch(batch)
```

## 🔒 安全设计

### 认证和授权

- SSH密钥认证
- 连接超时保护
- 权限最小化原则

### 数据保护

- 敏感信息加密存储
- 传输过程SSL/TLS保护
- 本地缓存安全清理

## 🚀 扩展性设计

### 新调度器支持

```python
class NewSchedulerAdapter(SchedulerAdapter):
    """新调度器适配器基类"""
    
    def query_nodes(self) -> List[Dict]:
        """实现节点查询"""
        
    def submit_job(self, script_path) -> str:
        """实现作业提交"""
```

### 插件系统

```python
class PluginManager:
    """插件管理器"""
    
    def load_plugin(self, plugin_name):
        """动态加载插件"""
        
    def register_hook(self, event, callback):
        """注册事件钩子"""
```

---

**CFX自动化系统v2.0 - 智能、高效、可扩展的集群计算解决方案** 🚀
   - SLURM/PBS脚本生成
   - 参数化配置

6. **transfer.py** - 文件传输模块
   - SSH/SFTP支持
   - 传输验证
   - 重试机制

7. **job_monitor.py** - 作业监控模块
   - 实时状态跟踪
   - 自动结果下载
   - 监控报告

8. **workflow_orchestrator.py** - 工作流编排模块
   - 端到端流程控制
   - 错误处理
   - 状态管理

## 设计原则

### 1. 模块化设计
- 每个模块职责单一
- 低耦合高内聚
- 易于测试和维护

### 2. 错误处理
- 多层次异常处理
- 详细错误日志
- 优雅降级

### 3. 配置驱动
- 外部配置文件
- 参数化设计
- 环境适配

### 4. 扩展性
- 插件化架构
- 策略模式
- 模板系统

## 数据流程

```
用户输入 → 配置加载 → CFX环境检测 → 集群查询 → 节点分配 → 脚本生成 → 文件传输 → 作业提交 → 监控 → 结果下载
```

## 配置系统

### 配置层次
1. 默认配置
2. 环境配置
3. 用户配置
4. 命令行参数

### 配置验证
- 必需字段检查
- 数据类型验证
- 逻辑关系验证
- 环境兼容性检查

## 错误处理策略

### 1. 连接错误
- 自动重试
- 指数退避
- 超时处理

### 2. 文件错误
- 完整性验证
- 备份恢复
- 清理机制

### 3. 作业错误
- 状态监控
- 失败重启
- 错误报告

## 性能优化

### 1. 并发处理
- 多线程上传
- 异步监控
- 批量操作

### 2. 缓存机制
- 节点状态缓存
- 配置缓存
- 结果缓存

### 3. 资源管理
- 连接池
- 内存管理
- 临时文件清理

## 安全考虑

### 1. 认证授权
- SSH密钥认证
- 权限最小化
- 安全传输

### 2. 数据保护
- 配置加密
- 传输加密
- 访问控制

### 3. 审计日志
- 操作记录
- 错误追踪
- 性能监控

## 测试策略

### 1. 单元测试
- 模块级测试
- Mock对象
- 边界条件

### 2. 集成测试
- 模块间交互
- 端到端流程
- 环境兼容

### 3. 性能测试
- 负载测试
- 压力测试
- 基准测试

## 部署指南

### 1. 环境准备
- Python 3.8+
- 依赖包安装
- 权限配置

### 2. 配置设置
- SSH连接配置
- CFX环境配置
- 集群参数配置

### 3. 验证测试
- 连接测试
- 功能测试
- 性能测试

## 维护指南

### 1. 日志管理
- 日志级别配置
- 日志轮转
- 错误分析

### 2. 监控告警
- 系统状态监控
- 异常告警
- 性能指标

### 3. 更新升级
- 版本管理
- 兼容性检查
- 回滚策略
