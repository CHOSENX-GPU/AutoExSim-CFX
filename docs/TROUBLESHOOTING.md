# CFX自动化系统故障排除指南

本文档提供CFX自动化系统常见问题的解决方案和故障排除方法。

## 🔧 常见问题解决方案

### 1. 智能节点分配问题

#### 问题：28核需求被分配44核

**症状**：
```
需求：28核
实际分配：n44:ppn=28 + n45:ppn=16 = 44核
```

**原因**：
- 系统使用了多节点组合分配
- 没有启用智能单节点优先分配

**解决方案**：
```yaml
# 配置文件中启用智能分配
enable_node_allocation: true
enable_node_detection: true
min_cores: 28

# 排队策略配置
queue_strategy_preference: "auto"
```

**验证**：
```bash
# 测试智能分配
python main.py --run config/your_config.yaml --steps connect_server query_cluster generate_scripts

# 检查分配结果
# 应该看到: n44:ppn=28 (单节点分配)
```

### 2. PBS节点核心数错误

#### 问题：节点核心数显示不正确

**症状**：
```
PBS节点 n54:
  np = 28          (正确的核心数)
  status: ncpus=56 (错误的核心数)
系统错误使用了56核
```

**原因**：
- 系统优先使用status中的ncpus字段
- 该字段可能包含超线程或其他错误信息

**解决方案**：
系统已自动修复，现在优先使用np字段：

```python
# 修复后的逻辑
if key == "np":
    current_node["cpus"] = self._parse_cpu_count(value)  # 优先设置

elif key == "ncpus":
    if node_info.get("cpus", 0) == 0:  # 只有np未设置时才使用ncpus
        node_info["cpus"] = ncpus
```

**验证**：
```bash
# 查询集群状态
python main.py --run config/your_config.yaml --steps connect_server query_cluster

# 检查report/step_query_cluster_report_*.json
# 确认所有n41-n60节点显示28核
```

### 3. PBS脚本格式错误

#### 问题：qsub提交失败

**症状**：
```
qsub: script is written in DOS/Windows text format
```

**原因**：
- 脚本使用Windows换行符（CRLF）
- PBS调度器需要Unix换行符（LF）

**解决方案**：
系统已自动修复，所有脚本使用Unix格式：

```python
# 文件写入时强制Unix换行符
with open(script_path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(script_content)
```

**验证**：
```bash
# 生成脚本后检查格式
python main.py --run config/your_config.yaml --steps generate_scripts

# 在PowerShell中检查换行符
(Get-Content job_2300.pbs -Raw).Replace("`r`n", "[CRLF]").Replace("`n", "[LF]")
# 应该只看到[LF]，没有[CRLF]
```

### 4. 排队策略选择问题

#### 问题：不知道选择哪种排队策略

**症状**：
- 有时节点充足，有时不足
- 作业数量变化很大
- 不确定用哪种策略最优

**解决方案**：
使用自动策略选择：

```yaml
# 配置文件
queue_strategy_preference: "auto"
force_queue_strategy: null  # 不强制使用特定策略
```

**策略选择逻辑**：
```text
可用节点数 >= 作业数  →  Parallel策略（每作业独立节点）
可用节点数 < 作业数   →  Sequential策略（依次执行）
作业数 > 8个         →  Batch策略（分批处理）
```

**验证**：
```bash
# 测试不同场景
python main.py --run config/queue_test_config.yaml --steps generate_scripts

# 查看日志中的策略选择
# 应该看到: "排队策略: parallel" 或 "排队策略: batch"
```

### 5. 集群连接问题

#### 问题：SSH连接失败

**症状**：
```
Connection timeout
Authentication failed
Permission denied
```

**解决方案**：

**检查配置**：
```yaml
# SSH连接配置
ssh_host: "10.212.67.254"        # 确保IP地址正确
ssh_port: 22                     # 默认SSH端口
ssh_user: "your_username"        # 确保用户名正确
ssh_password: "your_password"    # 可选：密码认证
ssh_key: "/path/to/private/key"  # 可选：密钥认证
```

**测试连接**：
```bash
# 单独测试连接
python main.py --run config/your_config.yaml --steps connect_server

