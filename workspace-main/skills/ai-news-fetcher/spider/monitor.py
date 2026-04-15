"""
监控告警模块 - 跟踪采集状态和异常
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class SiteHealth:
    """站点健康状态"""
    site_name: str
    last_crawl_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    consecutive_failures: int = 0
    total_crawls: int = 0
    total_success: int = 0
    avg_success_rate: float = 1.0
    
    @property
    def is_healthy(self) -> bool:
        """判断站点是否健康"""
        # 连续失败超过3次认为不健康
        if self.consecutive_failures >= 3:
            return False
        # 成功率低于50%认为不健康
        if self.avg_success_rate < 0.5:
            return False
        return True
    
    def record_success(self):
        """记录成功"""
        self.last_success_time = datetime.now()
        self.last_crawl_time = datetime.now()
        self.consecutive_failures = 0
        self.total_crawls += 1
        self.total_success += 1
        self._update_success_rate()
    
    def record_failure(self):
        """记录失败"""
        self.last_crawl_time = datetime.now()
        self.consecutive_failures += 1
        self.total_crawls += 1
        self._update_success_rate()
    
    def _update_success_rate(self):
        """更新成功率"""
        if self.total_crawls > 0:
            self.avg_success_rate = self.total_success / self.total_crawls


class ExtractionMonitor:
    """
    提取监控器
    
    监控提取失败率，异常时告警
    """
    
    def __init__(self, alert_threshold: float = 0.5, min_samples: int = 5):
        """
        Args:
            alert_threshold: 告警阈值（失败率）
            min_samples: 最小样本数（低于此值不告警）
        """
        self.alert_threshold = alert_threshold
        self.min_samples = min_samples
        self.stats: Dict[str, Dict] = {}
        self.site_health: Dict[str, SiteHealth] = {}
    
    def record_extraction(self, site: str, field: str, success: bool):
        """记录提取结果"""
        key = f"{site}.{field}"
        
        if key not in self.stats:
            self.stats[key] = {"total": 0, "failed": 0}
        
        self.stats[key]["total"] += 1
        if not success:
            self.stats[key]["failed"] += 1
        
        # 检查是否需要告警
        self._check_alert(site, field)
    
    def _check_alert(self, site: str, field: str):
        """检查是否需要告警"""
        key = f"{site}.{field}"
        stat = self.stats[key]
        
        if stat["total"] < self.min_samples:
            return
        
        fail_rate = stat["failed"] / stat["total"]
        
        if fail_rate > self.alert_threshold:
            self._alert(f"[{site}] 字段 '{field}' 提取失败率异常: {fail_rate:.1%}")
    
    def _alert(self, message: str):
        """发送告警（可扩展为邮件/钉钉/企业微信等）"""
        logger.warning(f"[ALERT] {message}")
        # TODO: 接入实际告警通道
    
    def get_site_health(self, site_name: str) -> SiteHealth:
        """获取站点健康状态"""
        if site_name not in self.site_health:
            self.site_health[site_name] = SiteHealth(site_name=site_name)
        return self.site_health[site_name]
    
    def save_state(self, filepath: str = "logs/monitor_state.json"):
        """保存监控状态到文件"""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "stats": self.stats,
            "site_health": {
                name: {
                    **asdict(health),
                    "last_crawl_time": health.last_crawl_time.isoformat() if health.last_crawl_time else None,
                    "last_success_time": health.last_success_time.isoformat() if health.last_success_time else None,
                }
                for name, health in self.site_health.items()
            },
            "updated_at": datetime.now().isoformat(),
        }
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_state(self, filepath: str = "logs/monitor_state.json"):
        """从文件加载监控状态"""
        path = Path(filepath)
        if not path.exists():
            return
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self.stats = data.get("stats", {})
            # TODO: 恢复 site_health 状态
            
        except Exception as e:
            logger.error(f"加载监控状态失败: {e}")


# 全局监控器实例
_default_monitor: Optional[ExtractionMonitor] = None


def get_monitor() -> ExtractionMonitor:
    """获取全局监控器实例"""
    global _default_monitor
    if _default_monitor is None:
        _default_monitor = ExtractionMonitor()
    return _default_monitor
