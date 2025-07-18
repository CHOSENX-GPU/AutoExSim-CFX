"""
CFX路径自动检测模块
自动检测用户系统中的ANSYS CFX安装路径和可执行文件
"""

import os
import platform
import winreg
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class CFXPathDetector:
    """CFX路径自动检测器"""
    
    def __init__(self):
        self.system = platform.system()
        self.detected_installations = []
    
    def detect_cfx_installations(self) -> List[Dict[str, str]]:
        """
        检测系统中的CFX安装
        
        Returns:
            List[Dict]: 包含检测到的CFX安装信息的列表
            每个字典包含: version, cfx_home, cfx_pre_executable, cfx_solver_executable
        """
        installations = []
        
        if self.system == "Windows":
            installations.extend(self._detect_windows_installations())
        elif self.system == "Linux":
            installations.extend(self._detect_linux_installations())
        else:
            logger.warning(f"不支持的操作系统: {self.system}")
        
        # 验证检测到的安装
        validated_installations = []
        for install in installations:
            if self._validate_installation(install):
                validated_installations.append(install)
        
        self.detected_installations = validated_installations
        return validated_installations
    
    def _detect_windows_installations(self) -> List[Dict[str, str]]:
        """检测Windows系统中的CFX安装"""
        installations = []
        
        # 方法1: 检查注册表
        installations.extend(self._check_windows_registry())
        
        # 方法2: 检查常见安装路径
        installations.extend(self._check_common_windows_paths())
        
        # 方法3: 检查环境变量
        installations.extend(self._check_environment_variables())
        
        return installations
    
    def _detect_linux_installations(self) -> List[Dict[str, str]]:
        """检测Linux系统中的CFX安装"""
        installations = []
        
        # 方法1: 检查常见Linux路径
        installations.extend(self._check_common_linux_paths())
        
        # 方法2: 检查环境变量
        installations.extend(self._check_environment_variables())
        
        # 方法3: 检查PATH中的CFX命令
        installations.extend(self._check_path_commands())
        
        return installations
    
    def _check_windows_registry(self) -> List[Dict[str, str]]:
        """检查Windows注册表中的ANSYS安装信息"""
        installations = []
        
        try:
            # 检查ANSYS注册表项
            registry_paths = [
                r"SOFTWARE\ANSYS Inc",
                r"SOFTWARE\WOW6432Node\ANSYS Inc",
            ]
            
            for registry_path in registry_paths:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path) as key:
                        i = 0
                        while True:
                            try:
                                subkey_name = winreg.EnumKey(key, i)
                                if "CFX" in subkey_name or "v" in subkey_name:
                                    installation = self._parse_registry_entry(registry_path, subkey_name)
                                    if installation:
                                        installations.append(installation)
                                i += 1
                            except OSError:
                                break
                except FileNotFoundError:
                    continue
                    
        except Exception as e:
            logger.warning(f"检查注册表时出错: {e}")
        
        return installations
    
    def _parse_registry_entry(self, registry_path: str, subkey_name: str) -> Optional[Dict[str, str]]:
        """解析注册表条目"""
        try:
            full_path = f"{registry_path}\\{subkey_name}"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, full_path) as key:
                try:
                    install_dir, _ = winreg.QueryValueEx(key, "InstallDir")
                    cfx_home = os.path.join(install_dir, "CFX")
                    
                    if os.path.exists(cfx_home):
                        return self._create_installation_info(cfx_home, subkey_name)
                except FileNotFoundError:
                    pass
        except Exception as e:
            logger.debug(f"解析注册表条目失败 {subkey_name}: {e}")
        
        return None
    
    def _check_common_windows_paths(self) -> List[Dict[str, str]]:
        """检查Windows常见安装路径"""
        installations = []
        
        # 常见的ANSYS安装路径
        common_paths = [
            r"C:\Program Files\ANSYS Inc",
            r"C:\Program Files (x86)\ANSYS Inc",
            r"D:\ANSYS Inc",
            r"E:\ANSYS Inc",
            r"F:\ANSYS Inc",
        ]
        
        for base_path in common_paths:
            if os.path.exists(base_path):
                installations.extend(self._scan_ansys_directory(base_path))
        
        return installations
    
    def _check_common_linux_paths(self) -> List[Dict[str, str]]:
        """检查Linux常见安装路径"""
        installations = []
        
        # 常见的Linux ANSYS安装路径
        common_paths = [
            "/usr/ansys_inc",
            "/opt/ansys_inc",
            "/usr/local/ansys_inc",
            "/home/ansys_inc",
            "/ansys_inc",
        ]
        
        for base_path in common_paths:
            if os.path.exists(base_path):
                installations.extend(self._scan_ansys_directory(base_path))
        
        return installations
    
    def _scan_ansys_directory(self, base_path: str) -> List[Dict[str, str]]:
        """扫描ANSYS目录寻找CFX安装"""
        installations = []
        
        try:
            for item in os.listdir(base_path):
                item_path = os.path.join(base_path, item)
                if os.path.isdir(item_path):
                    # 检查是否为版本目录 (如 v221, v231等)
                    if item.startswith('v') and item[1:].isdigit():
                        cfx_path = os.path.join(item_path, "CFX")
                        if os.path.exists(cfx_path):
                            installation = self._create_installation_info(cfx_path, item)
                            if installation:
                                installations.append(installation)
        except Exception as e:
            logger.debug(f"扫描目录失败 {base_path}: {e}")
        
        return installations
    
    def _check_environment_variables(self) -> List[Dict[str, str]]:
        """检查环境变量中的CFX路径"""
        installations = []
        
        # 检查常见的CFX环境变量
        cfx_env_vars = [
            "CFX_HOME",
            "ANSYS_CFX_HOME",
            "CFX_ROOT",
            "ANSYS_HOME",
        ]
        
        for env_var in cfx_env_vars:
            env_path = os.environ.get(env_var)
            if env_path and os.path.exists(env_path):
                # 如果路径不直接指向CFX，尝试在其子目录中找
                if os.path.basename(env_path) != "CFX":
                    cfx_path = os.path.join(env_path, "CFX")
                    if os.path.exists(cfx_path):
                        env_path = cfx_path
                
                installation = self._create_installation_info(env_path, f"env_{env_var}")
                if installation:
                    installations.append(installation)
        
        return installations
    
    def _check_path_commands(self) -> List[Dict[str, str]]:
        """检查PATH中的CFX命令"""
        installations = []
        
        cfx_commands = ["cfx5pre", "cfx5solve"]
        
        for command in cfx_commands:
            try:
                # 在Linux/Mac上使用which命令
                if self.system in ["Linux", "Darwin"]:
                    import subprocess
                    result = subprocess.run(["which", command], capture_output=True, text=True)
                    if result.returncode == 0:
                        command_path = result.stdout.strip()
                        cfx_bin_dir = os.path.dirname(command_path)
                        cfx_home = os.path.dirname(cfx_bin_dir)
                        
                        installation = self._create_installation_info(cfx_home, f"path_{command}")
                        if installation:
                            installations.append(installation)
            except Exception as e:
                logger.debug(f"检查PATH命令失败 {command}: {e}")
        
        return installations
    
    def _create_installation_info(self, cfx_home: str, version_hint: str) -> Optional[Dict[str, str]]:
        """创建安装信息字典"""
        try:
            cfx_home = os.path.abspath(cfx_home)
            bin_dir = os.path.join(cfx_home, "bin")
            
            # 检查bin目录是否存在
            if not os.path.exists(bin_dir):
                return None
            
            # 构建可执行文件路径
            if self.system == "Windows":
                cfx_pre_exe = os.path.join(bin_dir, "cfx5pre.exe")
                cfx_solver_exe = os.path.join(bin_dir, "cfx5solve.exe")
            else:
                cfx_pre_exe = os.path.join(bin_dir, "cfx5pre")
                cfx_solver_exe = os.path.join(bin_dir, "cfx5solve")
            
            # 验证可执行文件是否存在
            if not (os.path.exists(cfx_pre_exe) and os.path.exists(cfx_solver_exe)):
                return None
            
            # 尝试提取版本信息
            version = self._extract_version(cfx_home, version_hint)
            
            return {
                "version": version,
                "cfx_home": cfx_home,
                "cfx_pre_executable": cfx_pre_exe,
                "cfx_solver_executable": cfx_solver_exe,
                "bin_path": bin_dir
            }
            
        except Exception as e:
            logger.debug(f"创建安装信息失败: {e}")
            return None
    
    def _extract_version(self, cfx_home: str, version_hint: str) -> str:
        """提取版本信息"""
        # 从路径中提取版本
        path_parts = cfx_home.split(os.sep)
        for part in path_parts:
            if part.startswith('v') and part[1:].replace('.', '').isdigit():
                return part
        
        # 从版本提示中提取
        if version_hint.startswith('v'):
            return version_hint
        
        # 尝试从版本文件中读取
        version_files = [
            os.path.join(cfx_home, "version.txt"),
            os.path.join(cfx_home, "VERSION"),
            os.path.join(cfx_home, ".version"),
        ]
        
        for version_file in version_files:
            if os.path.exists(version_file):
                try:
                    with open(version_file, 'r') as f:
                        version = f.read().strip()
                        if version:
                            return version
                except:
                    continue
        
        return "unknown"
    
    def _validate_installation(self, installation: Dict[str, str]) -> bool:
        """验证安装是否有效"""
        try:
            # 检查必要的文件是否存在
            required_files = [
                installation["cfx_pre_executable"],
                installation["cfx_solver_executable"]
            ]
            
            for file_path in required_files:
                if not os.path.exists(file_path):
                    logger.debug(f"必要文件不存在: {file_path}")
                    return False
            
            # 检查是否可执行
            for file_path in required_files:
                if not os.access(file_path, os.X_OK):
                    logger.debug(f"文件不可执行: {file_path}")
                    return False
            
            return True
            
        except Exception as e:
            logger.debug(f"验证安装失败: {e}")
            return False
    
    def get_best_installation(self) -> Optional[Dict[str, str]]:
        """获取最佳的CFX安装"""
        if not self.detected_installations:
            return None
        
        # 按版本排序，选择最新版本
        def version_key(installation):
            version = installation["version"]
            if version.startswith('v'):
                try:
                    return int(version[1:])
                except:
                    return 0
            return 0
        
        sorted_installations = sorted(self.detected_installations, key=version_key, reverse=True)
        return sorted_installations[0]
    
    def get_installation_by_version(self, version: str) -> Optional[Dict[str, str]]:
        """根据版本获取安装"""
        for installation in self.detected_installations:
            if installation["version"] == version:
                return installation
        return None
    
    def list_installations(self) -> List[Tuple[str, str]]:
        """列出所有检测到的安装"""
        return [(inst["version"], inst["cfx_home"]) for inst in self.detected_installations]


