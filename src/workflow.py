"""
CFX自动化工作流程模块
整合所有功能，实现完整的自动化流程
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from .config import CFXAutomationConfig
from .cfx import CFXPreAutomation
from .slurm import SlurmJobManager
from .transfer import FileTransferManager

logger = logging.getLogger(__name__)


class CFXAutomationWorkflow:
    """CFX自动化工作流程类"""
    
    def __init__(self, config: CFXAutomationConfig):
        self.config = config
        self.cfx_pre = CFXPreAutomation(config)
        self.slurm_manager = SlurmJobManager(config)
        self.file_manager = FileTransferManager(config)
        
        # 工作流程状态
        self.workflow_status = {
            'initialized': False,
            'cfx_cases_generated': False,
            'slurm_scripts_generated': False,
            'files_uploaded': False,
            'jobs_submitted': False,
            'workflow_completed': False
        }
        
        # 记录执行结果
        self.execution_results = {
            'cfx_results': {},
            'slurm_results': {},
            'transfer_results': {},
            'submission_results': {}
        }

    def initialize_workflow(self) -> bool:
        """
        初始化工作流程
        
        Returns:
            bool: 初始化是否成功
        """
        logger.info("初始化CFX自动化工作流程...")
        
        try:
            # 验证配置
            errors = self.config.validate()
            if errors:
                logger.error("配置验证失败:")
                for error in errors:
                    logger.error(f"  - {error}")
                return False
            
            # 创建必要的目录
            os.makedirs(self.config.base_path, exist_ok=True)
            
            # 检查文件是否存在（警告但不阻止）
            if not os.path.exists(self.config.cfx_pre_executable):
                logger.warning(f"CFX-Pre可执行文件不存在: {self.config.cfx_pre_executable}")
            
            if not os.path.exists(self.config.cfx_file_path):
                logger.warning(f"CFX文件不存在: {self.config.cfx_file_path}")
            
            # 检查模板目录
            template_dir = Path(self.config.template_dir)
            if not template_dir.exists():
                logger.warning(f"模板目录不存在: {template_dir}")
            else:
                # 检查模板文件
                required_templates = [
                    self.config.session_template,
                    self.config.slurm_template,
                    self.config.batch_template
                ]
                
                for template in required_templates:
                    template_file = template_dir / template
                    if not template_file.exists():
                        logger.warning(f"模板文件不存在: {template_file}")
            
            self.workflow_status['initialized'] = True
            logger.info("工作流程初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"工作流程初始化失败: {e}")
            return False
    
    def generate_cfx_cases(self, pressure_list: List[float] = None) -> bool:
        """
        生成CFX算例
        
        Args:
            pressure_list: 背压列表（可选）
            
        Returns:
            bool: 生成是否成功
        """
        # 检查必要的文件是否存在
        if not os.path.exists(self.config.cfx_file_path):
            logger.error(f"CFX文件不存在: {self.config.cfx_file_path}")
            return False
        
        if not os.path.exists(self.config.cfx_pre_executable):
            logger.error(f"CFX-Pre可执行文件不存在: {self.config.cfx_pre_executable}")
            return False
        
        logger.info("生成CFX算例...")
        
        try:
            # 生成参数化算例
            generated_files = self.cfx_pre.generate_parametric_cases(pressure_list)
            
            # 验证生成的文件
            validation_results = self.cfx_pre.validate_generated_files(pressure_list)
            
            # 记录结果
            self.execution_results['cfx_results'] = {
                'generated_files': generated_files,
                'validation_results': validation_results,
                'success_count': sum(1 for result in validation_results.values() if result),
                'total_count': len(validation_results)
            }
            
            success = len(generated_files) > 0
            self.workflow_status['cfx_cases_generated'] = success
            
            if success:
                logger.info(f"CFX算例生成成功: {len(generated_files)} 个算例")
            else:
                logger.error("CFX算例生成失败")
            
            return success
            
        except Exception as e:
            logger.error(f"生成CFX算例失败: {e}")
            return False
    
    def generate_slurm_scripts(self, pressure_list: List[float] = None) -> bool:
        """
        生成Slurm作业脚本
        
        Args:
            pressure_list: 背压列表（可选）
            
        Returns:
            bool: 生成是否成功
        """
        if pressure_list is None:
            pressure_list = self.config.pressure_list
        
        # 检查模板文件是否存在
        template_dir = Path(self.config.template_dir)
        slurm_template_file = template_dir / self.config.slurm_template
        batch_template_file = template_dir / self.config.batch_template
        
        if not slurm_template_file.exists():
            logger.error(f"SLURM模板文件不存在: {slurm_template_file}")
            return False
        
        if not batch_template_file.exists():
            logger.error(f"批量提交模板文件不存在: {batch_template_file}")
            return False
        
        logger.info("生成Slurm作业脚本...")
        
        try:
            # 生成所有作业脚本
            generated_scripts = self.slurm_manager.generate_all_job_scripts(pressure_list)
            
            # 生成批量提交脚本
            batch_script = self.slurm_manager.generate_batch_submit_script(pressure_list)
            
            # 验证作业脚本
            validation_results = self.slurm_manager.validate_job_scripts(pressure_list)
            
            # 记录结果
            self.execution_results['slurm_results'] = {
                'generated_scripts': generated_scripts,
                'batch_script': batch_script,
                'validation_results': validation_results,
                'success_count': sum(1 for result in validation_results.values() if result),
                'total_count': len(validation_results)
            }
            
            success = len(generated_scripts) > 0
            self.workflow_status['slurm_scripts_generated'] = success
            
            if success:
                logger.info(f"Slurm作业脚本生成成功: {len(generated_scripts)} 个脚本")
            else:
                logger.error("Slurm作业脚本生成失败")
            
            return success
            
        except Exception as e:
            logger.error(f"生成Slurm作业脚本失败: {e}")
            return False
    
    def upload_files_to_server(self, 
                             exclude_patterns: List[str] = None,
                             dry_run: bool = False,
                             pressure_list: List[float] = None) -> bool:
        """
        上传文件到服务器
        
        Args:
            exclude_patterns: 排除的文件模式列表
            dry_run: 是否只模拟运行
            pressure_list: 背压列表（可选，默认使用配置中的列表）
            
        Returns:
            bool: 上传是否成功
        """
        if pressure_list is None:
            pressure_list = self.config.pressure_list
        
        # 检查是否有文件可以上传
        has_files_to_upload = False
        for pressure in pressure_list:
            local_folder = os.path.join(
                self.config.base_path,
                f"{self.config.folder_prefix}{pressure:g}"
            )
            if os.path.exists(local_folder):
                has_files_to_upload = True
                break
        
        if not has_files_to_upload:
            logger.error("没有找到可上传的文件夹")
            return False
        
        logger.info("上传文件到服务器...")
        
        # 确保批量提交脚本存在
        batch_script_local = os.path.join(self.config.base_path, self.config.batch_script_name)
        if not os.path.exists(batch_script_local):
            logger.warning(f"批量提交脚本不存在，正在生成: {batch_script_local}")
            # 生成批量提交脚本
            from .slurm import SlurmJobManager
            slurm_manager = SlurmJobManager(self.config)
            try:
                batch_script_success = slurm_manager.generate_batch_submit_script(
                    pressure_list=pressure_list,
                    output_file=batch_script_local
                )
                if not batch_script_success:
                    logger.error("生成批量提交脚本失败")
                    return False
            except Exception as e:
                logger.error(f"生成批量提交脚本失败: {e}")
                return False
        
        try:
            # 连接到服务器
            if not self.file_manager.connect():
                logger.error("连接服务器失败")
                return False
            
            # 设置默认排除模式
            if exclude_patterns is None:
                exclude_patterns = [
                    '*.tmp', '*.log', '*.bak', '*.out', '*.err',
                    '__pycache__', '.git', '.vscode', '*.pyc'
                ]
            
            # 上传每个背压文件夹
            all_success = True
            uploaded_folders = []
            
            for pressure in pressure_list:
                # 构建源文件夹路径
                local_folder = os.path.join(
                    self.config.base_path,
                    f"{self.config.folder_prefix}{pressure:g}"
                )
                
                # 构建远程文件夹路径
                remote_folder = os.path.join(
                    self.config.remote_base_path,
                    f"{self.config.folder_prefix}{pressure:g}"
                ).replace('\\', '/')
                
                # 检查本地文件夹是否存在
                if not os.path.exists(local_folder):
                    logger.warning(f"本地文件夹不存在: {local_folder}")
                    continue
                
                logger.info(f"上传背压文件夹: {pressure:g}")
                
                # 上传单个文件夹
                success = self.file_manager.sync_directory(
                    local_folder,
                    remote_folder,
                    exclude_patterns,
                    dry_run
                )
                
                if success:
                    uploaded_folders.append(f"P_{pressure:g}")
                    logger.info(f"背压文件夹上传成功: {pressure:g}")
                else:
                    logger.error(f"背压文件夹上传失败: {pressure:g}")
                    all_success = False
            
            # 上传批量提交脚本
            batch_script_local = os.path.join(self.config.base_path, self.config.batch_script_name)
            batch_script_remote = os.path.join(self.config.remote_base_path, self.config.batch_script_name).replace('\\', '/')
            
            if os.path.exists(batch_script_local):
                logger.info("上传批量提交脚本...")
                if not dry_run:
                    # 确保远程目录存在
                    self.file_manager.create_remote_directory(self.config.remote_base_path)
                    
                    # 上传批量提交脚本
                    script_success = self.file_manager.upload_file(
                        batch_script_local,
                        batch_script_remote
                    )
                    
                    if script_success:
                        logger.info("批量提交脚本上传成功")
                        # 设置执行权限
                        self.file_manager.execute_remote_command(f"chmod +x {batch_script_remote}")
                    else:
                        logger.error("批量提交脚本上传失败")
                        all_success = False
                else:
                    logger.info("模拟上传批量提交脚本")
            else:
                logger.warning(f"批量提交脚本不存在: {batch_script_local}")
                all_success = False
            
            # 记录结果
            self.execution_results['transfer_results'] = {
                'success': all_success,
                'uploaded_folders': uploaded_folders,
                'pressure_list': pressure_list,
                'local_base_path': self.config.base_path,
                'remote_base_path': self.config.remote_base_path,
                'exclude_patterns': exclude_patterns,
                'dry_run': dry_run
            }
            
            self.workflow_status['files_uploaded'] = all_success and not dry_run
            
            if all_success:
                if dry_run:
                    logger.info(f"文件上传模拟成功: {len(uploaded_folders)} 个文件夹")
                else:
                    logger.info(f"文件上传成功: {len(uploaded_folders)} 个文件夹")
            else:
                logger.error("部分或全部文件上传失败")
            
            return all_success
            
        except Exception as e:
            logger.error(f"上传文件失败: {e}")
            return False
        finally:
            self.file_manager.disconnect()
    
    def submit_jobs_to_cluster(self, pressure_list: List[float] = None) -> bool:
        """
        提交作业到集群
        
        Args:
            pressure_list: 背压列表（可选）
            
        Returns:
            bool: 提交是否成功
        """
        if pressure_list is None:
            pressure_list = self.config.pressure_list
        
        # 检查本地是否有批量提交脚本
        batch_script_local = os.path.join(self.config.base_path, self.config.batch_script_name)
        if not os.path.exists(batch_script_local):
            logger.warning(f"本地批量提交脚本不存在: {batch_script_local}")
            logger.info("将直接检查远程服务器上的脚本")
        
        logger.info("提交作业到集群...")
        
        try:
            # 连接到服务器
            if not self.file_manager.connect():
                logger.error("连接服务器失败")
                return False
            
            # 执行批量提交脚本
            batch_script_path = os.path.join(self.config.remote_base_path, self.config.batch_script_name).replace('\\', '/')
            
            # 检查批量提交脚本是否存在
            script_exists = self.file_manager.remote_file_exists(batch_script_path)
            
            if not script_exists:
                logger.error(f"批量提交脚本不存在: {batch_script_path}")
                return False
            
            logger.info(f"找到批量提交脚本: {batch_script_path}")
            
            # 确保脚本有执行权限
            self.file_manager.execute_remote_command(f"chmod +x {batch_script_path}")
            
            # 执行批量提交脚本
            result = self.file_manager.execute_remote_command(
                f"cd {self.config.remote_base_path.replace('\\', '/')} && ./{self.config.batch_script_name}",
                timeout=600  # 10分钟超时
            )
            
            # 记录结果
            self.execution_results['submission_results'] = {
                'success': result['success'],
                'command_output': result.get('stdout', ''),
                'command_error': result.get('stderr', ''),
                'return_code': result.get('return_code', -1)
            }
            
            success = result['success']
            self.workflow_status['jobs_submitted'] = success
            
            if success:
                logger.info("作业提交成功")
                if result.get('stdout'):
                    logger.info(f"提交结果: {result['stdout']}")
            else:
                logger.error("作业提交失败")
                if result.get('stderr'):
                    logger.error(f"错误信息: {result['stderr']}")
                if result.get('stdout'):
                    logger.error(f"标准输出: {result['stdout']}")
                logger.error(f"返回码: {result.get('return_code', -1)}")
                
                # 尝试检查脚本是否可执行
                check_result = self.file_manager.execute_remote_command(f"ls -la {batch_script_path}")
                if check_result.get('stdout'):
                    logger.error(f"脚本文件信息: {check_result['stdout']}")
                
                # 尝试直接运行脚本并获取详细错误
                debug_result = self.file_manager.execute_remote_command(f"bash -x {batch_script_path}")
                if debug_result.get('stderr'):
                    logger.error(f"调试信息: {debug_result['stderr']}")
                if debug_result.get('stdout'):
                    logger.error(f"调试输出: {debug_result['stdout']}")
            
            return success
            
        except Exception as e:
            logger.error(f"提交作业失败: {e}")
            return False
        finally:
            self.file_manager.disconnect()
    
    def run_complete_workflow(self, 
                            pressure_list: List[float] = None,
                            exclude_patterns: List[str] = None,
                            dry_run: bool = False) -> bool:
        """
        运行完整的自动化工作流程
        
        Args:
            pressure_list: 背压列表（可选）
            exclude_patterns: 排除的文件模式列表
            dry_run: 是否只模拟运行
            
        Returns:
            bool: 工作流程是否成功完成
        """
        logger.info("开始运行完整的CFX自动化工作流程...")
        
        workflow_start_time = datetime.now()
        
        try:
            # 步骤1: 初始化工作流程
            if not self.initialize_workflow():
                logger.error("工作流程初始化失败")
                return False
            
            # 步骤2: 生成CFX算例
            if not self.generate_cfx_cases(pressure_list):
                logger.error("CFX算例生成失败")
                return False
            
            # 步骤3: 生成Slurm作业脚本
            if not self.generate_slurm_scripts(pressure_list):
                logger.error("Slurm作业脚本生成失败")
                return False
            
            # 步骤4: 上传文件到服务器
            if not self.upload_files_to_server(exclude_patterns, dry_run, pressure_list):
                logger.error("文件上传失败")
                return False
            
            # 步骤5: 提交作业（仅在非模拟模式下）
            if not dry_run:
                if not self.submit_jobs_to_cluster(pressure_list):
                    logger.error("作业提交失败")
                    return False
            
            # 清理临时文件
            if self.config.cleanup_temp_files:
                self.cleanup_temporary_files()
            
            workflow_end_time = datetime.now()
            workflow_duration = workflow_end_time - workflow_start_time
            
            self.workflow_status['workflow_completed'] = True
            
            logger.info(f"CFX自动化工作流程完成! 总用时: {workflow_duration}")
            
            return True
            
        except Exception as e:
            logger.error(f"工作流程执行失败: {e}")
            return False
    
    def cleanup_temporary_files(self):
        """清理临时文件"""
        logger.info("清理临时文件...")
        
        try:
            # 清理CFX临时文件
            self.cfx_pre.cleanup_temp_files()
            
            # 清理Slurm临时文件
            self.slurm_manager.cleanup_job_files()
            
            logger.info("临时文件清理完成")
            
        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")
    
    def print_workflow_status(self):
        """打印工作流程状态"""
        print("\n=== CFX自动化工作流程状态 ===")
        
        status_items = [
            ('初始化', self.workflow_status['initialized']),
            ('CFX算例生成', self.workflow_status['cfx_cases_generated']),
            ('Slurm脚本生成', self.workflow_status['slurm_scripts_generated']),
            ('文件上传', self.workflow_status['files_uploaded']),
            ('作业提交', self.workflow_status['jobs_submitted']),
            ('工作流程完成', self.workflow_status['workflow_completed'])
        ]
        
        for step_name, status in status_items:
            status_str = "✓" if status else "✗"
            print(f"{step_name:<15} {status_str}")
        
        print()
    
    def print_execution_summary(self):
        """打印执行摘要"""
        print("\n=== 执行摘要 ===")
        
        # CFX结果
        if self.execution_results['cfx_results']:
            cfx_results = self.execution_results['cfx_results']
            print(f"CFX算例: {cfx_results['success_count']}/{cfx_results['total_count']} 成功")
        
        # Slurm结果
        if self.execution_results['slurm_results']:
            slurm_results = self.execution_results['slurm_results']
            print(f"Slurm脚本: {slurm_results['success_count']}/{slurm_results['total_count']} 成功")
        
        # 传输结果
        if self.execution_results['transfer_results']:
            transfer_results = self.execution_results['transfer_results']
            transfer_status = "成功" if transfer_results['success'] else "失败"
            print(f"文件传输: {transfer_status}")
        
        # 提交结果
        if self.execution_results['submission_results']:
            submission_results = self.execution_results['submission_results']
            submission_status = "成功" if submission_results['success'] else "失败"
            print(f"作业提交: {submission_status}")
        
        print()
    
    def get_workflow_report(self) -> Dict[str, Any]:
        """
        获取工作流程报告
        
        Returns:
            Dict[str, Any]: 工作流程报告
        """
        return {
            'workflow_status': self.workflow_status,
            'execution_results': self.execution_results,
            'config': self.config.to_dict(),
            'timestamp': datetime.now().isoformat()
        }
    
    def save_workflow_report(self, report_file: str = None):
        """
        保存工作流程报告
        
        Args:
            report_file: 报告文件路径（可选）
        """
        # 确保报告目录存在
        report_dir = Path(self.config.report_dir)
        report_dir.mkdir(parents=True, exist_ok=True)
        
        if report_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = report_dir / f"cfx_workflow_report_{timestamp}.json"
        else:
            # 如果提供了文件名但没有路径，放在报告目录中
            if not os.path.dirname(report_file):
                report_file = report_dir / report_file
        
        report = self.get_workflow_report()
        
        import json
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"工作流程报告已保存: {report_file}")
        return str(report_file)
    
    def ensure_report_directory(self) -> None:
        """
        确保报告目录存在
        """
        report_dir = Path(self.config.report_dir)
        report_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"报告目录已准备: {report_dir}")
    
    def monitor_job_status(self, 
                         pressure_list: List[float] = None,
                         check_interval: int = 300) -> Dict[str, Any]:
        """
        监控作业状态
        
        Args:
            pressure_list: 背压列表（可选）
            check_interval: 检查间隔（秒）
            
        Returns:
            Dict[str, Any]: 作业状态
        """
        if not self.workflow_status['jobs_submitted']:
            logger.error("作业未提交")
            return {}
        
        logger.info("监控作业状态...")
        
        try:
            if not self.file_manager.connect():
                logger.error("连接服务器失败")
                return {}
            
            # 检查作业状态
            result = self.file_manager.execute_remote_command("squeue -u $USER")
            
            job_status = {
                'check_time': datetime.now().isoformat(),
                'queue_output': result.get('stdout', ''),
                'queue_error': result.get('stderr', ''),
                'success': result['success']
            }
            
            return job_status
            
        except Exception as e:
            logger.error(f"监控作业状态失败: {e}")
            return {}
        finally:
            self.file_manager.disconnect()


# 为了向后兼容，添加别名
WorkflowManager = CFXAutomationWorkflow
