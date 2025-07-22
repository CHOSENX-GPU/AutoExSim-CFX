# CFX自动化系统安装部署指南

## 系统要求

### 软件要求

**操作系统**：
- Windows 10/11 (64位)
- Linux (Ubuntu 18.04+, CentOS 7+, RHEL 7+)
- macOS 10.15+（实验性支持）

**必需软件**：
- Python 3.8 或更高版本
- ANSYS CFX 2019.R2 或更高版本
- SSH客户端（Windows需要OpenSSH或PuTTY）

**可选软件**：
- Git（用于版本控制）
- VS Code（推荐的代码编辑器）
- WinSCP或FileZilla（图形化文件传输工具）

## 安装步骤

### 步骤1：环境准备

#### Windows环境

1. **安装Python**
   ```bash
   # 从 https://python.org 下载并安装Python 3.7+
   # 确保勾选"Add Python to PATH"选项
   
   # 验证安装
   python --version
   pip --version
   ```

2. **安装OpenSSH（Windows 10/11）**
   ```powershell
   # 使用PowerShell（管理员模式）
   Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0
   ```

3. **配置Git**
   ```bash
   # 下载并安装Git for Windows
   # 配置用户信息
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```

#### Linux环境

1. **安装Python和依赖**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3 python3-pip python3-venv git openssh-client
   
   # CentOS/RHEL
   sudo yum install python3 python3-pip git openssh-clients
   
   # 或使用dnf (CentOS 8+)
   sudo dnf install python3 python3-pip git openssh-clients
   ```

2. **创建Python符号链接（如果需要）**
   ```bash
   # 确保python命令可用
   sudo ln -s /usr/bin/python3 /usr/bin/python
   ```

### 步骤2：获取源代码

#### 方法1：Git克隆（推荐）

```bash
# 克隆仓库
git clone https://github.com/CHOSENX-GPU/AutoExSim-CFX.git cfx-automation
cd cfx-automation

# 检查版本
git tag
git checkout v1.0.0  # 切换到稳定版本
```

#### 方法2：下载压缩包

```bash
# 下载并解压
wget <download-url> -O cfx-automation.zip
unzip cfx-automation.zip
cd cfx-automation
```

### 步骤3：创建虚拟环境

#### 使用venv（推荐）

```bash
# 创建虚拟环境
python -m venv cfx_env

# 激活虚拟环境
# Windows
cfx_env\Scripts\activate

# Linux/macOS
source cfx_env/bin/activate

# 验证虚拟环境
which python
python --version
```

#### 使用conda（可选）

```bash
# 创建conda环境
conda create -n cfx_env python=3.9
conda activate cfx_env

# 安装基础包
conda install pip git
```

### 步骤4：安装依赖包

```bash
# 确保虚拟环境已激活
# 升级pip
python -m pip install --upgrade pip

# 安装生产依赖
pip install -r requirements.txt

# 安装开发依赖（可选）
pip install -r requirements-dev.txt

# 验证安装
python -c "import paramiko, yaml, jinja2; print('Dependencies installed successfully')"
```

### 步骤5：配置系统

#### 创建配置目录

```bash
# 创建必要的目录
mkdir -p config
mkdir -p logs
mkdir -p report
mkdir -p results

# 设置权限（Linux）
chmod 755 config logs report results
```

#### 配置SSH密钥

```bash
# 生成SSH密钥对（如果还没有）
ssh-keygen -t rsa -b 4096 -C "your.email@example.com"

# 将公钥复制到集群服务器
ssh-copy-id username@cluster.hostname

# 测试SSH连接
ssh username@cluster.hostname
```

### 步骤6：验证安装

#### 基本功能测试

```bash
# 测试主程序
python main.py --help

# 检测CFX环境
python main.py --detect-cfx

# 创建测试配置
python main.py --create-config config/test.yaml

# 验证配置
python main.py --validate config/test.yaml
```

#### 完整功能测试

```bash
# 编辑测试配置文件
# 设置正确的SSH信息和路径

# 测试连接
python main.py --cluster-status config/test.yaml

