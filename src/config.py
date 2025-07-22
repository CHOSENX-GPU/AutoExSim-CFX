"""
CFX自动化系统配置管理模块
支持多环境配置、CFX自动检测、YAML配置文件管理
"""

import os
import yaml
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class CFXAutomationConfig:
    """CFX自动化配置类 - 支持自动检测和多环境配置"""
    
    # CFX环境配置
    cfx_mode: str = "local"  # "local" 或 "server"
    cfx_home: str = ""
    cfx_bin_path: str = ""
    cfx_pre_executable: str = ""
    cfx_solver_executable: str = ""
    cfx_version: str = ""
    auto_detect_cfx: bool = True
    
    # 远程CFX配置
    remote_cfx_home: str = ""
    remote_cfx_bin_path: str = ""
    remote_cfx_version: str = ""
    
    # 老集群CFX配置 (使用module system)
    skip_cfx_verification: bool = False  # 跳过服务器CFX环境验证
    cfx_module_name: str = ""           # CFX模块名称
    
    # 基本配置
    job_name: str = "CFX_Job"
    base_path: str = "."
    project_name: str = "CFX_Project"
    
    # CFX文件配置
    cfx_file_path: str = ""
    pre_template_path: str = ""
    initial_file: str = ""  # 初始结果文件路径（用于重启计算）
    
    # CFX模型配置
    flow_analysis_name: str = "Flow Analysis 1"
    domain_name: str = "S1"
    outlet_boundary_name: str = "S1 Outlet"
    inlet_boundary_name: str = "R1 Inlet"
    outlet_location: str = "R2_OUTFLOW"
    inlet_location: str = "R1_INFLOW"
    pressure_blend: str = "0.05"
    pressure_unit: str = "Pa"
    cfx_version: str = "22.1"
    output_prefix: str = ""             # 输出文件前缀
    output_base_path: str = "."         # 输出基础路径
    slurm_template_path: str = ""       # 模板文件路径（用于向后兼容）
    
    # 边界条件高级设置
    modify_inlet: bool = False
    inlet_condition_type: str = "Total Pressure"
    inlet_total_pressure: str = "0 [Pa]"
    inlet_mass_flow: str = "1.0 [kg s^-1]"
    flow_regime: str = "Subsonic"
    pressure_averaging: str = "Average Over Whole Outlet"
    
    # 求解器高级参数
    max_iterations: int = 5000
    min_iterations: int = 1
    residual_target: str = "0.000001"
    residual_type: str = "RMS"
    turbulence_numerics: str = "First Order"
    advection_scheme: str = "High Resolution"
    length_scale_option: str = "Conservative"
    timescale_control: str = "Auto Timescale"
    timescale_factor: float = 1.0
    dynamic_model_control: str = "On"
    
    # 监测设置
    enable_efficiency_monitor: bool = True
    efficiency_method: str = "Total to Total"
    efficiency_type: str = "Both Compression and Expansion"
    monitor_balances: str = "Full"
    monitor_forces: str = "Full"
    monitor_particles: str = "Full"
    monitor_residuals: str = "Full"
    monitor_totals: str = "Full"
    
    # 流体和几何参数
    fluid_density: float = 1.225
    mean_radius: float = 0.2505
    rotational_speed: float = 2930
    mass_scale_factor_in: int = 10
    mass_scale_factor_out: int = -9
    
    # 自定义参数（可选）
    custom_expressions: List[Dict[str, str]] = field(default_factory=list)
    custom_monitors: List[Dict[str, str]] = field(default_factory=list)
    additional_boundary_conditions: List[Dict[str, str]] = field(default_factory=list)
    
    # 结果文件设置
    enable_result_files: bool = True
    file_compression: str = "Compressed"
    results_option: str = "Standard"
    additional_result_files: List[Dict[str, str]] = field(default_factory=list)
    
    # 文件命名配置
    folder_prefix: str = "P_Out_"
    def_file_prefix: str = ""
    
    # 背压参数配置
    pressure_list: List[float] = field(default_factory=lambda: [2187, 2189])
    pressure_unit: str = "Pa"
    
    # 服务器配置
    ssh_host: str = "cluster.example.com"
    ssh_port: int = 22
    ssh_user: str = "username"
    ssh_key: str = ""
    ssh_password: Optional[str] = None
    remote_base_path: str = "/home/username/CFX_Jobs"
    
    # 集群配置
    cluster_type: str = "university"  # university, group_new, group_old
    scheduler_type: str = "SLURM"  # SLURM, PBS
    
    # SLURM配置
    partition: str = "cpu-low"
    nodes: int = 1
    tasks_per_node: int = 32
    time_limit: str = "7-00:00:00"
    memory_per_node: str = "64GB"
    qos: str = ""
    
    # PBS配置
    queue: str = "default"
    ppn: int = 16
    walltime: str = "24:00:00"
    memory: str = "32GB"
    nodes_spec: str = ""  # PBS节点规格，如 "node3:ppn=28+node4:ppn=28"
    min_cores: int = 28  # 作业所需最小核心数 (用于智能节点分配)
    email: str = ""  # 邮箱地址
    email_events: str = "abe"  # 邮件事件 (a=abort, b=begin, e=end)
    
    # 节点分配配置
    enable_node_detection: bool = True
    enable_node_allocation: bool = True
    node_allocation_strategy: str = "hybrid"
    max_queue_jobs: int = 10
    nodelist: str = ""
    exclude_nodes: str = ""
    
    # 监控配置
    enable_monitoring: bool = True
    monitor_interval: int = 60
    auto_download_results: bool = True
    cleanup_remote_files: bool = False
    result_file_patterns: List[str] = field(
        default_factory=lambda: ["*.res", "*.out", "*.log", "*.err"]
    )
    
    # 文件传输配置
    transfer_retry_times: int = 3
    transfer_timeout: int = 300
    enable_checksum_verification: bool = True
    
    # 作业管理配置
    max_concurrent_jobs: int = 5
    job_submit_delay: int = 2
    
    @classmethod
    def from_yaml(cls, file_path: str) -> 'CFXAutomationConfig':
        """从YAML文件加载配置"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # 创建配置实例
            config = cls()
            
            # 更新配置
            for key, value in data.items():
                if hasattr(config, key):
                    setattr(config, key, value)
                else:
                    logger.warning(f"Unknown configuration key: {key}")
            
            logger.info(f"Configuration loaded from {file_path}")
            return config
            
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {file_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file {file_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise
    
    def to_yaml(self, file_path: str) -> None:
        """保存配置到YAML文件"""
        try:
            # 转换为字典
            config_dict = {}
            for key, value in self.__dict__.items():
                if not key.startswith('_'):
                    config_dict[key] = value
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
            
            logger.info(f"Configuration saved to {file_path}")
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise
    
    def validate(self) -> List[str]:
        """验证配置"""
        errors = []
        
        # 验证必需字段
        if not self.ssh_host:
            errors.append("ssh_host is required")
        
        if not self.ssh_user:
            errors.append("ssh_user is required")
        
        if not self.remote_base_path:
            errors.append("remote_base_path is required")
        
        # 验证CFX模式
        if self.cfx_mode not in ["local", "server"]:
            errors.append("cfx_mode must be 'local' or 'server'")
        
        # 验证集群类型
        if self.cluster_type not in ["university", "group_new", "group_old"]:
            errors.append("cluster_type must be 'university', 'group_new', or 'group_old'")
        
        # 验证调度器类型
        if self.scheduler_type not in ["SLURM", "PBS"]:
            errors.append("scheduler_type must be 'SLURM' or 'PBS'")
        
        # 验证分配策略
        valid_strategies = ["batch_allocation", "node_reuse", "smart_queue", "hybrid"]
        if self.node_allocation_strategy not in valid_strategies:
            errors.append(f"node_allocation_strategy must be one of: {valid_strategies}")
        
        return errors
    
    def get_cfx_executable_path(self, executable_name: str) -> str:
        """获取CFX可执行文件路径"""
        if self.cfx_bin_path:
            return os.path.join(self.cfx_bin_path, executable_name)
        elif self.cfx_home:
            return os.path.join(self.cfx_home, "bin", executable_name)
        else:
            return executable_name  # 假设在PATH中
    
    def get_remote_cfx_executable_path(self, executable_name: str) -> str:
        """获取远程CFX可执行文件路径"""
        if self.remote_cfx_bin_path:
            return os.path.join(self.remote_cfx_bin_path, executable_name)
        elif self.remote_cfx_home:
            return os.path.join(self.remote_cfx_home, "bin", executable_name)
        else:
            return executable_name


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def load_config(self, config_name: str) -> CFXAutomationConfig:
        """加载配置文件"""
        config_file = self.config_dir / f"{config_name}.yaml"
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        return CFXAutomationConfig.from_yaml(str(config_file))
    
    def save_config(self, config: CFXAutomationConfig, config_name: str) -> None:
        """保存配置文件"""
        config_file = self.config_dir / f"{config_name}.yaml"
        config.to_yaml(str(config_file))
    
    def list_configs(self) -> List[str]:
        """列出所有配置文件"""
        return [f.stem for f in self.config_dir.glob("*.yaml")]
    
    def create_default_configs(self) -> None:
        """创建默认配置文件"""
        configs = {
            "local_cfx_university": self._get_university_config(),
            "local_cfx_new_cluster": self._get_new_cluster_config(),
            "local_cfx_old_cluster": self._get_old_cluster_config(),
        }
        
        for name, config in configs.items():
            self.save_config(config, name)
            self.logger.info(f"Created default configuration: {name}")
    
    def _get_university_config(self) -> CFXAutomationConfig:
        """获取学校集群配置"""
        config = CFXAutomationConfig()
        config.cluster_type = "university"
        config.scheduler_type = "SLURM"
        config.enable_node_detection = False
        config.enable_node_allocation = False
        config.partition = "cpu-low"
        config.nodes = 1
        config.tasks_per_node = 32
        return config
    
    def _get_new_cluster_config(self) -> CFXAutomationConfig:
        """获取组内新集群配置"""
        config = CFXAutomationConfig()
        config.cluster_type = "group_new"
        config.scheduler_type = "SLURM"
        config.enable_node_detection = True
        config.enable_node_allocation = True
        config.node_allocation_strategy = "hybrid"
        return config
    
    def _get_old_cluster_config(self) -> CFXAutomationConfig:
        """获取组内老集群配置"""
        config = CFXAutomationConfig()
        config.cluster_type = "group_old"
        config.scheduler_type = "PBS"
        config.enable_node_detection = True
        config.enable_node_allocation = True
        config.node_allocation_strategy = "hybrid"
        config.queue = "default"
        config.ppn = 16
        return config


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """配置日志系统"""
    # 配置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 配置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 文件处理器（可选）
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
