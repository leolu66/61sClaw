"""
配置加载器 - 支持 YAML 配置和热更新
"""
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml
import logging

logger = logging.getLogger(__name__)


class ConfigLoader:
    """配置加载器 - 负责加载和管理站点配置"""
    
    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir) if config_dir else Path(__file__).parent.parent / "site-configs"
        self._cache: Dict[str, Dict] = {}  # 配置缓存
    
    def load_all(self, enabled_only: bool = True) -> List[Dict]:
        """
        加载所有站点配置
        
        Args:
            enabled_only: 只加载启用的站点
            
        Returns:
            配置列表
        """
        configs = []
        
        if not self.config_dir.exists():
            logger.error(f"配置目录不存在: {self.config_dir}")
            return configs
        
        for config_file in sorted(self.config_dir.glob("*.yaml")):
            # 跳过模板和备份文件
            if config_file.name.startswith(("_", ".")):
                continue
            if "-v" in config_file.name:  # 跳过旧版本备份
                continue
                
            try:
                config = self.load_single(config_file.stem)
                if config:
                    # 检查是否启用
                    if enabled_only and not config.get("site", {}).get("enabled", True):
                        logger.debug(f"跳过禁用站点: {config['site']['name']}")
                        continue
                    configs.append(config)
            except Exception as e:
                logger.error(f"加载配置失败 {config_file}: {e}")
                continue
        
        logger.info(f"成功加载 {len(configs)} 个站点配置")
        return configs
    
    def load_single(self, site_name: str) -> Optional[Dict]:
        """
        加载指定站点配置
        
        Args:
            site_name: 站点名称（文件名，不含扩展名）
            
        Returns:
            配置字典或 None
        """
        # 检查缓存
        if site_name in self._cache:
            return self._cache[site_name]
        
        config_path = self.config_dir / f"{site_name}.yaml"
        if not config_path.exists():
            logger.error(f"配置文件不存在: {config_path}")
            return None
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            
            # 基础校验
            if not self._validate_config(config):
                logger.error(f"配置验证失败: {site_name}")
                return None
            
            # 记录来源文件
            config["_meta"] = {
                "file": config_path.name,
                "loaded_at": str(Path(__file__).stat().st_mtime),
            }
            
            # 存入缓存
            self._cache[site_name] = config
            logger.debug(f"加载配置成功: {site_name}")
            return config
            
        except yaml.YAMLError as e:
            logger.error(f"YAML解析错误 {site_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"加载配置异常 {site_name}: {e}")
            return None
    
    def reload(self, site_name: Optional[str] = None):
        """
        重新加载配置
        
        Args:
            site_name: 指定站点，None 则清空所有缓存
        """
        if site_name:
            self._cache.pop(site_name, None)
            logger.info(f"已刷新配置缓存: {site_name}")
        else:
            self._cache.clear()
            logger.info("已清空所有配置缓存")
    
    def _validate_config(self, config: Dict) -> bool:
        """
        基础配置校验
        
        Returns:
            是否通过验证
        """
        if not isinstance(config, dict):
            logger.error("配置必须是字典类型")
            return False
        
        # 检查必需字段
        site = config.get("site")
        if not site:
            logger.error("缺少 site 配置节")
            return False
        
        if not site.get("name"):
            logger.error("缺少 site.name")
            return False
        
        if not site.get("base_url"):
            logger.error("缺少 site.base_url")
            return False
        
        # 检查是否有列表页或API配置
        if "list_page" not in config and "api" not in config:
            logger.error("必须配置 list_page 或 api")
            return False
        
        return True
    
    def get_template(self) -> Dict[str, Any]:
        """获取配置模板"""
        template_path = self.config_dir / "_template.yaml"
        if template_path.exists():
            with open(template_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        return {}


class ConfigVersionManager:
    """配置版本管理器 - 处理配置升级和迁移"""
    
    CURRENT_SCHEMA_VERSION = "1.0"
    
    def migrate(self, config: Dict) -> Dict:
        """
        迁移旧版本配置到当前版本
        
        Args:
            config: 旧配置
            
        Returns:
            迁移后的配置
        """
        version = config.get("_schema_version", "0.9")
        
        if version == self.CURRENT_SCHEMA_VERSION:
            return config
        
        logger.info(f"迁移配置版本: {version} -> {self.CURRENT_SCHEMA_VERSION}")
        
        # 版本迁移逻辑
        if version < "1.0":
            config = self._migrate_to_1_0(config)
        
        config["_schema_version"] = self.CURRENT_SCHEMA_VERSION
        return config
    
    def _migrate_to_1_0(self, config: Dict) -> Dict:
        """迁移到 1.0 版本"""
        # 1.0 版本之前的配置结构调整
        if "list" in config and "list_page" not in config:
            config["list_page"] = config.pop("list")
        
        if "detail" in config and "detail_page" not in config:
            config["detail_page"] = config.pop("detail")
        
        return config


# 便捷函数
def load_site_config(site_name: str) -> Optional[Dict]:
    """快捷加载单个站点配置"""
    loader = ConfigLoader()
    return loader.load_single(site_name)


def load_all_configs(enabled_only: bool = True) -> List[Dict]:
    """快捷加载所有站点配置"""
    loader = ConfigLoader()
    return loader.load_all(enabled_only)
