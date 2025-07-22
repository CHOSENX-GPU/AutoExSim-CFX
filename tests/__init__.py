"""
CFX自动化计算系统测试模块
使用pytest进行单元测试
"""

import pytest
import sys
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
