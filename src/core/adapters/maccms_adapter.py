"""
MacCMS API适配器

实现Type 0/1标准MacCMS API协议,支持:
- JSON格式 (type=0)
- XML格式 (type=1)
"""

import logging
from typing import List, Dict, Optional, Any
from ..vod_source import (
    VodSourceAdapter, 
    VodItem, 
    VodDetail, 
    Category,
    VodListResponse,
    VodDetailResponse,
    SourceType
)
from ..http_client import HTTPClient

logger = logging.getLogger(__name__)


class MacCMSSource(VodSourceAdapter):
    """
    MacCMS API数据源适配器
    
    支持标准的MacCMS API协议,包括:
    - /api.php/provide/vod/ 接口
    - ac=detail (获取详情)
    - ac=list (获取列表)
    - wd=keyword (搜索)
    """
    
    def __init__(self, source_config: Dict[str, Any]):
        super().__init__(source_config)
        self.api_base = self.api_url.rstrip('/')
        
        # 验证API地址
        if not self.api_base:
            raise ValueError("MacCMS API地址不能为空")
        
        # 初始化HTTP客户端
        self.http_client = HTTPClient(
            timeout=self.timeout,
            max_retries=3,
            retry_delay=1.0,
            enable_circuit_breaker=True
        )
    
    async def _request(self, params: Dict[str, Any]) -> Dict:
        """
        发送HTTP请求到MacCMS API
        
        Args:
            params: URL参数字典
        
        Returns:
            解析后的JSON响应
        
        Raises:
            Exception: 网络错误或响应格式错误
        """
        url = self.api_base  # api_base已经包含完整路径
        
        try:
            data = await self.http_client.get_json(url, params=params)
            return data
        except Exception as e:
            logger.error(f"MacCMS API请求失败 [{self.name}]: {e}")
            raise
    
    async def get_categories(self) -> List[Category]:
        """获取分类列表"""
        if self.is_cache_valid():
            return self._categories_cache
        
        try:
            # 调用ac=list获取分类
            params = {'ac': 'list', 'pg': 1}
            data = await self._request(params)
            
            categories = []
            class_list = data.get('class', [])
            
            for item in class_list:
                try:
                    cat = Category(
                        type_id=int(item.get('type_id', 0)),
                        type_name=item.get('type_name', ''),
                        type_flag=int(item.get('type_flag', 0))
                    )
                    categories.append(cat)
                except (ValueError, TypeError) as e:
                    logger.warning(f"分类数据解析失败: {item}, 错误: {e}")
                    continue
            
            self._categories_cache = categories
            return categories
            
        except Exception as e:
            logger.error(f"获取分类失败 [{self.name}]: {e}")
            raise
    
    async def get_vod_list(
        self, 
        type_id: int, 
        page: int = 1,
        filters: Optional[Dict[str, str]] = None
    ) -> VodListResponse:
        """获取影片列表"""
        try:
            params = {
                'ac': 'list',
                't': type_id,
                'pg': page
            }
            
            # 添加筛选条件 (如果API支持)
            if filters:
                params.update(filters)
            
            data = await self._request(params)
            
            # 检查响应状态
            if data.get('code') != 1:
                return VodListResponse(
                    code=data.get('code', 0),
                    msg=data.get('msg', 'error'),
                    page=page,
                    list=[]
                )
            
            # 解析影片列表
            vod_items = []
            vod_list = data.get('list', [])
            
            for item in vod_list:
                try:
                    # 标准化ID格式: source_id$vod_id
                    raw_id = str(item.get('vod_id', ''))
                    vod_id = f"{self.name}${raw_id}"
                    
                    vod_item = VodItem(
                        vod_id=vod_id,
                        vod_name=item.get('vod_name', ''),
                        vod_pic=item.get('vod_pic', ''),
                        vod_remarks=item.get('vod_remarks', ''),
                        vod_year=str(item.get('vod_year', '')),
                        vod_area=item.get('vod_area', ''),
                        vod_type=item.get('type_name', '')
                    )
                    vod_items.append(vod_item)
                except Exception as e:
                    logger.warning(f"影片数据解析失败: {item}, 错误: {e}")
                    continue
            
            return VodListResponse(
                code=1,
                msg="success",
                page=int(data.get('page', page)),
                pagecount=int(data.get('pagecount', 1)),
                limit=int(data.get('limit', 20)),
                total=int(data.get('total', len(vod_items))),
                list=vod_items,
                class_=data.get('class', [])
            )
            
        except Exception as e:
            logger.error(f"获取影片列表失败 [{self.name}]: {e}")
            raise
    
    async def get_vod_detail(self, vod_id: str) -> VodDetailResponse:
        """获取影片详情"""
        try:
            # 提取真实的vod_id (去除源前缀)
            if '$' in vod_id:
                real_id = vod_id.split('$', 1)[1]
            else:
                real_id = vod_id
            
            params = {
                'ac': 'detail',
                'ids': real_id
            }
            
            data = await self._request(params)
            
            # 检查响应
            if data.get('code') != 1 or not data.get('list'):
                return VodDetailResponse(
                    code=data.get('code', 0),
                    msg=data.get('msg', 'not found'),
                    list=[]
                )
            
            # 解析第一个影片详情
            item = data['list'][0]
            
            # 解析播放线路和集数
            play_from = []
            play_url = []
            
            vod_play_from = item.get('vod_play_from', '')
            vod_play_url = item.get('vod_play_url', '')
            
            if vod_play_from and vod_play_url:
                # 线路之间用$$$分隔
                from_list = vod_play_from.split('$$$')
                url_list = vod_play_url.split('$$$')
                
                for i, from_name in enumerate(from_list):
                    if i < len(url_list):
                        play_from.append(from_name.strip())
                        # 集数之间用#分隔
                        episodes = [ep.strip() for ep in url_list[i].split('#') if ep.strip()]
                        play_url.append(episodes)
            
            vod_detail = VodDetail(
                vod_id=f"{self.name}${item.get('vod_id', '')}",
                vod_name=item.get('vod_name', ''),
                vod_pic=item.get('vod_pic', ''),
                vod_content=item.get('vod_content', ''),
                vod_year=str(item.get('vod_year', '')),
                vod_area=item.get('vod_area', ''),
                vod_director=item.get('vod_director', ''),
                vod_actor=item.get('vod_actor', ''),
                vod_play_from=play_from,
                vod_play_url=play_url
            )
            
            return VodDetailResponse(
                code=1,
                msg="success",
                list=[vod_detail]
            )
            
        except Exception as e:
            logger.error(f"获取影片详情失败 [{self.name}]: {e}")
            raise
    
    async def search_vod(self, keyword: str, page: int = 1) -> VodListResponse:
        """搜索影片"""
        try:
            params = {
                'ac': 'list',
                'wd': keyword,
                'pg': page
            }
            
            data = await self._request(params)
            
            if data.get('code') != 1:
                return VodListResponse(
                    code=data.get('code', 0),
                    msg=data.get('msg', 'search error'),
                    page=page,
                    list=[]
                )
            
            # 解析搜索结果 (与get_vod_list类似)
            vod_items = []
            vod_list = data.get('list', [])
            
            for item in vod_list:
                try:
                    raw_id = str(item.get('vod_id', ''))
                    vod_id = f"{self.name}${raw_id}"
                    
                    vod_item = VodItem(
                        vod_id=vod_id,
                        vod_name=item.get('vod_name', ''),
                        vod_pic=item.get('vod_pic', ''),
                        vod_remarks=item.get('vod_remarks', ''),
                        vod_year=str(item.get('vod_year', '')),
                        vod_area=item.get('vod_area', ''),
                        vod_type=item.get('type_name', '')
                    )
                    vod_items.append(vod_item)
                except Exception as e:
                    logger.warning(f"搜索结果解析失败: {item}, 错误: {e}")
                    continue
            
            return VodListResponse(
                code=1,
                msg="success",
                page=int(data.get('page', page)),
                pagecount=int(data.get('pagecount', 1)),
                limit=int(data.get('limit', 20)),
                total=int(data.get('total', len(vod_items))),
                list=vod_items
            )
            
        except Exception as e:
            logger.error(f"搜索影片失败 [{self.name}]: {e}")
            raise
    
    async def cleanup(self):
        """清理资源"""
        await self.http_client.close()
