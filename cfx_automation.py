#!/usr/bin/env python3
"""
CFX自动化系统主程序
提供命令行界面和图形界面来运行CFX自动化工作流程
"""

import argparse
import logging
import sys
import os
from pathlib import Path
from typing import List, Optional

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import CFXAutomationConfig, ConfigManager
from src.workflow import CFXAutomationWorkflow
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
        print("请确保ANSYS CFX已正确安装，或手动配置路径")
    
    print()


def create_default_config(config_file: str):
    """创建默认配置文件"""
    print(f"创建默认配置文件: {config_file}")
    
    config = CFXAutomationConfig()
    
    # 尝试自动检测CFX安装
    if config.auto_detect_cfx:
        print("正在自动检测CFX安装...")
        config._auto_detect_cfx_paths()
    
    # 保存配置
    config.to_yaml(config_file)
    
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
            print("配置验证成功")
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
        print(f"CFX版本: {config.cfx_version}")
        print(f"CFX主目录: {config.cfx_home}")
        print(f"CFX-Pre: {config.cfx_pre_executable}")
        print(f"CFX-Solver: {config.cfx_solver_executable}")
        
        print("\n=== 作业配置 ===")
        print(f"作业名称: {config.job_name}")
        print(f"基础路径: {config.base_path}")
        print(f"CFX文件: {config.cfx_file_path}")
        print(f"背压列表: {config.pressure_list}")
        
        print("\n=== 服务器配置 ===")
        print(f"服务器: {config.ssh_user}@{config.ssh_host}:{config.ssh_port}")
        print(f"远程路径: {config.remote_base_path}")
        print(f"SSH密钥: {config.ssh_key}")
        
        print("\n=== Slurm配置 ===")
        print(f"分区: {config.partition}")
        print(f"节点数: {config.nodes}")
        print(f"每节点任务数: {config.tasks_per_node}")
        print(f"时间限制: {config.time_limit}")
        
    except Exception as e:
        print(f"显示配置信息失败: {e}")


def run_workflow(config_file: str, 
                pressure_list: Optional[List[float]] = None,
                exclude_patterns: Optional[List[str]] = None,
                dry_run: bool = False,
                steps: Optional[List[str]] = None):
    """运行工作流程"""
    print(f"运行CFX自动化工作流程: {config_file}")
    
    try:
        # 加载配置
        config = CFXAutomationConfig.from_yaml(config_file)
        
        # 创建工作流程
        workflow = CFXAutomationWorkflow(config)
        
        # 如果指定了压力列表，使用指定的值
        if pressure_list:
            config.pressure_list = pressure_list
        
        # 运行指定步骤或完整工作流程
        if steps:
            success = run_workflow_steps(workflow, steps, exclude_patterns, dry_run, config.pressure_list)
        else:
            success = workflow.run_complete_workflow(
                pressure_list=config.pressure_list,
                exclude_patterns=exclude_patterns,
                dry_run=dry_run
            )
        
        # 显示结果
        workflow.print_workflow_status()
        workflow.print_execution_summary()
        
        # 保存报告
        workflow.save_workflow_report()
        
        if success:
            print("\n✓ 工作流程执行成功!")
        else:
            print("\n✗ 工作流程执行失败!")
            return False
            
    except Exception as e:
        print(f"运行工作流程失败: {e}")
        return False
    
    return True


def run_workflow_steps(workflow: CFXAutomationWorkflow, 
                      steps: List[str],
                      exclude_patterns: Optional[List[str]] = None,
                      dry_run: bool = False,
                      pressure_list: Optional[List[float]] = None) -> bool:
    """运行指定的工作流程步骤"""
    step_functions = {
        'init': workflow.initialize_workflow,
        'cfx': lambda: workflow.generate_cfx_cases(pressure_list),
        'slurm': lambda: workflow.generate_slurm_scripts(pressure_list),
        'upload': lambda: workflow.upload_files_to_server(exclude_patterns, dry_run, pressure_list),
        'submit': lambda: workflow.submit_jobs_to_cluster(pressure_list)
    }
    
    for step in steps:
        if step not in step_functions:
            print(f"未知步骤: {step}")
            return False
        
        print(f"执行步骤: {step}")
        if not step_functions[step]():
            print(f"步骤执行失败: {step}")
            return False
    
    return True


