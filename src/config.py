"""
CFX自动化系统配置管理模块
支持多环境配置、CFX自动检测、YAML配置文件管理
"""

import os
import yaml
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

# 暂时注释掉CFX检测器，简化测试
# from .utils.cfx_detector import CFXPathDetector, auto_detect_cfx_config

logger = logging.getLogger(__name__)


@dataclass
class CFXAutomationConfig:
    """CFX自动化配置类 - 支持自动检测和多环境配置"""
    
    # CFX环境配置 - 如果为空，将自动检测
    cfx_home: str = ""
    cfx_pre_executable: str = ""
    cfx_solver_executable: str = ""
    cfx_version: str = ""
    auto_detect_cfx: bool = True
    cfx_bin_path: str = ""
    
    # 远程CFX配置
    remote_cfx_home: str = ""
    remote_cfx_bin_path: str = ""
    
    # 作业配置
    job_name: str = "CFX_Job"
    base_path: str = "."
    
    # CFX文件配置
    cfx_file_path: str = ""
    
    # CFX模型配置
    flow_analysis_name: str = "Flow Analysis 1"
    domain_name: str = "S1"
    boundary_name: str = "S1 Outlet"
    outlet_location: str = "R2_OUTFLOW"
    pressure_blend: str = "0.05"
    
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
    ssh_key: str = ""  # 默认为空，优先使用密码认证
    ssh_password: Optional[str] = None  # SSH密码（可选）
    remote_base_path: str = "/home/username/CFX_Jobs"
    
    # Slurm配置
    partition: str = "cpu-low"
    nodes: int = 1
    tasks_per_node: int = 32
    time_limit: str = "7-00:00:00"
    memory_per_node: str = "64GB"
    
    # 模板配置
    template_dir: str = "./templates"
    session_template: str = "create_def.pre.j2"
    slurm_template: str = "CFX_INI.slurm.j2"
    batch_template: str = "Submit_INI.sh.j2"
    
    # 生成的文件名称配置
    slurm_script_name: str = "CFX_INI.slurm"
    batch_script_name: str = "Submit_INI.sh"
    
    # 文件配置
    ini_file: Optional[str] = "INI.res"  # 初始化文件名
    has_ini_file: bool = True            # 是否使用初始化文件
    backup_enabled: bool = True
    cleanup_temp_files: bool = True
    
    # 报告配置
    report_dir: str = "./reports"  # 工作流程报告目录
    
    # 连接配置
    timeout: int = 300  # 连接超时时间（秒）
    
    def __post_init__(self):
        """初始化后处理"""
        if self.auto_detect_cfx and not self.cfx_home:
            self._auto_detect_cfx_paths()
    
    def validate(self) -> List[str]:
        """验证配置的有效性"""
        errors = []
        
        # 验证CFX可执行文件
        if self.cfx_pre_executable and not Path(self.cfx_pre_executable).exists():
            errors.append(f"CFX-Pre executable not found: {self.cfx_pre_executable}")
        
        if self.cfx_solver_executable and not Path(self.cfx_solver_executable).exists():
            errors.append(f"CFX-Solver executable not found: {self.cfx_solver_executable}")
        
        # 验证CFX文件
        if self.cfx_file_path and not Path(self.cfx_file_path).exists():
            errors.append(f"CFX file not found: {self.cfx_file_path}")
        
        # 验证基础路径
        if self.base_path and not Path(self.base_path).parent.exists():
            errors.append(f"Base path parent directory not found: {Path(self.base_path).parent}")
        
        # 验证模板目录
        if not Path(self.template_dir).exists():
            errors.append(f"Template directory not found: {self.template_dir}")
        
        # 验证背压参数
        if not self.pressure_list:
            errors.append("Pressure list cannot be empty")
        
        if not all(isinstance(p, (int, float)) for p in self.pressure_list):
            errors.append("Pressure list must contain numeric values")
        
        # 验证SSH配置
        if self.ssh_key and not Path(self.ssh_key).expanduser().exists():
            errors.append(f"SSH key not found: {self.ssh_key}")
        
        return errors
    
    def _auto_detect_cfx_paths(self):
        """自动检测CFX路径"""
        logger.info("正在自动检测CFX安装...")
        
        try:
            # 暂时禁用自动检测，使用配置文件中的路径
            logger.info("CFX自动检测已禁用，使用配置文件中的路径")
            return
            
            # 原始代码保留但注释掉
            # detected_config = auto_detect_cfx_config()
            # if detected_config:
            #     self.cfx_home = detected_config.get("cfx_home", "")
            #     self.cfx_pre_executable = detected_config.get("cfx_pre_executable", "")
            #     self.cfx_solver_executable = detected_config.get("cfx_solver_executable", "")
            #     self.cfx_version = detected_config.get("cfx_version", "")
            #     logger.info(f"自动检测到CFX {self.cfx_version} 在 {self.cfx_home}")
            # else:
            #     logger.warning("未能自动检测到CFX安装，请手动配置")
                
        except Exception as e:
            logger.error(f"自动检测CFX路径时出错: {e}")
    
    def get_cfx_installation_options(self) -> List[Dict[str, str]]:
        """获取所有可用的CFX安装选项"""
        # 暂时返回空列表
        logger.info("CFX安装选项检测已禁用")
        return []
        
        # 原始代码保留但注释掉
        # detector = CFXPathDetector()
        # installations = detector.detect_cfx_installations()
        # return installations
    
    def select_cfx_installation(self, version: str = None) -> bool:
        """选择特定版本的CFX安装"""
        # 暂时禁用CFX安装选择
        logger.info("CFX安装选择已禁用")
        return True
        
        # 原始代码保留但注释掉
        # detector = CFXPathDetector()
        # installations = detector.detect_cfx_installations()
        # 
        # if not installations:
        #     logger.error("未检测到CFX安装")
        #     return False
        # 
        # # 如果指定版本，查找该版本
        # if version:
        #     for installation in installations:
        #         if installation["version"] == version:
        #             self._apply_installation_config(installation)
        #             return True
        #     logger.error(f"未找到CFX版本 {version}")
        #     return False
        # 
        # # 否则选择最新版本
        # best_installation = detector.get_best_installation()
        # if best_installation:
        #     self._apply_installation_config(best_installation)
        #     return True
        # 
        # return False
    
    def _apply_installation_config(self, installation: Dict[str, str]):
        """应用安装配置"""
        self.cfx_home = installation["cfx_home"]
        self.cfx_pre_executable = installation["cfx_pre_executable"]
        self.cfx_solver_executable = installation["cfx_solver_executable"]
        self.cfx_version = installation["version"]
        
        logger.info(f"已选择CFX {self.cfx_version} 在 {self.cfx_home}")
    
    def show_detected_installations(self):
        """显示检测到的CFX安装"""
        # 暂时禁用CFX安装显示
        logger.info("CFX安装显示已禁用")
        print("CFX安装检测已禁用，请手动配置CFX路径")
        return
        
        # 原始代码保留但注释掉
        # detector = CFXPathDetector()
        # installations = detector.detect_cfx_installations()
        # 
        # if installations:
        #     print(f"检测到 {len(installations)} 个CFX安装:")
        #     for i, installation in enumerate(installations, 1):
        #         print(f"{i}. CFX {installation['version']}")
        #         print(f"   路径: {installation['cfx_home']}")
        #         print(f"   CFX-Pre: {installation['cfx_pre_executable']}")
        #         print(f"   CFX-Solver: {installation['cfx_solver_executable']}")
        #         print()
        # else:
        #     print("未检测到CFX安装")
        #     print("请确保ANSYS CFX已正确安装，或手动配置路径")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            # CFX环境配置
            'cfx_home': self.cfx_home,
            'cfx_pre_executable': self.cfx_pre_executable,
            'cfx_solver_executable': self.cfx_solver_executable,
            'cfx_version': self.cfx_version,
            'auto_detect_cfx': self.auto_detect_cfx,
            'cfx_bin_path': self.cfx_bin_path,
            
            # 远程CFX配置
            'remote_cfx_home': self.remote_cfx_home,
            'remote_cfx_bin_path': self.remote_cfx_bin_path,
            
            # 作业配置
            'job_name': self.job_name,
            'base_path': self.base_path,
            
            # CFX文件配置
            'cfx_file_path': self.cfx_file_path,
            
            # CFX模型配置
            'flow_analysis_name': self.flow_analysis_name,
            'domain_name': self.domain_name,
            'boundary_name': self.boundary_name,
            'outlet_location': self.outlet_location,
            'pressure_blend': self.pressure_blend,
            
            # 文件命名配置
            'folder_prefix': self.folder_prefix,
            'def_file_prefix': self.def_file_prefix,
            
            # 背压参数配置
            'pressure_list': self.pressure_list,
            'pressure_unit': self.pressure_unit,
            
            # 服务器配置
            'ssh_host': self.ssh_host,
            'ssh_port': self.ssh_port,
            'ssh_user': self.ssh_user,
            'ssh_key': self.ssh_key,
            'remote_base_path': self.remote_base_path,
            
            # Slurm配置
            'partition': self.partition,
            'nodes': self.nodes,
            'tasks_per_node': self.tasks_per_node,
            'time_limit': self.time_limit,
            'memory_per_node': self.memory_per_node,
            
            # 模板配置
            'template_dir': self.template_dir,
            'session_template': self.session_template,
            'slurm_template': self.slurm_template,
            'batch_template': self.batch_template,
            
            # 文件配置
            'ini_file': self.ini_file,
            'backup_enabled': self.backup_enabled,
            'cleanup_temp_files': self.cleanup_temp_files,
            
            # 报告配置
            'report_dir': self.report_dir
        }
    
    @classmethod
    def from_yaml(cls, config_file: str) -> 'CFXAutomationConfig':
        """从YAML文件加载配置"""
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        # 过滤掉None值和不相关的键
        filtered_data = {k: v for k, v in config_data.items() if v is not None}
        
        return cls(**filtered_data)
    
    def to_yaml(self, config_file: str):
        """保存配置到YAML文件"""
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, allow_unicode=True)


