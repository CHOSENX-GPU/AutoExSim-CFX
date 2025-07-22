"""
CFX核心模块
处理CFX相关操作：环境检测、.pre文件生成、.def文件生成等
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from jinja2 import Environment, FileSystemLoader, Template

from .config import CFXAutomationConfig
from .utils.cfx_detector import CFXPathDetector, auto_detect_cfx_config, verify_cfx_installation


class CFXEnvironmentError(Exception):
    """CFX环境错误"""
    pass


class CFXFileError(Exception):
    """CFX文件操作错误"""
    pass


class CFXManager:
    """CFX管理器"""
    
    def __init__(self, config: CFXAutomationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # CFX环境信息
        self.local_cfx_config = {}
        self.remote_cfx_config = {}
        
        # 初始化时检测CFX环境
        if config.auto_detect_cfx:
            self._detect_cfx_environment()
    
    def _detect_cfx_environment(self) -> None:
        """检测CFX环境"""
        self.logger.info("开始检测CFX环境...")
        
        try:
            # 检测本地CFX（如果需要）
            if self.config.cfx_mode == "local":
                self.local_cfx_config = auto_detect_cfx_config()
                is_valid, errors = verify_cfx_installation(self.local_cfx_config)
                
                if is_valid:
                    self.logger.info(f"本地CFX环境检测成功: {self.local_cfx_config['cfx_home']}")
                    # 更新配置
                    self._update_config_from_detection(self.local_cfx_config, is_local=True)
                else:
                    self.logger.warning(f"本地CFX环境检测失败: {errors}")
                    if not self.config.cfx_home:
                        raise CFXEnvironmentError(f"本地CFX环境不可用: {'; '.join(errors)}")
            
            # 服务器CFX配置验证将在SSH连接时进行
            self.logger.info("CFX环境检测完成")
            
        except Exception as e:
            self.logger.error(f"CFX环境检测失败: {e}")
            raise CFXEnvironmentError(f"CFX环境检测失败: {e}")
    
    def _update_config_from_detection(self, cfx_config: Dict[str, str], is_local: bool = True) -> None:
        """根据检测结果更新配置"""
        if is_local:
            self.logger.debug(f"检测到的CFX配置: {cfx_config}")
            
            if not self.config.cfx_home:
                self.config.cfx_home = cfx_config.get("cfx_home", "")
            if not self.config.cfx_bin_path:
                self.config.cfx_bin_path = cfx_config.get("cfx_bin_path", "")
            if not self.config.cfx_pre_executable:
                detected_pre = cfx_config.get("cfx_pre_executable", "")
                if detected_pre:
                    self.config.cfx_pre_executable = detected_pre
                elif self.config.cfx_bin_path:
                    # 自动构建可执行文件路径
                    self.config.cfx_pre_executable = os.path.join(self.config.cfx_bin_path, "cfx5pre.exe")
                elif self.config.cfx_home:
                    # 从CFX Home构建路径
                    self.config.cfx_pre_executable = os.path.join(self.config.cfx_home, "bin", "cfx5pre.exe")
                    
            if not self.config.cfx_solver_executable:
                detected_solver = cfx_config.get("cfx_solver_executable", "")
                if detected_solver:
                    self.config.cfx_solver_executable = detected_solver
                elif self.config.cfx_bin_path:
                    self.config.cfx_solver_executable = os.path.join(self.config.cfx_bin_path, "cfx5solve.exe")
                elif self.config.cfx_home:
                    self.config.cfx_solver_executable = os.path.join(self.config.cfx_home, "bin", "cfx5solve.exe")
                    
            if not self.config.cfx_version:
                self.config.cfx_version = cfx_config.get("cfx_version", "")
                
            # 记录最终配置
            self.logger.info(f"CFX配置更新完成:")
            self.logger.info(f"  CFX Home: {self.config.cfx_home}")
            self.logger.info(f"  CFX Pre: {self.config.cfx_pre_executable}")
            self.logger.info(f"  CFX Solver: {self.config.cfx_solver_executable}")
    
    def verify_server_cfx_environment(self, ssh_client) -> bool:
        """
        验证服务器CFX环境
        
        Args:
            ssh_client: SSH客户端连接
            
        Returns:
            bool: 验证是否成功
        """
        try:
            self.logger.info("验证服务器CFX环境...")
            
            # 检查CFX可执行文件
            executables = ["cfx5pre", "cfx5solve"]
            found_executables = {}
            
            for exe in executables:
                # 构建完整的可执行文件路径
                if self.config.remote_cfx_bin_path:
                    exe_path = os.path.join(self.config.remote_cfx_bin_path, exe).replace('\\', '/')
                elif self.config.remote_cfx_home:
                    exe_path = os.path.join(self.config.remote_cfx_home, "bin", exe).replace('\\', '/')
                else:
                    exe_path = exe  # 假设在PATH中
                
                # 直接检查文件是否存在且可执行
                test_cmd = f"test -x '{exe_path}' && echo 'FOUND' || echo 'NOT_FOUND'"
                stdin, stdout, stderr = ssh_client.exec_command(test_cmd)
                result = stdout.read().decode().strip()
                
                if result == "FOUND":
                    found_executables[exe] = exe_path
                    self.logger.debug(f"找到服务器CFX可执行文件: {exe} -> {exe_path}")
                else:
                    # 如果直接路径不存在，尝试使用which命令
                    stdin, stdout, stderr = ssh_client.exec_command(f"which {exe} 2>/dev/null || echo 'NOT_FOUND'")
                    which_result = stdout.read().decode().strip()
                    if which_result and which_result != "NOT_FOUND":
                        found_executables[exe] = which_result
                        self.logger.debug(f"通过which找到CFX可执行文件: {exe} -> {which_result}")
            
            if not found_executables:
                # 提供更详细的错误信息
                error_msg = f"服务器上未找到CFX可执行文件。检查的路径: "
                if self.config.remote_cfx_bin_path:
                    error_msg += f"bin路径={self.config.remote_cfx_bin_path}, "
                if self.config.remote_cfx_home:
                    error_msg += f"home路径={self.config.remote_cfx_home}/bin, "
                error_msg += "以及系统PATH"
                raise CFXEnvironmentError(error_msg)
            
            # 更新远程CFX配置
            if found_executables:
                # 从第一个可执行文件推断CFX路径
                first_exe = list(found_executables.values())[0]
                remote_bin_path = os.path.dirname(first_exe)
                remote_cfx_home = os.path.dirname(remote_bin_path)
                
                if not self.config.remote_cfx_home:
                    self.config.remote_cfx_home = remote_cfx_home
                if not self.config.remote_cfx_bin_path:
                    self.config.remote_cfx_bin_path = remote_bin_path
            
            self.logger.info("服务器CFX环境验证成功")
            return True
            
        except Exception as e:
            self.logger.error(f"服务器CFX环境验证失败: {e}")
            raise CFXEnvironmentError(f"服务器CFX环境验证失败: {e}")
    
    def generate_pre_files(self, job_configs: List[Dict]) -> List[str]:
        """
        生成.pre文件 - 创建单个包含循环逻辑的.pre文件
        
        Args:
            job_configs: 作业配置列表
            
        Returns:
            List[str]: 生成的.pre文件路径列表（通常只包含一个文件）
        """
        self.logger.info(f"生成包含{len(job_configs)}个压力参数的.pre文件...")
        
        try:
            # 加载模板
            template = self._load_pre_template()
            
            # 提取所有压力值
            pressure_values = [job_config.get("pressure", 0) for job_config in job_configs]
            
            # 准备模板变量
            template_vars = {
                "cfx_file_path": self.config.cfx_file_path,
                "flow_analysis_name": self.config.flow_analysis_name,
                "domain_name": self.config.domain_name,
                "outlet_boundary_name": self.config.outlet_boundary_name,
                "outlet_location": self.config.outlet_location,
                "pressure_blend": self.config.pressure_blend,
                "pressure_unit": self.config.pressure_unit,
                "folder_prefix": self.config.folder_prefix,
                "def_file_prefix": self.config.def_file_prefix,
                "pressure_list": pressure_values,
                "output_base_path": self.config.base_path,
                # CFX相关配置
                "cfx_version": getattr(self.config, 'cfx_version', '22.1'),
                "max_iterations": getattr(self.config, 'max_iterations', 5000),
                "residual_target": getattr(self.config, 'residual_target', '0.000001')
            }
            
            # 生成文件内容
            content = template.render(**template_vars)
            
            # 确定输出文件路径
            filename = "create_def_batch.pre"
            output_path = os.path.join(self.config.base_path, filename)
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"成功生成批量.pre文件: {output_path}")
            return [output_path]
            
        except Exception as e:
            self.logger.error(f"生成.pre文件失败: {e}")
            raise CFXFileError(f"生成.pre文件失败: {e}")
    
    def _load_pre_template(self) -> Template:
        """加载.pre模板文件"""
        template_path = self.config.pre_template_path
        
        if not template_path:
            # 使用默认模板路径
            template_path = os.path.join("templates", "create_def.pre.j2")
        
        if not os.path.exists(template_path):
            raise CFXFileError(f".pre模板文件不存在: {template_path}")
        
        try:
            template_dir = os.path.dirname(template_path)
            template_name = os.path.basename(template_path)
            
            env = Environment(loader=FileSystemLoader(template_dir))
            template = env.get_template(template_name)
            
            self.logger.debug(f"加载.pre模板: {template_path}")
            return template
            
        except Exception as e:
            raise CFXFileError(f"加载.pre模板失败: {e}")
    
    def _generate_single_pre_file(self, template: Template, job_config: Dict, index: int) -> str:
        """生成单个.pre文件"""
        try:
            # 准备模板变量
            template_vars = {
                "cfx_file_path": self.config.cfx_file_path,
                "flow_analysis_name": self.config.flow_analysis_name,
                "domain_name": self.config.domain_name,
                "outlet_boundary_name": self.config.outlet_boundary_name,
                "outlet_location": self.config.outlet_location,
                "pressure_blend": self.config.pressure_blend,
                "pressure_unit": self.config.pressure_unit,
                "folder_prefix": self.config.folder_prefix,
                **job_config  # 合并作业特定配置
            }
            
            # 生成文件内容
            content = template.render(**template_vars)
            
            # 确定输出文件路径
            pressure = job_config.get("pressure", index)
            filename = f"create_def_P{pressure}.pre"
            output_path = os.path.join(self.config.base_path, filename)
            
            # 写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return output_path
            
        except Exception as e:
            raise CFXFileError(f"生成.pre文件失败 (index={index}): {e}")
    
    def generate_def_files_local(self, pre_files: List[str]) -> List[str]:
        """
        在本地生成.def文件
        
        Args:
            pre_files: .pre文件路径列表
            
        Returns:
            List[str]: 生成的.def文件路径列表
        """
        if self.config.cfx_mode != "local":
            raise CFXFileError("CFX模式不是local，无法在本地生成.def文件")
        
        if not self.config.cfx_pre_executable:
            raise CFXFileError("未找到本地CFX Pre可执行文件")
        
        expected_def_count = len(self.config.pressure_list) if hasattr(self.config, 'pressure_list') else len(pre_files)
        self.logger.info(f"开始在本地生成{expected_def_count}个.def文件...")
        
        generated_def_files = []
        
        for pre_file in pre_files:
            try:
                def_files = self._execute_cfx_pre_local(pre_file)
                if def_files:
                    if isinstance(def_files, list):
                        generated_def_files.extend(def_files)
                        self.logger.debug(f"生成.def文件: {def_files}")
                    else:
                        generated_def_files.append(def_files)
                        self.logger.debug(f"生成.def文件: {def_files}")
            except Exception as e:
                self.logger.error(f"生成.def文件失败 ({pre_file}): {e}")
                # 可以选择继续或停止
                continue
        
        self.logger.info(f"成功生成{len(generated_def_files)}个.def文件")
        return generated_def_files
    
    def _execute_cfx_pre_local(self, pre_file: str) -> List[str]:
        """执行本地CFX Pre生成.def文件"""
        try:
            # 构造命令，规范化路径并转换为正斜杠
            normalized_pre_file = os.path.normpath(pre_file).replace('\\', '/')
            cmd = [
                self.config.cfx_pre_executable,
                "-batch", normalized_pre_file
            ]
            
            # 检查CFX文件是否存在
            if self.config.cfx_file_path and not os.path.exists(self.config.cfx_file_path):
                self.logger.error(f"CFX文件不存在: {self.config.cfx_file_path}")
                return None
            
            # 执行命令
            # 规范化路径以避免斜杠混用问题
            work_dir = os.path.dirname(os.path.normpath(pre_file)) or self.config.base_path
            work_dir = os.path.normpath(work_dir)
            
            self.logger.info(f"执行CFX Pre命令: {' '.join(cmd)}")
            self.logger.info(f"工作目录: {work_dir}")
            
            result = subprocess.run(
                cmd,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            # 记录详细输出
            self.logger.info(f"CFX Pre返回码: {result.returncode}")
            if result.stdout:
                self.logger.info(f"CFX Pre输出: {result.stdout}")
            if result.stderr:
                self.logger.warning(f"CFX Pre错误: {result.stderr}")
            
            if result.returncode != 0:
                self.logger.error(f"CFX Pre执行失败: {result.stderr}")
                return None
            
            # 查找生成的.def文件
            pre_dir = os.path.dirname(pre_file)
            pre_name = os.path.splitext(os.path.basename(pre_file))[0]
            
            self.logger.info(f"查找本次生成的.def文件...")
            
            # 根据我们的模板，.def文件应该在子目录中
            # 优先查找本次应该生成的.def文件
            expected_def_files = []
            for pressure in self.config.pressure_list:
                folder_name = f"{self.config.folder_prefix}{pressure}"
                folder_path = os.path.join(pre_dir, folder_name)
                
                # 如果def_file_prefix为空，尝试多种可能的文件名
                if not self.config.def_file_prefix:
                    possible_names = [
                        f"{pressure}.def",
                        f"Old_Cluster_{pressure}.def",
                        f"New_Cluster_{pressure}.def"
                    ]
                else:
                    possible_names = [f"{self.config.def_file_prefix}{pressure}.def"]
                
                # 查找存在的文件
                found_file = None
                for def_name in possible_names:
                    def_path = os.path.join(folder_path, def_name)
                    self.logger.debug(f"检查期望的.def文件: {def_path}")
                    if os.path.exists(def_path):
                        found_file = def_path
                        self.logger.info(f"找到生成的.def文件: {def_path}")
                        break
                
                if found_file:
                    expected_def_files.append(found_file)
            
            # 检查期望的文件是否都存在
            if expected_def_files:
                return expected_def_files
            
            # 如果没找到期望的.def文件，报告问题
            self.logger.warning(f"未找到期望的.def文件")
            for pressure in self.config.pressure_list:
                folder_name = f"{self.config.folder_prefix}{pressure}"
                folder_path = os.path.join(pre_dir, folder_name)
                self.logger.warning(f"  检查目录: {folder_path}")
            return []
            
        except subprocess.TimeoutExpired:
            self.logger.error(f"CFX Pre执行超时: {pre_file}")
            return None
        except Exception as e:
            self.logger.error(f"执行CFX Pre失败: {e}")
            return None
    
    def prepare_server_cfx_generation(self, ssh_client, pre_files: List[str], remote_dir: str) -> bool:
        """
        准备在服务器上生成.def文件（上传.pre和.cfx文件）
        
        Args:
            ssh_client: SSH客户端
            pre_files: .pre文件列表
            remote_dir: 远程目录
            
        Returns:
            bool: 准备是否成功
        """
        try:
            self.logger.info("准备服务器CFX生成环境...")
            
            # 确保远程目录存在
            ssh_client.exec_command(f"mkdir -p {remote_dir}")
            
            # 上传.cfx文件（如果存在）
            if self.config.cfx_file_path and os.path.exists(self.config.cfx_file_path):
                remote_cfx_path = f"{remote_dir}/{os.path.basename(self.config.cfx_file_path)}"
                sftp = ssh_client.open_sftp()
                sftp.put(self.config.cfx_file_path, remote_cfx_path)
                sftp.close()
                self.logger.debug(f"上传.cfx文件: {remote_cfx_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"准备服务器CFX环境失败: {e}")
            return False
    
    def generate_def_files_server(self, ssh_client, pre_files: List[str], remote_dir: str) -> List[str]:
        """
        在服务器上生成.def文件
        
        Args:
            ssh_client: SSH客户端
            pre_files: 远程.pre文件路径列表
            remote_dir: 远程工作目录
            
        Returns:
            List[str]: 生成的远程.def文件路径列表
        """
        self.logger.info(f"开始在服务器生成{len(pre_files)}个.def文件...")
        
        generated_def_files = []
        
        for pre_file in pre_files:
            try:
                def_file = self._execute_cfx_pre_server(ssh_client, pre_file, remote_dir)
                if def_file:
                    generated_def_files.append(def_file)
                    self.logger.debug(f"生成远程.def文件: {def_file}")
            except Exception as e:
                self.logger.error(f"服务器生成.def文件失败 ({pre_file}): {e}")
                continue
        
        self.logger.info(f"成功在服务器生成{len(generated_def_files)}个.def文件")
        return generated_def_files
    
    def _execute_cfx_pre_server(self, ssh_client, pre_file: str, remote_dir: str) -> Optional[str]:
        """在服务器执行CFX Pre"""
        try:
            # 构造远程命令
            cfx_pre_cmd = self.config.get_remote_cfx_executable_path("cfx5pre")
            cmd = f"cd {remote_dir} && {cfx_pre_cmd} -batch {pre_file}"
            
            self.logger.debug(f"执行远程CFX Pre命令: {cmd}")
            
            # 执行命令
            stdin, stdout, stderr = ssh_client.exec_command(cmd)
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status != 0:
                error_msg = stderr.read().decode()
                self.logger.error(f"远程CFX Pre执行失败: {error_msg}")
                return None
            
            # 查找生成的.def文件
            pre_name = os.path.splitext(os.path.basename(pre_file))[0]
            possible_def_names = [
                f"{pre_name}.def",
                f"{pre_name}_001.def"
            ]
            
            for def_name in possible_def_names:
                def_path = f"{remote_dir}/{def_name}"
                # 检查文件是否存在
                stdin, stdout, stderr = ssh_client.exec_command(f"test -f {def_path} && echo 'EXISTS'")
                result = stdout.read().decode().strip()
                if result == "EXISTS":
                    return def_path
            
            self.logger.warning(f"未找到生成的远程.def文件: {pre_file}")
            return None
            
        except Exception as e:
            self.logger.error(f"执行远程CFX Pre失败: {e}")
            return None
    
    def get_cfx_version_info(self) -> Dict[str, str]:
        """获取CFX版本信息"""
        version_info = {
            "local_version": self.config.cfx_version,
            "remote_version": self.config.remote_cfx_version,
            "local_cfx_home": self.config.cfx_home,
            "remote_cfx_home": self.config.remote_cfx_home
        }
        return version_info
