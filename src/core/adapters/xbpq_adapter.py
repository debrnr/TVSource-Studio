"""
XBPQ规则解析器

实现Type 2/4 XBPQ/XYQHiker规则引擎,支持:
- && 正则截取
- j: JSONPath路径
- p: CSS选择器 (Jsoup)
- 高级过滤和工具函数
"""

import re
import json
import logging
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
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
from bs4 import BeautifulSoup
import jsonpath_ng
from jsonpath_ng.ext import parse as jsonpath_parse

logger = logging.getLogger(__name__)


@dataclass
class XBPQRule:
    """XBPQ规则配置"""
    # 基础配置
    title: str = ""                    # 规则名称
    host: str = ""                     # 站点域名
    url: str = ""                      # 分类URL模板
    search_url: str = ""               # 搜索URL模板
    detail_url: str = ""               # 详情URL模板
    
    # 首页推荐
    home_url: str = ""                 # 首页URL
    recommend: str = ""                # 推荐区域选择器
    
    # 分类配置
    class_name: str = ""               # 分类名称 (用&分隔)
    class_url: str = ""                # 分类ID (用&分隔)
    
    # 列表页选择器
    list_rule: str = ""                # 列表区域选择器
    vod_id_rule: str = ""              # 影片ID选择器
    vod_name_rule: str = ""            # 影片名称选择器
    vod_pic_rule: str = ""             # 封面图选择器
    vod_remarks_rule: str = ""         # 备注选择器
    
    # 详情页选择器
    detail_name_rule: str = ""         # 详情名称
    detail_pic_rule: str = ""          # 详情封面
    detail_content_rule: str = ""      # 剧情简介
    detail_play_from_rule: str = ""    # 播放线路
    detail_play_url_rule: str = ""     # 播放地址
    
    # 搜索配置
    searchable: int = 1                # 是否支持搜索
    search_rule: str = ""              # 搜索结果选择器
    
    # 其他配置
    headers: Dict[str, str] = field(default_factory=dict)  # 请求头
    timeout: int = 10                  # 超时时间
    encoding: str = "utf-8"            # 编码格式


