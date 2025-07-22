"""
CFX模块测试
测试CFX环境检测和文件生成功能
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from config import CFXAutomationConfig
from cfx import CFXManager


class TestCFXManager:
    """CFX管理器测试"""
    
    @pytest.fixture
    def mock_config(self):
        """创建模拟配置"""
        return CFXAutomationConfig(
            project_name="test_cfx",
            cfx_mode="local",
            auto_detect_cfx=True,
            cfx_home="C:/Program Files/ANSYS Inc/v231/CFX",
            cluster_type="university",
            scheduler_type="SLURM",
            ssh_host="test.edu",
            ssh_user="user",
            remote_base_path="/home/user",
            pressure_list=[2187, 2189],
            job_settings={"partition": "cpu"}
        )
    
    def test_cfx_manager_initialization(self, mock_config):
        """测试CFX管理器初始化"""
        manager = CFXManager(mock_config)
        assert manager.config == mock_config
        assert manager.ssh_client is None
        assert manager.logger is not None
    
    @patch('cfx.platform.system')
    @patch('cfx.Path.exists')
    def test_detect_cfx_local_windows(self, mock_exists, mock_system, mock_config):
        """测试Windows本地CFX检测"""
        mock_system.return_value = "Windows"
        mock_exists.return_value = True
        
        manager = CFXManager(mock_config)
        result = manager._detect_cfx_local()
        
        assert result is not None
        assert "CFX" in result
    
    @patch('cfx.platform.system')
    @patch('cfx.Path.exists')
    def test_detect_cfx_local_linux(self, mock_exists, mock_system, mock_config):
        """测试Linux本地CFX检测"""
        mock_system.return_value = "Linux"
        mock_exists.return_value = True
        
        manager = CFXManager(mock_config)
        result = manager._detect_cfx_local()
        
        assert result is not None
    
    def test_generate_pre_content(self, mock_config):
        """测试Pre文件内容生成"""
        manager = CFXManager(mock_config)
        
        template_vars = {
            "model_file": "test_model.def",
            "pressure_values": [2187, 2189],
            "output_prefix": "CFX_P"
        }
        
        content = manager._generate_pre_content(template_vars)
        
        assert "2187" in content
        assert "2189" in content
        assert "test_model.def" in content
    
    @patch('cfx.subprocess.run')
    def test_run_cfx_pre_local(self, mock_run, mock_config):
        """测试本地CFX Pre执行"""
        mock_run.return_value = Mock(returncode=0, stdout="Success", stderr="")
        
        manager = CFXManager(mock_config)
        manager.cfx_pre_path = "mock_cfx_pre"
        
        result = manager._run_cfx_pre_local("test.pre")
        
        assert result is True
        mock_run.assert_called_once()
    
    @patch('cfx.CFXManager._connect_ssh')
    @patch('cfx.CFXManager._execute_ssh_command')
    def test_run_cfx_pre_server(self, mock_execute, mock_connect, mock_config):
        """测试服务器CFX Pre执行"""
        mock_config.cfx_mode = "server"
        mock_execute.return_value = (0, "Success", "")
        
        manager = CFXManager(mock_config)
        result = manager._run_cfx_pre_server("test.pre", "/remote/path")
        
        assert result is True
        mock_execute.assert_called()
    
    def test_generate_def_file_info(self, mock_config):
        """测试def文件信息生成"""
        manager = CFXManager(mock_config)
        
        pressures = [2187, 2189, 2191]
        result = manager._generate_def_file_info(pressures)
        
        assert len(result) == 3
        assert all("CFX_P_" in item["name"] for item in result)
        assert all(str(p) in item["name"] for item, p in zip(result, pressures))


if __name__ == "__main__":
    pytest.main([__file__])
