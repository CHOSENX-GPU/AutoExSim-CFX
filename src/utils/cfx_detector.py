"""
CFX环境自动检测模块
支持Windows和Linux环境下的CFX路径自动检测
"""

import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import Dict, Optional, List, Tuple
import platform

logger = logging.getLogger(__name__)


class CFXPathDetector:
    """CFX路径检测器"""
    
    def __init__(self):
        self.system = platform.system()
        self.logger = logging.getLogger(__name__)
    
    def detect_cfx_installation(self) -> Dict[str, str]:
        """
        自动检测CFX安装路径
        
        Returns:
            Dict包含CFX相关路径信息
        """
        cfx_info = {
            "cfx_home": "",
            "cfx_bin_path": "",
            "cfx_pre_executable": "",
            "cfx_solver_executable": "",
            "cfx_version": "",
            "detection_method": ""
        }
        
        try:
            if self.system == "Windows":
                cfx_info = self._detect_windows_cfx()
            elif self.system == "Linux":
                cfx_info = self._detect_linux_cfx()
            else:
                self.logger.warning(f"Unsupported operating system: {self.system}")
        
        except Exception as e:
            self.logger.error(f"Error detecting CFX installation: {e}")
        
        return cfx_info
    
    def _detect_windows_cfx(self) -> Dict[str, str]:
        """Windows环境CFX检测"""
        cfx_info = {
            "cfx_home": "",
            "cfx_bin_path": "",
            "cfx_pre_executable": "",
            "cfx_solver_executable": "",
            "cfx_version": "",
            "detection_method": ""
        }
        
        # 方法1: 检查注册表
        try:
            registry_path = self._check_windows_registry()
            if registry_path:
                cfx_info.update(self._validate_cfx_path(registry_path, "Windows Registry"))
                if cfx_info["cfx_home"]:
                    return cfx_info
        except ImportError:
            self.logger.warning("pywin32 not available, skipping registry detection")
        except Exception as e:
            self.logger.debug(f"Registry detection failed: {e}")
        
        # 方法2: 检查环境变量
        env_path = self._check_environment_variables()
        if env_path:
            cfx_info.update(self._validate_cfx_path(env_path, "Environment Variables"))
            if cfx_info["cfx_home"]:
                return cfx_info
        
        # 方法3: 检查常见安装路径
        common_paths = [
            r"C:\Program Files\ANSYS Inc",
            r"C:\ANSYS Inc",
            r"D:\ANSYS Inc",
            r"C:\Program Files (x86)\ANSYS Inc"
        ]
        
        for base_path in common_paths:
            found_path = self._search_cfx_in_directory(base_path)
            if found_path:
                cfx_info.update(self._validate_cfx_path(found_path, "Common Paths"))
                if cfx_info["cfx_home"]:
                    return cfx_info
        
        # 方法4: 检查PATH环境变量
        path_cfx = self._check_path_for_cfx()
        if path_cfx:
            cfx_info.update(path_cfx)
            cfx_info["detection_method"] = "PATH Environment"
        
        return cfx_info
    
    def _detect_linux_cfx(self) -> Dict[str, str]:
        """Linux环境CFX检测"""
        cfx_info = {
            "cfx_home": "",
            "cfx_bin_path": "",
            "cfx_pre_executable": "",
            "cfx_solver_executable": "",
            "cfx_version": "",
            "detection_method": ""
        }
        
        # 方法1: 检查环境变量
        env_path = self._check_environment_variables()
        if env_path:
            cfx_info.update(self._validate_cfx_path(env_path, "Environment Variables"))
            if cfx_info["cfx_home"]:
                return cfx_info
        
        # 方法2: 检查常见安装路径
        common_paths = [
            "/usr/ansys_inc",
            "/opt/ansys_inc",
            "/ansys_inc",
            "/usr/local/ansys_inc",
            "/home/ansys_inc"
        ]
        
        for base_path in common_paths:
            found_path = self._search_cfx_in_directory(base_path)
            if found_path:
                cfx_info.update(self._validate_cfx_path(found_path, "Common Paths"))
                if cfx_info["cfx_home"]:
                    return cfx_info
        
        # 方法3: 使用which命令查找
        path_cfx = self._check_path_for_cfx()
        if path_cfx:
            cfx_info.update(path_cfx)
            cfx_info["detection_method"] = "which command"
        
        return cfx_info
    
    def _check_windows_registry(self) -> Optional[str]:
        """检查Windows注册表中的CFX安装信息"""
        try:
            import winreg
            
            # ANSYS注册表路径
            registry_paths = [
                r"SOFTWARE\ANSYS Inc",
                r"SOFTWARE\WOW6432Node\ANSYS Inc"
            ]
            
            for reg_path in registry_paths:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                        # 枚举所有子键（版本）
                        i = 0
                        while True:
                            try:
                                version_key = winreg.EnumKey(key, i)
                                if "CFX" in version_key or version_key.startswith("v"):
                                    version_path = f"{reg_path}\\{version_key}"
                                    cfx_path = self._get_cfx_path_from_registry(version_path)
                                    if cfx_path:
                                        return cfx_path
                                i += 1
                            except WindowsError:
                                break
                except WindowsError:
                    continue
        
        except ImportError:
            raise
        except Exception as e:
            self.logger.debug(f"Registry check failed: {e}")
        
        return None
    
    def _get_cfx_path_from_registry(self, registry_path: str) -> Optional[str]:
        """从注册表路径获取CFX安装路径"""
        try:
            import winreg
            
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path) as key:
                try:
                    install_path, _ = winreg.QueryValueEx(key, "ANSYSROOT")
                    return install_path
                except WindowsError:
                    try:
                        install_path, _ = winreg.QueryValueEx(key, "InstallPath")
                        return install_path
                    except WindowsError:
                        pass
        except Exception as e:
            self.logger.debug(f"Failed to read registry path {registry_path}: {e}")
        
        return None
    
    def _check_environment_variables(self) -> Optional[str]:
        """检查环境变量中的CFX路径"""
        env_vars = ["ANSYS_ROOT", "CFX_HOME", "ANSYSROOT", "ANSYS_INC_ROOT"]
        
        for var in env_vars:
            path = os.environ.get(var)
            if path and os.path.exists(path):
                self.logger.debug(f"Found CFX path in environment variable {var}: {path}")
                return path
        
        return None
    
    def _search_cfx_in_directory(self, base_path: str) -> Optional[str]:
        """在指定目录中搜索CFX安装"""
        if not os.path.exists(base_path):
            return None
        
        try:
            # 查找CFX相关目录
            for item in os.listdir(base_path):
                item_path = os.path.join(base_path, item)
                if os.path.isdir(item_path):
                    # 检查是否是版本目录（如v231, v241等）
                    if item.startswith("v") and len(item) >= 3:
                        cfx_path = os.path.join(item_path, "CFX")
                        if os.path.exists(cfx_path):
                            return cfx_path
                    
                    # 直接检查CFX目录
                    if "CFX" in item.upper():
                        return item_path
        
        except (OSError, PermissionError) as e:
            self.logger.debug(f"Error searching directory {base_path}: {e}")
        
        return None
    
    def _check_path_for_cfx(self) -> Dict[str, str]:
        """检查PATH环境变量中的CFX可执行文件"""
        cfx_info = {
            "cfx_home": "",
            "cfx_bin_path": "",
            "cfx_pre_executable": "",
            "cfx_solver_executable": "",
            "cfx_version": "",
            "detection_method": ""
        }
        
        # 检查可执行文件
        executables = ["cfx5pre", "cfx5solve"]
        if self.system == "Windows":
            executables = [exe + ".exe" for exe in executables]
        
        found_executables = {}
        for exe in executables:
            path = self._which(exe)
            if path:
                found_executables[exe] = path
        
        if found_executables:
            # 从可执行文件路径推断CFX_HOME
            first_exe_path = list(found_executables.values())[0]
            bin_dir = os.path.dirname(first_exe_path)
            cfx_home = os.path.dirname(bin_dir)
            
            cfx_info["cfx_home"] = cfx_home
            cfx_info["cfx_bin_path"] = bin_dir
            cfx_info["cfx_pre_executable"] = found_executables.get(
                "cfx5pre.exe" if self.system == "Windows" else "cfx5pre", ""
            )
            cfx_info["cfx_solver_executable"] = found_executables.get(
                "cfx5solve.exe" if self.system == "Windows" else "cfx5solve", ""
            )
        
        return cfx_info
    
    def _which(self, executable: str) -> Optional[str]:
        """跨平台的which命令实现"""
        try:
            if self.system == "Windows":
                result = subprocess.run(
                    ["where", executable], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                if result.returncode == 0:
                    return result.stdout.strip().split('\n')[0]
            else:
                result = subprocess.run(
                    ["which", executable], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                if result.returncode == 0:
                    return result.stdout.strip()
        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            self.logger.debug(f"Error running which/where for {executable}: {e}")
        
        return None
    
    def _validate_cfx_path(self, cfx_path: str, method: str) -> Dict[str, str]:
        """验证CFX路径并返回详细信息"""
        cfx_info = {
            "cfx_home": "",
            "cfx_bin_path": "",
            "cfx_pre_executable": "",
            "cfx_solver_executable": "",
            "cfx_version": "",
            "detection_method": method
        }
        
        if not os.path.exists(cfx_path):
            return cfx_info
        
        # 查找bin目录
        bin_path = os.path.join(cfx_path, "bin")
        if not os.path.exists(bin_path):
            # 可能路径就是bin目录
            if os.path.basename(cfx_path) == "bin":
                bin_path = cfx_path
                cfx_path = os.path.dirname(cfx_path)
            else:
                return cfx_info
        
        # 检查可执行文件
        executables = {
            "cfx5pre": "cfx5pre.exe" if self.system == "Windows" else "cfx5pre",
            "cfx5solve": "cfx5solve.exe" if self.system == "Windows" else "cfx5solve"
        }
        
        found_executables = {}
        for key, exe_name in executables.items():
            exe_path = os.path.join(bin_path, exe_name)
            if os.path.exists(exe_path):
                found_executables[key] = exe_path
        
        if found_executables:
            cfx_info["cfx_home"] = cfx_path
            cfx_info["cfx_bin_path"] = bin_path
            cfx_info["cfx_pre_executable"] = found_executables.get("cfx5pre", "")
            cfx_info["cfx_solver_executable"] = found_executables.get("cfx5solve", "")
            
            # 尝试获取版本信息
            version = self._get_cfx_version(found_executables.get("cfx5pre", ""))
            cfx_info["cfx_version"] = version
            
            self.logger.info(f"CFX installation found via {method}: {cfx_path}")
        
        return cfx_info
    
    def _get_cfx_version(self, cfx_pre_path: str) -> str:
        """获取CFX版本信息"""
        if not cfx_pre_path or not os.path.exists(cfx_pre_path):
            return ""
        
        try:
            # 尝试运行CFX并获取版本信息
            result = subprocess.run(
                [cfx_pre_path, "-help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # 解析版本信息
            output = result.stdout + result.stderr
            for line in output.split('\n'):
                if 'version' in line.lower() or 'release' in line.lower():
                    # 提取版本号
                    import re
                    version_match = re.search(r'(\d+\.\d+)', line)
                    if version_match:
                        return version_match.group(1)
        
        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            self.logger.debug(f"Error getting CFX version: {e}")
        
        return ""


def auto_detect_cfx_config() -> Dict[str, str]:
    """
    自动检测CFX配置的便捷函数
    
    Returns:
        CFX配置字典
    """
    detector = CFXPathDetector()
    return detector.detect_cfx_installation()


def verify_cfx_installation(cfx_config: Dict[str, str]) -> Tuple[bool, List[str]]:
    """
    验证CFX安装
    
    Args:
        cfx_config: CFX配置字典
    
    Returns:
        (是否有效, 错误信息列表)
    """
    errors = []
    
    # 检查基本路径
    if not cfx_config.get("cfx_home"):
        errors.append("CFX home directory not found")
        return False, errors
    
    if not os.path.exists(cfx_config["cfx_home"]):
        errors.append(f"CFX home directory does not exist: {cfx_config['cfx_home']}")
    
    # 检查可执行文件
    for exe_key in ["cfx_pre_executable", "cfx_solver_executable"]:
        exe_path = cfx_config.get(exe_key)
        if exe_path and not os.path.exists(exe_path):
            errors.append(f"{exe_key} not found: {exe_path}")
    
    # 如果没有找到任何可执行文件
    if not cfx_config.get("cfx_pre_executable") and not cfx_config.get("cfx_solver_executable"):
        errors.append("No CFX executables found")
    
    is_valid = len(errors) == 0
    return is_valid, errors
