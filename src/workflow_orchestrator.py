"""
工作流编排模块
协调整个CFX自动化流程的执行
"""

import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import paramiko

from .config import CFXAutomationConfig
from .cfx import CFXManager
from .cluster_query import ClusterQueryManager
from .script_generator import ScriptGenerator
from .transfer import FileTransferManager
from .job_monitor import JobMonitor


class WorkflowError(Exception):
    """工作流执行错误"""
    pass


class WorkflowOrchestrator:
    """工作流编排器"""
    
    def __init__(self, config: CFXAutomationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 初始化各个模块
        self.cfx_manager = CFXManager(config)
        self.cluster_query = ClusterQueryManager(config) if config.enable_node_detection else None
        self.script_generator = ScriptGenerator(config)
        self.transfer_manager = FileTransferManager(config)
        self.job_monitor = JobMonitor(config)
        
        # SSH连接
        self.ssh_client = None
        
        # 执行状态
        self.execution_state = {
            "current_step": "",
            "completed_steps": [],
            "failed_steps": [],
            "start_time": None,
            "end_time": None,
            "total_jobs": 0,
            "successful_jobs": 0
        }
    
    def execute_full_workflow(self, job_configs: List[Dict]) -> Dict:
        """
        执行完整的工作流程
        
        Args:
            job_configs: 作业配置列表
            
        Returns:
            Dict: 执行结果报告
        """
        self.logger.info("开始执行CFX自动化工作流程...")
        
        try:
            # 初始化执行状态
            self._initialize_execution_state(job_configs)
            
            # 步骤1: 连接服务器
            self._execute_step("connect_server", self._connect_to_server)
            
            # 步骤2: 验证CFX环境
            self._execute_step("verify_cfx", self._verify_cfx_environment)
            
            # 步骤3: 生成.pre文件
            pre_files = self._execute_step("generate_pre", 
                                         lambda: self.cfx_manager.generate_pre_files(job_configs))
            
            # 步骤4: 生成.def文件（根据模式）
            def_files = self._execute_step("generate_def", 
                                         lambda: self._generate_def_files(pre_files, job_configs))
            
            # 步骤5: 集群节点查询（如果启用）
            cluster_status = None
            if self.config.enable_node_detection:
                cluster_status = self._execute_step("query_cluster", 
                                                  lambda: self.cluster_query.query_cluster_nodes(self.ssh_client))
            
            # 步骤6: 生成作业脚本（包含智能节点分配）
            # 使用简化的作业配置，智能分配在脚本生成时进行
            simple_jobs = self._create_simple_job_configs(job_configs, def_files)
            scripts = self._execute_step("generate_scripts", 
                                       lambda: self.script_generator.generate_job_scripts(simple_jobs, cluster_status))
            
            # 步骤8: 上传文件
            self._execute_step("upload_files", 
                             lambda: self._upload_files(def_files, scripts))
            
            # 步骤9: 提交作业
            submitted_jobs = self._execute_step("submit_jobs", 
                                              lambda: self._submit_jobs(scripts["submit_script"]))
            
            # 步骤10: 监控作业（如果启用）
            monitoring_report = None
            if self.config.enable_monitoring:
                monitoring_report = self._execute_step("monitor_jobs", 
                                                     lambda: self._monitor_jobs(submitted_jobs))
            
            # 生成最终报告
            report = self._generate_final_report(
                job_configs, simple_jobs, scripts, monitoring_report
            )
            
            self.execution_state["end_time"] = datetime.now().isoformat()
            self.logger.info("CFX自动化工作流程执行完成")
            
            return report
            
        except Exception as e:
            self.logger.error(f"工作流程执行失败: {e}")
            self.execution_state["end_time"] = datetime.now().isoformat()
            raise WorkflowError(f"工作流程执行失败: {e}")
        
        finally:
            # 清理资源
            self._cleanup_resources()
    
    def _initialize_execution_state(self, job_configs: List[Dict]) -> None:
        """初始化执行状态"""
        self.execution_state.update({
            "current_step": "",
            "completed_steps": [],
            "failed_steps": [],
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "total_jobs": len(job_configs),
            "successful_jobs": 0
        })
    
    def _execute_step(self, step_name: str, step_function) -> any:
        """执行工作流步骤"""
        self.execution_state["current_step"] = step_name
        self.logger.info(f"执行步骤: {step_name}")
        
        try:
            result = step_function()
            self.execution_state["completed_steps"].append(step_name)
            self.logger.info(f"步骤完成: {step_name}")
            return result
            
        except Exception as e:
            self.execution_state["failed_steps"].append(step_name)
            self.logger.error(f"步骤失败 {step_name}: {e}")
            raise WorkflowError(f"步骤失败 {step_name}: {e}")
    
    def _connect_to_server(self) -> None:
        """连接到服务器"""
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 连接参数
            connect_kwargs = {
                "hostname": self.config.ssh_host,
                "port": self.config.ssh_port,
                "username": self.config.ssh_user,
                "timeout": 30
            }
            
            # 认证方式
            if self.config.ssh_key and os.path.exists(self.config.ssh_key):
                connect_kwargs["key_filename"] = self.config.ssh_key
            elif self.config.ssh_password:
                connect_kwargs["password"] = self.config.ssh_password
            else:
                raise WorkflowError("未配置SSH认证信息")
            
            self.ssh_client.connect(**connect_kwargs)
            self.logger.info(f"已连接到服务器: {self.config.ssh_host}")
            
        except Exception as e:
            raise WorkflowError(f"服务器连接失败: {e}")
    
    def _verify_cfx_environment(self) -> None:
        """验证CFX环境"""
        # 检查是否配置了跳过CFX验证（老集群使用module system）
        skip_verification = getattr(self.config, 'skip_cfx_verification', False)
        self.logger.info(f"CFX验证设置: skip_cfx_verification = {skip_verification}")
        
        if skip_verification:
            self.logger.info("跳过服务器CFX环境验证 (老集群使用module system)")
            # 如果是local模式，仍需验证本地CFX环境是否可用
            if self.config.cfx_mode == "local":
                if not self.config.cfx_pre_executable:
                    self.logger.error("本地CFX环境未配置: cfx_pre_executable为空")
                    raise WorkflowError("本地CFX环境未配置或不可用")
                else:
                    self.logger.info(f"本地CFX环境已配置: {self.config.cfx_pre_executable}")
            return
            
        # 正常验证服务器CFX环境
        self.logger.info("执行正常的服务器CFX环境验证")
        if not self.cfx_manager.verify_server_cfx_environment(self.ssh_client):
            raise WorkflowError("服务器CFX环境验证失败")
        
        # 如果是local模式，验证本地CFX环境
        if self.config.cfx_mode == "local":
            if not self.config.cfx_pre_executable:
                raise WorkflowError("本地CFX环境未配置或不可用")
    
    def _generate_def_files(self, pre_files: List[str], job_configs: List[Dict]) -> List[str]:
        """生成.def文件"""
        if self.config.cfx_mode == "local":
            # 本地生成.def文件
            return self.cfx_manager.generate_def_files_local(pre_files)
        else:
            # 服务器生成.def文件
            # 首先上传.pre文件
            remote_pre_files = self.transfer_manager.upload_files(
                self.ssh_client, pre_files, self.config.remote_base_path
            )
            
            # 准备服务器CFX环境
            self.cfx_manager.prepare_server_cfx_generation(
                self.ssh_client, pre_files, self.config.remote_base_path
            )
            
            # 在服务器生成.def文件
            return self.cfx_manager.generate_def_files_server(
                self.ssh_client, list(remote_pre_files.values()), self.config.remote_base_path
            )
    
    def _create_simple_job_configs(self, job_configs: List[Dict], def_files: List[str]) -> List[Dict]:
        """创建简化的作业配置（不进行节点分配）"""
        simple_jobs = []
        
        for i, job_config in enumerate(job_configs):
            simple_job = job_config.copy()
            simple_job.update({
                "def_file": def_files[i] if i < len(def_files) else "",
                "allocated_cpus": getattr(self.config, 'min_cores', self.config.tasks_per_node),
                "creation_time": datetime.now().isoformat()
            })
            simple_jobs.append(simple_job)
        
        return simple_jobs

    def _upload_files(self, def_files: List[str], scripts: Dict) -> None:
        """上传文件到服务器"""
        files_to_upload = []
        
        # 添加.def文件（如果是local模式）
        if self.config.cfx_mode == "local":
            files_to_upload.extend(def_files)
        
        # 添加脚本文件
        files_to_upload.extend(scripts["job_scripts"])
        if scripts["submit_script"]:
            files_to_upload.append(scripts["submit_script"])
        if scripts["monitor_script"]:
            files_to_upload.append(scripts["monitor_script"])
        
        # 执行基本文件上传，保持目录结构
        uploaded_files = self.transfer_manager.upload_files(
            self.ssh_client, files_to_upload, self.config.remote_base_path, preserve_structure=True
        )
        
        # 单独处理初始文件上传到各个P_Out_文件夹
        if hasattr(self.config, 'initial_file') and self.config.initial_file:
            initial_file_path = self.config.initial_file
            if os.path.exists(initial_file_path):
                self.logger.info(f"开始上传初始文件到各个P_Out_文件夹: {initial_file_path}")
                self._upload_initial_files_to_folders(initial_file_path, def_files)
            else:
                self.logger.warning(f"初始文件不存在，跳过上传: {initial_file_path}")
        
        self.logger.info(f"文件上传完成: {len(uploaded_files)}个文件")
    
    def _upload_initial_files_to_folders(self, initial_file_path: str, def_files: List[str]) -> None:
        """直接上传初始文件到服务器的各个P_Out_文件夹"""
        try:
            # 获取初始文件的文件名
            initial_filename = os.path.basename(initial_file_path)
            
            # 为每个def文件所在的文件夹上传初始文件
            processed_folders = set()
            
            for def_file in def_files:
                # 获取def文件的相对路径
                rel_def_file = os.path.relpath(def_file, self.config.base_path)
                def_folder_rel = os.path.dirname(rel_def_file)
                
                # 避免重复处理同一个文件夹
                if def_folder_rel in processed_folders:
                    continue
                processed_folders.add(def_folder_rel)
                
                # 检查文件夹是否是P_Out_开头
                folder_name = os.path.basename(def_folder_rel)
                if folder_name.startswith(self.config.folder_prefix):
                    # 构建服务器端的目标路径
                    remote_folder = os.path.join(self.config.remote_base_path, def_folder_rel).replace('\\', '/')
                    remote_initial_file = f"{remote_folder}/{initial_filename}"
                    
                    self.logger.info(f"上传初始文件到: {remote_initial_file}")
                    
                    # 使用SFTP直接上传文件到目标路径
                    try:
                        sftp = self.ssh_client.open_sftp()
                        
                        # 确保远程目录存在
                        try:
                            sftp.stat(remote_folder)
                        except FileNotFoundError:
                            # 目录不存在，创建目录
                            self._create_remote_directory(sftp, remote_folder)
                        
                        # 上传文件
                        sftp.put(initial_file_path, remote_initial_file)
                        self.logger.info(f"✓ 初始文件上传成功: {folder_name}/{initial_filename}")
                        
                        sftp.close()
                        
                    except Exception as e:
                        self.logger.error(f"上传初始文件到 {folder_name} 失败: {e}")
                        
        except Exception as e:
            self.logger.error(f"上传初始文件到文件夹失败: {e}")
    
    def _create_remote_directory(self, sftp, remote_path: str) -> None:
        """递归创建远程目录"""
        try:
            sftp.stat(remote_path)
        except FileNotFoundError:
            # 目录不存在，先创建父目录
            parent_dir = os.path.dirname(remote_path)
            if parent_dir and parent_dir != remote_path:
                self._create_remote_directory(sftp, parent_dir)
            
            # 创建当前目录
            sftp.mkdir(remote_path)
            self.logger.debug(f"创建远程目录: {remote_path}")
    
    def _prepare_initial_files_for_folders(self, initial_file_path: str, def_files: List[str]) -> None:
        """为每个P_Out_文件夹准备初始文件副本"""
        try:
            import shutil
            
            # 获取初始文件的文件名
            initial_filename = os.path.basename(initial_file_path)
            
            # 为每个def文件所在的文件夹创建初始文件副本
            processed_folders = set()
            
            for def_file in def_files:
                # 获取def文件所在的文件夹
                def_folder = os.path.dirname(def_file)
                
                # 避免重复处理同一个文件夹
                if def_folder in processed_folders:
                    continue
                processed_folders.add(def_folder)
                
                # 检查文件夹是否是P_Out_开头
                folder_name = os.path.basename(def_folder)
                if folder_name.startswith(self.config.folder_prefix):
                    # 在该文件夹中创建初始文件副本
                    target_initial_file = os.path.join(def_folder, initial_filename)
                    
                    if not os.path.exists(target_initial_file):
                        self.logger.info(f"复制初始文件到: {target_initial_file}")
                        shutil.copy2(initial_file_path, target_initial_file)
                    else:
                        self.logger.info(f"初始文件已存在: {target_initial_file}")
                        
        except Exception as e:
            self.logger.error(f"准备初始文件副本失败: {e}")
    
    def _submit_jobs(self, submit_script: str) -> List[Dict]:
        """提交作业到队列"""
        if not submit_script:
            raise WorkflowError("批量提交脚本未生成")
        
        try:
            # 获取远程提交脚本路径
            remote_script = os.path.join(
                self.config.remote_base_path, 
                os.path.basename(submit_script)
            ).replace('\\', '/')
            
            # 设置执行权限
            chmod_cmd = f"chmod +x {remote_script}"
            stdin, stdout, stderr = self.ssh_client.exec_command(chmod_cmd)
            stdout.channel.recv_exit_status()
            
            # 执行提交脚本
            submit_cmd = f"cd {self.config.remote_base_path} && ./{os.path.basename(submit_script)}"
            self.logger.info(f"执行作业提交命令: {submit_cmd}")
            
            stdin, stdout, stderr = self.ssh_client.exec_command(submit_cmd)
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status != 0:
                error_msg = stderr.read().decode()
                raise WorkflowError(f"作业提交失败: {error_msg}")
            
            output = stdout.read().decode()
            self.logger.info("作业提交输出:")
            self.logger.info(output)
            
            # 解析提交的作业ID
            submitted_jobs = []
            for line in output.split('\n'):
                if 'Submitted batch job' in line:
                    # 从类似 "Submitted batch job 11122885" 的行中提取作业ID
                    try:
                        job_id = line.strip().split()[-1]
                        job_info = {
                            "job_id": job_id,
                            "output_line": line.strip()
                        }
                        submitted_jobs.append(job_info)
                    except Exception as e:
                        self.logger.warning(f"解析作业ID失败: {line.strip()} - {e}")
            
            self.logger.info(f"成功提交{len(submitted_jobs)}个作业")
            return submitted_jobs
            
        except Exception as e:
            raise WorkflowError(f"作业提交失败: {e}")
    
    def _get_submitted_jobs(self) -> List[Dict]:
        """获取当前用户已提交的作业信息"""
        try:
            # 查询当前用户的作业
            if self.config.scheduler_type == "SLURM":
                query_cmd = f"squeue -u {self.config.ssh_user} -o '%.10i %.12P %.20j %.8u %.2t %.10M %.6D %R'"
            else:
                # PBS调度器
                query_cmd = f"qstat -u {self.config.ssh_user}"
            
            stdin, stdout, stderr = self.ssh_client.exec_command(query_cmd)
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status != 0:
                error_msg = stderr.read().decode()
                self.logger.warning(f"查询作业状态失败: {error_msg}")
                return []
            
            output = stdout.read().decode()
            self.logger.info("当前作业状态查询结果:")
            self.logger.info(output)
            
            # 解析作业信息
            jobs = []
            lines = output.strip().split('\n')
            
            if len(lines) <= 1:  # 只有标题行或空输出
                return []
            
            # 跳过标题行
            for line in lines[1:]:
                if line.strip():
                    fields = line.split()
                    if len(fields) >= 5:
                        job_info = {
                            "job_id": fields[0],
                            "partition": fields[1] if len(fields) > 1 else "",
                            "name": fields[2] if len(fields) > 2 else "",
                            "user": fields[3] if len(fields) > 3 else "",
                            "state": fields[4] if len(fields) > 4 else "",
                            "time": fields[5] if len(fields) > 5 else "",
                            "nodes": fields[6] if len(fields) > 6 else "",
                            "nodelist": ' '.join(fields[7:]) if len(fields) > 7 else ""
                        }
                        jobs.append(job_info)
            
            self.logger.info(f"找到 {len(jobs)} 个正在运行或排队的作业")
            return jobs
            
        except Exception as e:
            self.logger.error(f"获取作业信息失败: {e}")
            return []
    
    def _monitor_jobs(self, submitted_jobs: List[Dict]) -> Dict:
        """监控作业执行"""
        if not self.config.enable_monitoring:
            self.logger.info("作业监控已禁用")
            return {}
        
        try:
            # 启动监控
            self.job_monitor.start_monitoring(self.ssh_client, submitted_jobs)
            
            # 执行监控循环
            monitoring_report = self.job_monitor.monitor_jobs(
                self.ssh_client, self.transfer_manager
            )
            
            return monitoring_report
            
        except KeyboardInterrupt:
            self.logger.info("监控被用户中断")
            return self.job_monitor._generate_monitoring_report()
        except Exception as e:
            raise WorkflowError(f"作业监控失败: {e}")
    
    def _generate_final_report(self, job_configs: List[Dict], allocated_jobs: List[Dict], 
                             scripts: Dict, monitoring_report: Optional[Dict]) -> Dict:
        """生成最终执行报告"""
        # 计算执行时长
        start_time = datetime.fromisoformat(self.execution_state["start_time"])
        end_time = datetime.fromisoformat(self.execution_state["end_time"]) if self.execution_state["end_time"] else datetime.now()
        execution_duration = int((end_time - start_time).total_seconds())
        
        report = {
            "execution_summary": {
                "total_jobs": len(job_configs),
                "successful_submissions": len(allocated_jobs) if allocated_jobs else 0,
                "execution_duration_seconds": execution_duration,
                "completed_steps": self.execution_state["completed_steps"],
                "failed_steps": self.execution_state["failed_steps"],
                "start_time": self.execution_state["start_time"],
                "end_time": self.execution_state["end_time"]
            },
            "configuration": {
                "cfx_mode": self.config.cfx_mode,
                "cluster_type": self.config.cluster_type,
                "scheduler_type": self.config.scheduler_type,
                "node_allocation_enabled": self.config.enable_node_allocation,
                "monitoring_enabled": self.config.enable_monitoring
            },
            "generated_files": {
                "job_scripts": scripts.get("job_scripts", []) if scripts else [],
                "submit_script": scripts.get("submit_script", "") if scripts else "",
                "monitor_script": scripts.get("monitor_script", "") if scripts else ""
            },
            "transfer_statistics": self.transfer_manager.get_transfer_statistics(),
            "monitoring_report": monitoring_report if monitoring_report else {},
            "report_generation_time": datetime.now().isoformat()
        }
        
        # 保存报告到文件
        self._save_execution_report(report)
        
        return report
    
    def _save_execution_report(self, report: Dict) -> None:
        """保存执行报告"""
        try:
            import json
            
            # 创建report目录 - 使用当前工作目录而不是config.base_path
            current_dir = os.getcwd()
            report_dir = os.path.join(current_dir, "report")
            os.makedirs(report_dir, exist_ok=True)
            
            report_file = os.path.join(
                report_dir,
                f"cfx_execution_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"执行报告已保存: {report_file}")
            
        except Exception as e:
            self.logger.error(f"保存执行报告失败: {e}")
    
    def _generate_step_report(self, step_name: str, result) -> None:
        """为单独步骤生成简单报告"""
        try:
            import json
            
            # 创建report目录 - 使用当前工作目录而不是config.base_path
            current_dir = os.getcwd()
            report_dir = os.path.join(current_dir, "report")
            os.makedirs(report_dir, exist_ok=True)
            
            # 生成步骤报告
            step_report = {
                "step_name": step_name,
                "execution_time": datetime.now().isoformat(),
                "status": "completed",
                "result": str(result) if result else None,
                "config_info": {
                    "pressure_list": getattr(self.config, 'pressure_list', []),
                    "cfx_mode": getattr(self.config, 'cfx_mode', 'unknown'),
                    "base_path": getattr(self.config, 'base_path', 'unknown')
                }
            }
            
            # 根据步骤类型添加特定信息
            if step_name in ["generate_def", "generate_scripts"] and hasattr(result, '__len__'):
                step_report["generated_files_count"] = len(result) if result else 0
            
            report_file = os.path.join(
                report_dir,
                f"step_{step_name}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(step_report, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"步骤报告已保存: {report_file}")
            
        except Exception as e:
            self.logger.error(f"保存步骤报告失败: {e}")
    
    def _cleanup_resources(self) -> None:
        """清理资源"""
        try:
            if self.ssh_client:
                self.ssh_client.close()
                self.logger.debug("SSH连接已关闭")
        except Exception as e:
            self.logger.warning(f"清理资源时出错: {e}")
    
    def execute_step_only(self, step_name: str, **kwargs) -> any:
        """
        只执行指定步骤（用于调试和部分执行）
        
        Args:
            step_name: 步骤名称
            **kwargs: 步骤参数
            
        Returns:
            步骤执行结果
        """
        self.logger.info(f"执行单独步骤: {step_name}")
        
        result = None
        try:
            if step_name == "connect_server":
                result = self._connect_to_server()
            elif step_name == "verify_cfx":
                result = self._verify_cfx_environment()
            elif step_name == "generate_pre":
                job_configs = kwargs.get("job_configs", [])
                result = self.cfx_manager.generate_pre_files(job_configs)
            elif step_name == "generate_def":
                # 对于单独执行，需要重新生成pre文件和job配置
                job_configs = [
                    {
                        "pressure": pressure,
                        "job_name": f"{self.config.def_file_prefix}{pressure}",
                        "output_dir": f"{self.config.folder_prefix}{pressure}"
                    }
                    for pressure in self.config.pressure_list
                ]
                
                # 获取预生成的.pre文件路径
                pre_file_path = os.path.join(
                    self.config.base_path, 
                    "create_def_batch.pre"
                )
                pre_files = [pre_file_path] if os.path.exists(pre_file_path) else []
                
                if not pre_files:
                    # 如果没有.pre文件，先生成
                    pre_files = self.cfx_manager.generate_pre_files(job_configs)
                
                result = self._generate_def_files(pre_files, job_configs)
            elif step_name == "generate_scripts":
                # 生成作业脚本需要先有.def文件和job配置
                job_configs = []
                
                for pressure in self.config.pressure_list:
                    job_config = {
                        "pressure": pressure,
                        "job_name": f"CFX_Job_{pressure}",
                        "output_dir": f"{self.config.folder_prefix}{pressure}",
                        "def_file": f"{self.config.folder_prefix}{pressure}/{pressure}.def"
                    }
                    
                    # 如果def_file_prefix不为空，调整def文件名
                    if self.config.def_file_prefix:
                        job_config["def_file"] = f"{self.config.folder_prefix}{pressure}/{self.config.def_file_prefix}{pressure}.def"
                    
                    # 添加初始文件信息（如果配置了）
                    if hasattr(self.config, 'initial_file') and self.config.initial_file:
                        # 使用相对路径，初始文件将在对应的P_Out_文件夹中
                        initial_filename = os.path.basename(self.config.initial_file)
                        job_config["initial_file"] = initial_filename
                        self.logger.info(f"添加initial_file到作业配置: {initial_filename} (来源: {self.config.initial_file})")
                    else:
                        self.logger.warning(f"未找到initial_file配置: hasattr={hasattr(self.config, 'initial_file')}, value={getattr(self.config, 'initial_file', 'NOT_FOUND')}")
                    
                    self.logger.info(f"压力{pressure}的作业配置: {job_config}")
                    job_configs.append(job_config)
                
                # 如果没有SSH连接但需要集群状态，先获取集群状态
                cluster_status = None
                if self.config.enable_node_detection and self.ssh_client:
                    try:
                        cluster_status = self.cluster_query.query_cluster_nodes(self.ssh_client)
                        self.logger.info(f"获取到集群状态，节点数量: {len(cluster_status)}")
                    except Exception as e:
                        self.logger.warning(f"获取集群状态失败: {e}")
                
                result = self.script_generator.generate_job_scripts(job_configs, cluster_status)
            elif step_name == "upload_files":
                # 上传文件到集群
                if not self.ssh_client:
                    self._connect_to_server()
                
                # 准备要上传的文件夹和文件列表
                upload_items = []
                uploaded_folders = []
                uploaded_sh_files = []
                
                # 添加每个压力参数对应的完整文件夹
                for pressure in self.config.pressure_list:
                    folder_name = f"{self.config.folder_prefix}{pressure}"
                    local_folder_path = os.path.join(self.config.base_path, folder_name)
                    
                    # 检查文件夹是否存在且包含文件
                    if os.path.exists(local_folder_path) and os.path.isdir(local_folder_path):
                        folder_files = []
                        # 添加文件夹中的所有文件
                        for root, dirs, files in os.walk(local_folder_path):
                            for file in files:
                                local_file_path = os.path.join(root, file)
                                # 计算相对路径以保持文件夹结构
                                rel_path = os.path.relpath(local_file_path, self.config.base_path)
                                upload_items.append(local_file_path)
                                folder_files.append(file)
                                self.logger.debug(f"添加文件到上传列表: {local_file_path} -> {rel_path}")
                        
                        if folder_files:
                            uploaded_folders.append({
                                "folder": folder_name,
                                "files": folder_files,
                                "file_count": len(folder_files)
                            })
                
                # 添加生成的.sh脚本文件
                generated_sh_files = [
                    "Submit_All.sh",
                    "Monitor_Jobs.sh"
                ]
                
                for sh_file in generated_sh_files:
                    script_file = os.path.join(self.config.base_path, sh_file)
                    if os.path.exists(script_file):
                        upload_items.append(script_file)
                        uploaded_sh_files.append(sh_file)
                        self.logger.debug(f"添加生成的脚本到上传列表: {script_file}")
                
                # 添加按作业命名的.sh文件（如果存在）
                for pressure in self.config.pressure_list:
                    job_name = f"CFX_Job_{pressure}"
                    job_sh_file = os.path.join(self.config.base_path, f"{job_name}.sh")
                    if os.path.exists(job_sh_file):
                        upload_items.append(job_sh_file)
                        uploaded_sh_files.append(f"{job_name}.sh")
                        self.logger.debug(f"添加作业脚本到上传列表: {job_sh_file}")
                
                # 详细输出要上传的内容
                self.logger.info(f"=== 文件上传清单 ===")
                
                # 计算基本文件数量和大小
                total_size = 0
                total_file_count = len(upload_items)
                
                for item in upload_items:
                    if os.path.exists(item):
                        total_size += os.path.getsize(item)
                        
                # 检查是否有初始文件需要额外上传
                initial_file_info = None
                if hasattr(self.config, 'initial_file') and self.config.initial_file:
                    if os.path.exists(self.config.initial_file):
                        initial_file_size = os.path.getsize(self.config.initial_file)
                        initial_file_size_mb = round(initial_file_size / (1024 * 1024), 2)
                        # 为每个P_Out_文件夹都会额外上传一份初始文件
                        additional_initial_files = len(self.config.pressure_list)
                        total_size += initial_file_size * additional_initial_files
                        total_file_count += additional_initial_files
                        initial_file_info = {
                            "name": os.path.basename(self.config.initial_file),
                            "size_mb": initial_file_size_mb,
                            "folders": additional_initial_files
                        }
                
                total_size_mb = round(total_size / (1024 * 1024), 2)
                self.logger.info(f"总计文件数量: {total_file_count}")
                self.logger.info(f"总计文件大小: {total_size_mb} MB")
                
                # 如果有初始文件，单独说明
                if initial_file_info:
                    self.logger.info(f"  (包含初始文件 {initial_file_info['name']} × {initial_file_info['folders']} = {initial_file_info['folders']}个额外文件)")
                
                # 输出文件夹信息
                if uploaded_folders:
                    self.logger.info(f"要上传的文件夹 ({len(uploaded_folders)}个):")
                    for folder_info in uploaded_folders:
                        self.logger.info(f"  📁 {folder_info['folder']} ({folder_info['file_count']}个文件)")
                        
                        # 显示现有文件
                        for file in folder_info['files']:
                            # 计算文件大小
                            file_path = os.path.join(self.config.base_path, folder_info['folder'], file)
                            if os.path.exists(file_path):
                                file_size = os.path.getsize(file_path)
                                size_str = f"{round(file_size / 1024, 1)} KB" if file_size < 1024*1024 else f"{round(file_size / (1024*1024), 2)} MB"
                                file_type = "CFX定义文件" if file.endswith('.def') else "SLURM作业脚本" if file.endswith('.slurm') else "其他"
                                self.logger.info(f"     └── {file} ({size_str}, {file_type})")
                            else:
                                self.logger.info(f"     └── {file} (文件不存在)")
                                
                    # 单独显示初始文件信息（如果有）
                    if initial_file_info:
                        self.logger.info(f"")
                        self.logger.info(f"额外上传初始文件到各文件夹:")
                        self.logger.info(f"  📄 {initial_file_info['name']} ({initial_file_info['size_mb']} MB, CFX初始文件)")
                        self.logger.info(f"     将复制到 {initial_file_info['folders']} 个P_Out_文件夹中")
                else:
                    self.logger.warning("  ⚠️  没有找到要上传的文件夹")
                
                # 输出.sh文件信息
                if uploaded_sh_files:
                    self.logger.info(f"要上传的.sh脚本文件 ({len(uploaded_sh_files)}个):")
                    for sh_file in uploaded_sh_files:
                        script_path = os.path.join(self.config.base_path, sh_file)
                        if os.path.exists(script_path):
                            file_size = os.path.getsize(script_path)
                            size_str = f"{round(file_size / 1024, 1)} KB"
                            script_type = "批量提交脚本" if "Submit" in sh_file else "监控脚本" if "Monitor" in sh_file else "Shell脚本"
                            self.logger.info(f"  📜 {sh_file} ({size_str}, {script_type})")
                        else:
                            self.logger.info(f"  📜 {sh_file} (文件不存在)")
                else:
                    self.logger.warning("  ⚠️  没有找到要上传的.sh脚本文件")
                
                self.logger.info(f"=== 上传目标 ===")
                self.logger.info(f"远程目录: {self.config.remote_base_path}")
                self.logger.info(f"保持目录结构: 是")
                
                # 如果没有找到文件，记录警告
                if not upload_items:
                    self.logger.warning("没有找到要上传的文件或文件夹")
                    result = {"uploaded_files": [], "failed_files": []}
                else:
                    # 先创建远程目录结构
                    try:
                        # 确保远程基础目录存在
                        stdin, stdout, stderr = self.ssh_client.exec_command(f"mkdir -p {self.config.remote_base_path}")
                        stdout.read()  # 等待命令完成
                        self.logger.info(f"创建远程基础目录: {self.config.remote_base_path}")
                        
                        # 为每个压力参数创建远程目录
                        for pressure in self.config.pressure_list:
                            folder_name = f"{self.config.folder_prefix}{pressure}"
                            remote_folder = f"{self.config.remote_base_path}/{folder_name}"
                            stdin, stdout, stderr = self.ssh_client.exec_command(f"mkdir -p {remote_folder}")
                            stdout.read()  # 等待命令完成
                            self.logger.debug(f"创建远程目录: {remote_folder}")
                            
                    except Exception as e:
                        self.logger.warning(f"创建远程目录时出错: {e}")
                    
                    # 执行上传，保持目录结构
                    self.logger.info(f"准备上传{len(upload_items)}个文件到集群 (保持目录结构)")
                    result = self.transfer_manager.upload_files(
                        ssh_client=self.ssh_client,
                        file_list=upload_items,
                        remote_dir=self.config.remote_base_path,
                        preserve_structure=True
                    )
                    
                    # 单独处理初始文件上传到各个P_Out_文件夹
                    if hasattr(self.config, 'initial_file') and self.config.initial_file:
                        initial_file_path = self.config.initial_file
                        if os.path.exists(initial_file_path):
                            self.logger.info(f"开始上传初始文件到各个P_Out_文件夹: {initial_file_path}")
                            
                            # 构建模拟的def文件列表用于初始文件上传
                            def_files_for_initial = []
                            for pressure in self.config.pressure_list:
                                folder_name = f"{self.config.folder_prefix}{pressure}"
                                local_folder_path = os.path.join(self.config.base_path, folder_name)
                                def_file = os.path.join(local_folder_path, f"{pressure}.def")
                                def_files_for_initial.append(def_file)
                            
                            self._upload_initial_files_to_folders(initial_file_path, def_files_for_initial)
                        else:
                            self.logger.warning(f"初始文件不存在，跳过上传: {initial_file_path}")
            elif step_name == "submit_jobs":
                # 提交作业到队列
                if not self.ssh_client:
                    self._connect_to_server()
                
                # 找到Submit_All.sh脚本
                submit_script = os.path.join(self.config.base_path, "Submit_All.sh")
                if not os.path.exists(submit_script):
                    raise WorkflowError("Submit_All.sh脚本未找到，请先执行generate_scripts步骤")
                
                result = self._submit_jobs(submit_script)
            elif step_name == "monitor_jobs":
                # 监控作业状态
                if not self.ssh_client:
                    self._connect_to_server()
                
                # 获取已提交的作业信息（从用户作业队列查询）
                submitted_jobs = self._get_submitted_jobs()
                
                if not submitted_jobs:
                    self.logger.warning("未找到正在运行的作业")
                    result = {"status": "no_jobs", "jobs": []}
                else:
                    # 执行监控
                    result = self._monitor_jobs(submitted_jobs)
            elif step_name == "query_cluster":
                if not self.ssh_client:
                    self._connect_to_server()
                result = self.cluster_query.query_cluster_nodes(self.ssh_client)
            else:
                raise WorkflowError(f"未知步骤: {step_name}")
            
            # 为单独步骤生成简单报告
            self.logger.info(f"正在为步骤 {step_name} 生成报告...")
            self._generate_step_report(step_name, result)
            
            return result
                
        except Exception as e:
            self.logger.error(f"步骤执行失败 {step_name}: {e}")
            raise
        
        finally:
            # 只在特定步骤后清理资源
            if step_name in ["connect_server", "query_cluster"]:
                # 这些步骤需要保持连接给后续步骤使用
                pass
            else:
                self._cleanup_resources()
    
    def get_execution_status(self) -> Dict:
        """获取当前执行状态"""
        return {
            "current_step": self.execution_state["current_step"],
            "completed_steps": self.execution_state["completed_steps"],
            "failed_steps": self.execution_state["failed_steps"],
            "progress": len(self.execution_state["completed_steps"]) / 10,  # 假设总共10个步骤
            "start_time": self.execution_state["start_time"],
            "total_jobs": self.execution_state["total_jobs"]
        }