class SelectorParser:
    """选择器语法解析器"""
    
    @staticmethod
    def parse(rule_str: str) -> Tuple[str, str]:
        """
        解析选择器语法
        
        Args:
            rule_str: 规则字符串,如:
                - "div.item&&a.title" (正则)
                - "j:$.data.list[*]" (JSONPath)
                - "p:div.content > h1" (CSS选择器)
        
        Returns:
            (selector_type, selector_value)
            selector_type: 'regex' | 'json' | 'css'
            selector_value: 实际的选择器表达式
        """
        if not rule_str:
            return ('regex', '')
        
        rule_str = rule_str.strip()
        
        # JSONPath
        if rule_str.startswith('j:'):
            return ('json', rule_str[2:])
        
        # CSS选择器
        elif rule_str.startswith('p:'):
            return ('css', rule_str[2:])
        
        # 正则表达式 (默认)
        else:
            return ('regex', rule_str)
    
    @staticmethod
    def extract(html: str, rule_str: str, base_url: str = "") -> List[str]:
        """
        根据规则提取内容
        
        Args:
            html: HTML文本或JSON字符串
            rule_str: 规则字符串
            base_url: 基础URL (用于补全相对路径)
        
        Returns:
            提取结果列表
        """
        if not rule_str or not html:
            return []
        
        selector_type, selector_value = SelectorParser.parse(rule_str)
        
        try:
            if selector_type == 'json':
                return SelectorParser._extract_json(html, selector_value)
            elif selector_type == 'css':
                return SelectorParser._extract_css(html, selector_value, base_url)
            else:
                return SelectorParser._extract_regex(html, selector_value, base_url)
        except Exception as e:
            logger.error(f"选择器解析失败 [{selector_type}]: {rule_str}, 错误: {e}")
            return []
    
    @staticmethod
    def _extract_regex(html: str, pattern: str, base_url: str = "") -> List[str]:
        """正则表达式提取"""
        # 处理&&分隔的多段正则
        parts = [p.strip() for p in pattern.split('&&') if p.strip()]
        
        if not parts:
            return []
        
        current_matches = [html]
        
        for part in parts:
            new_matches = []
            for text in current_matches:
                try:
                    # 查找所有匹配
                    matches = re.findall(part, text, re.DOTALL | re.IGNORECASE)
                    
                    if matches:
                        for match in matches:
                            if isinstance(match, tuple):
                                # 多个捕获组,取第一个非空
                                value = next((m for m in match if m), '')
                            else:
                                value = match
                            
                            # 清理空白
                            value = value.strip()
                            
                            # 补全URL
                            if value and base_url and (value.startswith('/') or value.startswith('./')):
                                from urllib.parse import urljoin
                                value = urljoin(base_url, value)
                            
                            if value:
                                new_matches.append(value)
                except re.error as e:
                    logger.warning(f"正则表达式错误 [{part}]: {e}")
                    continue
            
            current_matches = new_matches
            
            # 如果某一步没有匹配,提前退出
            if not current_matches:
                break
        
        return current_matches
    
    @staticmethod
    def _extract_json(json_str: str, jsonpath: str) -> List[str]:
        """JSONPath提取"""
        try:
            data = json.loads(json_str) if isinstance(json_str, str) else json_str
            expr = jsonpath_parse(jsonpath)
            matches = expr.find(data)
            return [str(match.value) for match in matches]
        except Exception as e:
            logger.error(f"JSONPath解析失败: {jsonpath}, 错误: {e}")
            return []
    
    @staticmethod
    def _extract_css(html: str, css_selector: str, base_url: str = "") -> List[str]:
        """CSS选择器提取 (使用BeautifulSoup)"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            elements = soup.select(css_selector)
            
            results = []
            for elem in elements:
                # 尝试获取不同属性
                value = None
                
                # 如果是img标签,获取src
                if elem.name == 'img':
                    value = elem.get('data-src') or elem.get('src') or elem.get('original')
                
                # 如果是a标签,获取href
                elif elem.name == 'a':
                    value = elem.get('href')
                
                # 否则获取文本
                else:
                    value = elem.get_text(strip=True)
                
                if value:
                    # 补全URL
                    if base_url and value.startswith('/'):
                        from urllib.parse import urljoin
                        value = urljoin(base_url, value)
                    
                    results.append(value)
            
            return results
        except Exception as e:
            logger.error(f"CSS选择器解析失败: {css_selector}, 错误: {e}")
            return []


class XBPQSource(VodSourceAdapter):
    """
    XBPQ规则引擎数据源适配器
    
    通过配置化的规则解析HTML页面,无需编写代码即可适配任意网站。
    """
    
    def __init__(self, source_config: Dict[str, Any]):
        super().__init__(source_config)
        
        # 加载XBPQ规则
        self.rule = self._load_rule()
        
        if not self.rule.host:
            raise ValueError("XBPQ规则必须配置host字段")
        
        # 初始化HTTP客户端
        self.http_client = HTTPClient(
            timeout=self.rule.timeout,
            max_retries=3,
            retry_delay=1.0,
            enable_circuit_breaker=True
        )
    
    def _load_rule(self) -> XBPQRule:
        """从配置文件加载XBPQ规则"""
        ext = self.ext_config
        
        if isinstance(ext, str):
            # ext是文件路径,读取JSON文件
            import os
            if os.path.exists(ext):
                with open(ext, 'r', encoding='utf-8') as f:
                    ext = json.load(f)
            else:
                raise FileNotFoundError(f"XBPQ规则文件不存在: {ext}")
        
        rule = XBPQRule(
            title=ext.get('title', self.name),
            # 兼容多种host字段命名
            host=ext.get('host') or ext.get('首页推荐链接') or ext.get('homeUrl') or '',
            url=ext.get('url', ''),
            search_url=ext.get('searchUrl') or ext.get('search_url', ''),
            detail_url=ext.get('detailUrl', ''),
            home_url=ext.get('homeUrl', ''),
            recommend=ext.get('推荐', ''),
            class_name=ext.get('class_name') or ext.get('分类名称', ''),
            class_url=ext.get('class_url') or ext.get('分类名称替换词', ''),
            list_rule=ext.get('一级') or ext.get('分类列表数组规则', ''),
            vod_id_rule=ext.get('vod_id') or ext.get('分类片单链接', ''),
            vod_name_rule=ext.get('vod_name') or ext.get('分类片单标题', ''),
            vod_pic_rule=ext.get('vod_pic') or ext.get('分类片单图片', ''),
            vod_remarks_rule=ext.get('vod_remarks') or ext.get('分类片单副标题', ''),
            detail_name_rule=ext.get('二级名称') or ext.get('类型详情', ''),
            detail_pic_rule=ext.get('二级图片') or ext.get('详情页图片', ''),
            detail_content_rule=ext.get('二级简介') or ext.get('简介详情', ''),
            detail_play_from_rule=ext.get('二级线路') or ext.get('线路列表数组规则', ''),
            detail_play_url_rule=ext.get('二级剧集') or ext.get('选集标题链接是否Jsoup写法', ''),
            searchable=ext.get('searchable', 1),
            search_rule=ext.get('搜索') or ext.get('sea_arr_rule', ''),
            headers=ext.get('headers', {}),
            timeout=ext.get('timeout', 10),
            encoding=ext.get('编码') or ext.get('网页编码格式', 'utf-8')
        )
        
        return rule
    
    async def _request(self, url: str, params: Dict = None) -> str:
        """发送HTTP请求"""
        from urllib.parse import urljoin
        
        full_url = urljoin(self.rule.host, url) if not url.startswith('http') else url
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            **self.rule.headers
        }
        
        try:
            response = await self.http_client.get(full_url, params=params, headers=headers)
            return await response.text(encoding=self.rule.encoding)
        except Exception as e:
            logger.error(f"XBPQ请求失败 [{self.name}]: {full_url}, 错误: {e}")
            raise
    
    async def cleanup(self):
        """清理资源"""
        await self.http_client.close()
    
    async def get_categories(self) -> List[Category]:
        """获取分类列表"""
        if self.is_cache_valid():
            return self._categories_cache
        
        categories = []
        
        # 从class_name和class_url解析
        if self.rule.class_name and self.rule.class_url:
            names = self.rule.class_name.split('&')
            urls = self.rule.class_url.split('&')
            
            for i, name in enumerate(names):
                if i < len(urls):
                    cat = Category(
                        type_id=i + 1,  # 使用索引作为ID
                        type_name=name.strip(),
                        type_flag=0
                    )
                    categories.append(cat)
        
        self._categories_cache = categories
        return categories
    
    async def get_vod_list(
        self, 
        type_id: int, 
        page: int = 1,
        filters: Optional[Dict[str, str]] = None
    ) -> VodListResponse:
        """获取影片列表"""
        try:
            # 构建URL
            url_template = self.rule.url
            if not url_template:
                return VodListResponse(code=0, msg="未配置列表URL规则", list=[])
            
            # 替换模板变量
            url = url_template.replace('fypage', str(page))
            url = url.replace('fyclass', str(type_id))
            
            # 发送请求
            html = await self._request(url)
            
            # 解析列表
            vod_items = []
            
            # 首先提取列表区域
            if self.rule.list_rule:
                list_areas = SelectorParser.extract(html, self.rule.list_rule, self.rule.host)
            else:
                list_areas = [html]
            
            # 从每个区域提取影片信息
            for area in list_areas:
                try:
                    vod_ids = SelectorParser.extract(area, self.rule.vod_id_rule, self.rule.host)
                    vod_names = SelectorParser.extract(area, self.rule.vod_name_rule)
                    vod_pics = SelectorParser.extract(area, self.rule.vod_pic_rule, self.rule.host)
                    vod_remarks = SelectorParser.extract(area, self.rule.vod_remarks_rule)
                    
                    # 组合成VodItem
                    max_count = min(len(vod_ids), len(vod_names))
                    for i in range(max_count):
                        vod_item = VodItem(
                            vod_id=f"{self.name}${vod_ids[i]}" if i < len(vod_ids) else "",
                            vod_name=vod_names[i] if i < len(vod_names) else "",
                            vod_pic=vod_pics[i] if i < len(vod_pics) else "",
                            vod_remarks=vod_remarks[i] if i < len(vod_remarks) else ""
                        )
                        vod_items.append(vod_item)
                except Exception as e:
                    logger.warning(f"解析单个影片失败: {e}")
                    continue
            
            return VodListResponse(
                code=1,
                msg="success",
                page=page,
                pagecount=999,  # XBPQ通常不知道总页数
                limit=len(vod_items),
                total=len(vod_items),
                list=vod_items
            )
            
        except Exception as e:
            logger.error(f"XBPQ获取列表失败 [{self.name}]: {e}")
            raise
    
    async def get_vod_detail(self, vod_id: str) -> VodDetailResponse:
        """获取影片详情"""
        try:
            # 提取真实ID
            if '$' in vod_id:
                real_id = vod_id.split('$', 1)[1]
            else:
                real_id = vod_id
            
            # 构建详情URL
            if self.rule.detail_url:
                detail_url = self.rule.detail_url.replace('fyid', real_id)
            else:
                detail_url = real_id
            
            html = await self._request(detail_url)
            
            # 解析详情
            name = SelectorParser.extract(html, self.rule.detail_name_rule)
            pic = SelectorParser.extract(html, self.rule.detail_pic_rule, self.rule.host)
            content = SelectorParser.extract(html, self.rule.detail_content_rule)
            play_from = SelectorParser.extract(html, self.rule.detail_play_from_rule)
            play_url_raw = SelectorParser.extract(html, self.rule.detail_play_url_rule)
            
            # 解析播放地址 (格式: 第1集$URL1#第2集$URL2)
            play_url = []
            if play_url_raw:
                for line in play_url_raw:
                    episodes = [ep.strip() for ep in line.split('#') if ep.strip()]
                    play_url.append(episodes)
            
            vod_detail = VodDetail(
                vod_id=vod_id,
                vod_name=name[0] if name else "",
                vod_pic=pic[0] if pic else "",
                vod_content=content[0] if content else "",
                vod_play_from=play_from,
                vod_play_url=play_url
            )
            
            return VodDetailResponse(
                code=1,
                msg="success",
                list=[vod_detail]
            )
            
        except Exception as e:
            logger.error(f"XBPQ获取详情失败 [{self.name}]: {e}")
            raise
    
    async def search_vod(self, keyword: str, page: int = 1) -> VodListResponse:
        """搜索影片"""
        if not self.rule.searchable or not self.rule.search_url:
            return VodListResponse(code=0, msg="不支持搜索", list=[])
        
        try:
            # 构建搜索URL
            search_url = self.rule.search_url.replace('**', keyword)
            search_url = search_url.replace('#TruePage#', str(page))
            
            html = await self._request(search_url)
            
            # 解析搜索结果 (与列表类似)
            vod_items = []
            
            if self.rule.search_rule:
                search_areas = SelectorParser.extract(html, self.rule.search_rule, self.rule.host)
            else:
                search_areas = [html]
            
            for area in search_areas:
                try:
                    vod_ids = SelectorParser.extract(area, self.rule.vod_id_rule, self.rule.host)
                    vod_names = SelectorParser.extract(area, self.rule.vod_name_rule)
                    vod_pics = SelectorParser.extract(area, self.rule.vod_pic_rule, self.rule.host)
                    vod_remarks = SelectorParser.extract(area, self.rule.vod_remarks_rule)
                    
                    max_count = min(len(vod_ids), len(vod_names))
                    for i in range(max_count):
                        vod_item = VodItem(
                            vod_id=f"{self.name}${vod_ids[i]}" if i < len(vod_ids) else "",
                            vod_name=vod_names[i] if i < len(vod_names) else "",
                            vod_pic=vod_pics[i] if i < len(vod_pics) else "",
                            vod_remarks=vod_remarks[i] if i < len(vod_remarks) else ""
                        )
                        vod_items.append(vod_item)
                except Exception as e:
                    logger.warning(f"解析搜索结果失败: {e}")
                    continue
            
            return VodListResponse(
                code=1,
                msg="success",
                page=page,
                list=vod_items
            )
            
        except Exception as e:
            logger.error(f"XBPQ搜索失败 [{self.name}]: {e}")
            raise
