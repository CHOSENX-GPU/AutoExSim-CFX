"""
PBS智能节点分配模块
专门为PBS调度器设计，支持多节点配置如 "node3:ppn=28+node4:ppn=28"
"""
import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass

@dataclass
class PBSNodeSpec:
    """PBS节点规格"""
    node_name: str
    ppn: int  # 每节点处理器数
    available: bool = True
    current_load: int = 0  # 当前负载
    max_jobs: int = 2  # 最大作业数

@dataclass
class PBSAllocationResult:
    """PBS分配结果"""
    nodes_spec: str  # 生成的nodes_spec字符串
    total_cpus: int
    node_count: int
    allocated_nodes: List[str]
    load_distribution: Dict[str, int]
    warnings: List[str]

class PBSNodeAllocator:
    """PBS节点分配器"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def _convert_to_short_name(self, node_name: str) -> str:
        """转换节点名称为短格式：node41 -> n41"""
        if node_name.startswith("node"):
            return "n" + node_name[4:]  # 去掉"node"前缀，添加"n"前缀
        return node_name  # 如果已经是短格式，保持不变
        
    def parse_nodes_spec(self, nodes_spec: str) -> List[PBSNodeSpec]:
        """
        解析PBS节点规格字符串
        例如: "node3:ppn=28+node4:ppn=28" -> [PBSNodeSpec(node3, 28), PBSNodeSpec(node4, 28)]
        """
        if not nodes_spec:
            return []
            
        # 分割多个节点
        node_specs = []
        parts = nodes_spec.split('+')
        
        for part in parts:
            part = part.strip()
            if ':ppn=' in part:
                # 格式: node3:ppn=28
                node_name, ppn_part = part.split(':ppn=')
                try:
                    ppn = int(ppn_part)
                    node_specs.append(PBSNodeSpec(
                        node_name=node_name.strip(),
                        ppn=ppn,
                        available=True,
                        current_load=0
                    ))
                except ValueError:
                    self.logger.warning(f"无法解析PPN值: {ppn_part}")
            else:
                # 简单格式: node3 (使用默认ppn)
                node_specs.append(PBSNodeSpec(
                    node_name=part,
                    ppn=getattr(self.config, 'ppn', 28),
                    available=True,
                    current_load=0
                ))
        
        return node_specs
    
    def build_nodes_spec(self, node_specs: List[PBSNodeSpec]) -> str:
        """
        根据节点规格列表构建PBS nodes_spec字符串
        """
        if not node_specs:
            return ""
            
        spec_parts = []
        for spec in node_specs:
            if spec.available:
                # 转换节点名称为短格式：node41 -> n41
                short_node_name = self._convert_to_short_name(spec.node_name)
                spec_parts.append(f"{short_node_name}:ppn={spec.ppn}")
        
        return "+".join(spec_parts)
    
    def allocate_for_job(self, job: Dict, available_nodes: List[PBSNodeSpec] = None) -> PBSAllocationResult:
        """
        为单个作业分配节点
        
        Args:
            job: 作业配置
            available_nodes: 可用节点列表，如果为None则从配置中解析或智能检测
            
        Returns:
            PBSAllocationResult: 分配结果
        """
        warnings = []
        
        # 获取可用节点
        if available_nodes is None:
            nodes_spec = getattr(self.config, 'nodes_spec', '')
            if nodes_spec:
                # 从配置中解析节点规格
                available_nodes = self.parse_nodes_spec(nodes_spec)
            else:
                # 智能检测可用节点
                available_nodes = self._detect_available_nodes()
                warnings.append("智能检测可用节点")
        
        if not available_nodes:
            # 如果还是没有节点，创建默认配置
            default_ppn = getattr(self.config, 'ppn', 28)
            default_nodes = getattr(self.config, 'nodes', None) or 2  # 默认2个节点
            
            available_nodes = []
            for i in range(default_nodes):
                available_nodes.append(PBSNodeSpec(
                    node_name=f"node{i+1}",
                    ppn=default_ppn,
                    available=True,
                    current_load=0
                ))
            warnings.append("使用默认节点配置")
        
        # 获取作业需求
        required_cpus = job.get('allocated_cpus', job.get('cpus', getattr(self.config, 'tasks_per_node', 28)))
        
        # 分配策略
        allocation_strategy = getattr(self.config, 'node_allocation_strategy', 'hybrid')
        
        if allocation_strategy == 'single_node':
            result = self._allocate_single_node(job, available_nodes, required_cpus)
        elif allocation_strategy == 'multi_node':
            result = self._allocate_multi_node(job, available_nodes, required_cpus)
        elif allocation_strategy == 'hybrid':
            result = self._allocate_hybrid(job, available_nodes, required_cpus)
        else:
            result = self._allocate_auto(job, available_nodes, required_cpus)
        
        result.warnings.extend(warnings)
        return result
    
    def _detect_available_nodes(self) -> List[PBSNodeSpec]:
        """
        智能检测可用节点
        根据集群类型和配置推断可能的节点配置
        """
        cluster_type = getattr(self.config, 'cluster_type', 'group_old')
        
        if cluster_type == 'group_old':
            # 老集群的实际节点配置
            # node41-node60: 28核/节点 (20个节点)
            # node61-node62: 16核/节点 (2个节点)
            nodes = []
            
            # 添加node41-node60 (28核节点)
            for i in range(41, 61):
                nodes.append(PBSNodeSpec(f"node{i:02d}", 28, True, 0))
            
            # 添加node61-node62 (16核节点)
            for i in range(61, 63):
                nodes.append(PBSNodeSpec(f"node{i:02d}", 16, True, 0))
            
            return nodes
            
        elif cluster_type == 'group_new':
            # 新集群有统一的节点配置
            ppn = getattr(self.config, 'ppn', 28)
            return [
                PBSNodeSpec(f"compute{i:02d}", ppn, True, 0) 
                for i in range(1, 9)  # compute01-compute08
            ]
        else:
            # 学校集群或其他，使用配置的默认值
            ppn = getattr(self.config, 'ppn', 28)
            return [
                PBSNodeSpec(f"node{i}", ppn, True, 0) 
                for i in range(1, 5)  # node1-node4
            ]
    
    def _allocate_single_node(self, job: Dict, available_nodes: List[PBSNodeSpec], required_cpus: int) -> PBSAllocationResult:
        """单节点分配策略"""
        # 获取最小核心数要求
        min_cores = getattr(self.config, 'min_cores', required_cpus)
        
        # 寻找能满足需求的单个节点，优先选择刚好满足要求的节点
        suitable_nodes = []
        for node in available_nodes:
            if node.available and node.ppn >= min_cores:
                suitable_nodes.append(node)
        
        if not suitable_nodes:
            return PBSAllocationResult("", 0, 0, [], {}, ["没有满足最小核心数要求的节点"])
        
        # 选择最优节点：优先选择核心数刚好满足需求的节点
        best_node = None
        for node in suitable_nodes:
            if node.ppn >= min_cores:
                if best_node is None or node.ppn < best_node.ppn:
                    best_node = node
        
        if best_node:
            allocated_nodes = [best_node.node_name]
            # 使用节点的实际核心数，而不是只用min_cores
            actual_cpus = best_node.ppn
            # 转换节点名称为短格式：node41 -> n41
            short_node_name = self._convert_to_short_name(best_node.node_name)
            nodes_spec = f"{short_node_name}:ppn={actual_cpus}"
            
            return PBSAllocationResult(
                nodes_spec=nodes_spec,
                total_cpus=actual_cpus,
                node_count=1,
                allocated_nodes=allocated_nodes,
                load_distribution={best_node.node_name: actual_cpus},
                warnings=[f"使用单节点分配: {best_node.node_name}({actual_cpus}核)，满足最小核心数要求({min_cores}核)"]
            )
        
        # 如果没有单个节点能满足，返回警告
        return PBSAllocationResult(
            nodes_spec="",
            total_cpus=0,
            node_count=0,
            allocated_nodes=[],
            load_distribution={},
            warnings=["没有单个节点能满足CPU需求"]
        )
    
    def _allocate_multi_node(self, job: Dict, available_nodes: List[PBSNodeSpec], required_cpus: int) -> PBSAllocationResult:
        """多节点分配策略 - 优化版，考虑最佳节点组合"""
        allocated_specs = []
        allocated_nodes = []
        total_cpus = 0
        load_distribution = {}
        
        remaining_cpus = required_cpus
        
        # 按节点容量排序（大节点优先）
        sorted_nodes = sorted(available_nodes, key=lambda x: x.ppn, reverse=True)
        
        # 第一种策略：精确匹配组合（优先考虑）
        # 为32核和44核任务优化：使用28核+16核组合
        if required_cpus in [32, 44]:
            # 寻找28核+16核的组合
            node_28 = next((n for n in sorted_nodes if n.ppn == 28 and n.available), None)
            node_16 = next((n for n in sorted_nodes if n.ppn == 16 and n.available), None)
            
            if node_28 and node_16:
                allocated_specs = [node_28, node_16]
                allocated_nodes = [node_28.node_name, node_16.node_name]
                total_cpus = node_28.ppn + node_16.ppn  # 28 + 16 = 44
                
                if required_cpus == 32:
                    load_distribution = {
                        node_28.node_name: 28,
                        node_16.node_name: 4  # 只用16核节点的4核
                    }
                    warnings = [f"优化分配：使用28核+16核节点组合，总计{total_cpus}核"]
                else:  # 44核
                    load_distribution = {
                        node_28.node_name: 28,
                        node_16.node_name: 16  # 完整使用16核节点
                    }
                    warnings = [f"完美匹配：28核+16核节点组合，100%利用率"]
                
                nodes_spec = self.build_nodes_spec(allocated_specs)
                return PBSAllocationResult(
                    nodes_spec=nodes_spec,
                    total_cpus=total_cpus,
                    node_count=len(allocated_specs),
                    allocated_nodes=allocated_nodes,
                    load_distribution=load_distribution,
                    warnings=warnings
                )
        
        # 第二种策略：标准多节点分配
        for node in sorted_nodes:
            if not node.available or remaining_cpus <= 0:
                continue
                
            # 计算这个节点需要的CPU数
            cpus_for_this_node = min(remaining_cpus, node.ppn)
            
            if cpus_for_this_node > 0:
                allocated_specs.append(node)
                allocated_nodes.append(node.node_name)
                total_cpus += node.ppn  # PBS分配整个节点
                load_distribution[node.node_name] = cpus_for_this_node
                remaining_cpus -= cpus_for_this_node
        
        if remaining_cpus > 0:
            warnings = [f"仍有{remaining_cpus}个CPU未分配"]
        else:
            warnings = []
        
        nodes_spec = self.build_nodes_spec(allocated_specs)
        
        return PBSAllocationResult(
            nodes_spec=nodes_spec,
            total_cpus=total_cpus,
            node_count=len(allocated_specs),
            allocated_nodes=allocated_nodes,
            load_distribution=load_distribution,
            warnings=warnings
        )
    
    def _allocate_hybrid(self, job: Dict, available_nodes: List[PBSNodeSpec], required_cpus: int) -> PBSAllocationResult:
        """混合分配策略：优先尝试单节点，不行再多节点"""
        # 先尝试单节点
        single_result = self._allocate_single_node(job, available_nodes, required_cpus)
        if single_result.node_count > 0:
            single_result.warnings.append("使用单节点分配")
            return single_result
        
        # 单节点不行，尝试多节点
        multi_result = self._allocate_multi_node(job, available_nodes, required_cpus)
        multi_result.warnings.append("使用多节点分配")
        return multi_result
    
    def _allocate_auto(self, job: Dict, available_nodes: List[PBSNodeSpec], required_cpus: int) -> PBSAllocationResult:
        """自动分配策略：使用配置中的nodes_spec"""
        # 直接使用配置中的nodes_spec
        nodes_spec = getattr(self.config, 'nodes_spec', '')
        if not nodes_spec:
            return self._allocate_hybrid(job, available_nodes, required_cpus)
        
        allocated_specs = self.parse_nodes_spec(nodes_spec)
        allocated_nodes = [spec.node_name for spec in allocated_specs]
        total_cpus = sum(spec.ppn for spec in allocated_specs)
        
        # 简单的负载分布
        load_distribution = {}
        cpus_per_node = required_cpus // len(allocated_specs) if allocated_specs else 0
        remaining = required_cpus % len(allocated_specs) if allocated_specs else 0
        
        for i, spec in enumerate(allocated_specs):
            load = cpus_per_node
            if i < remaining:
                load += 1
            load_distribution[spec.node_name] = min(load, spec.ppn)
        
        return PBSAllocationResult(
            nodes_spec=nodes_spec,
            total_cpus=total_cpus,
            node_count=len(allocated_specs),
            allocated_nodes=allocated_nodes,
            load_distribution=load_distribution,
            warnings=["使用配置指定的节点规格"]
        )
    
    def allocate_for_multiple_jobs(self, jobs: List[Dict]) -> List[PBSAllocationResult]:
        """
        为多个作业分配节点
        考虑作业之间的资源竞争和负载均衡
        """
        results = []
        
        # 解析可用节点
        nodes_spec = getattr(self.config, 'nodes_spec', '')
        available_nodes = self.parse_nodes_spec(nodes_spec)
        
        # 为每个节点维护负载状态
        node_loads = {node.node_name: 0 for node in available_nodes}
        max_jobs_per_node = getattr(self.config, 'max_concurrent_jobs', 2)
        
        for job in jobs:
            # 更新节点可用性（基于当前负载）
            for node in available_nodes:
                current_jobs = sum(1 for r in results 
                                 if node.node_name in r.allocated_nodes)
                node.available = current_jobs < max_jobs_per_node
            
            # 分配当前作业
            result = self.allocate_for_job(job, available_nodes)
            results.append(result)
            
            # 更新负载统计
            for node_name, load in result.load_distribution.items():
                if node_name in node_loads:
                    node_loads[node_name] += load
        
        # 添加负载均衡警告
        if len(set(node_loads.values())) > 1:
            max_load = max(node_loads.values())
            min_load = min(node_loads.values())
            if max_load - min_load > 10:  # 负载差异超过10个CPU
                for result in results:
                    result.warnings.append(f"节点负载不均衡: 最大{max_load}, 最小{min_load}")
        
        return results
    
    def generate_optimized_nodes_spec(self, jobs: List[Dict]) -> str:
        """
        根据作业列表生成优化的nodes_spec
        """
        if not jobs:
            return getattr(self.config, 'nodes_spec', '')
        
        # 计算总CPU需求
        total_cpu_demand = sum(
            job.get('allocated_cpus', job.get('cpus', getattr(self.config, 'tasks_per_node', 28)))
            for job in jobs
        )
        
        # 获取可用节点
        nodes_spec = getattr(self.config, 'nodes_spec', '')
        available_nodes = self.parse_nodes_spec(nodes_spec)
        
        if not available_nodes:
            return nodes_spec
        
        # 计算需要的节点数
        ppn = getattr(self.config, 'ppn', 28)
        needed_nodes = (total_cpu_demand + ppn - 1) // ppn  # 向上取整
        
        # 选择最优节点组合
        selected_nodes = available_nodes[:min(needed_nodes, len(available_nodes))]
        
        return self.build_nodes_spec(selected_nodes)