# 试运行模式测试
python main.py --run config/test.yaml --dry-run
```

## 配置指南

### CFX环境配置

#### 自动检测配置

```bash
# 检测CFX安装
python main.py --detect-cfx

# 输出示例：
# 检测到 1 个CFX安装:
# 1. CFX 2022.R1
#    路径: D:\ANSYS Inc\v221\CFX
#    CFX-Pre: D:\ANSYS Inc\v221\CFX\bin\cfx5pre.exe
#    CFX-Solver: D:\ANSYS Inc\v221\CFX\bin\cfx5solve.exe
```

#### 手动配置

如果自动检测失败，需要手动配置CFX路径：

```yaml
# config/my_project.yaml
cfx_mode: "local"
auto_detect_cfx: false
cfx_home: "/path/to/ansys/cfx"
cfx_bin_path: "/path/to/ansys/cfx/bin"
```

### 集群连接配置

#### SSH密钥认证（推荐）

```yaml
ssh_host: "cluster.university.edu"
ssh_port: 22
ssh_user: "your_username"
ssh_key: "~/.ssh/id_rsa"  # 私钥路径
ssh_password: ""           # 留空使用密钥
```

#### 密码认证

```yaml
ssh_host: "cluster.university.edu"
ssh_port: 22
ssh_user: "your_username"
ssh_key: ""                # 留空
ssh_password: "your_password"  # 不推荐，安全性较低
```

### 项目路径配置

```yaml
# 本地项目路径
base_path: "/path/to/your/cfx/project"
cfx_file_path: "model.cfx"

