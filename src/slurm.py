"""
Slurm作业管理模块
自动生成Slurm作业脚本，管理作业提交和监控
"""

import os
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from .config import CFXAutomationConfig, TemplateManager

logger = logging.getLogger(__name__)


class SlurmJobManager:
    """Slurm作业管理类"""
    
    def __init__(self, config: CFXAutomationConfig):
        self.config = config
        self.template_manager = TemplateManager(config.template_dir)

    def generate_job_script(self, 
                          pressure: float,
                          case_dir: str,
                          ini_file: Optional[str] = None,
                          **kwargs) -> str:
        """
        生成单个背压的Slurm作业脚本
        
        Args:
            pressure: 背压值
            case_dir: 算例目录
            ini_file: 初始化文件路径（可选）
            **kwargs: 额外的模板变量
            
        Returns:
            str: 生成的作业脚本路径
        """
        logger.info(f"生成Slurm作业脚本: 背压 {pressure}")
        
        # 确保目标目录存在
        os.makedirs(case_dir, exist_ok=True)
        
        # 准备模板变量
        template_vars = self._prepare_job_template_vars(pressure, case_dir, ini_file, **kwargs)
        
        # 复制INI文件
        if ini_file and os.path.exists(ini_file):
            ini_target = os.path.join(case_dir, self.config.ini_file if self.config.ini_file else 'INI.res')
            shutil.copy2(ini_file, ini_target)
            logger.info(f"复制INI文件: {ini_file} -> {ini_target}")
        
        # 生成作业脚本
        script_file = os.path.join(case_dir, self.config.slurm_script_name)
        self.template_manager.render_to_file(
            self.config.slurm_template,
            script_file,
            **template_vars
        )
        
        logger.info(f"Slurm作业脚本已生成: {script_file}")
        return script_file
    
    def _prepare_job_template_vars(self, 
                                 pressure: float,
                                 case_dir: str,
                                 ini_file: Optional[str] = None,
                                 **kwargs) -> Dict[str, Any]:
        """准备作业模板变量"""
        template_vars = {
            # 基础作业信息
            'job_name': self.config.job_name,
            'pressure': pressure,
            'pressure_str': f'{pressure:g}',
            'def_file': f'{self.config.def_file_prefix}{pressure:g}.def',
            'slurm_job_name': f'{self.config.job_name}_{pressure:g}',
            'slurm_output_file': f'{self.config.job_name}_{pressure:g}.out',
            'error_file': f'{self.config.job_name}_{pressure:g}.err',
            
            # Slurm配置
            'partition': self.config.partition,
            'nodes': self.config.nodes,
            'tasks_per_node': self.config.tasks_per_node,
            'time_limit': self.config.time_limit,
            'memory_per_node': self.config.memory_per_node,
            
            # CFX配置
            'cfx_bin_path': self.config.cfx_bin_path,
            'remote_cfx_bin_path': self.config.remote_cfx_bin_path,
            'cfx_solver_executable': self.config.cfx_solver_executable,
            
            # 文件配置
            'has_ini_file': self.config.has_ini_file and self.config.ini_file is not None,
            'ini_file': self.config.ini_file if self.config.ini_file else 'INI.res',
            'case_dir': case_dir,
            
            # 时间戳
            'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            
            # 额外参数
            **kwargs
        }
        
        return template_vars
    
    def generate_all_job_scripts(self, 
                               pressure_list: List[float] = None,
                               ini_file: Optional[str] = None) -> List[str]:
        """
        生成所有背压的Slurm作业脚本
        
        Args:
            pressure_list: 背压列表（可选，默认使用配置中的列表）
            ini_file: 初始化文件路径（可选）
            
        Returns:
            List[str]: 生成的作业脚本路径列表
        """
        if pressure_list is None:
            pressure_list = self.config.pressure_list
        
        if ini_file is None:
            ini_file = self.config.ini_file
        
        logger.info(f"生成所有Slurm作业脚本，背压列表: {pressure_list}")
        
        generated_scripts = []
        
        for pressure in pressure_list:
            # 确定算例目录
            case_dir = os.path.join(
                self.config.base_path,
                f"{self.config.folder_prefix}{pressure:g}"
            )
            
            # 生成作业脚本
            script_file = self.generate_job_script(pressure, case_dir, ini_file)
            generated_scripts.append(script_file)
        
        logger.info(f"所有Slurm作业脚本生成完成，共生成 {len(generated_scripts)} 个脚本")
        return generated_scripts
    
    def generate_batch_submit_script(self, 
                                   pressure_list: List[float] = None,
                                   output_file: str = None) -> str:
        """
        生成批量提交脚本
        
        Args:
            pressure_list: 背压列表（可选，默认使用配置中的列表）
            output_file: 输出文件路径（可选）
            
        Returns:
            str: 生成的批量提交脚本路径
        """
        if pressure_list is None:
            pressure_list = self.config.pressure_list
        
        if output_file is None:
            output_file = os.path.join(self.config.base_path, self.config.batch_script_name)
        
        logger.info(f"生成批量提交脚本: {output_file}")
        
        # 准备模板变量
        template_vars = {
            'job_name': self.config.job_name,
            'pressure_list': pressure_list,
            'folder_prefix': self.config.folder_prefix,
            'base_path': self.config.base_path,
            'remote_base_path': self.config.remote_base_path,
            'slurm_script_name': self.config.slurm_script_name,
            'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'script_author': 'CFX Automation System'
        }
        
        # 生成批量提交脚本
        self.template_manager.render_to_file(
            self.config.batch_template,
            output_file,
            **template_vars
        )
        
        # 设置执行权限
        os.chmod(output_file, 0o755)
        
        logger.info(f"批量提交脚本已生成: {output_file}")
        return output_file
    
    def validate_job_scripts(self, pressure_list: List[float] = None) -> Dict[str, bool]:
        """
        验证作业脚本
        
        Args:
            pressure_list: 背压列表（可选，默认使用配置中的列表）
            
        Returns:
            Dict[str, bool]: 验证结果字典
        """
        if pressure_list is None:
            pressure_list = self.config.pressure_list
        
        validation_results = {}
        
        for pressure in pressure_list:
            case_dir = os.path.join(
                self.config.base_path,
                f"{self.config.folder_prefix}{pressure:g}"
            )
            
            script_file = os.path.join(case_dir, self.config.slurm_script_name)
            def_file = os.path.join(case_dir, f'{self.config.def_file_prefix}{pressure:g}.def')
            
            # 检查脚本文件是否存在
            script_exists = os.path.exists(script_file)
            
            # 检查定义文件是否存在
            def_exists = os.path.exists(def_file)
            
            # 检查INI文件是否存在（如果需要）
            ini_exists = True
            if self.config.ini_file:
                ini_file = os.path.join(case_dir, 'INI.res')
                ini_exists = os.path.exists(ini_file)
            
            # 综合验证结果
            is_valid = script_exists and def_exists and ini_exists
            validation_results[f"P_{pressure:g}"] = is_valid
            
            if is_valid:
                logger.info(f"验证成功: 背压 {pressure}")
            else:
                logger.warning(f"验证失败: 背压 {pressure} - 脚本:{script_exists}, 定义文件:{def_exists}, INI文件:{ini_exists}")
        
        success_count = sum(1 for result in validation_results.values() if result)
        total_count = len(validation_results)
        
        logger.info(f"作业脚本验证完成: {success_count}/{total_count} 个脚本有效")
        
        return validation_results
    
    def get_job_status(self, pressure_list: List[float] = None) -> Dict[str, Dict[str, Any]]:
        """
        获取作业状态
        
        Args:
            pressure_list: 背压列表（可选，默认使用配置中的列表）
            
        Returns:
            Dict[str, Dict[str, Any]]: 作业状态字典
        """
        if pressure_list is None:
            pressure_list = self.config.pressure_list
        
        status = {}
        
        for pressure in pressure_list:
            case_dir = os.path.join(
                self.config.base_path,
                f"{self.config.folder_prefix}{pressure:g}"
            )
            
            script_file = os.path.join(case_dir, self.config.slurm_script_name)
            def_file = os.path.join(case_dir, f'{self.config.def_file_prefix}{pressure:g}.def')
            ini_file = os.path.join(case_dir, 'INI.res')
            output_file = os.path.join(case_dir, f'{self.config.job_name}_{pressure:g}.out')
            error_file = os.path.join(case_dir, f'{self.config.job_name}_{pressure:g}.err')
            
            job_status = {
                'pressure': pressure,
                'case_dir': case_dir,
                'script_file': script_file,
                'def_file': def_file,
                'ini_file': ini_file,
                'output_file': output_file,
                'error_file': error_file,
                'script_exists': os.path.exists(script_file),
                'def_exists': os.path.exists(def_file),
                'ini_exists': os.path.exists(ini_file),
                'output_exists': os.path.exists(output_file),
                'error_exists': os.path.exists(error_file),
                'script_size': os.path.getsize(script_file) if os.path.exists(script_file) else 0,
                'def_size': os.path.getsize(def_file) if os.path.exists(def_file) else 0,
                'script_mtime': os.path.getmtime(script_file) if os.path.exists(script_file) else None,
                'def_mtime': os.path.getmtime(def_file) if os.path.exists(def_file) else None
            }
            
            # 判断状态
            if job_status['script_exists'] and job_status['def_exists']:
                if self.config.ini_file and not job_status['ini_exists']:
                    job_status['status'] = 'missing_ini'
                else:
                    job_status['status'] = 'ready'
            elif job_status['def_exists']:
                job_status['status'] = 'missing_script'
            else:
                job_status['status'] = 'not_ready'
            
            status[f"P_{pressure:g}"] = job_status
        
        return status
    
    def print_job_status(self, pressure_list: List[float] = None):
        """
        打印作业状态
        
        Args:
            pressure_list: 背压列表（可选，默认使用配置中的列表）
        """
        status = self.get_job_status(pressure_list)
        
        print("\n=== Slurm作业状态 ===")
        print(f"{'压力值':<10} {'状态':<15} {'脚本文件':<10} {'定义文件':<10} {'INI文件':<10}")
        print("-" * 70)
        
        for job_name, job_info in status.items():
            pressure = job_info['pressure']
            status_str = job_info['status']
            script_exists = "✓" if job_info['script_exists'] else "✗"
            def_exists = "✓" if job_info['def_exists'] else "✗"
            ini_exists = "✓" if job_info['ini_exists'] else "✗"
            
            print(f"{pressure:<10} {status_str:<15} {script_exists:<10} {def_exists:<10} {ini_exists:<10}")
        
        print()
    
    def cleanup_job_files(self, pressure_list: List[float] = None, file_types: List[str] = None):
        """
        清理作业文件
        
        Args:
            pressure_list: 背压列表（可选，默认使用配置中的列表）
            file_types: 要清理的文件类型列表（可选）
        """
        if not self.config.cleanup_temp_files:
            return
        
        if pressure_list is None:
            pressure_list = self.config.pressure_list
        
        if file_types is None:
            file_types = ['*.out', '*.err', '*.log', '*.tmp']
        
        logger.info("清理作业文件...")
        
        for pressure in pressure_list:
            case_dir = os.path.join(
                self.config.base_path,
                f"{self.config.folder_prefix}{pressure:g}"
            )
            
            # 清理指定类型的文件
            for pattern in file_types:
                import glob
                for file in glob.glob(os.path.join(case_dir, pattern)):
                    try:
                        os.remove(file)
                        logger.debug(f"删除作业文件: {file}")
                    except Exception as e:
                        logger.warning(f"删除作业文件失败: {file} - {e}")
        
        logger.info("作业文件清理完成")
    
    def estimate_job_resources(self, pressure_list: List[float] = None) -> Dict[str, Any]:
        """
        估算作业资源需求
        
        Args:
            pressure_list: 背压列表（可选，默认使用配置中的列表）
            
        Returns:
            Dict[str, Any]: 资源需求估算
        """
        if pressure_list is None:
            pressure_list = self.config.pressure_list
        
        total_jobs = len(pressure_list)
        total_nodes = total_jobs * self.config.nodes
        total_cores = total_jobs * self.config.tasks_per_node
        
        # 估算内存需求（假设每个核心需要2GB内存）
        memory_per_core = 2  # GB
        total_memory = total_cores * memory_per_core
        
        # 估算磁盘需求（假设每个作业需要10GB磁盘空间）
        disk_per_job = 10  # GB
        total_disk = total_jobs * disk_per_job
        
        # 估算运行时间
        time_parts = self.config.time_limit.split('-')
        if len(time_parts) == 2:
            days = int(time_parts[0])
            hours_minutes = time_parts[1].split(':')
            hours = int(hours_minutes[0])
            total_hours = days * 24 + hours
        else:
            hours_minutes = self.config.time_limit.split(':')
            total_hours = int(hours_minutes[0])
        
        resource_estimate = {
            'total_jobs': total_jobs,
            'total_nodes': total_nodes,
            'total_cores': total_cores,
            'total_memory_gb': total_memory,
            'total_disk_gb': total_disk,
            'estimated_runtime_hours': total_hours,
            'partition': self.config.partition,
            'nodes_per_job': self.config.nodes,
            'cores_per_job': self.config.tasks_per_node,
            'memory_per_job_gb': self.config.tasks_per_node * memory_per_core,
            'disk_per_job_gb': disk_per_job
        }
        
        return resource_estimate
    
    def print_resource_estimate(self, pressure_list: List[float] = None):
        """
        打印资源需求估算
        
        Args:
            pressure_list: 背压列表（可选，默认使用配置中的列表）
        """
        estimate = self.estimate_job_resources(pressure_list)
        
        print("\n=== 作业资源需求估算 ===")
        print(f"总作业数: {estimate['total_jobs']}")
        print(f"总节点数: {estimate['total_nodes']}")
        print(f"总核心数: {estimate['total_cores']}")
        print(f"总内存需求: {estimate['total_memory_gb']} GB")
        print(f"总磁盘需求: {estimate['total_disk_gb']} GB")
        print(f"预计运行时间: {estimate['estimated_runtime_hours']} 小时")
        print(f"队列分区: {estimate['partition']}")
        print(f"每个作业: {estimate['nodes_per_job']} 节点, {estimate['cores_per_job']} 核心")
        print()


# 为了向后兼容，添加别名
SlurmManager = SlurmJobManager
