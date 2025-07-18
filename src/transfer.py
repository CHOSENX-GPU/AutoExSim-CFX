"""
文件传输模块
自动化文件传输、SSH连接和远程命令执行
"""

import os
import logging
import paramiko
import stat
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

from .config import CFXAutomationConfig

logger = logging.getLogger(__name__)


class FileTransferManager:
    """文件传输管理类"""
    
    def __init__(self, config: CFXAutomationConfig):
        self.config = config
        self.ssh_client = None
        self.sftp_client = None
        self.is_connected = False
        
    def connect(self) -> bool:
        """
        连接到远程服务器
        
        Returns:
            bool: 连接是否成功
        """
        try:
            logger.info(f"连接到远程服务器: {self.config.ssh_host}:{self.config.ssh_port}")
            
            # 创建SSH客户端
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 连接到服务器
            if self.config.ssh_password:
                # 优先使用密码连接
                self.ssh_client.connect(
                    hostname=self.config.ssh_host,
                    port=self.config.ssh_port,
                    username=self.config.ssh_user,
                    password=self.config.ssh_password,
                    timeout=30,
                    look_for_keys=False,  # 禁用密钥查找
                    allow_agent=False     # 禁用SSH代理
                )
            elif self.config.ssh_key and os.path.exists(Path(self.config.ssh_key).expanduser()):
                # 使用SSH密钥连接
                self.ssh_client.connect(
                    hostname=self.config.ssh_host,
                    port=self.config.ssh_port,
                    username=self.config.ssh_user,
                    key_filename=str(Path(self.config.ssh_key).expanduser()),
                    timeout=30
                )
            else:
                # 使用密码连接
                if hasattr(self.config, 'ssh_password') and self.config.ssh_password:
                    # 使用配置中的密码
                    self.ssh_client.connect(
                        hostname=self.config.ssh_host,
                        port=self.config.ssh_port,
                        username=self.config.ssh_user,
                        password=self.config.ssh_password,
                        timeout=30,
                        look_for_keys=False,
                        allow_agent=False
                    )
                else:
                    # 交互式输入密码
                    import getpass
                    password = getpass.getpass(f"请输入 {self.config.ssh_user}@{self.config.ssh_host} 的密码: ")
                    self.ssh_client.connect(
                        hostname=self.config.ssh_host,
                        port=self.config.ssh_port,
                        username=self.config.ssh_user,
                        password=password,
                        timeout=30,
                        look_for_keys=False,
                        allow_agent=False
                    )
            
            # 创建SFTP客户端
            self.sftp_client = self.ssh_client.open_sftp()
            
            self.is_connected = True
            logger.info("远程服务器连接成功")
            return True
            
        except Exception as e:
            logger.error(f"连接远程服务器失败: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.sftp_client:
            self.sftp_client.close()
            self.sftp_client = None
        
        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None
        
        self.is_connected = False
        logger.info("已断开远程服务器连接")
    
    def execute_remote_command(self, 
                             command: str, 
                             timeout: int = 300) -> Dict[str, Any]:
        """
        执行远程命令
        
        Args:
            command: 要执行的命令
            timeout: 超时时间（秒）
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        if not self.is_connected:
            logger.error("未连接到远程服务器")
            return {'success': False, 'error': '未连接到远程服务器'}
        
        try:
            logger.info(f"执行远程命令: {command}")
            
            stdin, stdout, stderr = self.ssh_client.exec_command(command, timeout=timeout)
            
            # 获取执行结果
            stdout_data = stdout.read().decode('utf-8')
            stderr_data = stderr.read().decode('utf-8')
            return_code = stdout.channel.recv_exit_status()
            
            result = {
                'success': return_code == 0,
                'return_code': return_code,
                'stdout': stdout_data,
                'stderr': stderr_data,
                'command': command
            }
            
            if return_code == 0:
                logger.info(f"远程命令执行成功: {command}")
                if stdout_data:
                    logger.debug(f"命令输出: {stdout_data}")
            else:
                logger.error(f"远程命令执行失败: {command} (返回码: {return_code})")
                if stderr_data:
                    logger.error(f"错误输出: {stderr_data}")
            
            return result
            
        except Exception as e:
            logger.error(f"执行远程命令异常: {e}")
            return {'success': False, 'error': str(e)}
    
    def upload_file(self, 
                   local_path: str, 
                   remote_path: str,
                   preserve_times: bool = True) -> bool:
        """
        上传单个文件
        
        Args:
            local_path: 本地文件路径
            remote_path: 远程文件路径
            preserve_times: 是否保留文件时间戳
            
        Returns:
            bool: 上传是否成功
        """
        if not self.is_connected:
            logger.error("未连接到远程服务器")
            return False
        
        try:
            if not os.path.exists(local_path):
                logger.error(f"本地文件不存在: {local_path}")
                return False
            
            # 确保远程目录存在
            remote_dir = os.path.dirname(remote_path)
            if remote_dir:
                self.create_remote_directory(remote_dir)
            
            # 上传文件
            logger.info(f"上传文件: {local_path} -> {remote_path}")
            self.sftp_client.put(local_path, remote_path)
            
            # 设置时间戳
            if preserve_times:
                local_stat = os.stat(local_path)
                self.sftp_client.utime(remote_path, (local_stat.st_atime, local_stat.st_mtime))
            
            # 验证上传
            if self.remote_file_exists(remote_path):
                logger.info(f"文件上传成功: {remote_path}")
                return True
            else:
                logger.error(f"文件上传失败: {remote_path}")
                return False
                
        except Exception as e:
            logger.error(f"上传文件失败: {local_path} -> {remote_path} - {e}")
            return False
    
    def upload_directory(self, 
                        local_path: str, 
                        remote_path: str,
                        exclude_patterns: List[str] = None,
                        progress_callback: Optional[Callable] = None) -> bool:
        """
        上传整个目录
        
        Args:
            local_path: 本地目录路径
            remote_path: 远程目录路径
            exclude_patterns: 排除的文件模式列表
            progress_callback: 进度回调函数
            
        Returns:
            bool: 上传是否成功
        """
        if not self.is_connected:
            logger.error("未连接到远程服务器")
            return False
        
        try:
            if not os.path.exists(local_path):
                logger.error(f"本地目录不存在: {local_path}")
                return False
            
            if exclude_patterns is None:
                exclude_patterns = ['*.tmp', '*.log', '*.bak', '__pycache__']
            
            logger.info(f"上传目录: {local_path} -> {remote_path}")
            
            # 确保远程目录存在
            self.create_remote_directory(remote_path)
            
            # 递归上传目录内容
            success = True
            total_files = 0
            uploaded_files = 0
            
            # 统计文件数量
            for root, dirs, files in os.walk(local_path):
                for file in files:
                    if not self._should_exclude_file(file, exclude_patterns):
                        total_files += 1
            
            # 上传文件
            for root, dirs, files in os.walk(local_path):
                # 计算相对路径
                rel_path = os.path.relpath(root, local_path)
                if rel_path == '.':
                    remote_root = remote_path
                else:
                    remote_root = os.path.join(remote_path, rel_path).replace('\\', '/')
                
                # 创建远程目录
                self.create_remote_directory(remote_root)
                
                # 上传文件
                for file in files:
                    if self._should_exclude_file(file, exclude_patterns):
                        continue
                    
                    local_file = os.path.join(root, file)
                    remote_file = os.path.join(remote_root, file).replace('\\', '/')
                    
                    if self.upload_file(local_file, remote_file):
                        uploaded_files += 1
                    else:
                        success = False
                    
                    # 调用进度回调
                    if progress_callback:
                        progress_callback(uploaded_files, total_files)
            
            if success:
                logger.info(f"目录上传成功: {uploaded_files}/{total_files} 个文件")
            else:
                logger.warning(f"目录上传部分失败: {uploaded_files}/{total_files} 个文件")
            
            return success
            
        except Exception as e:
            logger.error(f"上传目录失败: {local_path} -> {remote_path} - {e}")
            return False
    
    def download_file(self, 
                     remote_path: str, 
                     local_path: str,
                     preserve_times: bool = True) -> bool:
        """
        下载单个文件
        
        Args:
            remote_path: 远程文件路径
            local_path: 本地文件路径
            preserve_times: 是否保留文件时间戳
            
        Returns:
            bool: 下载是否成功
        """
        if not self.is_connected:
            logger.error("未连接到远程服务器")
            return False
        
        try:
            if not self.remote_file_exists(remote_path):
                logger.error(f"远程文件不存在: {remote_path}")
                return False
            
            # 确保本地目录存在
            local_dir = os.path.dirname(local_path)
            if local_dir:
                os.makedirs(local_dir, exist_ok=True)
            
            # 下载文件
            logger.info(f"下载文件: {remote_path} -> {local_path}")
            self.sftp_client.get(remote_path, local_path)
            
            # 设置时间戳
            if preserve_times:
                remote_stat = self.sftp_client.stat(remote_path)
                os.utime(local_path, (remote_stat.st_atime, remote_stat.st_mtime))
            
            # 验证下载
            if os.path.exists(local_path):
                logger.info(f"文件下载成功: {local_path}")
                return True
            else:
                logger.error(f"文件下载失败: {local_path}")
                return False
                
        except Exception as e:
            logger.error(f"下载文件失败: {remote_path} -> {local_path} - {e}")
            return False
    
    def sync_directory(self, 
                      local_path: str, 
                      remote_path: str,
                      exclude_patterns: List[str] = None,
                      dry_run: bool = False) -> bool:
        """
        同步目录到远程服务器
        
        Args:
            local_path: 本地目录路径
            remote_path: 远程目录路径
            exclude_patterns: 排除的文件模式列表
            dry_run: 是否只模拟运行
            
        Returns:
            bool: 同步是否成功
        """
        logger.info(f"同步目录: {local_path} -> {remote_path}")
        
        if dry_run:
            logger.info("模拟运行模式 - 不会实际传输文件")
            return self._simulate_sync(local_path, remote_path, exclude_patterns)
        else:
            return self.upload_directory(local_path, remote_path, exclude_patterns)
    
    def create_remote_directory(self, remote_path: str) -> bool:
        """
        创建远程目录
        
        Args:
            remote_path: 远程目录路径
            
        Returns:
            bool: 创建是否成功
        """
        try:
            # 使用mkdir -p命令创建目录
            result = self.execute_remote_command(f"mkdir -p {remote_path}")
            return result['success']
            
        except Exception as e:
            logger.error(f"创建远程目录失败: {remote_path} - {e}")
            return False
    
    def remote_file_exists(self, remote_path: str) -> bool:
        """
        检查远程文件是否存在
        
        Args:
            remote_path: 远程文件路径
            
        Returns:
            bool: 文件是否存在
        """
        try:
            result = self.execute_remote_command(f"test -f {remote_path}")
            return result['success']
            
        except Exception as e:
            logger.debug(f"检查远程文件失败: {remote_path} - {e}")
            return False
    
    def remote_directory_exists(self, remote_path: str) -> bool:
        """
        检查远程目录是否存在
        
        Args:
            remote_path: 远程目录路径
            
        Returns:
            bool: 目录是否存在
        """
        try:
            result = self.execute_remote_command(f"test -d {remote_path}")
            return result['success']
            
        except Exception as e:
            logger.debug(f"检查远程目录失败: {remote_path} - {e}")
            return False
    
    def get_remote_file_info(self, remote_path: str) -> Dict[str, Any]:
        """
        获取远程文件信息
        
        Args:
            remote_path: 远程文件路径
            
        Returns:
            Dict[str, Any]: 文件信息
        """
        try:
            result = self.execute_remote_command(f"stat {remote_path}")
            
            if result['success']:
                # 解析stat输出
                stat_output = result['stdout']
                file_info = {
                    'exists': True,
                    'path': remote_path,
                    'stat_output': stat_output
                }
                
                # 提取文件大小
                import re
                size_match = re.search(r'Size:\s+(\d+)', stat_output)
                if size_match:
                    file_info['size'] = int(size_match.group(1))
                
                return file_info
            else:
                return {'exists': False, 'path': remote_path}
                
        except Exception as e:
            logger.error(f"获取远程文件信息失败: {remote_path} - {e}")
            return {'exists': False, 'path': remote_path, 'error': str(e)}
    
    def _should_exclude_file(self, filename: str, exclude_patterns: List[str]) -> bool:
        """
        检查文件是否应该被排除
        
        Args:
            filename: 文件名
            exclude_patterns: 排除模式列表
            
        Returns:
            bool: 是否应该排除
        """
        if not exclude_patterns:
            return False
        
        import fnmatch
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(filename, pattern):
                return True
        return False
    
    def _simulate_sync(self, 
                      local_path: str, 
                      remote_path: str,
                      exclude_patterns: List[str]) -> bool:
        """
        模拟同步操作
        
        Args:
            local_path: 本地目录路径
            remote_path: 远程目录路径
            exclude_patterns: 排除模式列表
            
        Returns:
            bool: 模拟是否成功
        """
        try:
            print(f"\n=== 同步模拟 ===")
            print(f"本地目录: {local_path}")
            print(f"远程目录: {remote_path}")
            print(f"排除模式: {exclude_patterns}")
            print()
            
            total_files = 0
            total_size = 0
            
            for root, dirs, files in os.walk(local_path):
                for file in files:
                    if self._should_exclude_file(file, exclude_patterns):
                        continue
                    
                    local_file = os.path.join(root, file)
                    rel_path = os.path.relpath(local_file, local_path)
                    remote_file = os.path.join(remote_path, rel_path).replace('\\', '/')
                    
                    file_size = os.path.getsize(local_file)
                    total_files += 1
                    total_size += file_size
                    
                    print(f"将上传: {rel_path} ({file_size} 字节)")
            
            print(f"\n总计: {total_files} 个文件, {total_size} 字节")
            print("=== 模拟结束 ===\n")
            
            return True
            
        except Exception as e:
            logger.error(f"模拟同步失败: {e}")
            return False
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()
    
    def get_connection_status(self) -> Dict[str, Any]:
        """
        获取连接状态
        
        Returns:
            Dict[str, Any]: 连接状态信息
        """
        return {
            'is_connected': self.is_connected,
            'host': self.config.ssh_host,
            'port': self.config.ssh_port,
            'user': self.config.ssh_user,
            'key_file': self.config.ssh_key,
            'remote_base_path': self.config.remote_base_path
        }
    
    def test_connection(self) -> bool:
        """
        测试连接
        
        Returns:
            bool: 连接测试是否成功
        """
        try:
            if not self.is_connected:
                if not self.connect():
                    return False
            
            # 执行简单的测试命令
            result = self.execute_remote_command("echo 'Connection test successful'")
            return result['success']
            
        except Exception as e:
            logger.error(f"连接测试失败: {e}")
            return False
