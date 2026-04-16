"""
数据源配置管理器

负责:
- 加载和管理TVBox数据源配置
- 自动创建对应的适配器实例
- 支持热更新和缓存
- 提供统一的访问接口
"""

import json
import logging
import os
from typing import List, Dict, Optional, Any
from pathlib import Path
from ..core.vod_source import VodSourceAdapter, SourceType
from ..core.adapters.maccms_adapter import MacCMSSource
from ..core.adapters.xbpq_adapter import XBPQSource
from ..core.adapters.drpy2_adapter import DRPY2Source

logger = logging.getLogger(__name__)


class SourceConfig:
    """单个数据源配置"""
    
    def __init__(self, config_dict: Dict[str, Any]):
        self.name = config_dict.get('name', '')
        self.type = config_dict.get('type', 0)
        self.api = config_dict.get('api', '')
        self.ext = config_dict.get('ext', {})
        self.timeout = config_dict.get('timeout', 10)
        self.enabled = config_dict.get('enabled', True)
        
        # 验证配置
        self._validate()
    
    def _validate(self):
        """验证配置有效性"""
        if not self.name:
            raise ValueError("数据源配置缺少name字段")
        
        if self.type not in [0, 1, 2, 3, 4]:
            raise ValueError(f"不支持的数据源类型: {self.type}")
        
        if not self.api and self.type != 2:
            raise ValueError(f"数据源 [{self.name}] 缺少api字段")
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'name': self.name,
            'type': self.type,
            'api': self.api,
            'ext': self.ext,
            'timeout': self.timeout,
            'enabled': self.enabled
        }


class SourceManager:
    """
    数据源管理器
    
    统一管理所有数据源的配置和适配器实例,
    支持动态加载、缓存和健康检查。
    """
    
    def __init__(self, config_path: str = "data/sources/source_config.json"):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.sources: Dict[str, SourceConfig] = {}
        self.adapters: Dict[str, VodSourceAdapter] = {}
        
        # 加载配置
        self.load_config()
    
    def load_config(self):
        """从JSON文件加载配置"""
        if not os.path.exists(self.config_path):
            logger.warning(f"配置文件不存在: {self.config_path}, 使用默认配置")
            self._create_default_config()
            return
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            sources_list = config_data.get('sources', [])
            
            for source_dict in sources_list:
                try:
                    source_config = SourceConfig(source_dict)
                    if source_config.enabled:
                        self.sources[source_config.name] = source_config
                        logger.info(f"加载数据源: {source_config.name} (Type {source_config.type})")
                except Exception as e:
                    logger.error(f"加载数据源配置失败: {source_dict}, 错误: {e}")
                    continue
            
            logger.info(f"成功加载 {len(self.sources)} 个数据源")
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            raise
    
    def _create_default_config(self):
        """创建默认配置文件"""
        default_config = {
            "version": "1.0",
            "description": "TVSource Studio 数据源配置",
            "sources": [
                {
                    "name": "测试MacCMS源",
                    "type": 0,
                    "api": "https://example.com/api.php/provide/vod/",
                    "timeout": 10,
                    "enabled": False
                }
            ]
        }
        
        # 创建目录
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        
        logger.info(f"已创建默认配置文件: {self.config_path}")
    
    def get_adapter(self, source_name: str) -> VodSourceAdapter:
        """
        获取数据源适配器实例 (带缓存)
        
        Args:
            source_name: 数据源名称
        
        Returns:
            适配器实例
        
        Raises:
            KeyError: 数据源不存在
            ValueError: 创建适配器失败
        """
        # 检查缓存
        if source_name in self.adapters:
            return self.adapters[source_name]
        
        # 获取配置
        if source_name not in self.sources:
            raise KeyError(f"数据源不存在: {source_name}")
        
        source_config = self.sources[source_name]
        
        # 创建适配器
        adapter = self._create_adapter(source_config)
        
        # 缓存
        self.adapters[source_name] = adapter
        
        return adapter
    
    def _create_adapter(self, source_config: SourceConfig) -> VodSourceAdapter:
        """
        根据配置创建适配器实例
        
        Args:
            source_config: 数据源配置
        
        Returns:
            适配器实例
        """
        config_dict = source_config.to_dict()
        
        try:
            if source_config.type in [0, 1]:
                # MacCMS API
                adapter = MacCMSSource(config_dict)
                
            elif source_config.type in [2, 4]:
                # XBPQ/XYQHiker规则引擎
                adapter = XBPQSource(config_dict)
                
            elif source_config.type == 3:
                # DRPY2 JS爬虫
                adapter = DRPY2Source(config_dict)
                
            else:
                raise ValueError(f"不支持的数据源类型: {source_config.type}")
            
            logger.info(f"创建适配器成功: {source_config.name} ({adapter.__class__.__name__})")
            return adapter
            
        except Exception as e:
            logger.error(f"创建适配器失败 [{source_config.name}]: {e}")
            raise
    
    def get_all_adapters(self) -> Dict[str, VodSourceAdapter]:
        """获取所有适配器实例"""
        for name in self.sources.keys():
            if name not in self.adapters:
                try:
                    self.get_adapter(name)
                except Exception as e:
                    logger.error(f"加载适配器失败 [{name}]: {e}")
        
        return self.adapters
    
    def add_source(self, source_config: Dict[str, Any]):
        """
        动态添加数据源
        
        Args:
            source_config: 数据源配置字典
        """
        try:
            config = SourceConfig(source_config)
            self.sources[config.name] = config
            
            # 清除适配器缓存
            if config.name in self.adapters:
                del self.adapters[config.name]
            
            # 保存到文件
            self.save_config()
            
            logger.info(f"添加数据源成功: {config.name}")
            
        except Exception as e:
            logger.error(f"添加数据源失败: {e}")
            raise
    
    def remove_source(self, source_name: str):
        """
        移除数据源
        
        Args:
            source_name: 数据源名称
        """
        if source_name in self.sources:
            del self.sources[source_name]
        
        if source_name in self.adapters:
            del self.adapters[source_name]
        
        self.save_config()
        logger.info(f"移除数据源: {source_name}")
    
    def save_config(self):
        """保存配置到文件"""
        config_data = {
            "version": "1.0",
            "sources": [config.to_dict() for config in self.sources.values()]
        }
        
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        
        logger.info("配置已保存")
    
    def clear_cache(self, source_name: Optional[str] = None):
        """
        清除适配器缓存
        
        Args:
            source_name: 指定数据源名称,None则清除所有
        """
        if source_name:
            if source_name in self.adapters:
                del self.adapters[source_name]
                logger.info(f"清除缓存: {source_name}")
        else:
            self.adapters.clear()
            logger.info("清除所有适配器缓存")
    
    async def health_check(self, source_name: str) -> bool:
        """
        健康检查
        
        Args:
            source_name: 数据源名称
        
        Returns:
            True=健康, False=异常
        """
        try:
            adapter = self.get_adapter(source_name)
            categories = await adapter.get_categories()
            return len(categories) > 0
        except Exception as e:
            logger.error(f"健康检查失败 [{source_name}]: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        stats = {
            "total_sources": len(self.sources),
            "active_adapters": len(self.adapters),
            "sources_by_type": {}
        }
        
        for source in self.sources.values():
            type_name = SourceType(source.type).name
            if type_name not in stats["sources_by_type"]:
                stats["sources_by_type"][type_name] = 0
            stats["sources_by_type"][type_name] += 1
        
        return stats
