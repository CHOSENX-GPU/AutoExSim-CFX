"""
配置模块测试
测试配置加载、验证和序列化功能
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch

from config import CFXAutomationConfig, ConfigManager


class TestCFXAutomationConfig:
    """配置类测试"""
    
    def test_config_creation(self):
        """测试配置对象创建"""
        config_data = {
            "project_name": "test_project",
            "cfx_mode": "local",
            "cluster_type": "university",
            "scheduler_type": "SLURM",
            "ssh_host": "test.cluster.edu",
            "ssh_user": "test_user",
            "remote_base_path": "/home/test_user",
            "pressure_list": [2187, 2189],
            "job_settings": {
                "partition": "cpu",
                "tasks_per_node": 32
            }
        }
        
        config = CFXAutomationConfig(**config_data)
        assert config.project_name == "test_project"
        assert config.cfx_mode == "local"
        assert len(config.pressure_list) == 2
    
    def test_config_validation(self):
        """测试配置验证"""
        # 有效配置
        valid_config = CFXAutomationConfig(
            project_name="test",
            cfx_mode="local",
            cluster_type="university",
            scheduler_type="SLURM",
            ssh_host="test.edu",
            ssh_user="user",
            remote_base_path="/home/user",
            pressure_list=[2187],
            job_settings={"partition": "cpu"}
        )
        
        assert valid_config.validate() == []
        
        # 无效配置
        invalid_config = CFXAutomationConfig(
            project_name="",  # 空项目名
            cfx_mode="invalid",  # 无效模式
            cluster_type="university",
            scheduler_type="SLURM",
            ssh_host="",  # 空主机
            ssh_user="user",
            remote_base_path="/home/user",
            pressure_list=[],  # 空压力列表
            job_settings={}
        )
        
        errors = invalid_config.validate()
        assert len(errors) > 0


class TestConfigManager:
    """配置管理器测试"""
    
    def test_load_config(self):
        """测试配置加载"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                "project_name": "test_project",
                "cfx_mode": "local",
                "cluster_type": "university",
                "scheduler_type": "SLURM",
                "ssh_host": "test.cluster.edu",
                "ssh_user": "test_user",
                "remote_base_path": "/home/test_user",
                "pressure_list": [2187, 2189],
                "job_settings": {"partition": "cpu", "tasks_per_node": 32}
            }
            yaml.dump(config_data, f)
            temp_file = f.name
        
        try:
            config = ConfigManager.load_config(temp_file)
            assert config.project_name == "test_project"
            assert config.cfx_mode == "local"
        finally:
            Path(temp_file).unlink()
    
    def test_save_config(self):
        """测试配置保存"""
        config_data = {
            "project_name": "test_save",
            "cfx_mode": "local",
            "cluster_type": "university",
            "scheduler_type": "SLURM",
            "ssh_host": "test.edu",
            "ssh_user": "user",
            "remote_base_path": "/home/user",
            "pressure_list": [2187],
            "job_settings": {"partition": "cpu"}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_file = f.name
        
        try:
            ConfigManager.save_config(config_data, temp_file)
            
            # 验证保存的文件
            with open(temp_file, 'r', encoding='utf-8') as f:
                loaded_data = yaml.safe_load(f)
            
            assert loaded_data["project_name"] == "test_save"
            assert loaded_data["cfx_mode"] == "local"
        finally:
            Path(temp_file).unlink()


if __name__ == "__main__":
    pytest.main([__file__])