def interactive_mode():
    """交互式模式"""
    print("=== CFX自动化系统 - 交互式模式 ===")
    
    while True:
        print("\n可用命令:")
        print("1. detect - 检测CFX安装")
        print("2. config - 配置管理")
        print("3. run - 运行工作流程")
        print("4. status - 查看状态")
        print("5. quit - 退出")
        
        choice = input("\n请选择操作 (1-5): ").strip()
        
        if choice == '1':
            detect_cfx_installations()
        elif choice == '2':
            config_menu()
        elif choice == '3':
            run_menu()
        elif choice == '4':
            status_menu()
        elif choice == '5':
            print("再见!")
            break
        else:
            print("无效选择，请重试")


def config_menu():
    """配置菜单"""
    print("\n=== 配置管理 ===")
    print("1. 创建默认配置")
    print("2. 验证配置")
    print("3. 显示配置信息")
    print("4. 返回主菜单")
    
    choice = input("请选择操作 (1-4): ").strip()
    
    if choice == '1':
        config_file = input("配置文件路径 [config/development.yaml]: ").strip()
        if not config_file:
            config_file = "config/development.yaml"
        create_default_config(config_file)
    elif choice == '2':
        config_file = input("配置文件路径 [config/development.yaml]: ").strip()
        if not config_file:
            config_file = "config/development.yaml"
        validate_config(config_file)
    elif choice == '3':
        config_file = input("配置文件路径 [config/development.yaml]: ").strip()
        if not config_file:
            config_file = "config/development.yaml"
        show_config_info(config_file)
    elif choice == '4':
        return
    else:
        print("无效选择")


def run_menu():
    """运行菜单"""
    print("\n=== 运行工作流程 ===")
    
    config_file = input("配置文件路径 [config/development.yaml]: ").strip()
    if not config_file:
        config_file = "config/development.yaml"
    
    print("1. 完整工作流程")
    print("2. 指定步骤")
    print("3. 模拟运行")
    
    choice = input("请选择运行模式 (1-3): ").strip()
    
    if choice == '1':
        run_workflow(config_file)
    elif choice == '2':
        steps_input = input("请输入步骤 (用空格分隔): init cfx slurm upload submit: ").strip()
        steps = steps_input.split() if steps_input else None
        run_workflow(config_file, steps=steps)
    elif choice == '3':
        run_workflow(config_file, dry_run=True)
    else:
        print("无效选择")


def status_menu():
    """状态菜单"""
    print("\n=== 状态查看 ===")
    print("功能开发中...")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='CFX自动化系统')
    parser.add_argument('--config', '-c', default='config/development.yaml', 
                       help='配置文件路径')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='日志级别')
    parser.add_argument('--log-file', help='日志文件路径')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 检测命令
    detect_parser = subparsers.add_parser('detect', help='检测CFX安装')
    
    # 配置命令
    config_parser = subparsers.add_parser('config', help='配置管理')
    config_group = config_parser.add_mutually_exclusive_group(required=True)
    config_group.add_argument('--create', action='store_true', help='创建默认配置')
    config_group.add_argument('--validate', action='store_true', help='验证配置')
    config_group.add_argument('--show', action='store_true', help='显示配置信息')
    
    # 运行命令
    run_parser = subparsers.add_parser('run', help='运行工作流程')
    run_parser.add_argument('--pressure-list', nargs='+', type=float, 
                           help='背压列表')
    run_parser.add_argument('--exclude', nargs='+', 
                           help='排除的文件模式')
    run_parser.add_argument('--dry-run', action='store_true', 
                           help='模拟运行')
    run_parser.add_argument('--steps', nargs='+', 
                           choices=['init', 'cfx', 'slurm', 'upload', 'submit'],
                           help='指定运行步骤')
    
    # 交互模式
    interactive_parser = subparsers.add_parser('interactive', help='交互式模式')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.log_level, args.log_file)
    
    # 确保配置目录存在
    os.makedirs(os.path.dirname(args.config), exist_ok=True)
    
    # 执行命令
    if args.command == 'detect':
        detect_cfx_installations()
    elif args.command == 'config':
        if args.create:
            create_default_config(args.config)
        elif args.validate:
            validate_config(args.config)
        elif args.show:
            show_config_info(args.config)
    elif args.command == 'run':
        success = run_workflow(
            args.config,
            pressure_list=args.pressure_list,
            exclude_patterns=args.exclude,
            dry_run=args.dry_run,
            steps=args.steps
        )
        sys.exit(0 if success else 1)
    elif args.command == 'interactive':
        interactive_mode()
    else:
        # 如果没有指定命令，显示帮助
        parser.print_help()


if __name__ == '__main__':
    main()
