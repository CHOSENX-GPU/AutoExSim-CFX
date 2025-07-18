"""
Ansys CFX自动化系统
基于Python的CFX全自动化流程实现
"""

__version__ = "1.0.2"
__author__ = "CHSOENX"
__email__ = "zja20021112@gamil.com"

from .cfx import CFXPreAutomation
from .slurm import SlurmJobManager
from .transfer import FileTransferManager
from .workflow import CFXAutomationWorkflow
from .config import CFXAutomationConfig, ConfigManager, TemplateManager

__all__ = [
    'CFXPreAutomation',
    'SlurmJobManager', 
    'FileTransferManager',
    'CFXAutomationWorkflow',
    'CFXAutomationConfig',
    'ConfigManager',
    'TemplateManager'
]