# 远程工作路径
remote_base_path: "/home/username/cfx_jobs"
```

## 部署方案

### 方案1：单用户本地部署

**适用场景**：个人研究、小规模计算

**部署步骤**：
1. 在个人工作站安装系统
2. 配置到校级集群的连接
3. 设置个人项目目录

**优点**：
- 安装简单
- 配置灵活
- 数据私有

**缺点**：
- 单点故障
- 无法共享资源

### 方案2：团队共享部署

**适用场景**：研究团队、多用户环境

**部署步骤**：
1. 在共享服务器安装系统
2. 创建多用户配置
3. 设置项目权限管理

**配置示例**：
```bash
# 创建团队目录结构
/opt/cfx-automation/
├── bin/                    # 系统可执行文件
├── config/                 # 全局配置
├── users/                  # 用户配置目录
│   ├── user1/
│   ├── user2/
│   └── shared/
└── logs/                   # 系统日志
```

### 方案3：容器化部署

**适用场景**：云环境、大规模部署

**Dockerfile示例**：
```dockerfile
FROM python:3.9-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    openssh-client \
    git \
    && rm -rf /var/lib/apt/lists/*

# 创建工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要目录
RUN mkdir -p config logs report results

# 设置入口点
ENTRYPOINT ["python", "main.py"]
```

**使用示例**：
```bash
# 构建镜像
docker build -t cfx-automation .

# 运行容器
docker run -v $(pwd)/config:/app/config \
           -v $(pwd)/results:/app/results \
           cfx-automation --help
```

## 性能优化

### 系统性能优化

#### Python优化

```bash
# 使用更快的Python实现
pip install cython numpy

# 设置Python优化
export PYTHONOPTIMIZE=1
```

#### 网络优化

```bash
# SSH连接优化
echo "Host cluster.university.edu
    KeepAlive yes
    ServerAliveInterval 60
    ServerAliveCountMax 3
    Compression yes" >> ~/.ssh/config
```

#### 文件系统优化

```bash
# 设置临时目录（高速存储）
export TMPDIR=/tmp/cfx_temp
mkdir -p $TMPDIR

# 调整文件系统缓存
echo 'vm.dirty_ratio = 15' >> /etc/sysctl.conf
echo 'vm.dirty_background_ratio = 5' >> /etc/sysctl.conf
```

### 应用配置优化

```yaml
# 传输优化
transfer_retry_times: 3
transfer_timeout: 600
enable_checksum_verification: true

# 监控优化
monitor_interval: 300
auto_download_results: true

# 作业优化
max_concurrent_jobs: 10
job_submit_delay: 2
```

## 安全配置

### 网络安全

#### SSH安全配置

```bash
# 配置SSH客户端
echo "Host *
    Protocol 2
    HashKnownHosts yes
    StrictHostKeyChecking ask
    VisualHostKey yes" >> ~/.ssh/config

# 设置密钥权限
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub
```

#### 防火墙配置

```bash
# Linux防火墙配置
sudo ufw allow out 22/tcp
sudo ufw allow out 443/tcp
sudo ufw enable
```

### 数据安全

#### 敏感信息保护

```yaml
# 不要在配置文件中保存密码
ssh_password: ""  # 使用密钥认证

# 使用环境变量
ssh_password: "${SSH_PASSWORD}"
```

#### 文件权限

```bash
# 设置配置文件权限
chmod 600 config/*.yaml

# 设置日志文件权限
chmod 640 logs/*.log
```

## 监控和维护

### 日志管理

#### 日志配置

```yaml
# 在配置文件中设置日志
log_level: "INFO"
log_file: "logs/cfx_automation.log"
log_rotation: true
log_max_size: "100MB"
log_backup_count: 5
```

#### 日志分析

```bash
# 查看最近的错误
grep "ERROR" logs/cfx_automation.log | tail -20

# 监控实时日志
tail -f logs/cfx_automation.log

# 分析性能
grep "执行时间" logs/cfx_automation.log
```

### 系统监控

#### 资源监控

```bash
# 监控CPU和内存使用
top -p $(pgrep -f "python.*main.py")

# 监控磁盘使用
df -h
du -sh results/*

# 监控网络连接
netstat -an | grep :22
```

#### 健康检查

```bash
# 创建健康检查脚本
#!/bin/bash
# health_check.sh

echo "=== CFX自动化系统健康检查 ==="

# 检查Python环境
python --version || echo "ERROR: Python不可用"

# 检查依赖包
python -c "import paramiko, yaml, jinja2" || echo "ERROR: 依赖包缺失"

# 检查CFX环境
python main.py --detect-cfx | grep "检测到" || echo "WARNING: CFX环境未检测到"

# 检查磁盘空间
df -h | grep -E "(90|9[5-9]|100)%" && echo "WARNING: 磁盘空间不足"

echo "健康检查完成"
```

### 备份策略

#### 配置备份

```bash
# 备份配置文件
tar -czf config_backup_$(date +%Y%m%d).tar.gz config/

# 定期备份脚本
#!/bin/bash
# backup.sh
BACKUP_DIR="/backup/cfx-automation"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/cfx_automation_$DATE.tar.gz \
    config/ \
    templates/ \
    logs/ \
    --exclude="*.pyc" \
    --exclude="__pycache__"

# 保留最近30天的备份
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

#### 结果备份

```bash
# 备份重要结果
rsync -av results/ backup_server:/backup/cfx_results/

# 清理旧结果
find results/ -name "*.res" -mtime +90 -delete
```

## 故障排除

### 常见问题解决

#### 安装问题

**问题**：pip安装失败
```bash
# 解决方案
pip install --upgrade pip
pip install --user <package_name>
# 或使用国内镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple <package_name>
```

**问题**：权限错误
```bash
# 解决方案
sudo chown -R $USER:$USER /path/to/cfx-automation
chmod -R 755 /path/to/cfx-automation
```

#### 运行问题

**问题**：CFX检测失败
```bash
# 检查CFX安装
ls -la "/path/to/ansys/cfx/bin/"
# 手动设置路径
export CFX_HOME="/path/to/ansys/cfx"
```

**问题**：SSH连接失败
```bash
# 测试SSH连接
ssh -v username@hostname
# 检查密钥权限
chmod 600 ~/.ssh/id_rsa
```

### 调试工具

```bash
# 启用详细日志
python main.py --log-level DEBUG --run config.yaml

# 逐步执行
python main.py --run config.yaml --steps connect_server
python main.py --run config.yaml --steps verify_cfx

# 试运行模式
python main.py --run config.yaml --dry-run
```

---

按照本指南完成安装和配置后，CFX自动化系统就可以正常运行了。如有问题，请参考故障排除部分或查看详细的日志信息。
