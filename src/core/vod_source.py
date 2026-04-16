"""
TVSource Studio - 统一视频源适配器接口

定义所有数据源适配器必须实现的标准接口,支持:
- MacCMS API (Type 0/1)
- XBPQ规则引擎 (Type 2/4)
- DRPY2 JS爬虫 (Type 3)
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class SourceType(Enum):
    """数据源类型枚举"""
    MACCMS_API = 0        # MacCMS标准API
    MACCMS_XML = 1        # MacCMS XML格式
    XBPQ_RULE = 2         # XBPQ规则引擎
    DRPY2_JS = 3          # DRPY2 JavaScript爬虫
    XYQHIKER_RULE = 4     # XYQHiker规则引擎


@dataclass
class VodItem:
    """影片条目(列表页使用)"""
    vod_id: str                    # 影片ID (格式: source_id$vod_id)
    vod_name: str                  # 影片名称
    vod_pic: str                   # 封面图片URL
    vod_remarks: str = ""          # 备注信息(如: HD、更新至XX集)
    vod_year: str = ""             # 年份
    vod_area: str = ""             # 地区
    vod_type: str = ""             # 类型


@dataclass
class VodDetail:
    """影片详情(详情页使用)"""
    vod_id: str                    # 影片ID
    vod_name: str                  # 影片名称
    vod_pic: str                   # 封面图片URL
    vod_content: str = ""          # 剧情简介
    vod_year: str = ""             # 年份
    vod_area: str = ""             # 地区
    vod_director: str = ""         # 导演
    vod_actor: str = ""            # 主演
    vod_play_from: List[str] = field(default_factory=list)     # 播放线路名称列表
    vod_play_url: List[List[str]] = field(default_factory=list)  # 播放地址列表 [[ep1, ep2], [ep1, ep2]]


@dataclass
class Category:
    """分类信息"""
    type_id: int                   # 分类ID
    type_name: str                 # 分类名称
    type_flag: int = 0             # 分类标识


@dataclass
class VodListResponse:
    """影片列表响应"""
    code: int = 1                  # 状态码 (1=成功)
    msg: str = "success"           # 消息
    page: int = 1                  # 当前页码
    pagecount: int = 1             # 总页数
    limit: int = 20                # 每页数量
    total: int = 0                 # 总记录数
    list: List[VodItem] = field(default_factory=list)  # 影片列表
    class_: List[Category] = field(default_factory=list, metadata={"name": "class"})  # 分类列表


@dataclass
class VodDetailResponse:
    """影片详情响应"""
    code: int = 1
    msg: str = "success"
    page: int = 1
    pagecount: int = 1
    limit: int = 1
    total: int = 1
    list: List[VodDetail] = field(default_factory=list)


class VodSourceAdapter(ABC):
    """
    视频源适配器抽象基类
    
    所有数据源适配器必须实现此接口,确保统一的调用方式。
    支持懒加载和缓存机制。
    """
    
    def __init__(self, source_config: Dict[str, Any]):
        """
        初始化适配器
        
        Args:
            source_config: 数据源配置字典,包含:
                - name: 数据源名称
                - type: 数据源类型 (SourceType枚举值)
                - api: API地址或JS文件路径
                - ext: 扩展配置(XBPQ规则JSON等)
                - timeout: 请求超时时间(秒)
        """
        self.source_config = source_config
        self.name = source_config.get('name', 'Unknown')
        self.source_type = SourceType(source_config.get('type', 0))
        self.api_url = source_config.get('api', '')
        self.ext_config = source_config.get('ext', {})
        self.timeout = source_config.get('timeout', 10)
        
        # 缓存机制
        self._categories_cache: Optional[List[Category]] = None
        self._cache_ttl = 3600  # 缓存有效期(秒)
    
    @abstractmethod
    async def get_categories(self) -> List[Category]:
        """
        获取分类列表
        
        Returns:
            分类列表,用于首页导航栏显示
        
        Raises:
            Exception: 获取失败时抛出异常
        """
        pass
    
    @abstractmethod
    async def get_vod_list(
        self, 
        type_id: int, 
        page: int = 1,
        filters: Optional[Dict[str, str]] = None
    ) -> VodListResponse:
        """
        获取影片列表
        
        Args:
            type_id: 分类ID
            page: 页码 (从1开始)
            filters: 筛选条件 (如: {"year": "2024", "area": "大陆"})
        
        Returns:
            标准化的影片列表响应
        
        Raises:
            Exception: 获取失败时抛出异常
        """
        pass
    
    @abstractmethod
    async def get_vod_detail(self, vod_id: str) -> VodDetailResponse:
        """
        获取影片详情
        
        Args:
            vod_id: 影片ID (可能包含源前缀,如: "source1$12345")
        
        Returns:
            标准化的影片详情响应
        
        Raises:
            Exception: 获取失败时抛出异常
        """
        pass
    
    @abstractmethod
    async def search_vod(self, keyword: str, page: int = 1) -> VodListResponse:
        """
        搜索影片
        
        Args:
            keyword: 搜索关键词
            page: 页码
        
        Returns:
            搜索结果列表
        
        Raises:
            Exception: 搜索失败时抛出异常
        """
        pass
    
    def clear_cache(self):
        """清除缓存"""
        self._categories_cache = None
    
    def is_cache_valid(self) -> bool:
        """检查缓存是否有效"""
        return self._categories_cache is not None
    
    def __repr__(self):
        return f"<{self.__class__.__name__} name={self.name} type={self.source_type.name}>"