class ConfigManager:
    """配置管理器 - 支持多环境配置"""
    
    def __init__(self, config_dir: str = "./config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
    def get_config(self, environment: str = "development") -> CFXAutomationConfig:
        """获取指定环境的配置"""
        config_file = self.config_dir / f"{environment}.yaml"
        
        if config_file.exists():
            return CFXAutomationConfig.from_yaml(str(config_file))
        else:
            # 创建默认配置
            config = CFXAutomationConfig()
            config.to_yaml(str(config_file))
            return config
    
    def save_config(self, config: CFXAutomationConfig, environment: str = "development"):
        """保存配置到指定环境"""
        config_file = self.config_dir / f"{environment}.yaml"
        config.to_yaml(str(config_file))
    
    def validate_config(self, config: CFXAutomationConfig) -> bool:
        """验证配置"""
        errors = config.validate()
        if errors:
            print("配置验证失败:")
            for error in errors:
                print(f"  - {error}")
            return False
        return True
    
    def list_environments(self) -> List[str]:
        """列出所有环境"""
        return [f.stem for f in self.config_dir.glob("*.yaml")]


class TemplateManager:
    """模板管理器 - 使用Jinja2处理模板"""
    
    def __init__(self, template_dir: str):
        self.template_dir = Path(template_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def render_template(self, template_name: str, **kwargs) -> str:
        """渲染模板"""
        template = self.env.get_template(template_name)
        return template.render(**kwargs)
    
    def render_to_file(self, template_name: str, output_file: str, **kwargs):
        """渲染模板到文件"""
        content = self.render_template(template_name, **kwargs)
        
        # 确保Unix行结束符（LF），特别是对于.sh文件
        if output_file.endswith('.sh'):
            content = content.replace('\r\n', '\n').replace('\r', '\n')
        
        with open(output_file, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)
    
    def list_templates(self) -> List[str]:
        """列出所有模板"""
        return [f.name for f in self.template_dir.glob("*.j2")]
