"""
智能节点分配模块
实现4种分配策略：batch_allocation, node_reuse, smart_queue, hybrid
"""

import logging
import math
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass

from .config import CFXAutomationConfig


@dataclass
class AllocationResult:
    """分配结果"""
    strategy: str
    jobs: List[Dict]
    allocation_summary: Dict
    efficiency_score: float
    estimated_time: int  # 预估完成时间（分钟）
    node_utilization: float
    warnings: List[str]


class NodeAllocationError(Exception):
    """节点分配错误"""
    pass


class NodeAllocationManager:
    """节点分配管理器"""
    
    def __init__(self, config: CFXAutomationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 分配策略映射
        self.strategies = {
            "batch_allocation": self._batch_allocation,
            "node_reuse": self._node_reuse,
            "smart_queue": self._smart_queue,
            "hybrid": self._hybrid_allocation
        }
    
    def allocate_nodes(self, strategy: str, nodes: List[Dict], jobs: List[Dict]) -> AllocationResult:
        """
        执行节点分配
        
        Args:
            strategy: 分配策略名称
            nodes: 可用节点列表
            jobs: 作业列表
            
        Returns:
            AllocationResult: 分配结果
        """
        if strategy not in self.strategies:
            raise NodeAllocationError(f"不支持的分配策略: {strategy}")
        
        self.logger.info(f"执行分配策略: {strategy}")
        
        try:
            # 过滤可用节点
            available_nodes = self._filter_available_nodes(nodes)
            
            if not available_nodes:
                raise NodeAllocationError("没有可用节点")
            
            # 执行分配策略
            allocation_func = self.strategies[strategy]
            allocated_jobs = allocation_func(available_nodes, jobs)
            
            # 计算分配摘要
            summary = self._calculate_allocation_summary(allocated_jobs, available_nodes)
            
            # 计算效率评分
            efficiency = self._calculate_efficiency_score(allocated_jobs, available_nodes)
            
            # 预估完成时间
            estimated_time = self._estimate_completion_time(allocated_jobs)
            
            # 计算节点利用率
            utilization = self._calculate_node_utilization(allocated_jobs, available_nodes)
            
            # 生成警告
            warnings = self._generate_warnings(allocated_jobs, available_nodes)
            
            result = AllocationResult(
                strategy=strategy,
                jobs=allocated_jobs,
                allocation_summary=summary,
                efficiency_score=efficiency,
                estimated_time=estimated_time,
                node_utilization=utilization,
                warnings=warnings
            )
            
            self.logger.info(f"分配完成: {len(allocated_jobs)}个作业, 效率评分: {efficiency:.2f}")
            return result
            
        except Exception as e:
            self.logger.error(f"节点分配失败: {e}")
            raise NodeAllocationError(f"节点分配失败: {e}")
    
    def compare_strategies(self, nodes: List[Dict], jobs: List[Dict]) -> Dict[str, AllocationResult]:
        """
        比较所有分配策略
        
        Args:
            nodes: 可用节点列表
            jobs: 作业列表
            
        Returns:
            Dict[str, AllocationResult]: 各策略的分配结果
        """
        self.logger.info("开始比较所有分配策略...")
        
        results = {}
        
        for strategy_name in self.strategies.keys():
            try:
                result = self.allocate_nodes(strategy_name, nodes, jobs)
                results[strategy_name] = result
                self.logger.debug(f"策略 {strategy_name}: 效率={result.efficiency_score:.2f}")
            except Exception as e:
                self.logger.warning(f"策略 {strategy_name} 执行失败: {e}")
                # 创建失败结果
                results[strategy_name] = AllocationResult(
                    strategy=strategy_name,
                    jobs=[],
                    allocation_summary={"error": str(e)},
                    efficiency_score=0.0,
                    estimated_time=0,
                    node_utilization=0.0,
                    warnings=[f"分配失败: {e}"]
                )
        
        return results
    
    def _filter_available_nodes(self, nodes: List[Dict]) -> List[Dict]:
        """过滤可用节点"""
        available_nodes = []
        
        for node in nodes:
            # 检查节点可用性
            if not node.get("available", False):
                continue
            
            # 检查最小资源要求
            if node.get("cpus", 0) < 1:
                continue
            
            # 检查分区限制（如果指定）
            if self.config.partition and node.get("partition") != self.config.partition:
                continue
            
            # 检查排除节点
            if self.config.exclude_nodes:
                excluded = self.config.exclude_nodes.split(',')
                if node.get("name", "") in excluded:
                    continue
            
            available_nodes.append(node)
        
        # 按资源排序（CPU数量降序）
        available_nodes.sort(key=lambda x: x.get("cpus", 0), reverse=True)
        
        self.logger.debug(f"过滤得到{len(available_nodes)}个可用节点")
        return available_nodes
    
    def _batch_allocation(self, nodes: List[Dict], jobs: List[Dict]) -> List[Dict]:
        """
        批次分配策略：将作业按批次分配到不同节点
        适用于节点数量充足的情况
        """
        allocated_jobs = []
        node_index = 0
        
        for i, job in enumerate(jobs):
            if node_index >= len(nodes):
                # 如果节点用完，从头开始轮询
                node_index = 0
            
            node = nodes[node_index]
            
            # 计算作业所需的CPU数量
            required_cpus = job.get("cpus", self.config.tasks_per_node)
            
            # 检查节点是否有足够资源
            if node.get("cpus", 0) >= required_cpus:
                allocated_job = job.copy()
                allocated_job.update({
                    "allocated_node": node["name"],
                    "allocated_cpus": min(required_cpus, node.get("cpus", 0)),
                    "allocated_memory": node.get("memory", 0),
                    "partition": node.get("partition", ""),
                    "allocation_time": datetime.now().isoformat()
                })
                allocated_jobs.append(allocated_job)
                
                # 移动到下一个节点
                node_index += 1
            else:
                self.logger.warning(f"节点 {node['name']} 资源不足，跳过作业 {i}")
        
        return allocated_jobs
    
    def _node_reuse(self, nodes: List[Dict], jobs: List[Dict]) -> List[Dict]:
        """
        节点复用策略：优先填满单个节点再使用下一个节点
        适用于作业较小、希望提高节点利用率的情况
        """
        allocated_jobs = []
        
        # 为每个节点维护剩余资源
        node_resources = []
        for node in nodes:
            node_resources.append({
                "node": node,
                "remaining_cpus": node.get("cpus", 0),
                "remaining_memory": node.get("memory", 0),
                "allocated_jobs": 0
            })
        
        for i, job in enumerate(jobs):
            required_cpus = job.get("cpus", self.config.tasks_per_node)
            required_memory = job.get("memory", 0)
            
            # 寻找第一个有足够资源的节点
            allocated = False
            for node_res in node_resources:
                if (node_res["remaining_cpus"] >= required_cpus and 
                    node_res["remaining_memory"] >= required_memory):
                    
                    # 分配作业到这个节点
                    allocated_job = job.copy()
                    allocated_job.update({
                        "allocated_node": node_res["node"]["name"],
                        "allocated_cpus": required_cpus,
                        "allocated_memory": required_memory,
                        "partition": node_res["node"].get("partition", ""),
                        "allocation_time": datetime.now().isoformat()
                    })
                    allocated_jobs.append(allocated_job)
                    
                    # 更新节点剩余资源
                    node_res["remaining_cpus"] -= required_cpus
                    node_res["remaining_memory"] -= required_memory
                    node_res["allocated_jobs"] += 1
                    
                    allocated = True
                    break
            
            if not allocated:
                self.logger.warning(f"作业 {i} 无法分配到任何节点")
        
        return allocated_jobs
    
    def _smart_queue(self, nodes: List[Dict], jobs: List[Dict]) -> List[Dict]:
        """
        智能排队策略：根据作业大小和节点容量进行智能匹配
        考虑作业优先级和资源需求
        """
        allocated_jobs = []
        
        # 按作业大小排序（大作业优先）
        sorted_jobs = sorted(jobs, key=lambda x: x.get("cpus", self.config.tasks_per_node), reverse=True)
        
        # 为每个节点维护资源信息
        node_resources = []
        for node in nodes:
            node_resources.append({
                "node": node,
                "remaining_cpus": node.get("cpus", 0),
                "remaining_memory": node.get("memory", 0),
                "allocated_jobs": [],
                "utilization": 0.0
            })
        
        for job in sorted_jobs:
            required_cpus = job.get("cpus", self.config.tasks_per_node)
            required_memory = job.get("memory", 0)
            
            # 找到最佳匹配节点
            best_node = None
            best_score = -1
            
            for node_res in node_resources:
                if (node_res["remaining_cpus"] >= required_cpus and 
                    node_res["remaining_memory"] >= required_memory):
                    
                    # 计算匹配分数（考虑资源利用率和负载均衡）
                    cpu_ratio = required_cpus / node_res["node"].get("cpus", 1)
                    memory_ratio = required_memory / max(node_res["node"].get("memory", 1), 1)
                    load_factor = 1.0 - (len(node_res["allocated_jobs"]) / max(self.config.max_concurrent_jobs, 1))
                    
                    score = (cpu_ratio + memory_ratio) * load_factor
                    
                    if score > best_score:
                        best_score = score
                        best_node = node_res
            
            if best_node:
                # 分配作业
                allocated_job = job.copy()
                allocated_job.update({
                    "allocated_node": best_node["node"]["name"],
                    "allocated_cpus": required_cpus,
                    "allocated_memory": required_memory,
                    "partition": best_node["node"].get("partition", ""),
                    "allocation_time": datetime.now().isoformat(),
                    "match_score": best_score
                })
                allocated_jobs.append(allocated_job)
                
                # 更新节点资源
                best_node["remaining_cpus"] -= required_cpus
                best_node["remaining_memory"] -= required_memory
                best_node["allocated_jobs"].append(allocated_job)
                best_node["utilization"] = 1.0 - (best_node["remaining_cpus"] / best_node["node"].get("cpus", 1))
        
        return allocated_jobs
    
    def _hybrid_allocation(self, nodes: List[Dict], jobs: List[Dict]) -> List[Dict]:
        """
        混合分配策略：结合多种策略的优点
        根据作业数量和节点数量动态选择最佳策略
        """
        job_count = len(jobs)
        node_count = len(nodes)
        
        # 根据作业密度选择策略
        job_density = job_count / max(node_count, 1)
        
        if job_density <= 1.0:
            # 作业少，节点多 -> 使用批次分配
            self.logger.debug("混合策略选择：批次分配（作业密度低）")
            return self._batch_allocation(nodes, jobs)
        elif job_density <= 3.0:
            # 中等密度 -> 使用智能排队
            self.logger.debug("混合策略选择：智能排队（作业密度中等）")
            return self._smart_queue(nodes, jobs)
        else:
            # 作业多，节点少 -> 使用节点复用
            self.logger.debug("混合策略选择：节点复用（作业密度高）")
            return self._node_reuse(nodes, jobs)
    
    def _calculate_allocation_summary(self, allocated_jobs: List[Dict], nodes: List[Dict]) -> Dict:
        """计算分配摘要"""
        if not allocated_jobs:
            return {
                "total_jobs": 0,
                "allocated_jobs": 0,
                "failed_jobs": 0,
                "nodes_used": 0,
                "total_cpus_allocated": 0,
                "allocation_rate": 0.0
            }
        
        # 统计使用的节点
        used_nodes = set(job.get("allocated_node") for job in allocated_jobs)
        
        # 统计分配的CPU
        total_cpus = sum(job.get("allocated_cpus", 0) for job in allocated_jobs)
        
        return {
            "total_jobs": len(allocated_jobs),
            "allocated_jobs": len(allocated_jobs),
            "failed_jobs": 0,  # 这里假设都成功分配
            "nodes_used": len(used_nodes),
            "total_cpus_allocated": total_cpus,
            "allocation_rate": 1.0,  # 分配成功率
            "used_nodes": list(used_nodes)
        }
    
    def _calculate_efficiency_score(self, allocated_jobs: List[Dict], nodes: List[Dict]) -> float:
        """计算效率评分（0-100分）"""
        if not allocated_jobs or not nodes:
            return 0.0
        
        # 计算资源利用率
        total_allocated_cpus = sum(job.get("allocated_cpus", 0) for job in allocated_jobs)
        total_available_cpus = sum(node.get("cpus", 0) for node in nodes)
        
        if total_available_cpus == 0:
            return 0.0
        
        cpu_utilization = total_allocated_cpus / total_available_cpus
        
        # 计算负载均衡度
        node_loads = {}
        for job in allocated_jobs:
            node = job.get("allocated_node")
            if node:
                node_loads[node] = node_loads.get(node, 0) + job.get("allocated_cpus", 0)
        
        if node_loads:
            load_variance = sum((load - sum(node_loads.values()) / len(node_loads)) ** 2 
                              for load in node_loads.values()) / len(node_loads)
            load_balance = 1.0 / (1.0 + load_variance / 100)  # 标准化
        else:
            load_balance = 1.0
        
        # 综合评分
        efficiency = (cpu_utilization * 0.7 + load_balance * 0.3) * 100
        return min(efficiency, 100.0)
    
    def _estimate_completion_time(self, allocated_jobs: List[Dict]) -> int:
        """预估完成时间（分钟）"""
        if not allocated_jobs:
            return 0
        
        # 按节点分组计算并行时间
        node_jobs = {}
        for job in allocated_jobs:
            node = job.get("allocated_node")
            if node:
                if node not in node_jobs:
                    node_jobs[node] = []
                node_jobs[node].append(job)
        
        # 假设每个作业的运行时间
        avg_job_time = job.get("estimated_runtime", 60)  # 默认60分钟
        
        # 计算每个节点的完成时间
        node_times = []
        for node, jobs in node_jobs.items():
            # 假设节点内作业并行执行
            node_time = avg_job_time * math.ceil(len(jobs) / max(1, self.config.max_concurrent_jobs))
            node_times.append(node_time)
        
        # 返回最长的节点时间
        return max(node_times) if node_times else avg_job_time
    
    def _calculate_node_utilization(self, allocated_jobs: List[Dict], nodes: List[Dict]) -> float:
        """计算节点利用率"""
        if not nodes:
            return 0.0
        
        total_cpus = sum(node.get("cpus", 0) for node in nodes)
        allocated_cpus = sum(job.get("allocated_cpus", 0) for job in allocated_jobs)
        
        if total_cpus == 0:
            return 0.0
        
        return allocated_cpus / total_cpus
    
    def _generate_warnings(self, allocated_jobs: List[Dict], nodes: List[Dict]) -> List[str]:
        """生成分配警告"""
        warnings = []
        
        # 检查节点利用率
        utilization = self._calculate_node_utilization(allocated_jobs, nodes)
        if utilization < 0.3:
            warnings.append(f"节点利用率较低 ({utilization:.1%})，考虑减少使用的节点数量")
        elif utilization > 0.9:
            warnings.append(f"节点利用率很高 ({utilization:.1%})，可能出现资源竞争")
        
        # 检查负载均衡
        node_loads = {}
        for job in allocated_jobs:
            node = job.get("allocated_node")
            if node:
                node_loads[node] = node_loads.get(node, 0) + 1
        
        if node_loads:
            max_load = max(node_loads.values())
            min_load = min(node_loads.values())
            if max_load > min_load * 2:
                warnings.append("节点负载不均衡，部分节点可能过载")
        
        # 检查未分配的作业
        unallocated = len([job for job in allocated_jobs if not job.get("allocated_node")])
        if unallocated > 0:
            warnings.append(f"有{unallocated}个作业未能分配到节点")
        
        return warnings
