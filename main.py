#!/usr/bin/env python3
"""
CFX自动化系统主程序
提供命令行界面来运行CFX自动化工作流程
"""

import argparse
import logging
import sys
import os
import json
from pathlib import Path
from typing import List, Optional, Dict

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import CFXAutomationConfig
from src.workflow_orchestrator import WorkflowOrchestrator, WorkflowError
from src.utils.cfx_detector import CFXPathDetector


def setup_logging(log_level: str = 'INFO', log_file: str = None):
    """设置日志配置"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 配置根日志记录器
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )
    
    # 如果指定了日志文件，也输出到文件
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(file_handler)


def detect_cfx_installations():
    """检测CFX安装"""
    print("=== CFX安装检测 ===")
    
    detector = CFXPathDetector()
    installation = detector.detect_cfx_installation()
    
    if installation and installation.get('cfx_home'):
        print("检测到CFX安装:")
        print(f"CFX版本: {installation.get('cfx_version', 'Unknown')}")
        print(f"CFX主目录: {installation.get('cfx_home', 'N/A')}")
        print(f"CFX bin路径: {installation.get('cfx_bin_path', 'N/A')}")
        print(f"CFX-Pre: {installation.get('cfx_pre_executable', 'N/A')}")
        print(f"CFX-Solver: {installation.get('cfx_solver_executable', 'N/A')}")
        print(f"检测方法: {installation.get('detection_method', 'N/A')}")
        print()
    else:
        print("未检测到CFX安装")
        print("请确保ANSYS CFX已正确安装，或手动配置路径")
    
    print()


def create_default_config(config_file: str):
    """创建默认配置文件"""
    print(f"创建默认配置文件: {config_file}")
    
    # 创建配置目录
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    
    # 基础配置模板
    default_config = {
        "cfx_mode": "local",
        "auto_detect_cfx": True,
        "cfx_home": "",
        "cfx_bin_path": "",
        "remote_cfx_home": "/path/to/remote/cfx",
        "remote_cfx_bin_path": "/path/to/remote/cfx/bin",
        
        "project_name": "CFX_Project",
        "job_name": "CFX_Job",
        "base_path": "D:/CFX_Projects/",
        
        "cfx_file_path": "path/to/your/model.cfx",
        "pre_template_path": "templates/create_def.pre.j2",
        
        "flow_analysis_name": "Flow Analysis 1",
        "domain_name": "Domain1",
        "boundary_name": "Outlet",
        "outlet_location": "OUTLET",
        "pressure_blend": "0.05",
        
        "folder_prefix": "P_",
        "def_file_prefix": "",
        "pressure_list": [1000, 2000, 3000],
        "pressure_unit": "Pa",
        
        "ssh_host": "your.cluster.hostname",
        "ssh_port": 22,
        "ssh_user": "your_username",
        "ssh_password": "",
        "ssh_key": "",
        "remote_base_path": "/home/user/cfx_jobs",
        
        "cluster_type": "university",
        "scheduler_type": "SLURM",
        
        "enable_node_detection": False,
        "enable_node_allocation": False,
        
        "partition": "cpu",
        "nodes": 1,
        "tasks_per_node": 32,
        "time_limit": "24:00:00",
        "memory_per_node": "64GB",
        "qos": "",
        
        "enable_monitoring": True,
        "monitor_interval": 300,
        "auto_download_results": True,
        "cleanup_remote_files": False,
        "result_file_patterns": ["*.res", "*.out", "*.log", "*.err"],
        
        "transfer_retry_times": 3,
        "transfer_timeout": 300,
        "enable_checksum_verification": True,
        
        "max_concurrent_jobs": 5,
        "job_submit_delay": 5
    }
    
    # 尝试自动检测CFX安装
    detector = CFXPathDetector()
    installation = detector.detect_cfx_installation()
    if installation and installation.get('cfx_home'):
        default_config["cfx_home"] = installation["cfx_home"]
        default_config["cfx_bin_path"] = installation["cfx_bin_path"]
        print(f"自动检测到CFX安装: {installation.get('cfx_version', 'Unknown')}")
    
    # 保存配置
    import yaml
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
    
    print(f"默认配置已保存到: {config_file}")
    print("请编辑配置文件以适应您的环境")


def validate_config(config_file: str):
    """验证配置文件"""
    print(f"验证配置文件: {config_file}")
    
    try:
        config = CFXAutomationConfig.from_yaml(config_file)
        errors = config.validate()
        
        if errors:
            print("配置验证失败:")
            for error in errors:
                print(f"  - {error}")
            return False
        else:
            print("✓ 配置验证成功")
            return True
            
    except Exception as e:
        print(f"配置文件加载失败: {e}")
        return False


def show_config_info(config_file: str):
    """显示配置信息"""
    print(f"配置信息: {config_file}")
    
    try:
        config = CFXAutomationConfig.from_yaml(config_file)
        
        print("\n=== CFX环境 ===")
        print(f"CFX模式: {config.cfx_mode}")
        print(f"CFX主目录: {config.cfx_home}")
        print(f"CFX bin路径: {config.cfx_bin_path}")
        
        print("\n=== 项目配置 ===")
        print(f"项目名称: {config.project_name}")
        print(f"作业名称: {config.job_name}")
        print(f"基础路径: {config.base_path}")
        print(f"CFX文件: {config.cfx_file_path}")
        print(f"初始文件: {config.initial_file if hasattr(config, 'initial_file') and config.initial_file else '未设置'}")
        print(f"压力列表: {config.pressure_list}")
        
        print("\n=== 服务器配置 ===")
        print(f"服务器: {config.ssh_user}@{config.ssh_host}:{config.ssh_port}")
        print(f"远程路径: {config.remote_base_path}")
        print(f"SSH密钥: {config.ssh_key}")
        print(f"SSH密码: {'已设置' if hasattr(config, 'ssh_password') and config.ssh_password else '未设置'}")
        
        print("\n=== 集群配置 ===")
        print(f"集群类型: {config.cluster_type}")
        print(f"调度器: {config.scheduler_type}")
        
        # 根据调度器类型显示相应的队列/分区信息
        if config.scheduler_type == "PBS":
            queue_name = getattr(config, 'queue', 'N/A')
            print(f"队列: {queue_name}")
            # PBS相关配置
            walltime = getattr(config, 'walltime', 'N/A')
            memory = getattr(config, 'memory', 'N/A')
            min_cores = getattr(config, 'min_cores', 'N/A')
            print(f"运行时间: {walltime}")
            print(f"内存要求: {memory}")
            print(f"最小核心数: {min_cores}")
        else:
            partition_name = getattr(config, 'partition', 'N/A')
            print(f"分区: {partition_name}")
            print(f"节点数: {config.nodes}")
            print(f"每节点任务数: {config.tasks_per_node}")
            print(f"时间限制: {config.time_limit}")
        
    except Exception as e:
        print(f"显示配置信息失败: {e}")


def run_workflow(config_file: str, 
                pressure_list: Optional[List[float]] = None,
                dry_run: bool = False,
                steps: Optional[List[str]] = None):
    """运行工作流程"""
    print(f"运行CFX自动化工作流程: {config_file}")
    
    try:
        # 加载配置
        config = CFXAutomationConfig.from_yaml(config_file)
        
        # 验证配置
        errors = config.validate()
        if errors:
            print("配置验证失败:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        # 创建工作流编排器
        orchestrator = WorkflowOrchestrator(config)
        
        # 准备作业配置
        if pressure_list:
            config.pressure_list = pressure_list
        
        job_configs = []
        for i, pressure in enumerate(config.pressure_list):
            job_config = {
                "job_id": f"{config.job_name}_{i+1}",
                "pressure": pressure,
                "pressure_unit": config.pressure_unit,
                "folder_name": f"{config.folder_prefix}{pressure}",
                "output_dir": f"{config.folder_prefix}{pressure}",  # 添加output_dir字段
                "def_file_name": f"{config.def_file_prefix}P_{pressure}.def"
            }
            job_configs.append(job_config)
        
        # 运行工作流程
        if dry_run:
            print("=== 试运行模式 ===")
            print(f"将处理 {len(job_configs)} 个作业:")
            for job in job_configs:
                print(f"  - {job['job_id']}: 压力={job['pressure']} {job['pressure_unit']}")
            return True
        
        if steps:
            success = run_workflow_steps(orchestrator, steps, job_configs)
        else:
            success = run_complete_workflow(orchestrator, job_configs)
        
        if success:
            print("\n✓ 工作流程执行成功!")
        else:
            print("\n✗ 工作流程执行失败!")
            return False
            
    except Exception as e:
        print(f"运行工作流程失败: {e}")
        return False
    
    return True


def run_complete_workflow(orchestrator: WorkflowOrchestrator, job_configs: List[Dict]) -> bool:
    """运行完整工作流程"""
    try:
        report = orchestrator.execute_full_workflow(job_configs)
        
        # 显示执行摘要
        print("\n=== 执行摘要 ===")
        summary = report["execution_summary"]
        print(f"总作业数: {summary['total_jobs']}")
        print(f"成功提交: {summary['successful_submissions']}")
        print(f"执行时长: {summary['execution_duration_seconds']}秒")
        print(f"完成步骤: {', '.join(summary['completed_steps'])}")
        
        if summary['failed_steps']:
            print(f"失败步骤: {', '.join(summary['failed_steps'])}")
        
        return len(summary['failed_steps']) == 0
        
    except WorkflowError as e:
        print(f"工作流程执行失败: {e}")
        return False


def run_workflow_steps(orchestrator: WorkflowOrchestrator, 
                      steps: List[str], 
                      job_configs: List[Dict]) -> bool:
    """运行指定的工作流程步骤"""
    available_steps = [
        'connect_server', 'verify_cfx', 'generate_pre', 
        'generate_def', 'query_cluster', 'generate_scripts', 
        'upload_files', 'submit_jobs', 'monitor_jobs'
    ]
    
    for step in steps:
        if step not in available_steps:
            print(f"未知步骤: {step}")
            print(f"可用步骤: {', '.join(available_steps)}")
            return False
    
    try:
        for step in steps:
            print(f"\n执行步骤: {step}")
            
            if step == 'generate_pre':
                result = orchestrator.execute_step_only(step, job_configs=job_configs)
            else:
                result = orchestrator.execute_step_only(step)
            
            print(f"✓ 步骤完成: {step}")
        
        return True
        
    except Exception as e:
        print(f"步骤执行失败: {e}")
        return False


def query_cluster_status(config_file: str):
    """查询集群状态"""
    try:
        config = CFXAutomationConfig.from_yaml(config_file)
        orchestrator = WorkflowOrchestrator(config)
        
        print("连接到集群...")
        orchestrator.execute_step_only('connect_server')
        
        print("查询集群状态...")
        if config.enable_node_detection:
            result = orchestrator.execute_step_only('query_cluster')
            
            # result直接是节点列表，不是包含success的字典
            if result and isinstance(result, list):
                nodes = result
                print(f"\n=== 集群节点状态 ===")
                print(f"总节点数: {len(nodes)}")
                
                # 对于PBS，查找状态为'idle'的可用节点，或者检查available字段
                if config.scheduler_type == "PBS":
                    available_nodes = [n for n in nodes if isinstance(n, dict) and n.get('available', False)]
                else:
                    available_nodes = [n for n in nodes if isinstance(n, dict) and n.get('state') == 'idle']
                    
                print(f"可用节点: {len(available_nodes)}")
                
                if available_nodes:
                    print("\n可用节点详情:")
                    for node in available_nodes:
                        if isinstance(node, dict):
                            print(f"  - {node.get('name', 'N/A')}: "
                                  f"CPU={node.get('cpus', 'N/A')}, "
                                  f"内存={node.get('memory', 'N/A')}")
                else:
                    print("当前没有可用节点")
            else:
                print("集群状态查询失败或返回数据格式异常")
        else:
            print("节点检测功能未启用")
        
    except Exception as e:
        print(f"查询集群状态失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='CFX自动化系统 - 批量CFX计算工作流程自动化',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python main.py --detect-cfx              检测CFX安装
  python main.py --create-config config.yaml   创建默认配置文件
  python main.py --validate config.yaml         验证配置文件
  python main.py --info config.yaml             显示配置信息
  python main.py --run config.yaml              运行完整工作流程
  python main.py --run config.yaml --dry-run    试运行模式
  python main.py --run config.yaml --steps connect_server verify_cfx
  python main.py --cluster-status config.yaml   查询集群状态
        """
    )
    
    # 全局选项
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='日志级别')
    parser.add_argument('--log-file', help='日志文件路径')
    
    # 功能选项
    parser.add_argument('--detect-cfx', action='store_true', help='检测CFX安装')
    parser.add_argument('--create-config', metavar='CONFIG_FILE', help='创建默认配置文件')
    parser.add_argument('--validate', metavar='CONFIG_FILE', help='验证配置文件')
    parser.add_argument('--info', metavar='CONFIG_FILE', help='显示配置信息')
    parser.add_argument('--cluster-status', metavar='CONFIG_FILE', help='查询集群状态')
    
    # 工作流程选项
    parser.add_argument('--run', metavar='CONFIG_FILE', help='运行工作流程')
    parser.add_argument('--pressure-list', nargs='+', type=float, 
                       help='指定压力列表（覆盖配置文件中的设置）')
    parser.add_argument('--dry-run', action='store_true', help='试运行模式（不实际执行）')
    parser.add_argument('--steps', nargs='+', 
                       choices=['connect_server', 'verify_cfx', 'generate_pre', 
                               'generate_def', 'query_cluster', 'generate_scripts',
                               'upload_files', 'submit_jobs', 'monitor_jobs'],
                       help='只执行指定步骤')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.log_level, args.log_file)
    
    # 检查是否指定了任何操作
    if not any([args.detect_cfx, args.create_config, args.validate, 
                args.info, args.run, args.cluster_status]):
        parser.print_help()
        return 1
    
    try:
        # 执行相应的操作
        if args.detect_cfx:
            detect_cfx_installations()
        
        if args.create_config:
            create_default_config(args.create_config)
        
        if args.validate:
            if not validate_config(args.validate):
                return 1
        
        if args.info:
            show_config_info(args.info)
        
        if args.cluster_status:
            query_cluster_status(args.cluster_status)
        
        if args.run:
            success = run_workflow(
                args.run, 
                pressure_list=args.pressure_list,
                dry_run=args.dry_run,
                steps=args.steps
            )
            if not success:
                return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\n操作被用户中断")
        return 1
    except Exception as e:
        print(f"程序执行失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
