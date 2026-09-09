"""
系统配置管理模块
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

# 配置文件路径
CONFIG_FILE = Path(__file__).parent.parent / "config" / "system_config.json"

# 默认配置
DEFAULT_CONFIG = {
    "streaming_threshold": 1000,  # 流式处理触发阈值（范围: 100-1,000,000）
    "batch_size": 500,            # 每批处理帧数（范围: 50-50,000）
    "batch_size_for_save": 1000,  # 批量保存的批次大小（范围: 100-50,000）
    "detection_frequency": {      # 检测频率控制配置
        "enabled": True,
        "mode": "adaptive",
        "high_frequency": {
            "interval_seconds": 1,
            "frames_per_interval": 1
        },
        "medium_frequency": {
            "interval_seconds": 30,
            "frames_per_interval": 1
        },
        "low_frequency": {
            "interval_seconds": 60,
            "frames_per_interval": 1
        },
        "adaptive": {
            "small_dataset_threshold": 1000,
            "medium_dataset_threshold": 5000,
            "large_dataset_threshold": 10000,
            "small_dataset_interval": 1,
            "medium_dataset_interval": 30,
            "large_dataset_interval": 60
        }
    }
}

class SystemConfig:
    """系统配置管理器"""
    
    def __init__(self):
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并默认配置，确保所有键都存在
                    merged_config = DEFAULT_CONFIG.copy()
                    merged_config.update(config)
                    return merged_config
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                return DEFAULT_CONFIG.copy()
        else:
            # 配置文件不存在，创建默认配置
            self._save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """保存配置文件"""
        try:
            # 确保配置目录存在
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        self._config[key] = value
        self._save_config(self._config)
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()
    
    def update(self, config_dict: Dict[str, Any]) -> None:
        """批量更新配置"""
        self._config.update(config_dict)
        self._save_config(self._config)
    
    def reset_to_default(self) -> None:
        """重置为默认配置"""
        self._config = DEFAULT_CONFIG.copy()
        self._save_config(self._config)

# 全局配置实例
system_config = SystemConfig()

# 便捷函数
def get_config(key: str, default: Any = None) -> Any:
    """获取配置值"""
    return system_config.get(key, default)

def set_config(key: str, value: Any) -> None:
    """设置配置值"""
    system_config.set(key, value)

def get_all_config() -> Dict[str, Any]:
    """获取所有配置"""
    return system_config.get_all()

def update_config(config_dict: Dict[str, Any]) -> None:
    """批量更新配置"""
    system_config.update(config_dict)
