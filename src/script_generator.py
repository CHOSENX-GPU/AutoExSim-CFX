"""
作业脚本生成模块
支持SLURM和PBS调度系统的作业脚本生成
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, Template

try:
    from .config import CFXAutomationConfig
except ImportError:
    from config import CFXAutomationConfig

try:
    from .pbs_node_allocator import PBSNodeAllocator
except ImportError:
    from pbs_node_allocator import PBSNodeAllocator


class ScriptGenerationError(Exception):
    """脚本生成错误"""
    pass


class ScriptGenerator:
    """脚本生成器"""
    
    def __init__(self, config: CFXAutomationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 模板目录
        self.template_dir = self._get_template_directory()
        self.env = Environment(loader=FileSystemLoader(self.template_dir))
        
        # 添加自定义过滤器
        self.env.filters['strftime'] = lambda date, fmt: date.strftime(fmt) if hasattr(date, 'strftime') else datetime.now().strftime(fmt)
    
    def _get_template_directory(self) -> str:
        """获取模板目录"""
        # 优先使用配置的模板目录
        if hasattr(self.config, 'template_dir') and self.config.template_dir:
            return self.config.template_dir
        
        # 默认模板目录
        default_template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
        if os.path.exists(default_template_dir):
            return default_template_dir
        
        # 相对路径
        return "templates"
    
    def generate_job_scripts(self, allocated_jobs: List[Dict], cluster_status: Dict = None) -> Dict[str, List[str]]:
        """
        生成作业脚本
        
        Args:
            allocated_jobs: 已分配的作业列表
            cluster_status: 集群状态信息
            
        Returns:
            Dict: 包含生成的脚本路径信息
        """
        self.logger.info(f"开始生成{len(allocated_jobs)}个作业脚本...")
        
        try:
            generated_scripts = {
                "job_scripts": [],
                "submit_script": "",
                "monitor_script": "",
                "queue_strategy": "sequential"  # 添加排队策略信息
            }
            
            # 如果是PBS调度器，需要统一管理节点分配
            allocated_nodes_tracker = set()  # 跟踪已分配的节点
            
            # 检查可用节点数量并确定排队策略
            available_node_count = self._get_available_node_count(cluster_status)
            queue_strategy = self._determine_queue_strategy(len(allocated_jobs), available_node_count)
            
            self.logger.info(f"可用节点数: {available_node_count}, 作业数: {len(allocated_jobs)}, 排队策略: {queue_strategy}")
            
            # 根据排队策略生成脚本
            if queue_strategy == "parallel":
                # 并行策略：每个作业分配独立节点
                self._generate_parallel_jobs(allocated_jobs, cluster_status, allocated_nodes_tracker, generated_scripts)
            elif queue_strategy == "sequential":
                # 顺序策略：作业排队执行
                self._generate_sequential_jobs(allocated_jobs, cluster_status, generated_scripts)
            elif queue_strategy == "batch":
                # 批次策略：分批执行作业
                self._generate_batch_jobs(allocated_jobs, cluster_status, available_node_count, generated_scripts)
            
            generated_scripts["queue_strategy"] = queue_strategy
            
            # 生成批量提交脚本（包含排队逻辑）
            submit_script = self._generate_submit_script(generated_scripts["job_scripts"], queue_strategy, available_node_count)
            if submit_script:
                generated_scripts["submit_script"] = submit_script
                self.logger.info(f"✓ 生成批量提交脚本: {submit_script}")
            
            # 生成监控脚本
            monitor_script = self._generate_monitor_script(allocated_jobs)
            if monitor_script:
                generated_scripts["monitor_script"] = monitor_script
                self.logger.info(f"✓ 生成监控脚本: {monitor_script}")
            
            # 汇总输出
            self.logger.info("=" * 60)
            self.logger.info("脚本生成汇总:")
            self.logger.info(f"  ✓ 作业脚本: {len(generated_scripts['job_scripts'])} 个")
            self.logger.info(f"  ✓ 排队策略: {queue_strategy}")
            if submit_script:
                self.logger.info(f"  ✓ 提交脚本: 1 个 (Submit_All.sh)")
            if monitor_script:
                self.logger.info(f"  ✓ 监控脚本: 1 个 (Monitor_Jobs.sh)")
            self.logger.info("=" * 60)
            
            return generated_scripts
            
        except Exception as e:
            self.logger.error(f"脚本生成失败: {e}")
            raise ScriptGenerationError(f"脚本生成失败: {e}")
    
    def _generate_single_job_script(self, job: Dict, cluster_status: Dict = None, allocated_nodes_tracker: set = None, use_best_real_node: bool = False) -> Optional[str]:
        """生成单个作业脚本"""
        try:
            # 根据调度器类型选择模板
            if self.config.scheduler_type == "SLURM":
                template_name = self._get_slurm_template_name()
            elif self.config.scheduler_type == "PBS":
                template_name = self._get_pbs_template_name()
            else:
                raise ScriptGenerationError(f"不支持的调度器类型: {self.config.scheduler_type}")
            
            # 加载模板
            template = self.env.get_template(template_name)
            
            # 准备模板变量
            template_vars = self._prepare_template_variables(job, cluster_status, allocated_nodes_tracker, use_best_real_node)
            
            # 渲染模板
            content = template.render(**template_vars)
            
            # 生成脚本文件
            script_filename = self._get_job_script_filename(job)
            
            # 如果作业有输出目录，在该目录下生成脚本
            if "output_dir" in job and job["output_dir"]:
                script_dir = os.path.join(self.config.base_path, job["output_dir"])
                os.makedirs(script_dir, exist_ok=True)
                script_path = os.path.join(script_dir, script_filename)
            else:
                script_path = os.path.join(self.config.base_path, script_filename)
            
            with open(script_path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(content)
            
            self.logger.debug(f"生成作业脚本: {script_path}")
            return script_path
            
        except Exception as e:
            self.logger.error(f"生成单个作业脚本失败: {e}")
            return None
    
    def _get_slurm_template_name(self) -> str:
        """获取SLURM模板名称"""
        if self.config.cluster_type == "university":
            return "CFX_University.slurm.j2"
        elif self.config.cluster_type == "group_new":
            # 组内新集群使用统一的sbatch模板
            return getattr(self.config, 'sbatch_template', 'CFX_Group_Cluster.sbatch.j2')
        else:
            return "CFX_Group_Cluster.slurm.j2"  # 默认模板
    
    def _get_pbs_template_name(self) -> str:
        """获取PBS模板名称"""
        return "CFX_Group_PBS.pbs.j2"
    
    def _prepare_template_variables(self, job: Dict, cluster_status: Dict = None, allocated_nodes_tracker: set = None, use_best_real_node: bool = False) -> Dict:
        """准备模板变量"""
        
        # 调试日志：检查job中的initial_file
        self.logger.info(f"[DEBUG] 作业数据 - pressure: {job.get('pressure')}, initial_file: {job.get('initial_file', 'NOT_FOUND')}")
        
        # 基础变量
        variables = {
            # 作业基本信息 - 生成包含压力参数的作业名称
            "job_name": self._generate_job_name(job),
            "project_name": self.config.project_name,
            
            # 作业参数
            "pressure": job.get("pressure", ""),  # 添加压力参数
            
            # 资源配置
            "nodes": job.get("nodes", self.config.nodes),
            "tasks_per_node": job.get("allocated_cpus", self.config.tasks_per_node),
            "total_tasks": job.get("total_tasks", getattr(self.config, 'total_tasks', job.get("allocated_cpus", self.config.tasks_per_node))),
            "cpus": job.get("allocated_cpus", self.config.tasks_per_node),
            "memory": self._format_memory(job.get("allocated_memory", 0)),
            
            # 时间限制
            "time_limit": job.get("time_limit", self.config.time_limit),
            "walltime": job.get("walltime", self.config.walltime),
            
            # CFX配置 - 处理def文件路径
            "def_file": self._get_relative_def_file_path(job),
            "cfx_solver": self.config.get_remote_cfx_executable_path("cfx5solve"),
            "cfx_version": self.config.remote_cfx_version,
            "remote_cfx_bin_path": self.config.remote_cfx_bin_path,
            "cfx_bin_path": self.config.remote_cfx_bin_path,  # 为新模板添加别名
            "cfx_module": getattr(self.config, 'cfx_module', ''),
            "cfx_module_name": getattr(self.config, 'cfx_module_name', ''),  # 新增cfx_module_name
            "use_module": getattr(self.config, 'use_module', False),
            
            # 初始文件（如果有）
            "initial_file": job.get("initial_file", ""),
            "initial_file_basename": os.path.basename(job.get("initial_file", "")) if job.get("initial_file") else "",
            
            # 输出文件 - 基于压力参数或def文件名
            "output_file": job.get("output_file", f"{job.get('pressure', 'job')}.out"),
            "error_file": job.get("error_file", f"{job.get('pressure', 'job')}.err"),
            "result_file": self._get_result_file_name(job),
            
            # 工作目录和输出目录
            "work_dir": self.config.remote_base_path,
            "output_dir": job.get("output_dir", ""),
            
            # 邮件通知（如果配置）
            "email": getattr(self.config, 'email', ''),
            "email_events": getattr(self.config, 'email_events', 'END,FAIL')
        }
        
        # 调度器特定变量
        if self.config.scheduler_type == "SLURM":
            variables.update({
                "partition": job.get("partition", self.config.partition),
                "qos": self.config.qos,
                "account": getattr(self.config, 'account', ''),
                "nodelist": job.get("allocated_node", self.config.nodelist),
                "exclude": self.config.exclude_nodes
            })
        elif self.config.scheduler_type == "PBS":
            # PBS特定配置 - 使用智能节点分配器
            # 创建PBS节点分配器
            pbs_allocator = PBSNodeAllocator(self.config)
            
            # 准备可用节点列表（排除已分配的节点）
            available_nodes = None
            self.logger.info(f"集群状态类型: {type(cluster_status)}, 内容: {cluster_status is not None}")
            
            if cluster_status:
                # cluster_status直接是节点列表，转换为PBSNodeSpec格式
                available_nodes = []
                nodes_list = cluster_status if isinstance(cluster_status, list) else cluster_status.get("nodes", [])
                
                self.logger.info(f"节点列表类型: {type(nodes_list)}, 长度: {len(nodes_list) if hasattr(nodes_list, '__len__') else 'N/A'}")
                
                if use_best_real_node:
                    # 使用最优真实节点（排队策略）
                    best_nodes = [node for node in nodes_list if node.get("available", False)]
                    if best_nodes:
                        # 选择最优的可用节点
                        best_node = best_nodes[0]
                        from .pbs_node_allocator import PBSNodeSpec
                        available_nodes.append(PBSNodeSpec(
                            node_name=best_node["name"],
                            ppn=best_node.get("cpus", 28),
                            available=True,
                            current_load=0
                        ))
                        self.logger.info(f"使用最优真实节点进行排队: {best_node['name']}")
                    else:
                        # 如果没有可用节点，使用所有真实节点中的第一个
                        if nodes_list:
                            fallback_node = nodes_list[0]
                            from .pbs_node_allocator import PBSNodeSpec
                            available_nodes.append(PBSNodeSpec(
                                node_name=fallback_node["name"],
                                ppn=fallback_node.get("cpus", 28),
                                available=True,  # 强制标记为可用，用于排队
                                current_load=0
                            ))
                            self.logger.info(f"使用真实节点进行排队（节点可能繁忙）: {fallback_node['name']}")
                else:
                    # 正常分配模式
                    for node in nodes_list:
                        # 排除已分配的节点
                        if (node.get("available", False) and 
                            (allocated_nodes_tracker is None or node["name"] not in allocated_nodes_tracker)):
                            from .pbs_node_allocator import PBSNodeSpec
                            available_nodes.append(PBSNodeSpec(
                                node_name=node["name"],
                                ppn=node.get("cpus", 28),
                                available=True,
                                current_load=0
                            ))
                    
                    # 如果没有可用节点了，选择最优的真实节点进行排队
                    if not available_nodes and nodes_list:
                        self.logger.warning("所有节点已分配完毕，选择最优真实节点进行排队")
                        # 选择第一个可用的真实节点
                        best_real_nodes = [node for node in nodes_list if node.get("available", False)]
                        if best_real_nodes:
                            fallback_node = best_real_nodes[0]
                        else:
                            # 如果连可用节点都没有，选择任意真实节点
                            fallback_node = nodes_list[0]
                        
                        from .pbs_node_allocator import PBSNodeSpec
                        available_nodes.append(PBSNodeSpec(
                            node_name=fallback_node["name"],
                            ppn=fallback_node.get("cpus", 28),
                            available=True,  # 强制标记为可用，用于排队
                            current_load=0
                        ))
                        self.logger.info(f"回退到真实节点排队: {fallback_node['name']}")
                    
                    self.logger.info(f"使用真实集群状态，找到{len(available_nodes)}个可用节点（排除已分配: {len(allocated_nodes_tracker) if allocated_nodes_tracker else 0}个）")
            else:
                self.logger.warning("没有接收到集群状态信息，将使用智能检测节点")
            
            # 为当前作业分配节点
            allocation_result = pbs_allocator.allocate_for_job(job, available_nodes)
            
            # 如果分配失败，使用默认配置
            if not allocation_result.nodes_spec:
                pbs_nodes_spec = getattr(self.config, 'nodes_spec', f"1:ppn={job.get('allocated_cpus', getattr(self.config, 'ppn', 16))}")
                self.logger.warning("PBS节点分配失败，使用默认配置")
            else:
                pbs_nodes_spec = allocation_result.nodes_spec
                self.logger.info(f"PBS节点分配成功: {pbs_nodes_spec}")
                
                # 将分配的节点添加到跟踪器中（仅在非排队模式下）
                if allocated_nodes_tracker is not None and not use_best_real_node:
                    for node_name in allocation_result.allocated_nodes:
                        allocated_nodes_tracker.add(node_name)
                        self.logger.debug(f"节点 {node_name} 已添加到分配跟踪器")
                
                # 记录分配详情
                if allocation_result.warnings:
                    for warning in allocation_result.warnings:
                        self.logger.warning(f"PBS分配警告: {warning}")
            
            variables.update({
                "queue": getattr(self.config, 'queue', 'batch'),
                "ppn": job.get("allocated_cpus", getattr(self.config, 'ppn', 16)),
                "nodes_spec": pbs_nodes_spec,
                "walltime": getattr(self.config, 'walltime', '24:00:00'),
                "email": getattr(self.config, 'email', ''),
                "email_events": getattr(self.config, 'email_events', 'abe'),
                "memory_per_node": self._format_memory(job.get("allocated_memory", 0), pbs_format=True),
                # 添加分配结果信息
                "allocated_nodes": allocation_result.allocated_nodes if allocation_result.nodes_spec else [],
                "total_allocated_cpus": allocation_result.total_cpus if allocation_result.nodes_spec else job.get('allocated_cpus', getattr(self.config, 'ppn', 16)),
                "node_count": allocation_result.node_count if allocation_result.nodes_spec else 1
            })
        
        # 添加作业特定变量
        variables.update(job)
        
        # 重新设置def_file为相对路径（避免被job字典覆盖）
        variables["def_file"] = self._get_relative_def_file_path(job)
        
        return variables
    
    def _get_available_node_count(self, cluster_status: Dict = None) -> int:
        """获取可用节点数量"""
        if not cluster_status:
            # 如果没有集群状态，使用配置的默认值
            return getattr(self.config, 'default_available_nodes', 2)
        
        if isinstance(cluster_status, list):
            # cluster_status直接是节点列表
            return sum(1 for node in cluster_status if node.get("available", False))
        elif isinstance(cluster_status, dict) and "nodes" in cluster_status:
            # cluster_status包含节点信息
            return sum(1 for node in cluster_status["nodes"] if node.get("available", False))
        else:
            return getattr(self.config, 'default_available_nodes', 2)
    
    def _determine_queue_strategy(self, job_count: int, available_nodes: int) -> str:
        """确定排队策略"""
        if available_nodes >= job_count:
            # 节点数量充足，可以并行执行
            return "parallel"
        elif available_nodes >= 1:
            if job_count <= available_nodes * 2:
                # 适中的作业数量，使用批次策略
                return "batch"
            else:
                # 作业数量较多，使用顺序策略
                return "sequential"
        else:
            # 没有可用节点，只能顺序等待
            return "sequential"
    
    def _generate_parallel_jobs(self, allocated_jobs: List[Dict], cluster_status: Dict, 
                               allocated_nodes_tracker: set, generated_scripts: Dict):
        """生成并行执行的作业脚本"""
        self.logger.info("使用并行策略：每个作业分配独立节点")
        
        for job in allocated_jobs:
            script_path = self._generate_single_job_script(job, cluster_status, allocated_nodes_tracker, False)
            if script_path:
                generated_scripts["job_scripts"].append(script_path)
                rel_path = os.path.relpath(script_path, self.config.base_path)
                self.logger.info(f"  ✓ 生成作业脚本: {rel_path}")
    
    def _generate_sequential_jobs(self, allocated_jobs: List[Dict], cluster_status: Dict, 
                                 generated_scripts: Dict):
        """生成顺序执行的作业脚本"""
        self.logger.info("使用顺序策略：作业将依次排队执行")
        
        # 获取所有真实可用节点（包括已分配的）
        all_available_nodes = self._get_all_real_nodes(cluster_status)
        
        # 为顺序执行，使用最优的真实节点（允许重复使用同一节点）
        for job in allocated_jobs:
            script_path = self._generate_single_job_script(job, cluster_status, None, use_best_real_node=True)
            if script_path:
                generated_scripts["job_scripts"].append(script_path)
                rel_path = os.path.relpath(script_path, self.config.base_path)
                self.logger.info(f"  ✓ 生成作业脚本: {rel_path} (排队执行)")
    
    def _generate_batch_jobs(self, allocated_jobs: List[Dict], cluster_status: Dict, 
                            available_nodes: int, generated_scripts: Dict):
        """生成批次执行的作业脚本"""
        self.logger.info(f"使用批次策略：{available_nodes}个节点分批执行{len(allocated_jobs)}个作业")
        
        # 将作业分成批次
        batch_size = available_nodes
        batches = [allocated_jobs[i:i + batch_size] for i in range(0, len(allocated_jobs), batch_size)]
        
        self.logger.info(f"作业分为{len(batches)}个批次，每批次最多{batch_size}个作业")
        
        for batch_idx, batch_jobs in enumerate(batches):
            allocated_nodes_tracker = set()  # 每个批次重新分配节点
            self.logger.info(f"生成第{batch_idx + 1}批次（{len(batch_jobs)}个作业）:")
            
            for job in batch_jobs:
                # 为批次中的作业添加批次信息
                job_with_batch = job.copy()
                job_with_batch["batch_id"] = batch_idx + 1
                job_with_batch["total_batches"] = len(batches)
                
                script_path = self._generate_single_job_script(job_with_batch, cluster_status, allocated_nodes_tracker, False)
                if script_path:
                    generated_scripts["job_scripts"].append(script_path)
                    rel_path = os.path.relpath(script_path, self.config.base_path)
                    self.logger.info(f"    ✓ 批次{batch_idx + 1}: {rel_path}")
    
    def _get_all_real_nodes(self, cluster_status: Dict = None) -> List[Dict]:
        """获取所有真实节点列表（包括不可用的）"""
        if not cluster_status:
            return []
        
        if isinstance(cluster_status, list):
            return cluster_status
        elif isinstance(cluster_status, dict) and "nodes" in cluster_status:
            return cluster_status["nodes"]
        else:
            return []
    
    def _format_memory(self, memory_mb: int, pbs_format: bool = False) -> str:
        """格式化内存大小"""
        if memory_mb <= 0:
            return self.config.memory_per_node if not pbs_format else self.config.memory
        
        if memory_mb < 1024:
            return f"{memory_mb}MB"
        else:
            memory_gb = memory_mb / 1024
            if pbs_format:
                return f"{memory_gb:.0f}gb"
            else:
                return f"{memory_gb:.0f}GB"
    
    def _generate_job_name(self, job: Dict) -> str:
        """生成包含压力参数的作业名称"""
        # 如果作业已有明确的名称，直接使用
        if job.get("name"):
            return job["name"]
        
        # 优先使用压力参数生成名称
        if "pressure" in job:
            base_name = getattr(self.config, 'job_name', 'CFX_Job')
            # 移除base_name中可能存在的尾部下划线
            base_name = base_name.rstrip('_')
            return f"{base_name}_{job['pressure']}"
        
        # 使用ID生成名称
        if job.get('id'):
            base_name = getattr(self.config, 'job_name', 'CFX_Job')
            base_name = base_name.rstrip('_')
            return f"{base_name}_{job['id']}"
        
        # 默认名称
        return getattr(self.config, 'job_name', 'CFX_Job')
    
    def _get_job_script_filename(self, job: Dict) -> str:
        """获取作业脚本文件名"""
        # 使用相同的作业名称生成逻辑
        job_name = self._generate_job_name(job)
        
        if self.config.scheduler_type == "SLURM":
            return f"{job_name}.slurm"
        elif self.config.scheduler_type == "PBS":
            return f"{job_name}.pbs"
        else:
            return f"{job_name}.sh"
    
    def _get_relative_def_file_path(self, job: Dict) -> str:
        """获取相对于作业目录的def文件路径"""
        def_file = job.get("def_file", "")
        output_dir = job.get("output_dir", "")
        
        if not def_file:
            return ""
        
        # 如果有输出目录，从def文件路径中提取文件名
        if output_dir and def_file.startswith(output_dir + "/"):
            # 去掉输出目录前缀，只保留文件名
            return def_file[len(output_dir) + 1:]
        elif output_dir:
            # 如果def文件路径不包含输出目录前缀，则使用文件名
            return os.path.basename(def_file)
        else:
            # 没有输出目录时，使用完整路径
            return def_file
    
    def _get_result_file_name(self, job: Dict) -> str:
        """获取CFX结果文件名"""
        # CFX通常生成的结果文件名是基于def文件名 + _001.res
        def_file = job.get("def_file", "")
        if def_file:
            # 获取不带扩展名的文件名
            base_name = os.path.splitext(os.path.basename(def_file))[0]
            return f"{base_name}_001.res"
        elif "pressure" in job:
            # 如果有压力参数，使用压力参数作为基础名称
            return f"{job['pressure']}_001.res"
        else:
            # 默认名称
            return "job_001.res"
    
    def _generate_submit_script(self, job_scripts: List[str], queue_strategy: str = "sequential", 
                               available_nodes: int = 1) -> Optional[str]:
        """生成批量提交脚本"""
        try:
            template_name = "Submit_All.sh.j2"
            
            # 如果模板不存在，生成默认脚本
            try:
                template = self.env.get_template(template_name)
                self.logger.debug(f"成功加载模板: {template_name}")
            except Exception as e:
                self.logger.warning(f"模板加载失败，使用默认脚本: {e}")
                return self._generate_default_submit_script(job_scripts, queue_strategy, available_nodes)
            
            # 准备变量
            script_paths = []
            for script in job_scripts:
                # 计算相对于base_path的路径
                rel_path = os.path.relpath(script, self.config.base_path)
                script_paths.append(rel_path)
            
            # 获取背压列表
            pressure_list = getattr(self.config, 'pressure_list', [2300, 2400, 2500, 2600])
            
            variables = {
                "job_scripts": script_paths,
                "scheduler_type": self.config.scheduler_type,
                "submit_delay": getattr(self.config, 'job_submit_delay', 2),
                "max_concurrent": min(self.config.max_concurrent_jobs, available_nodes),
                # 新增变量支持新模板
                "job_name": getattr(self.config, 'job_name', 'CFX_Job'),
                "pressure_list": pressure_list,
                "remote_base_path": self.config.remote_base_path,
                "folder_prefix": "P_Out_",
                "slurm_script_name": "job_*.slurm",
                # 排队策略相关变量
                "queue_strategy": queue_strategy,
                "available_nodes": available_nodes,
                "total_jobs": len(job_scripts)
            }
            
            self.logger.debug(f"模板变量: {variables}")
            
            # 渲染模板
            try:
                content = template.render(**variables)
                self.logger.debug("模板渲染成功")
            except Exception as e:
                self.logger.error(f"模板渲染失败: {e}")
                return self._generate_default_submit_script(job_scripts, queue_strategy, available_nodes)
            
            # 保存脚本
            script_path = os.path.join(self.config.base_path, "Submit_All.sh")
            with open(script_path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(content)
            
            # 设置执行权限
            os.chmod(script_path, 0o755)
            
            self.logger.debug(f"生成批量提交脚本: {script_path}")
            return script_path
            
        except Exception as e:
            self.logger.error(f"生成批量提交脚本失败: {e}")
            return None
    
    def _generate_default_submit_script(self, job_scripts: List[str], queue_strategy: str = "sequential", 
                                       available_nodes: int = 1) -> str:
        """生成默认提交脚本"""
        script_lines = [
            "#!/bin/bash", 
            "# CFX作业批量提交脚本", 
            f"# 排队策略: {queue_strategy}",
            f"# 可用节点数: {available_nodes}",
            f"# 总作业数: {len(job_scripts)}",
            ""
        ]
        
        submit_cmd = "sbatch" if self.config.scheduler_type == "SLURM" else "qsub"
        
        if queue_strategy == "parallel":
            # 并行策略：同时提交所有作业
            script_lines.append("echo \"并行提交所有作业...\"")
            for script in job_scripts:
                rel_path = os.path.relpath(script, self.config.base_path)
                script_lines.append(f"echo \"提交作业: {rel_path}\"")
                script_lines.append(f"{submit_cmd} {rel_path} &")
            script_lines.append("wait  # 等待所有作业提交完成")
            
        elif queue_strategy == "sequential":
            # 顺序策略：依次提交作业
            script_lines.append("echo \"顺序提交作业（等待前一个完成后提交下一个）...\"")
            for i, script in enumerate(job_scripts):
                rel_path = os.path.relpath(script, self.config.base_path)
                script_lines.append(f"echo \"提交作业 {i+1}/{len(job_scripts)}: {rel_path}\"")
                script_lines.append(f"JOB_ID=$({submit_cmd} {rel_path})")
                if i < len(job_scripts) - 1:  # 不是最后一个作业
                    if self.config.scheduler_type == "SLURM":
                        script_lines.append("echo \"等待作业完成...\"")
                        script_lines.append("while squeue -j $JOB_ID &>/dev/null; do sleep 30; done")
                    else:  # PBS
                        script_lines.append("echo \"等待作业完成...\"")
                        script_lines.append("while qstat $JOB_ID &>/dev/null; do sleep 30; done")
                script_lines.append("")
                
        elif queue_strategy == "batch":
            # 批次策略：分批提交
            batch_size = available_nodes
            script_lines.append(f"echo \"分批提交作业（每批{batch_size}个）...\"")
            
            for i in range(0, len(job_scripts), batch_size):
                batch_scripts = job_scripts[i:i + batch_size]
                batch_num = i // batch_size + 1
                
                script_lines.append(f"echo \"提交第{batch_num}批次（{len(batch_scripts)}个作业）...\"")
                
                # 提交当前批次的所有作业
                job_ids = []
                for script in batch_scripts:
                    rel_path = os.path.relpath(script, self.config.base_path)
                    script_lines.append(f"echo \"  提交: {rel_path}\"")
                    script_lines.append(f"JOB_ID=$({submit_cmd} {rel_path})")
                    script_lines.append("JOB_IDS=\"$JOB_IDS $JOB_ID\"")
                
                # 等待当前批次完成（如果不是最后一批）
                if i + batch_size < len(job_scripts):
                    script_lines.append("echo \"等待当前批次完成...\"")
                    if self.config.scheduler_type == "SLURM":
                        script_lines.append("for job_id in $JOB_IDS; do")
                        script_lines.append("    while squeue -j $job_id &>/dev/null; do sleep 30; done")
                        script_lines.append("done")
                    else:  # PBS
                        script_lines.append("for job_id in $JOB_IDS; do")
                        script_lines.append("    while qstat $job_id &>/dev/null; do sleep 30; done")
                        script_lines.append("done")
                    script_lines.append("JOB_IDS=\"\"  # 清空作业ID列表")
                script_lines.append("")
        
        script_lines.append("echo \"所有作业已提交\"")
        
        content = "\n".join(script_lines)
        
        script_path = os.path.join(self.config.base_path, "Submit_All.sh")
        with open(script_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)
        
        os.chmod(script_path, 0o755)
        return script_path
    
    def _generate_monitor_script(self, allocated_jobs: List[Dict]) -> Optional[str]:
        """生成监控脚本"""
        try:
            template_name = "Monitor_Jobs.sh.j2"
            
            # 如果模板不存在，生成默认脚本
            try:
                template = self.env.get_template(template_name)
            except:
                return self._generate_default_monitor_script(allocated_jobs)
            
            # 准备变量
            job_names = [job.get("name", f"job_{job.get('id', '')}") for job in allocated_jobs]
            
            variables = {
                "job_names": job_names,
                "scheduler_type": self.config.scheduler_type,
                "check_interval": getattr(self.config, 'monitor_interval', 60),
                "result_patterns": getattr(self.config, 'result_file_patterns', ["*.res", "*.out", "*.log"])
            }
            
            # 渲染模板
            content = template.render(**variables)
            
            # 保存脚本
            script_path = os.path.join(self.config.base_path, "Monitor_Jobs.sh")
            with open(script_path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(content)
            
            os.chmod(script_path, 0o755)
            
            self.logger.debug(f"生成监控脚本: {script_path}")
            return script_path
            
        except Exception as e:
            self.logger.error(f"生成监控脚本失败: {e}")
            return None
    
    def _generate_default_monitor_script(self, allocated_jobs: List[Dict]) -> str:
        """生成默认监控脚本"""
        script_lines = [
            "#!/bin/bash",
            "# CFX作业监控脚本",
            "",
            f"SCHEDULER=\"{self.config.scheduler_type}\"",
            "CHECK_INTERVAL=60",
            "",
            "# 作业名称列表"
        ]
        
        job_names = [job.get("name", f"job_{job.get('id', '')}") for job in allocated_jobs]
        script_lines.append(f"JOBS=({' '.join(job_names)})")
        script_lines.append("")
        
        # 添加监控逻辑
        if self.config.scheduler_type == "SLURM":
            check_cmd = "squeue -n"
        else:
            check_cmd = "qstat -f"
        
        script_lines.extend([
            "echo \"开始监控作业...\"",
            "while true; do",
            "    running_jobs=0",
            "    for job in \"${JOBS[@]}\"; do",
            f"        if {check_cmd} $job &>/dev/null; then",
            "            running_jobs=$((running_jobs + 1))",
            "        fi",
            "    done",
            "",
            "    if [ $running_jobs -eq 0 ]; then",
            "        echo \"所有作业已完成\"",
            "        break",
            "    else",
            "        echo \"$(date): $running_jobs 个作业仍在运行\"",
            "    fi",
            "",
            "    sleep $CHECK_INTERVAL",
            "done",
            "",
            "echo \"监控结束\""
        ])
        
        content = "\n".join(script_lines)
        
        script_path = os.path.join(self.config.base_path, "Monitor_Jobs.sh")
        with open(script_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)
        
        os.chmod(script_path, 0o755)
        return script_path
    
    def validate_templates(self) -> Dict[str, bool]:
        """验证模板文件"""
        templates_to_check = []
        
        if self.config.scheduler_type == "SLURM":
            templates_to_check.append(self._get_slurm_template_name())
        elif self.config.scheduler_type == "PBS":
            templates_to_check.append(self._get_pbs_template_name())
        
        templates_to_check.extend([
            "Submit_All.sh.j2",
            "Monitor_Jobs.sh.j2",
            "create_def.pre.j2"
        ])
        
        validation_results = {}
        
        for template_name in templates_to_check:
            try:
                template_path = os.path.join(self.template_dir, template_name)
                exists = os.path.exists(template_path)
                validation_results[template_name] = exists
                
                if exists:
                    # 尝试加载模板
                    template = self.env.get_template(template_name)
                    validation_results[f"{template_name}_loadable"] = True
                else:
                    validation_results[f"{template_name}_loadable"] = False
                    self.logger.warning(f"模板文件不存在: {template_path}")
                    
            except Exception as e:
                validation_results[template_name] = False
                validation_results[f"{template_name}_loadable"] = False
                self.logger.error(f"模板验证失败 {template_name}: {e}")
        
        return validation_results
