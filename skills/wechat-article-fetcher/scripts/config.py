#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号文章工具 - 配置模块
外部配置文件，避免修改主程序
"""

import json
import os
from typing import List, Dict

DEFAULT_CONFIG = {
    "accounts": [
        {"name": "究模智", "enabled": True},
        {"name": "新智元", "enabled": True},
        # 可以在这里添加更多公众号
        # {"name": "机器之心", "enabled": False},
        # {"name": "量子位", "enabled": False},
    ],
    "fetch": {
        "articles_per_account": 10,
        "random_order": True,  # 随机顺序获取，避免被检测
        "min_delay": 2,        # 最小延迟（秒）
        "max_delay": 5,        # 最大延迟（秒）
        "timeout": 30,         # 请求超时
    },
    "output": {
        "base_dir": r"D:\anthropic\wechat",
        "naming_pattern": "{account}_{title}.md",  # 文件名格式
        "include_images": True,
        "include_metadata": True,
    },
    "wechat": {
        # 从环境变量或外部文件读取敏感信息
        "cookie": None,  # 从环境变量 WECHAT_COOKIE 读取
        "token": None,   # 从环境变量 WECHAT_TOKEN 读取
    }
}


class Config:
    """配置管理器"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or self._default_config_path()
        self._config = self._load_config()
    
    def _default_config_path(self) -> str:
        """默认配置文件路径"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, "config.json")
    
    def _load_config(self) -> Dict:
        """加载配置"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载配置失败: {e}，使用默认配置")
        
        # 创建默认配置文件
        config = DEFAULT_CONFIG.copy()
        self._fill_from_env(config)
        self.save(config)
        return config
    
    def _fill_from_env(self, config: Dict):
        """从环境变量填充敏感信息"""
        import os
        config["wechat"]["cookie"] = os.environ.get("XTC_WECHAT_COOKIE", config["wechat"].get("cookie", ""))
        config["wechat"]["token"] = os.environ.get("XTC_WECHAT_TOKEN", config["wechat"].get("token", ""))
        
        # 如果没有配置，提示用户
        if not config["wechat"]["cookie"] or not config["wechat"]["token"]:
            print("\n⚠️ 微信公众号 Cookie 未设置！")
            print("请在公众号后台获取 Cookie 和 Token，然后设置环境变量：")
            print("  set XTC_WECHAT_COOKIE=你的Cookie")
            print("  set XTC_WECHAT_TOKEN=你的Token")
    
    def save(self, config: Dict = None):
        """保存配置到文件"""
        config = config or self._config
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def get(self, key: str, default=None):
        """获取配置项"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value):
        """设置配置项"""
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save()
    
    @property
    def enabled_accounts(self) -> List[str]:
        """获取启用的公众号列表"""
        accounts = self.get("accounts", [])
        return [a["name"] for a in accounts if a.get("enabled", True)]
    
    @property
    def cookie(self) -> str:
        """获取 Cookie"""
        return self.get("wechat.cookie", "")
    
    @property
    def token(self) -> str:
        """获取 Token"""
        return self.get("wechat.token", "")


# 全局配置实例
_config_instance = None

def get_config(config_path: str = None) -> Config:
    """获取配置实例（单例模式）"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_path)
    return _config_instance