def auto_detect_cfx_config() -> Dict[str, str]:
    """
    自动检测CFX配置
    
    Returns:
        Dict: 包含检测到的CFX配置信息
    """
    detector = CFXPathDetector()
    installations = detector.detect_cfx_installations()
    
    if not installations:
        logger.warning("未检测到CFX安装")
        return {}
    
    # 选择最佳安装
    best_installation = detector.get_best_installation()
    
    if best_installation:
        logger.info(f"检测到CFX {best_installation['version']} 在 {best_installation['cfx_home']}")
        return {
            "cfx_home": best_installation["cfx_home"],
            "cfx_pre_executable": best_installation["cfx_pre_executable"],
            "cfx_solver_executable": best_installation["cfx_solver_executable"],
            "cfx_version": best_installation["version"]
        }
    
    return {}


if __name__ == "__main__":
    # 测试检测功能
    logging.basicConfig(level=logging.INFO)
    
    print("正在检测CFX安装...")
    detector = CFXPathDetector()
    installations = detector.detect_cfx_installations()
    
    if installations:
        print(f"检测到 {len(installations)} 个CFX安装:")
        for i, installation in enumerate(installations, 1):
            print(f"{i}. CFX {installation['version']}")
            print(f"   路径: {installation['cfx_home']}")
            print(f"   CFX-Pre: {installation['cfx_pre_executable']}")
            print(f"   CFX-Solver: {installation['cfx_solver_executable']}")
            print()
        
        best = detector.get_best_installation()
        if best:
            print(f"推荐使用: CFX {best['version']}")
    else:
        print("未检测到CFX安装")
