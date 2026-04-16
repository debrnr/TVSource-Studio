"""
TVSource Studio Core Module

核心模块包含:
- vod_source: 统一适配器接口
- adapters: 各种数据源适配器实现
- source_manager: 配置管理器
- http_client: HTTP客户端(重试+熔断)
- batch_processor: 批量请求处理器
"""

from .vod_source import (
    VodSourceAdapter,
    VodItem,
    VodDetail,
    Category,
    VodListResponse,
    VodDetailResponse,
    SourceType
)

from .source_manager import SourceManager, SourceConfig
from .http_client import HTTPClient, CircuitBreaker
from .batch_processor import BatchProcessor, MultiSourceAggregator

__all__ = [
    'VodSourceAdapter',
    'VodItem',
    'VodDetail',
    'Category',
    'VodListResponse',
    'VodDetailResponse',
    'SourceType',
    'SourceManager',
    'SourceConfig',
    'HTTPClient',
    'CircuitBreaker',
    'BatchProcessor',
    'MultiSourceAggregator'
]
