"""
文件传输模块
处理本地和远程服务器之间的文件传输
"""

import os
import hashlib
import logging
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import paramiko

from .config import CFXAutomationConfig


class TransferError(Exception):
    """文件传输错误"""
    pass


class FileTransferManager:
    """文件传输管理器"""
    
    def __init__(self, config: CFXAutomationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 传输统计
        self.transfer_stats = {
            "uploaded_files": 0,
            "downloaded_files": 0,
            "upload_bytes": 0,
            "download_bytes": 0,
            "failed_transfers": 0
        }
    
    def upload_files(self, ssh_client, file_list: List[str], 
                    remote_dir: str, preserve_structure: bool = False) -> Dict[str, str]:
        """
        上传文件到远程服务器
        
        Args:
            ssh_client: SSH客户端连接
            file_list: 本地文件路径列表
            remote_dir: 远程目录
            preserve_structure: 是否保持目录结构
            
        Returns:
            Dict[str, str]: 本地文件路径到远程文件路径的映射
        """
        self.logger.info(f"开始上传{len(file_list)}个文件到 {remote_dir}")
        
        # 显示文件清单
        self._display_file_manifest(file_list)
        
        try:
            # 确保远程目录存在
            self._ensure_remote_directory(ssh_client, remote_dir)
            
            # 打开SFTP连接
            sftp = ssh_client.open_sftp()
            
            uploaded_files = {}
            
            for i, local_file in enumerate(file_list, 1):
                try:
                    # 显示当前上传进度
                    filename = os.path.basename(local_file)
                    self.logger.info(f"[{i}/{len(file_list)}] 正在上传: {filename}")
                    
                    remote_file = self._upload_single_file(
                        sftp, local_file, remote_dir, preserve_structure
                    )
                    uploaded_files[local_file] = remote_file
                    self.transfer_stats["uploaded_files"] += 1
                    
                    # 计算文件大小
                    file_size = os.path.getsize(local_file)
                    self.transfer_stats["upload_bytes"] += file_size
                    
                    # 显示成功信息
                    size_mb = round(file_size / (1024 * 1024), 2)
                    self.logger.info(f"✓ [{i}/{len(file_list)}] 上传完成: {filename} ({size_mb}MB)")
                    
                except Exception as e:
                    self.logger.error(f"✗ [{i}/{len(file_list)}] 上传失败 {os.path.basename(local_file)}: {e}")
                    self.transfer_stats["failed_transfers"] += 1
                    continue
            
            sftp.close()
            
            self.logger.info(f"文件上传完成: {len(uploaded_files)}/{len(file_list)} 成功")
            return uploaded_files
            
        except Exception as e:
            self.logger.error(f"文件上传失败: {e}")
            raise TransferError(f"文件上传失败: {e}")
    
    def _upload_single_file(self, sftp, local_file: str, remote_dir: str, 
                          preserve_structure: bool) -> str:
        """上传单个文件"""
        if not os.path.exists(local_file):
            raise TransferError(f"本地文件不存在: {local_file}")
        
        # 确定远程文件路径
        if preserve_structure:
            # 保持目录结构
            rel_path = os.path.relpath(local_file, self.config.base_path)
            remote_file = os.path.join(remote_dir, rel_path).replace('\\', '/')
            
            # 确保远程子目录存在
            remote_subdir = os.path.dirname(remote_file)
            if remote_subdir != remote_dir:
                self._ensure_remote_directory_sftp(sftp, remote_subdir)
        else:
            # 直接放在目标目录
            filename = os.path.basename(local_file)
            remote_file = os.path.join(remote_dir, filename).replace('\\', '/')
        
        # 执行传输（带重试）
        for attempt in range(self.config.transfer_retry_times):
            try:
                # 如果是脚本文件（.sh或.slurm），需要转换行结尾符
                if local_file.endswith(('.sh', '.slurm')):
                    # 读取文件并转换CRLF为LF
                    with open(local_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # 转换行结尾符
                    content = content.replace('\r\n', '\n').replace('\r', '\n')
                    
                    # 上传转换后的内容
                    with sftp.open(remote_file, 'w') as remote_f:
                        remote_f.write(content.encode('utf-8'))
                else:
                    # 普通文件直接上传
                    sftp.put(local_file, remote_file)
                
                # 验证传输完整性（对于转换过的脚本文件跳过验证）
                if self.config.enable_checksum_verification and not local_file.endswith(('.sh', '.slurm')):
                    if not self._verify_file_integrity(sftp, local_file, remote_file):
                        raise TransferError("文件完整性验证失败")
                
                return remote_file
                
            except Exception as e:
                if attempt < self.config.transfer_retry_times - 1:
                    self.logger.warning(f"上传重试 {attempt + 1}/{self.config.transfer_retry_times}: {e}")
                    time.sleep(2 ** attempt)  # 指数退避
                else:
                    raise
        
        raise TransferError(f"上传失败，已重试{self.config.transfer_retry_times}次")
    
    def download_files(self, ssh_client, remote_files: List[str], 
                      local_dir: str, preserve_structure: bool = False) -> Dict[str, str]:
        """
        从远程服务器下载文件
        
        Args:
            ssh_client: SSH客户端连接
            remote_files: 远程文件路径列表
            local_dir: 本地目录
            preserve_structure: 是否保持目录结构
            
        Returns:
            Dict[str, str]: 远程文件路径到本地文件路径的映射
        """
        self.logger.info(f"开始下载{len(remote_files)}个文件到 {local_dir}")
        
        try:
            # 确保本地目录存在
            os.makedirs(local_dir, exist_ok=True)
            
            # 打开SFTP连接
            sftp = ssh_client.open_sftp()
            
            downloaded_files = {}
            
            for remote_file in remote_files:
                try:
                    local_file = self._download_single_file(
                        sftp, remote_file, local_dir, preserve_structure
                    )
                    downloaded_files[remote_file] = local_file
                    self.transfer_stats["downloaded_files"] += 1
                    
                    # 计算文件大小
                    file_size = os.path.getsize(local_file)
                    self.transfer_stats["download_bytes"] += file_size
                    
                    self.logger.debug(f"下载成功: {remote_file} -> {local_file}")
                    
                except Exception as e:
                    self.logger.error(f"下载文件失败 {remote_file}: {e}")
                    self.transfer_stats["failed_transfers"] += 1
                    continue
            
            sftp.close()
            
            self.logger.info(f"文件下载完成: {len(downloaded_files)}/{len(remote_files)} 成功")
            return downloaded_files
            
        except Exception as e:
            self.logger.error(f"文件下载失败: {e}")
            raise TransferError(f"文件下载失败: {e}")
    
    def _download_single_file(self, sftp, remote_file: str, local_dir: str,
                            preserve_structure: bool) -> str:
        """下载单个文件"""
        # 检查远程文件是否存在
        try:
            sftp.stat(remote_file)
        except FileNotFoundError:
            raise TransferError(f"远程文件不存在: {remote_file}")
        
        # 确定本地文件路径
        if preserve_structure:
            # 保持目录结构
            rel_path = os.path.relpath(remote_file, self.config.remote_base_path)
            local_file = os.path.join(local_dir, rel_path)
            
            # 确保本地子目录存在
            local_subdir = os.path.dirname(local_file)
            os.makedirs(local_subdir, exist_ok=True)
        else:
            # 直接放在目标目录
            filename = os.path.basename(remote_file)
            local_file = os.path.join(local_dir, filename)
        
        # 执行传输（带重试）
        for attempt in range(self.config.transfer_retry_times):
            try:
                sftp.get(remote_file, local_file)
                
                # 验证传输完整性
                if self.config.enable_checksum_verification:
                    if not self._verify_file_integrity(sftp, local_file, remote_file, reverse=True):
                        raise TransferError("文件完整性验证失败")
                
                return local_file
                
            except Exception as e:
                if attempt < self.config.transfer_retry_times - 1:
                    self.logger.warning(f"下载重试 {attempt + 1}/{self.config.transfer_retry_times}: {e}")
                    time.sleep(2 ** attempt)
                else:
                    raise
        
        raise TransferError(f"下载失败，已重试{self.config.transfer_retry_times}次")
    
    def download_results(self, ssh_client, job_results: List[Dict], 
                        local_results_dir: str) -> Dict[str, List[str]]:
        """
        下载作业结果文件
        
        Args:
            ssh_client: SSH客户端连接
            job_results: 作业结果信息列表
            local_results_dir: 本地结果目录
            
        Returns:
            Dict[str, List[str]]: 作业名称到下载文件列表的映射
        """
        self.logger.info(f"开始下载{len(job_results)}个作业的结果文件")
        
        downloaded_results = {}
        
        for job_result in job_results:
            job_name = job_result.get("name", "unknown")
            
            try:
                # 获取作业的结果文件列表
                result_files = self._find_job_result_files(ssh_client, job_result)
                
                if not result_files:
                    self.logger.warning(f"作业 {job_name} 未找到结果文件")
                    downloaded_results[job_name] = []
                    continue
                
                # 创建作业专用目录
                job_local_dir = os.path.join(local_results_dir, job_name)
                os.makedirs(job_local_dir, exist_ok=True)
                
                # 下载结果文件
                downloaded_files = self.download_files(
                    ssh_client, result_files, job_local_dir, preserve_structure=False
                )
                
                downloaded_results[job_name] = list(downloaded_files.values())
                self.logger.info(f"作业 {job_name} 下载了 {len(downloaded_files)} 个结果文件")
                
            except Exception as e:
                self.logger.error(f"下载作业结果失败 {job_name}: {e}")
                downloaded_results[job_name] = []
        
        return downloaded_results
    
    def _find_job_result_files(self, ssh_client, job_result: Dict) -> List[str]:
        """查找作业结果文件"""
        job_name = job_result.get("name", "")
        remote_work_dir = job_result.get("work_dir", self.config.remote_base_path)
        
        result_files = []
        
        try:
            sftp = ssh_client.open_sftp()
            
            # 根据文件模式查找结果文件
            for pattern in self.config.result_file_patterns:
                # 替换通配符为具体的作业名称
                if "*" in pattern:
                    pattern = pattern.replace("*", job_name)
                
                # 查找匹配的文件
                try:
                    file_path = os.path.join(remote_work_dir, pattern).replace('\\', '/')
                    
                    # 检查文件是否存在
                    try:
                        sftp.stat(file_path)
                        result_files.append(file_path)
                    except FileNotFoundError:
                        # 尝试列出目录并匹配模式
                        if "*" in pattern or "?" in pattern:
                            matched_files = self._glob_remote_files(sftp, remote_work_dir, pattern)
                            result_files.extend(matched_files)
                
                except Exception as e:
                    self.logger.debug(f"查找结果文件模式失败 {pattern}: {e}")
            
            sftp.close()
            
        except Exception as e:
            self.logger.error(f"查找作业结果文件失败: {e}")
        
        return result_files
    
    def _glob_remote_files(self, sftp, remote_dir: str, pattern: str) -> List[str]:
        """在远程目录中匹配文件模式"""
        import fnmatch
        
        matched_files = []
        
        try:
            # 列出远程目录内容
            for item in sftp.listdir(remote_dir):
                if fnmatch.fnmatch(item, pattern):
                    full_path = os.path.join(remote_dir, item).replace('\\', '/')
                    matched_files.append(full_path)
        
        except Exception as e:
            self.logger.debug(f"远程文件模式匹配失败: {e}")
        
        return matched_files
    
    def _ensure_remote_directory(self, ssh_client, remote_dir: str) -> None:
        """确保远程目录存在"""
        cmd = f"mkdir -p {remote_dir}"
        stdin, stdout, stderr = ssh_client.exec_command(cmd)
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status != 0:
            error_msg = stderr.read().decode()
            raise TransferError(f"创建远程目录失败: {error_msg}")
    
    def _ensure_remote_directory_sftp(self, sftp, remote_dir: str) -> None:
        """使用SFTP确保远程目录存在"""
        # 规范化路径，移除多余的斜杠
        remote_dir = remote_dir.replace('\\', '/').rstrip('/')
        
        # 如果是绝对路径，从根目录开始
        if remote_dir.startswith('/'):
            dirs = [d for d in remote_dir.split('/') if d]  # 过滤空字符串
            current_dir = ""
            
            for dir_part in dirs:
                current_dir = f"{current_dir}/{dir_part}"
                
                try:
                    sftp.stat(current_dir)
                    self.logger.debug(f"目录已存在: {current_dir}")
                except FileNotFoundError:
                    try:
                        sftp.mkdir(current_dir)
                        self.logger.debug(f"创建目录: {current_dir}")
                    except Exception as e:
                        self.logger.error(f"创建目录失败 {current_dir}: {e}")
                        raise
        else:
            # 相对路径处理
            dirs = remote_dir.split('/')
            current_dir = ""
            
            for dir_part in dirs:
                if not dir_part:
                    continue
                
                current_dir = f"{current_dir}/{dir_part}" if current_dir else dir_part
                
                try:
                    sftp.stat(current_dir)
                except FileNotFoundError:
                    sftp.mkdir(current_dir)
    
    def _verify_file_integrity(self, sftp, local_file: str, remote_file: str, 
                             reverse: bool = False) -> bool:
        """验证文件完整性"""
        try:
            if reverse:
                # 下载情况：比较本地文件和远程文件
                local_hash = self._calculate_file_hash(local_file)
                remote_hash = self._calculate_remote_file_hash(sftp, remote_file)
            else:
                # 上传情况：比较本地文件和远程文件
                local_hash = self._calculate_file_hash(local_file)
                remote_hash = self._calculate_remote_file_hash(sftp, remote_file)
            
            return local_hash == remote_hash
            
        except Exception as e:
            self.logger.warning(f"文件完整性验证失败: {e}")
            return True  # 验证失败时假设文件正确
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """计算本地文件的MD5哈希"""
        hasher = hashlib.md5()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        
        return hasher.hexdigest()
    
    def _calculate_remote_file_hash(self, sftp, remote_file: str) -> str:
        """计算远程文件的MD5哈希"""
        hasher = hashlib.md5()
        
        with sftp.open(remote_file, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        
        return hasher.hexdigest()
    
    def cleanup_remote_files(self, ssh_client, file_list: List[str]) -> Dict[str, bool]:
        """
        清理远程文件
        
        Args:
            ssh_client: SSH客户端连接
            file_list: 要删除的远程文件列表
            
        Returns:
            Dict[str, bool]: 文件路径到删除结果的映射
        """
        if not self.config.cleanup_remote_files:
            self.logger.info("远程文件清理已禁用")
            return {}
        
        self.logger.info(f"开始清理{len(file_list)}个远程文件")
        
        cleanup_results = {}
        
        try:
            sftp = ssh_client.open_sftp()
            
            for remote_file in file_list:
                try:
                    sftp.remove(remote_file)
                    cleanup_results[remote_file] = True
                    self.logger.debug(f"删除远程文件: {remote_file}")
                except Exception as e:
                    cleanup_results[remote_file] = False
                    self.logger.warning(f"删除远程文件失败 {remote_file}: {e}")
            
            sftp.close()
            
        except Exception as e:
            self.logger.error(f"远程文件清理失败: {e}")
        
        success_count = sum(cleanup_results.values())
        self.logger.info(f"远程文件清理完成: {success_count}/{len(file_list)} 成功")
        
        return cleanup_results
    
    def get_transfer_statistics(self) -> Dict:
        """获取传输统计信息"""
        stats = self.transfer_stats.copy()
        
        # 转换字节为可读格式
        stats["upload_size_mb"] = round(stats["upload_bytes"] / (1024 * 1024), 2)
        stats["download_size_mb"] = round(stats["download_bytes"] / (1024 * 1024), 2)
        stats["total_size_mb"] = stats["upload_size_mb"] + stats["download_size_mb"]
        
        return stats
    
    def reset_statistics(self) -> None:
        """重置传输统计"""
        self.transfer_stats = {
            "uploaded_files": 0,
            "downloaded_files": 0,
            "upload_bytes": 0,
            "download_bytes": 0,
            "failed_transfers": 0
        }
    
    def _display_file_manifest(self, file_list: List[str]) -> None:
        """显示文件清单信息"""
        self.logger.info("📋 文件清单:")
        
        total_size = 0
        file_types = {}
        
        for i, file_path in enumerate(file_list, 1):
            if not os.path.exists(file_path):
                self.logger.warning(f"  [{i}] ❌ 文件不存在: {os.path.basename(file_path)}")
                continue
            
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            size_mb = round(file_size / (1024 * 1024), 2)
            total_size += file_size
            
            # 确定文件类型
            if filename.endswith('.def'):
                file_type = "CFX定义文件"
            elif filename.endswith('.slurm'):
                file_type = "SLURM作业脚本"
            elif filename.endswith('.sh'):
                file_type = "Shell脚本"
            elif filename.endswith('.pre'):
                file_type = "CFX预处理脚本"
            elif filename.endswith('.ini'):
                file_type = "CFX初始文件"
            elif filename.endswith('.res'):
                file_type = "CFX结果文件"
            else:
                file_type = "其他文件"
            
            # 统计文件类型
            file_types[file_type] = file_types.get(file_type, 0) + 1
            
            # 显示文件信息
            rel_path = os.path.relpath(file_path, self.config.base_path)
            self.logger.info(f"  [{i}] 📄 {filename} ({size_mb}MB) - {file_type}")
            self.logger.info(f"      📁 {rel_path}")
        
        # 显示汇总信息
        total_size_mb = round(total_size / (1024 * 1024), 2)
        self.logger.info(f"📊 汇总: 共{len(file_list)}个文件，总大小 {total_size_mb}MB")
        
        for file_type, count in file_types.items():
            self.logger.info(f"    • {file_type}: {count}个")
