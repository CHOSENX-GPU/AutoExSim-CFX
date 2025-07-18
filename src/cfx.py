"""
CFX-Pre自动化模块
自动生成CFX Session文件，执行CFX-Pre，生成定义文件
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from .config import CFXAutomationConfig, TemplateManager

logger = logging.getLogger(__name__)


class CFXPreAutomation:
    """CFX-Pre自动化类"""
    
    def __init__(self, config: CFXAutomationConfig):
        self.config = config
        self.template_manager = TemplateManager(config.template_dir)
        
        # 暂时跳过CFX-Pre可执行文件验证（用于测试）
        if config.cfx_pre_executable and os.path.exists(config.cfx_pre_executable):
            logger.info(f"CFX-Pre executable found: {config.cfx_pre_executable}")
        else:
            logger.warning(f"CFX-Pre executable not found: {config.cfx_pre_executable}")
            logger.info("继续执行，但CFX-Pre功能将被禁用")

    def generate_session_file(self, output_file: str, **kwargs) -> str:
        """
        生成CFX Session文件
        
        Args:
            output_file: 输出文件路径
            **kwargs: 额外的模板变量
            
        Returns:
            str: 生成的Session文件路径
        """
        logger.info(f"生成CFX Session文件: {output_file}")
        
        # 准备模板变量
        template_vars = self._prepare_template_vars(**kwargs)
        
        # 渲染模板
        self.template_manager.render_to_file(
            self.config.session_template,
            output_file,
            **template_vars
        )
        
        logger.info(f"CFX Session文件已生成: {output_file}")
        return output_file
    
    def _prepare_template_vars(self, **kwargs) -> Dict[str, Any]:
        """准备模板变量"""
        template_vars = {
            # 基础配置
            'cfx_version': self.config.cfx_version,
            'cfx_file_path': self.config.cfx_file_path,
            'base_path': self.config.base_path,
            'pressure_list': self.config.pressure_list,
            
            # CFX模型配置
            'flow_analysis_name': self.config.flow_analysis_name,
            'domain_name': self.config.domain_name,
            'boundary_name': self.config.boundary_name,
            'outlet_location': self.config.outlet_location,
            'pressure_blend': self.config.pressure_blend,
            
            # 文件命名配置
            'folder_prefix': self.config.folder_prefix,
            'def_file_prefix': self.config.def_file_prefix,
            
            # 作业配置
            'job_name': self.config.job_name,
            'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            
            # 额外参数
            **kwargs
        }
        
        return template_vars
    
    def execute_session(self, session_file: str, cfx_file: str = None) -> bool:
        """
        执行CFX-Pre Session文件
        
        Args:
            session_file: Session文件路径
            cfx_file: CFX文件路径（可选，默认使用配置中的路径）
            
        Returns:
            bool: 执行是否成功
        """
        if cfx_file is None:
            cfx_file = self.config.cfx_file_path
        
        if not os.path.exists(session_file):
            logger.error(f"Session文件不存在: {session_file}")
            return False
        
        if not os.path.exists(cfx_file):
            logger.error(f"CFX文件不存在: {cfx_file}")
            return False
        
        logger.info(f"执行CFX-Pre Session: {session_file}")
        
        # 构建命令
        command = [
            self.config.cfx_pre_executable,
            '-batch',
            session_file
        ]
        
        try:
            # 执行命令
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=3600,  # 1小时超时
                cwd=os.path.dirname(session_file)
            )
            
            # 检查执行结果
            if result.returncode == 0:
                logger.info("CFX-Pre Session执行成功")
                if result.stdout:
                    logger.debug(f"CFX-Pre输出: {result.stdout}")
                return True
            else:
                logger.error(f"CFX-Pre Session执行失败 (返回码: {result.returncode})")
                if result.stderr:
                    logger.error(f"错误信息: {result.stderr}")
                if result.stdout:
                    logger.error(f"输出信息: {result.stdout}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("CFX-Pre Session执行超时")
            return False
        except Exception as e:
            logger.error(f"CFX-Pre Session执行异常: {e}")
            return False
    
    def generate_parametric_cases(self, pressure_list: List[float] = None) -> List[str]:
        """
        生成参数化算例
        
        Args:
            pressure_list: 背压列表（可选，默认使用配置中的列表）
            
        Returns:
            List[str]: 生成的定义文件路径列表
        """
        if pressure_list is None:
            pressure_list = self.config.pressure_list
        
        logger.info(f"生成参数化算例，背压列表: {pressure_list}")
        
        # 为所有背压值创建目录
        for pressure in pressure_list:
            case_dir = os.path.join(
                self.config.base_path,
                f"{self.config.folder_prefix}{pressure:g}"
            )
            os.makedirs(case_dir, exist_ok=True)
        
        # 生成统一的Session文件（在基础路径下）
        session_file = os.path.join(self.config.base_path, "create_def.pre")
        self.generate_session_file(
            session_file,
            pressure_list=pressure_list,  # 传递整个压力列表
            current_case_dir=self.config.base_path
        )
        
        # 执行一次Session文件，生成所有def文件
        generated_files = []
        if self.execute_session(session_file):
            logger.info("成功执行Session文件，检查生成的def文件")
            
            # 检查每个背压值对应的def文件是否生成
            for pressure in pressure_list:
                case_dir = os.path.join(
                    self.config.base_path,
                    f"{self.config.folder_prefix}{pressure:g}"
                )
                def_file = os.path.join(case_dir, f"{self.config.def_file_prefix}{pressure:g}.def")
                
                if os.path.exists(def_file):
                    generated_files.append(def_file)
                    logger.info(f"def文件生成成功: {def_file}")
                else:
                    logger.warning(f"def文件未生成: {def_file}")
        else:
            logger.error("Session文件执行失败")
        
        logger.info(f"总共生成了 {len(generated_files)} 个def文件")
        return generated_files
    
    def validate_generated_files(self, pressure_list: List[float] = None) -> Dict[str, bool]:
        """
        验证生成的文件
        
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
            
            def_file = os.path.join(case_dir, f"{self.config.def_file_prefix}{pressure:g}.def")
            
            # 检查定义文件是否存在
            if os.path.exists(def_file):
                # 检查文件大小
                file_size = os.path.getsize(def_file)
                if file_size > 0:
                    validation_results[def_file] = True
                    logger.info(f"验证成功: {def_file} ({file_size} bytes)")
                else:
                    validation_results[def_file] = False
                    logger.warning(f"验证失败: {def_file} (文件大小为0)")
            else:
                validation_results[def_file] = False
                logger.warning(f"验证失败: {def_file} (文件不存在)")
        
        success_count = sum(1 for result in validation_results.values() if result)
        total_count = len(validation_results)
        
        logger.info(f"文件验证完成: {success_count}/{total_count} 个文件有效")
        
        return validation_results
    
    def cleanup_temp_files(self, pressure_list: List[float] = None):
        """
        清理临时文件
        
        Args:
            pressure_list: 背压列表（可选，默认使用配置中的列表）
        """
        if not self.config.cleanup_temp_files:
            return
        
        if pressure_list is None:
            pressure_list = self.config.pressure_list
        
        logger.info("清理临时文件...")
        
        for pressure in pressure_list:
            case_dir = os.path.join(
                self.config.base_path,
                f"{self.config.folder_prefix}{pressure:g}"
            )
            
            # 清理临时文件
            temp_files = [
                "create_def.pre",
                "*.tmp",
                "*.bak",
                "*.log"
            ]
            
            for pattern in temp_files:
                import glob
                for file in glob.glob(os.path.join(case_dir, pattern)):
                    try:
                        os.remove(file)
                        logger.debug(f"删除临时文件: {file}")
                    except Exception as e:
                        logger.warning(f"删除临时文件失败: {file} - {e}")
        
        logger.info("临时文件清理完成")
    
    def get_case_status(self, pressure_list: List[float] = None) -> Dict[str, Dict[str, Any]]:
        """
        获取算例状态
        
        Args:
            pressure_list: 背压列表（可选，默认使用配置中的列表）
            
        Returns:
            Dict[str, Dict[str, Any]]: 算例状态字典
        """
        if pressure_list is None:
            pressure_list = self.config.pressure_list
        
        status = {}
        
        for pressure in pressure_list:
            case_dir = os.path.join(
                self.config.base_path,
                f"{self.config.folder_prefix}{pressure:g}"
            )
            
            def_file = os.path.join(case_dir, f"{self.config.def_file_prefix}{pressure:g}.def")
            session_file = os.path.join(case_dir, "create_def.pre")
            
            case_status = {
                'pressure': pressure,
                'case_dir': case_dir,
                'def_file': def_file,
                'session_file': session_file,
                'case_dir_exists': os.path.exists(case_dir),
                'def_file_exists': os.path.exists(def_file),
                'session_file_exists': os.path.exists(session_file),
                'def_file_size': os.path.getsize(def_file) if os.path.exists(def_file) else 0,
                'def_file_mtime': os.path.getmtime(def_file) if os.path.exists(def_file) else None
            }
            
            # 判断状态
            if case_status['def_file_exists'] and case_status['def_file_size'] > 0:
                case_status['status'] = 'completed'
            elif case_status['case_dir_exists']:
                case_status['status'] = 'in_progress'
            else:
                case_status['status'] = 'not_started'
            
            status[f"P_{pressure:g}"] = case_status
        
        return status
    
    def print_case_status(self, pressure_list: List[float] = None):
        """
        打印算例状态
        
        Args:
            pressure_list: 背压列表（可选，默认使用配置中的列表）
        """
        status = self.get_case_status(pressure_list)
        
        print("\n=== CFX算例状态 ===")
        print(f"{'压力值':<10} {'状态':<12} {'定义文件':<15} {'文件大小':<10}")
        print("-" * 60)
        
        for case_name, case_info in status.items():
            pressure = case_info['pressure']
            status_str = case_info['status']
            def_exists = "✓" if case_info['def_file_exists'] else "✗"
            file_size = f"{case_info['def_file_size']} B" if case_info['def_file_size'] > 0 else "0 B"
            
            print(f"{pressure:<10} {status_str:<12} {def_exists:<15} {file_size:<10}")
        
        print()


# 为了向后兼容，添加别名
CFXManager = CFXPreAutomation
