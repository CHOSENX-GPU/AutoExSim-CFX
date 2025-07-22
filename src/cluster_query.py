"""
集群查询模块
支持SLURM和PBS调度系统的节点状态查询
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime

try:
    from .config import CFXAutomationConfig
except ImportError:
    from config import CFXAutomationConfig


class ClusterQueryError(Exception):
    """集群查询错误"""
    pass


class ClusterQueryManager:
    """集群查询管理器"""
    
    def __init__(self, config: CFXAutomationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 支持的调度器
        self.supported_schedulers = ["SLURM", "PBS"]
    
    def detect_scheduler_type(self, ssh_client) -> Optional[str]:
        """
        自动检测调度器类型
        
        Args:
            ssh_client: SSH客户端连接
            
        Returns:
            str: 调度器类型 (SLURM/PBS) 或 None
        """
        try:
            # 检测SLURM
            stdin, stdout, stderr = ssh_client.exec_command("which sinfo")
            if stdout.channel.recv_exit_status() == 0:
                self.logger.info("检测到SLURM调度器")
                return "SLURM"
            
            # 检测PBS
            stdin, stdout, stderr = ssh_client.exec_command("which pbsnodes")
            if stdout.channel.recv_exit_status() == 0:
                self.logger.info("检测到PBS调度器")
                return "PBS"
            
            self.logger.warning("未检测到支持的调度器")
            return None
            
        except Exception as e:
            self.logger.error(f"调度器检测失败: {e}")
            return None
    
    def query_cluster_nodes(self, ssh_client, scheduler_type: Optional[str] = None) -> List[Dict]:
        """
        查询集群节点信息
        
        Args:
            ssh_client: SSH客户端连接
            scheduler_type: 调度器类型，如果未指定则自动检测
            
        Returns:
            List[Dict]: 节点信息列表
        """
        if not scheduler_type:
            scheduler_type = self.detect_scheduler_type(ssh_client)
        
        if not scheduler_type:
            raise ClusterQueryError("无法检测调度器类型")
        
        if scheduler_type == "SLURM":
            return self._query_slurm_nodes(ssh_client)
        elif scheduler_type == "PBS":
            return self._query_pbs_nodes(ssh_client)
        else:
            raise ClusterQueryError(f"不支持的调度器类型: {scheduler_type}")
    
    def _query_slurm_nodes(self, ssh_client) -> List[Dict]:
        """查询SLURM节点信息"""
        try:
            self.logger.info("查询SLURM节点信息...")
            
            # 执行sinfo命令获取节点信息
            cmd = "sinfo -N -h -o '%N %c %m %t %P %f'"
            stdin, stdout, stderr = ssh_client.exec_command(cmd)
            
            if stdout.channel.recv_exit_status() != 0:
                error_msg = stderr.read().decode()
                raise ClusterQueryError(f"SLURM查询失败: {error_msg}")
            
            output = stdout.read().decode()
            return self._parse_slurm_output(output)
            
        except Exception as e:
            self.logger.error(f"SLURM节点查询失败: {e}")
            raise ClusterQueryError(f"SLURM节点查询失败: {e}")
    
    def _parse_slurm_output(self, output: str) -> List[Dict]:
        """解析SLURM输出"""
        nodes = []
        
        for line in output.strip().split('\n'):
            if not line.strip():
                continue
            
            parts = line.split()
            if len(parts) >= 5:
                node_info = {
                    "name": parts[0],
                    "cpus": self._parse_cpu_count(parts[1]),
                    "memory": self._parse_memory_size(parts[2]),
                    "state": self._normalize_slurm_state(parts[3]),
                    "partition": parts[4] if len(parts) > 4 else "",
                    "features": parts[5] if len(parts) > 5 else "",
                    "scheduler": "SLURM",
                    "available": self._is_slurm_node_available(parts[3]),
                    "query_time": datetime.now().isoformat()
                }
                nodes.append(node_info)
        
        self.logger.info(f"解析到{len(nodes)}个SLURM节点")
        return nodes
    
    def _normalize_slurm_state(self, state: str) -> str:
        """标准化SLURM节点状态"""
        state_map = {
            "idle": "idle",
            "alloc": "allocated",
            "mix": "mixed",
            "down": "down",
            "drain": "draining",
            "comp": "completing",
            "resv": "reserved"
        }
        return state_map.get(state.lower(), state)
    
    def _is_slurm_node_available(self, state: str) -> bool:
        """判断SLURM节点是否可用"""
        available_states = ["idle", "mix"]
        return state.lower() in available_states
    
    def _query_pbs_nodes(self, ssh_client) -> List[Dict]:
        """查询PBS节点信息"""
        try:
            self.logger.info("查询PBS节点信息...")
            
            # 执行pbsnodes命令获取节点信息
            cmd = "pbsnodes -a"
            stdin, stdout, stderr = ssh_client.exec_command(cmd)
            
            if stdout.channel.recv_exit_status() != 0:
                error_msg = stderr.read().decode()
                raise ClusterQueryError(f"PBS查询失败: {error_msg}")
            
            output = stdout.read().decode()
            return self._parse_pbs_output(output)
            
        except Exception as e:
            self.logger.error(f"PBS节点查询失败: {e}")
            raise ClusterQueryError(f"PBS节点查询失败: {e}")
    
    def _parse_pbs_output(self, output: str) -> List[Dict]:
        """解析PBS输出"""
        nodes = []
        current_node = None
        
        for line in output.split('\n'):
            original_line = line
            line = line.strip()
            
            if not line:
                if current_node:
                    nodes.append(current_node)
                    current_node = None
                continue
            
            # 新节点开始 - 节点名不以空格或制表符开头
            if not original_line.startswith(' ') and not original_line.startswith('\t') and not '=' in line:
                if current_node:
                    nodes.append(current_node)
                
                current_node = {
                    "name": line,
                    "cpus": 0,
                    "memory": 0,
                    "state": "unknown",
                    "scheduler": "PBS",
                    "available": False,
                    "properties": [],
                    "jobs": [],
                    "power_state": "unknown",
                    "node_type": "unknown",
                    "query_time": datetime.now().isoformat()
                }
                self.logger.debug(f"找到节点: {line}")
                
            elif current_node and '=' in line:
                # 解析节点属性 - 属性行以空格开头
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key == "state":
                        current_node["state"] = self._normalize_pbs_state(value)
                        current_node["available"] = self._is_pbs_node_available(value)
                        self.logger.debug(f"  状态: {value} -> {current_node['state']}, 可用: {current_node['available']}")
                        
                    elif key == "np":
                        current_node["cpus"] = self._parse_cpu_count(value)
                        self.logger.debug(f"  CPU核心数: {current_node['cpus']}")
                        
                    elif key == "properties":
                        if value:
                            current_node["properties"] = [prop.strip() for prop in value.split(',')]
                        self.logger.debug(f"  属性: {current_node['properties']}")
                        
                    elif key == "power_state":
                        current_node["power_state"] = value
                        
                    elif key == "ntype":
                        current_node["node_type"] = value
                        
                    elif key == "jobs":
                        if value:
                            # 解析作业信息 例如: 0-27/50197.hn
                            current_node["jobs"] = [job.strip() for job in value.split(',') if job.strip()]
                        else:
                            current_node["jobs"] = []
                            
                    elif key == "status":
                        # 解析status字段中的内存信息
                        self._parse_pbs_status_field(current_node, value)
        
        # 添加最后一个节点
        if current_node:
            nodes.append(current_node)
        
        self.logger.info(f"解析到{len(nodes)}个PBS节点")
        return nodes
    
    def _parse_pbs_status_field(self, node_info: Dict, status_str: str):
        """解析PBS status字段"""
        try:
            # status字段包含很多信息，用逗号分隔
            status_pairs = status_str.split(',')
            
            for pair in status_pairs:
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 解析内存信息 (totmem, availmem, physmem)
                    if key == "totmem":
                        node_info["memory"] = self._parse_memory_size(value)
                    elif key == "availmem":
                        node_info["available_memory"] = self._parse_memory_size(value)
                    elif key == "physmem":
                        node_info["physical_memory"] = self._parse_memory_size(value)
                    elif key == "ncpus":
                        # 有时status中的ncpus与np不同，优先使用np字段的值
                        ncpus = self._parse_cpu_count(value)
                        if ncpus > 0 and node_info.get("cpus", 0) == 0:
                            # 只有在cpus还未设置时才使用ncpus（np字段优先级更高）
                            node_info["cpus"] = ncpus
                    elif key == "loadave":
                        try:
                            node_info["load_average"] = float(value)
                        except:
                            pass
                    elif key == "idletime":
                        try:
                            node_info["idle_time"] = int(value)
                        except:
                            pass
                            
        except Exception as e:
            self.logger.warning(f"解析status字段失败: {e}")
    
    def _normalize_pbs_state(self, state: str) -> str:
        """标准化PBS节点状态"""
        state_map = {
            "free": "idle",
            "job-exclusive": "allocated", 
            "job-sharing": "mixed",
            "down": "down",
            "offline": "offline",
            "busy": "busy",
            "state-unknown": "unknown"
        }
        return state_map.get(state.lower(), state)
    
    def _is_pbs_node_available(self, state: str) -> bool:
        """判断PBS节点是否可用"""
        # 根据实际集群情况，free状态的节点可用
        # job-sharing状态在某些配置下也可能可用，但通常job-exclusive表示完全占用
        available_states = ["free"]
        return state.lower() in available_states
    
    def _parse_cpu_count(self, cpu_str: str) -> int:
        """解析CPU数量"""
        try:
            # 提取数字
            match = re.search(r'\d+', str(cpu_str))
            if match:
                return int(match.group())
            return 0
        except:
            return 0
    
    def _parse_memory_size(self, memory_str: str) -> int:
        """解析内存大小（转换为MB）"""
        try:
            if not memory_str:
                return 0
            
            # 提取数字和单位
            match = re.match(r'(\d+(?:\.\d+)?)\s*([KMGT]?B?)', str(memory_str).upper())
            if not match:
                return 0
            
            size = float(match.group(1))
            unit = match.group(2)
            
            # 转换为MB
            if unit.startswith('K'):
                return int(size / 1024)
            elif unit.startswith('M') or not unit:
                return int(size)
            elif unit.startswith('G'):
                return int(size * 1024)
            elif unit.startswith('T'):
                return int(size * 1024 * 1024)
            else:
                return int(size)
        except:
            return 0
    
    def get_node_summary(self, nodes: List[Dict]) -> Dict:
        """
        获取节点摘要信息
        
        Args:
            nodes: 节点信息列表
            
        Returns:
            Dict: 摘要信息
        """
        if not nodes:
            return {
                "total_nodes": 0,
                "available_nodes": 0,
                "total_cores": 0,
                "available_cores": 0,
                "total_memory": 0,
                "available_memory": 0,
                "states": {},
                "partitions": {}
            }
        
        summary = {
            "total_nodes": len(nodes),
            "available_nodes": sum(1 for node in nodes if node.get("available", False)),
            "total_cores": sum(node.get("cpus", 0) for node in nodes),
            "available_cores": sum(node.get("cpus", 0) for node in nodes if node.get("available", False)),
            "total_memory": sum(node.get("memory", 0) for node in nodes),
            "available_memory": sum(node.get("memory", 0) for node in nodes if node.get("available", False)),
            "states": {},
            "partitions": {},
            "scheduler": nodes[0].get("scheduler", "unknown") if nodes else "unknown"
        }
        
        # 统计状态分布
        for node in nodes:
            state = node.get("state", "unknown")
            summary["states"][state] = summary["states"].get(state, 0) + 1
            
            partition = node.get("partition", "default")
            if partition:
                if partition not in summary["partitions"]:
                    summary["partitions"][partition] = {
                        "nodes": 0,
                        "cores": 0,
                        "memory": 0
                    }
                summary["partitions"][partition]["nodes"] += 1
                summary["partitions"][partition]["cores"] += node.get("cpus", 0)
                summary["partitions"][partition]["memory"] += node.get("memory", 0)
        
        return summary
    
    def filter_available_nodes(self, nodes: List[Dict], 
                             min_cores: int = 1, 
                             min_memory: int = 0,
                             partition: Optional[str] = None) -> List[Dict]:
        """
        过滤可用节点
        
        Args:
            nodes: 节点信息列表
            min_cores: 最小CPU核心数
            min_memory: 最小内存（MB）
            partition: 指定分区
            
        Returns:
            List[Dict]: 过滤后的可用节点列表
        """
        filtered_nodes = []
        
        for node in nodes:
            # 检查可用性
            if not node.get("available", False):
                continue
            
            # 检查CPU
            if node.get("cpus", 0) < min_cores:
                continue
            
            # 检查内存
            if node.get("memory", 0) < min_memory:
                continue
            
            # 检查分区
            if partition and node.get("partition", "") != partition:
                continue
            
            filtered_nodes.append(node)
        
        self.logger.debug(f"过滤得到{len(filtered_nodes)}个可用节点")
        return filtered_nodes
    
    def get_queue_status(self, ssh_client, scheduler_type: Optional[str] = None) -> Dict:
        """
        获取队列状态信息
        
        Args:
            ssh_client: SSH客户端连接
            scheduler_type: 调度器类型
            
        Returns:
            Dict: 队列状态信息
        """
        if not scheduler_type:
            scheduler_type = self.detect_scheduler_type(ssh_client)
        
        if scheduler_type == "SLURM":
            return self._get_slurm_queue_status(ssh_client)
        elif scheduler_type == "PBS":
            return self._get_pbs_queue_status(ssh_client)
        else:
            return {"error": f"不支持的调度器类型: {scheduler_type}"}
    
    def _get_slurm_queue_status(self, ssh_client) -> Dict:
        """获取SLURM队列状态"""
        try:
            cmd = "squeue -h -o '%i %j %u %t %r'"
            stdin, stdout, stderr = ssh_client.exec_command(cmd)
            
            if stdout.channel.recv_exit_status() != 0:
                return {"error": "SLURM队列查询失败"}
            
            output = stdout.read().decode()
            jobs = []
            
            for line in output.strip().split('\n'):
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 4:
                        jobs.append({
                            "job_id": parts[0],
                            "name": parts[1],
                            "user": parts[2],
                            "state": parts[3],
                            "reason": ' '.join(parts[4:]) if len(parts) > 4 else ""
                        })
            
            return {
                "scheduler": "SLURM",
                "total_jobs": len(jobs),
                "jobs": jobs,
                "query_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"SLURM队列状态查询失败: {e}")
            return {"error": str(e)}
    
    def _get_pbs_queue_status(self, ssh_client) -> Dict:
        """获取PBS队列状态"""
        try:
            cmd = "qstat -f"
            stdin, stdout, stderr = ssh_client.exec_command(cmd)
            
            if stdout.channel.recv_exit_status() != 0:
                return {"error": "PBS队列查询失败"}
            
            output = stdout.read().decode()
            # PBS输出解析较复杂，这里提供基本实现
            jobs = []
            
            # 简化的解析逻辑
            job_blocks = output.split('Job Id:')
            for block in job_blocks[1:]:  # 跳过第一个空块
                lines = block.strip().split('\n')
                if lines:
                    job_id = lines[0].strip()
                    jobs.append({
                        "job_id": job_id,
                        "name": "",
                        "user": "",
                        "state": "",
                        "reason": ""
                    })
            
            return {
                "scheduler": "PBS",
                "total_jobs": len(jobs),
                "jobs": jobs,
                "query_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"PBS队列状态查询失败: {e}")
            return {"error": str(e)}