# 手动SSH测试
ssh your_username@10.212.67.254
```

**常见解决方法**：
- 确认集群IP地址和端口
- 检查用户名和密码
- 确认SSH密钥权限：`chmod 600 ~/.ssh/id_rsa`
- 检查网络连接和防火墙设置

### 6. CFX环境检测问题

#### 问题：CFX路径检测失败

**症状**：
```
CFX environment not found
CFX executable not detected
```

**解决方案**：

**手动指定CFX路径**：
```yaml
# 配置文件
auto_detect_cfx: false
cfx_home: "D:/ANSYS Inc/v221/CFX"
cfx_pre_executable: "D:/ANSYS Inc/v221/CFX/bin/cfx5pre.exe"
cfx_solver_executable: "D:/ANSYS Inc/v221/CFX/bin/cfx5solve.exe"
```

**检查CFX安装**：
```bash
# Windows
dir "C:\Program Files\ANSYS Inc"
dir "D:\ANSYS Inc"

# 查找CFX可执行文件
where cfx5pre
where cfx5solve
```

### 7. 文件传输问题

#### 问题：文件上传失败

**症状**：
```
File transfer failed
SFTP connection error
Permission denied (upload)
```

**解决方案**：

**检查远程路径权限**：
```bash
# 确保远程目录存在且有写权限
ssh user@cluster "mkdir -p /home/user/CFX_Jobs"
ssh user@cluster "chmod 755 /home/user/CFX_Jobs"
```

**检查文件大小**：
```yaml
# 配置文件 - 增加传输超时时间
transfer_timeout: 300  # 5分钟
max_file_size: 1000    # 1GB限制
```

## 🔍 调试方法

### 单步执行调试

```bash
# 逐步执行每个步骤
python main.py --config config.yaml --steps connect_server
python main.py --config config.yaml --steps query_cluster
python main.py --config config.yaml --steps generate_scripts
python main.py --config config.yaml --steps upload_files
python main.py --config config.yaml --steps submit_jobs
```

### 详细日志输出

```bash
# 启用详细日志
python main.py --config config.yaml --verbose

# 或者在配置文件中设置
log_level: "DEBUG"
```

### 检查生成的报告

```bash
# 查看执行报告
ls report/
cat report/step_*_report_*.json
```

### 验证集群状态

```bash
# 手动查询集群状态
ssh user@cluster "pbsnodes -a"  # PBS
ssh user@cluster "sinfo -N"     # SLURM
```

## 📊 性能优化建议

### 1. 节点分配优化

```yaml
# 推荐配置
enable_node_allocation: true
enable_node_detection: true
min_cores: 28                    # 根据实际需求设置
tasks_per_node: 28               # 与min_cores保持一致
queue_strategy_preference: "auto"
```

### 2. 传输性能优化

```yaml
# 并行传输配置
max_parallel_transfers: 4        # 并行传输数量
transfer_chunk_size: 8192        # 传输块大小
enable_compression: true         # 启用压缩
```

### 3. 监控优化

```yaml
# 监控配置
enable_monitoring: true
monitoring_interval: 30          # 30秒检查一次
monitoring_timeout: 7200         # 2小时超时
```

## 🛠️ 高级故障排除

### 日志分析

```bash
# 查看详细日志
grep -E "(ERROR|WARNING)" *.log
grep "节点分配" *.log
grep "排队策略" *.log
```

### 配置验证

```python
# 验证配置文件
python -c "
from src.config import CFXAutomationConfig
config = CFXAutomationConfig('config/your_config.yaml')
print('配置加载成功')
print(f'调度器类型: {config.scheduler_type}')
print(f'启用节点检测: {config.enable_node_detection}')
"
```

### 手动测试组件

```python
# 测试集群查询
python -c "
from src.cluster_query import ClusterQueryManager
from src.config import CFXAutomationConfig
import paramiko

config = CFXAutomationConfig('config/your_config.yaml')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname=config.ssh_host, username=config.ssh_user, password=config.ssh_password)

cluster_query = ClusterQueryManager(config)
nodes = cluster_query.query_cluster_nodes(ssh)
print(f'找到 {len(nodes)} 个节点')
for node in nodes[:3]:
    print(f'节点: {node[\"name\"]}, 核心数: {node[\"cpus\"]}, 状态: {node[\"state\"]}')
"
```

## 📞 获取帮助

### 检查系统状态

```bash
# 系统信息
python --version
pip list | grep -E "(paramiko|jinja2|pyyaml)"

# 配置信息
python main.py --config config.yaml --version
```

### 生成诊断报告

```bash
# 生成完整的诊断信息
python main.py --config config.yaml --diagnose
```

### 社区支持

- 查看项目文档：`docs/` 目录
- 提交Issue：描述问题现象和错误日志
- 参考示例配置：`config/` 目录下的示例文件

---

**记住**：大多数问题都可以通过启用智能分配和自动策略选择来解决！
