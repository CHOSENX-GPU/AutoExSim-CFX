# CFX自动化系统快速参考

## 命令速查表

### 基础操作

```bash
# 检测CFX环境
python main.py --detect-cfx

# 创建配置文件
python main.py --create-config config/project.yaml

# 验证配置
python main.py --validate config/project.yaml

# 查看配置信息
python main.py --info config/project.yaml

# 查询集群状态
python main.py --cluster-status config/project.yaml
```

### 工作流程执行

```bash
# 运行完整工作流程
python main.py --run config/project.yaml

# 指定压力参数
python main.py --run config/project.yaml --pressure-list 1000 2000 3000

# 试运行模式
python main.py --run config/project.yaml --dry-run

# 执行特定步骤
python main.py --run config/project.yaml --steps generate_scripts upload_files

# 启用调试模式
python main.py --log-level DEBUG --run config/project.yaml
```

## 工作流程步骤

| 步骤 | 功能 | 输出 |
|------|------|------|
| `connect_server` | 连接集群 | SSH连接状态 |
| `verify_cfx` | 验证CFX环境 | 环境检查结果 |
| `generate_pre` | 生成预处理脚本 | `.pre`文件 |
| `generate_def` | 生成定义文件 | `.def`文件 |
| `query_cluster` | 查询集群状态 | 节点信息 |
| `allocate_nodes` | 分配计算节点 | 节点分配结果 |
| `generate_scripts` | 生成作业脚本 | `.slurm`, `.sh`文件 |
| `upload_files` | 上传文件到集群 | 传输统计 |
| `submit_jobs` | 提交作业 | 作业ID列表 |
| `monitor_jobs` | 监控作业状态 | 作业状态报告 |

## 常用组合

### 开发调试
```bash
# 1. 生成和验证脚本
python main.py --run config.yaml --steps generate_pre generate_def generate_scripts

# 2. 上传测试
python main.py --run config.yaml --steps upload_files

# 3. 提交少量作业测试
python main.py --run config.yaml --pressure-list 1000 --steps submit_jobs
```

### 生产运行
```bash
# 完整参数化研究
python main.py --run config.yaml --pressure-list 500 1000 1500 2000 2500 3000
```

### 监控管理
```bash
# 检查集群状态
python main.py --cluster-status config.yaml

# 监控现有作业
python main.py --run config.yaml --steps monitor_jobs
```

## 配置文件模板

### 最小配置
```yaml
# 基本设置
cfx_mode: "local"
base_path: "/path/to/your/project"
cfx_file_path: "model.cfx"

# 参数设置
pressure_list: [1000, 2000, 3000]

# 集群设置
ssh_host: "cluster.university.edu"
ssh_user: "username"
ssh_key: "~/.ssh/id_rsa"
remote_base_path: "/home/user/cfx_jobs"

# 调度器设置
scheduler_type: "SLURM"
partition: "cpu"
```

## 故障排除速查

| 错误信息 | 可能原因 | 解决方案 |
|----------|----------|----------|
| `未检测到CFX安装` | CFX路径问题 | 手动设置`cfx_home` |
| `服务器连接失败` | SSH配置问题 | 检查SSH密钥/密码 |
| `文件上传失败` | 权限问题 | 检查远程目录权限 |
| `作业提交失败` | 脚本缺失 | 先执行`generate_scripts` |

## 文件结构说明

```
项目目录/
├── config/                 # 配置文件
│   ├── local_cfx_new_cluster.yaml
│   └── my_project.yaml
├── report/                 # 自动生成的报告
│   ├── cfx_execution_report_*.json
│   └── step_*_report_*.json
├── P_1000/                 # 压力参数文件夹
│   ├── 1000.def
│   └── job_1000.slurm
├── Submit_All.sh           # 批量提交脚本
└── Monitor_Jobs.sh         # 监控脚本
```

## 报告文件位置

所有JSON报告文件自动保存在当前目录的 `./report/` 文件夹下：

- **完整工作流程报告**: `cfx_execution_report_YYYYMMDD_HHMMSS.json`
- **单步骤报告**: `step_<step_name>_report_YYYYMMDD_HHMMSS.json`

## 高级功能

### 自定义参数列表
```bash
# 非等间距参数
python main.py --run config.yaml --pressure-list 100 500 1000 2000 5000

# 精细化研究
python main.py --run config.yaml --pressure-list 950 1000 1050 1100 1150
```

### 部分重新运行
```bash
# 只重新上传和提交
python main.py --run config.yaml --steps upload_files submit_jobs

# 只监控现有作业
python main.py --run config.yaml --steps monitor_jobs
```

### 调试模式
```bash
# 详细日志输出
python main.py --log-level DEBUG --log-file debug.log --run config.yaml

# 单步骤调试
python main.py --log-level DEBUG --run config.yaml --steps connect_server
```
