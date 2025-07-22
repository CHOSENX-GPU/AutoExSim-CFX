"""
CFX自动化系统包初始化
"""

__version__ = "2.0.0"
__author__ = "CFX Automation Team"
__description__ = "ANSYS CFX HPC集群自动化计算系统"

# 导入主要类
from .config import CFXAutomationConfig, ConfigManager
from .cfx import CFXManager
from .cluster_query import ClusterQueryManager
from .allocation import NodeAllocationManager
from .script_generator import ScriptGenerator
from .transfer import FileTransferManager
from .job_monitor import JobMonitor
from .workflow_orchestrator import WorkflowOrchestrator

# 导入工具函数
from .utils.cfx_detector import auto_detect_cfx_config, verify_cfx_installation

__all__ = [
    "CFXAutomationConfig",
    "ConfigManager", 
    "CFXManager",
    "ClusterQueryManager",
    "NodeAllocationManager",
    "ScriptGenerator",
    "FileTransferManager",
    "JobMonitor",
    "WorkflowOrchestrator",
    "auto_detect_cfx_config",
    "verify_cfx_installation"
]
