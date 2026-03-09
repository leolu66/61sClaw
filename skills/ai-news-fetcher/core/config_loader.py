#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ConfigLoader - 配置加载器
支持YAML配置文件读取和热更新
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime


class ConfigLoader:
    """配置加载器 - 支持热更新"""
    
    def __init__(self, config_dir: str = "site-configs"):
        self.config_dir = Path(config_dir)
        self.configs: Dict[str, Dict] = {}
        self.last_modified: Dict[str, float] = {}
        
    def load_all(self) -> Dict[str, Dict]:
        """加载所有站点配置"""
        if not self.config_dir.exists():
            print(f"[警告] 配置目录不存在: {self.config_dir}")
            return {}
        
        for yaml_file in self.config_dir.glob("*.yaml"):
            if yaml_file.name.startswith("_"):
                continue
            self._load_single(yaml_file)
        
        return self.configs
    
    def _load_single(self, yaml_file: Path) -> Optional[Dict]:
        """加载单个配置文件"""
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            site_name = yaml_file.stem
            self.configs[site_name] = config
            self.last_modified[yaml_file] = yaml_file.stat().st_mtime
            
            print(f"[配置] 已加载: {site_name}")
            return config
            
        except Exception as e:
            print(f"[错误] 加载配置失败 {yaml_file}: {e}")
            return None
    
    def get(self, site_name: str) -> Optional[Dict]:
        """获取指定站点配置"""
        return self.configs.get(site_name)
    
    def reload_if_changed(self) -> list:
        """检查并热更新变更的配置"""
        updated = []
        
        for yaml_file in self.config_dir.glob("*.yaml"):
            if yaml_file.name.startswith("_"):
                continue
                
            current_mtime = yaml_file.stat().st_mtime
            last_mtime = self.last_modified.get(yaml_file, 0)
            
            if current_mtime > last_mtime:
                config = self._load_single(yaml_file)
                if config:
                    updated.append(yaml_file.stem)
                    print(f"[热更新] 配置已更新: {yaml_file.stem}")
        
        return updated
    
    def list_sites(self) -> list:
        """列出所有已加载的站点"""
        return list(self.configs.keys())
    
    def get_enabled_sites(self) -> Dict[str, Dict]:
        """获取所有启用的站点配置"""
        return {
            name: config for name, config in self.configs.items()
            if config.get('site', {}).get('enabled', True)
        }


if __name__ == "__main__":
    # 测试配置加载
    loader = ConfigLoader("../site-configs")
    configs = loader.load_all()
    
    print(f"\n已加载 {len(configs)} 个站点配置:")
    for name in loader.list_sites():
        config = loader.get(name)
        site_info = config.get('site', {})
        print(f"  - {site_info.get('name', name)} ({name})")
        print(f"    URL: {site_info.get('base_url', 'N/A')}")
        print(f"    方法: {config.get('fetch', {}).get('method', 'requests')}")
        print()
