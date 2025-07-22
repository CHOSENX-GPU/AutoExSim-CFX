"""
作业监控模块
监控作业执行状态，自动下载结果
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum

from .config import CFXAutomationConfig


class JobState(Enum):
    """作业状态枚举"""
    PENDING = "pending"      # 排队中
    RUNNING = "running"      # 运行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败
    CANCELLED = "cancelled"  # 已取消
    TIMEOUT = "timeout"      # 超时
    UNKNOWN = "unknown"      # 未知状态


class JobMonitorError(Exception):
    """作业监控错误"""
    pass


class JobMonitor:
    """作业监控器"""
    
    def __init__(self, config: CFXAutomationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 监控状态
        self.monitoring = False
        self.monitored_jobs = {}
        self.monitoring_history = []
        
        # 统计信息
        self.stats = {
            "total_jobs": 0,
            "completed_jobs": 0,
            "failed_jobs": 0,
            "running_jobs": 0,
            "pending_jobs": 0,
            "monitoring_start_time": None,
            "last_update_time": None
        }
    
    def start_monitoring(self, ssh_client, jobs: List[Dict]) -> None:
        """
        开始监控作业
        
        Args:
            ssh_client: SSH客户端连接
            jobs: 要监控的作业列表
        """
        if not self.config.enable_monitoring:
            self.logger.info("作业监控已禁用")
            return
        
        self.logger.info(f"开始监控{len(jobs)}个作业...")
        
        # 初始化监控状态
        self.monitoring = True
        self.monitored_jobs = {}
        self.stats["total_jobs"] = len(jobs)
        self.stats["monitoring_start_time"] = datetime.now().isoformat()
        
        # 初始化作业状态
        for job in jobs:
            job_id = job.get("job_id") or job.get("name", "")
            self.monitored_jobs[job_id] = {
                "job_info": job,
                "state": JobState.PENDING,
                "start_time": None,
                "end_time": None,
                "runtime": 0,
                "last_check": None,
                "error_message": "",
                "result_files": [],
                "downloaded": False
            }
    
    def monitor_jobs(self, ssh_client, transfer_manager=None) -> Dict:
        """
        执行作业监控循环
        
        Args:
            ssh_client: SSH客户端连接
            transfer_manager: 文件传输管理器（用于下载结果）
            
        Returns:
            Dict: 监控报告
        """
        self.logger.info("开始作业监控循环...")
        
        try:
            while self.monitoring and self._has_active_jobs():
                # 检查所有作业状态
                self._check_all_jobs(ssh_client)
                
                # 下载已完成作业的结果
                if transfer_manager and self.config.auto_download_results:
                    self._download_completed_results(ssh_client, transfer_manager)
                
                # 更新统计信息
                self._update_statistics()
                
                # 记录监控历史
                self._record_monitoring_snapshot()
                
                # 检查是否需要继续监控
                if not self._has_active_jobs():
                    self.logger.info("所有作业已完成，结束监控")
                    break
                
                # 等待下次检查
                self.logger.debug(f"等待{self.config.monitor_interval}秒后进行下次检查...")
                time.sleep(self.config.monitor_interval)
            
            # 生成最终报告
            report = self._generate_monitoring_report()
            
            # 保存监控报告
            self._save_monitoring_report(report)
            
            return report
            
        except KeyboardInterrupt:
            self.logger.info("监控被用户中断")
            self.monitoring = False
            return self._generate_monitoring_report()
        except Exception as e:
            self.logger.error(f"作业监控失败: {e}")
            raise JobMonitorError(f"作业监控失败: {e}")
    
    def _check_all_jobs(self, ssh_client) -> None:
        """检查所有作业状态"""
        scheduler_type = self.config.scheduler_type
        
        for job_id, job_data in self.monitored_jobs.items():
            try:
                # 跳过已完成的作业
                if job_data["state"] in [JobState.COMPLETED, JobState.FAILED, JobState.CANCELLED]:
                    continue
                
                # 检查作业状态
                new_state, job_info = self._check_job_status(ssh_client, job_id, scheduler_type)
                
                # 更新作业状态
                self._update_job_state(job_id, new_state, job_info)
                
                job_data["last_check"] = datetime.now().isoformat()
                
            except Exception as e:
                self.logger.error(f"检查作业状态失败 {job_id}: {e}")
                job_data["error_message"] = str(e)
    
    def _check_job_status(self, ssh_client, job_id: str, scheduler_type: str) -> Tuple[JobState, Dict]:
        """检查单个作业状态"""
        if scheduler_type == "SLURM":
            return self._check_slurm_job(ssh_client, job_id)
        elif scheduler_type == "PBS":
            return self._check_pbs_job(ssh_client, job_id)
        else:
            raise JobMonitorError(f"不支持的调度器类型: {scheduler_type}")
    
    def _check_slurm_job(self, ssh_client, job_id: str) -> Tuple[JobState, Dict]:
        """检查SLURM作业状态"""
        try:
            # 使用sacct命令查询作业信息
            cmd = f"sacct -j {job_id} -n -o JobID,State,Start,End,ExitCode --parsable2"
            stdin, stdout, stderr = ssh_client.exec_command(cmd)
            
            if stdout.channel.recv_exit_status() != 0:
                # 作业可能已经不在队列中，尝试squeue
                cmd = f"squeue -j {job_id} -h -o '%T'"
                stdin, stdout, stderr = ssh_client.exec_command(cmd)
                
                if stdout.channel.recv_exit_status() == 0:
                    output = stdout.read().decode().strip()
                    if output:
                        state = self._parse_slurm_state(output)
                        return state, {"slurm_state": output}
                
                # 作业不在队列中，假设已完成
                return JobState.COMPLETED, {}
            
            output = stdout.read().decode().strip()
            if not output:
                return JobState.UNKNOWN, {}
            
            # 解析sacct输出
            lines = output.split('\n')
            for line in lines:
                if line.strip():
                    parts = line.split('|')
                    if len(parts) >= 3:
                        state_str = parts[1]
                        start_time = parts[2] if len(parts) > 2 else ""
                        end_time = parts[3] if len(parts) > 3 else ""
                        exit_code = parts[4] if len(parts) > 4 else ""
                        
                        state = self._parse_slurm_state(state_str)
                        
                        job_info = {
                            "slurm_state": state_str,
                            "start_time": start_time,
                            "end_time": end_time,
                            "exit_code": exit_code
                        }
                        
                        return state, job_info
            
            return JobState.UNKNOWN, {}
            
        except Exception as e:
            self.logger.debug(f"SLURM状态检查失败 {job_id}: {e}")
            return JobState.UNKNOWN, {"error": str(e)}
    
    def _check_pbs_job(self, ssh_client, job_id: str) -> Tuple[JobState, Dict]:
        """检查PBS作业状态"""
        try:
            # 使用qstat命令查询作业信息
            cmd = f"qstat -f {job_id}"
            stdin, stdout, stderr = ssh_client.exec_command(cmd)
            
            if stdout.channel.recv_exit_status() != 0:
                # 作业可能已完成，不在队列中
                return JobState.COMPLETED, {}
            
            output = stdout.read().decode()
            
            # 解析qstat输出
            job_info = {}
            current_key = None
            
            for line in output.split('\n'):
                line = line.strip()
                if '=' in line and not line.startswith('\t'):
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    job_info[key] = value
                    current_key = key
                elif line.startswith('\t') and current_key:
                    # 继续上一行的值
                    job_info[current_key] += ' ' + line.strip()
            
            # 解析作业状态
            job_state = job_info.get("job_state", "")
            state = self._parse_pbs_state(job_state)
            
            return state, job_info
            
        except Exception as e:
            self.logger.debug(f"PBS状态检查失败 {job_id}: {e}")
            return JobState.UNKNOWN, {"error": str(e)}
    
    def _parse_slurm_state(self, state_str: str) -> JobState:
        """解析SLURM作业状态"""
        state_map = {
            "PENDING": JobState.PENDING,
            "RUNNING": JobState.RUNNING,
            "COMPLETED": JobState.COMPLETED,
            "CANCELLED": JobState.CANCELLED,
            "FAILED": JobState.FAILED,
            "TIMEOUT": JobState.TIMEOUT,
            "NODE_FAIL": JobState.FAILED,
            "PREEMPTED": JobState.CANCELLED,
            "OUT_OF_MEMORY": JobState.FAILED
        }
        
        return state_map.get(state_str.upper(), JobState.UNKNOWN)
    
    def _parse_pbs_state(self, state_str: str) -> JobState:
        """解析PBS作业状态"""
        state_map = {
            "Q": JobState.PENDING,    # Queued
            "R": JobState.RUNNING,    # Running
            "C": JobState.COMPLETED,  # Completed
            "E": JobState.COMPLETED,  # Exiting
            "H": JobState.PENDING,    # Held
            "T": JobState.RUNNING,    # Transferring
            "W": JobState.PENDING,    # Waiting
            "S": JobState.PENDING     # Suspended
        }
        
        return state_map.get(state_str.upper(), JobState.UNKNOWN)
    
    def _update_job_state(self, job_id: str, new_state: JobState, job_info: Dict) -> None:
        """更新作业状态"""
        job_data = self.monitored_jobs[job_id]
        old_state = job_data["state"]
        
        if old_state != new_state:
            self.logger.info(f"作业 {job_id} 状态变更: {old_state.value} -> {new_state.value}")
            
            job_data["state"] = new_state
            
            # 记录开始时间
            if new_state == JobState.RUNNING and not job_data["start_time"]:
                job_data["start_time"] = datetime.now().isoformat()
            
            # 记录结束时间
            if new_state in [JobState.COMPLETED, JobState.FAILED, JobState.CANCELLED]:
                if not job_data["end_time"]:
                    job_data["end_time"] = datetime.now().isoformat()
                
                # 计算运行时间
                if job_data["start_time"]:
                    start_time = datetime.fromisoformat(job_data["start_time"])
                    end_time = datetime.fromisoformat(job_data["end_time"])
                    job_data["runtime"] = int((end_time - start_time).total_seconds())
        
        # 更新作业信息
        job_data.setdefault("job_status_info", {}).update(job_info)
    
    def _download_completed_results(self, ssh_client, transfer_manager) -> None:
        """下载已完成作业的结果"""
        for job_id, job_data in self.monitored_jobs.items():
            if (job_data["state"] == JobState.COMPLETED and 
                not job_data["downloaded"]):
                
                try:
                    self.logger.info(f"下载作业结果: {job_id}")
                    
                    # 准备结果目录
                    local_results_dir = os.path.join(
                        self.config.base_path, "results", job_id
                    )
                    
                    # 下载结果文件
                    result_info = {
                        "name": job_id,
                        "work_dir": self.config.remote_base_path
                    }
                    
                    downloaded_files = transfer_manager.download_results(
                        ssh_client, [result_info], local_results_dir
                    )
                    
                    job_data["result_files"] = downloaded_files.get(job_id, [])
                    job_data["downloaded"] = True
                    
                    self.logger.info(f"作业 {job_id} 结果下载完成: {len(job_data['result_files'])} 个文件")
                    
                except Exception as e:
                    self.logger.error(f"下载作业结果失败 {job_id}: {e}")
                    job_data["error_message"] = f"结果下载失败: {e}"
    
    def _has_active_jobs(self) -> bool:
        """检查是否有活跃的作业"""
        active_states = [JobState.PENDING, JobState.RUNNING]
        return any(job_data["state"] in active_states for job_data in self.monitored_jobs.values())
    
    def _update_statistics(self) -> None:
        """更新统计信息"""
        state_counts = {}
        for job_data in self.monitored_jobs.values():
            state = job_data["state"]
            state_counts[state] = state_counts.get(state, 0) + 1
        
        self.stats.update({
            "completed_jobs": state_counts.get(JobState.COMPLETED, 0),
            "failed_jobs": state_counts.get(JobState.FAILED, 0) + state_counts.get(JobState.CANCELLED, 0),
            "running_jobs": state_counts.get(JobState.RUNNING, 0),
            "pending_jobs": state_counts.get(JobState.PENDING, 0),
            "last_update_time": datetime.now().isoformat()
        })
    
    def _record_monitoring_snapshot(self) -> None:
        """记录监控快照"""
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "stats": self.stats.copy(),
            "job_states": {
                job_id: {
                    "state": job_data["state"].value,
                    "runtime": job_data["runtime"],
                    "downloaded": job_data["downloaded"]
                }
                for job_id, job_data in self.monitored_jobs.items()
            }
        }
        
        self.monitoring_history.append(snapshot)
        
        # 限制历史记录长度
        if len(self.monitoring_history) > 1000:
            self.monitoring_history = self.monitoring_history[-500:]
    
    def _generate_monitoring_report(self) -> Dict:
        """生成监控报告"""
        # 计算总运行时间
        total_runtime = sum(job_data["runtime"] for job_data in self.monitored_jobs.values())
        
        # 统计结果下载情况
        downloaded_count = sum(1 for job_data in self.monitored_jobs.values() if job_data["downloaded"])
        
        report = {
            "summary": {
                "total_jobs": self.stats["total_jobs"],
                "completed_jobs": self.stats["completed_jobs"],
                "failed_jobs": self.stats["failed_jobs"],
                "success_rate": self.stats["completed_jobs"] / max(self.stats["total_jobs"], 1),
                "total_runtime_seconds": total_runtime,
                "average_runtime_seconds": total_runtime / max(self.stats["completed_jobs"], 1),
                "downloaded_results": downloaded_count,
                "monitoring_duration": self._calculate_monitoring_duration()
            },
            "jobs": {
                job_id: {
                    "name": job_data["job_info"].get("name", job_id),
                    "state": job_data["state"].value,
                    "start_time": job_data["start_time"],
                    "end_time": job_data["end_time"],
                    "runtime_seconds": job_data["runtime"],
                    "downloaded": job_data["downloaded"],
                    "result_files_count": len(job_data["result_files"]),
                    "error_message": job_data["error_message"]
                }
                for job_id, job_data in self.monitored_jobs.items()
            },
            "monitoring_history": self.monitoring_history,
            "report_generation_time": datetime.now().isoformat()
        }
        
        return report
    
    def _calculate_monitoring_duration(self) -> int:
        """计算监控持续时间（秒）"""
        if not self.stats["monitoring_start_time"]:
            return 0
        
        start_time = datetime.fromisoformat(self.stats["monitoring_start_time"])
        current_time = datetime.now()
        
        return int((current_time - start_time).total_seconds())
    
    def _save_monitoring_report(self, report: Dict) -> None:
        """保存监控报告"""
        try:
            report_file = os.path.join(
                self.config.base_path, 
                f"monitoring_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"监控报告已保存: {report_file}")
            
        except Exception as e:
            self.logger.error(f"保存监控报告失败: {e}")
    
    def stop_monitoring(self) -> None:
        """停止监控"""
        self.monitoring = False
        self.logger.info("作业监控已停止")
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """获取指定作业状态"""
        job_data = self.monitored_jobs.get(job_id)
        if not job_data:
            return None
        
        return {
            "job_id": job_id,
            "state": job_data["state"].value,
            "start_time": job_data["start_time"],
            "end_time": job_data["end_time"],
            "runtime": job_data["runtime"],
            "downloaded": job_data["downloaded"],
            "result_files": job_data["result_files"],
            "error_message": job_data["error_message"]
        }
    
    def get_monitoring_summary(self) -> Dict:
        """获取监控摘要"""
        return {
            "monitoring": self.monitoring,
            "stats": self.stats.copy(),
            "active_jobs": self._has_active_jobs(),
            "job_count": len(self.monitored_jobs)
        }
