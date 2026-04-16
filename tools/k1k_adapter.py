#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
k1k.cc 网站数据适配器 - 将网页数据转换为MacCMS API格式

注意：此脚本仅供个人学习研究使用，请遵守robots.txt协议，设置合理的请求间隔
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import time
from typing import List, Dict, Optional


class K1KAdapter:
    """k1k.cc网站数据适配器"""
    
    def __init__(self):
        self.base_url = 'http://www.k1k.cc'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
        # 请求间隔（秒），避免对目标服务器造成压力
        self.request_delay = 2
    
    def _fetch_page(self, url: str) -> Optional[str]:
        """获取页面内容（带限流）"""
        try:
            time.sleep(self.request_delay)
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                return response.text
            else:
                print(f"HTTP {response.status_code}: {url}")
                return None
        except Exception as e:
            print(f"请求失败: {e}")
            return None
    
    def _extract_downurls(self, html: str) -> Optional[str]:
        """从HTML中提取downurls变量"""
        match = re.search(r'var\s+downurls\s*=\s*"([^"]*)"', html)
        if match:
            return match.group(1)
        return None
    
    def _parse_play_urls(self, downurls_str: str) -> List[Dict]:
        """解析播放地址字符串
        
        格式: [线路名称]URL#URL#URL
        示例: [手机MP4]HD中字$url1#HD国语$url2
        """
        if not downurls_str:
            return []
        
        plays = []
        # 提取线路名称
        line_match = re.match(r'\[([^\]]+)\](.*)', downurls_str)
        if line_match:
            line_name = line_match.group(1)
            urls_str = line_match.group(2)
            
            # 分割多个URL（用#分隔）
            url_pairs = urls_str.split('#')
            for pair in url_pairs:
                if '$' in pair:
                    episode, url = pair.split('$', 1)
                    plays.append({
                        'episode': episode.strip(),
                        'url': url.strip(),
                        'line': line_name
                    })
        
        return plays
    
    def get_categories(self) -> List[Dict]:
        """获取分类列表"""
        categories = [
            {"type_id": 1, "type_name": "电影"},
            {"type_id": 2, "type_name": "连续剧"},
            {"type_id": 3, "type_name": "综艺"},
            {"type_id": 4, "type_name": "动漫"},
        ]
        return categories
    
    def get_movie_list(self, type_id: int = 1, page: int = 1, pagesize: int = 20) -> Dict:
        """获取影片列表
        
        Args:
            type_id: 分类ID (1=电影, 2=连续剧, 3=综艺, 4=动漫)
            page: 页码
            pagesize: 每页数量
            
        Returns:
            MacCMS API格式的响应
        """
        # 映射分类到URL路径
        type_map = {
            1: '/movie/list',
            2: '/ju/list',
            3: '/zy/list',
            4: '/dm/list',
        }
        
        path = type_map.get(type_id, '/movie/list')
        url = f"{self.base_url}{path}"
        
        print(f"正在获取分类列表: {url}")
        html = self._fetch_page(url)
        
        if not html:
            return self._empty_response(page)
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # 查找影片列表项
        movies = []
        
        # 尝试不同的选择器
        img_list = soup.find('ul', class_='img-list') or soup.find('div', class_='img-list')
        if img_list:
            items = img_list.find_all('li')
        else:
            items = []
        
        for item in items[:pagesize]:
            movie = self._parse_movie_item(item)
            if movie:
                movies.append(movie)
        
        # 估算总数（假设每页数量相同）
        total = len(items)  # 使用实际找到的数量
        pagecount = max(1, (total + pagesize - 1) // pagesize)
        
        return {
            "code": 1,
            "msg": "数据列表",
            "page": page,
            "pagecount": pagecount,
            "limit": pagesize,
            "total": total,
            "list": movies
        }
    
    def _parse_movie_item(self, item) -> Optional[Dict]:
        """解析单个影片项"""
        try:
            # 提取链接
            link_tag = item.find('a', href=True)
            if not link_tag:
                return None
            
            href = link_tag.get('href', '')
            vod_id = href.split('/')[-1] if '/' in href else ''
            
            # 提取标题
            title = link_tag.get('title', '') or link_tag.get_text(strip=True)
            
            # 提取图片
            img_tag = item.find('img')
            vod_pic = img_tag.get('data-original') or img_tag.get('src') if img_tag else ''
            
            # 提取备注信息
            remarks_tag = item.find('span', class_='note')
            vod_remarks = remarks_tag.get_text(strip=True) if remarks_tag else ''
            
            # 提取年份/类型
            info_tag = item.find('p', class_='info')
            vod_year = ''
            vod_area = ''
            if info_tag:
                info_text = info_tag.get_text(strip=True)
                # 尝试提取年份
                year_match = re.search(r'(20\d{2})', info_text)
                if year_match:
                    vod_year = year_match.group(1)
            
            return {
                "vod_id": vod_id,
                "vod_name": title,
                "type_id": 1,  # 需要根据实际分类调整
                "type_name": "电影",
                "vod_pic": vod_pic if vod_pic.startswith('http') else f"{self.base_url}{vod_pic}",
                "vod_remarks": vod_remarks,
                "vod_year": vod_year,
                "vod_area": vod_area,
                "vod_actor": "",
                "vod_director": "",
                "vod_content": "",
                "vod_play_from": "",
                "vod_play_url": ""
            }
        except Exception as e:
            print(f"解析影片项失败: {e}")
            return None
    
    def get_movie_detail(self, vod_id: str) -> Dict:
        """获取影片详情
        
        Args:
            vod_id: 影片ID
            
        Returns:
            MacCMS API格式的详情响应
        """
        # 需要判断是电影还是连续剧
        # 简化处理：先尝试电影路径
        url = f"{self.base_url}/movie/{vod_id}"
        
        print(f"正在获取影片详情: {url}")
        html = self._fetch_page(url)
        
        if not html:
            # 尝试连续剧路径
            url = f"{self.base_url}/ju/{vod_id}"
            html = self._fetch_page(url)
        
        if not html:
            return self._empty_detail_response()
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # 提取基本信息
        title_tag = soup.find('h1')
        vod_name = title_tag.get_text(strip=True) if title_tag else ''
        
        # 提取downurls
        downurls_str = self._extract_downurls(html)
        plays = self._parse_play_urls(downurls_str) if downurls_str else []
        
        # 构建播放URL字符串
        vod_play_from = "k1k线路"
        vod_play_url = "#".join([f"{p['episode']}${p['url']}" for p in plays])
        
        # 提取简介
        desc_tag = soup.find('div', class_='intro') or soup.find('meta', attrs={'name': 'description'})
        vod_content = desc_tag.get('content', '') if desc_tag else ''
        
        movie = {
            "vod_id": vod_id,
            "vod_name": vod_name,
            "type_id": 1,
            "type_name": "电影",
            "vod_pic": "",
            "vod_remarks": "",
            "vod_year": "",
            "vod_area": "",
            "vod_actor": "",
            "vod_director": "",
            "vod_content": vod_content[:500],
            "vod_play_from": vod_play_from,
            "vod_play_url": vod_play_url
        }
        
        return {
            "code": 1,
            "msg": "数据列表",
            "page": 1,
            "pagecount": 1,
            "limit": 1,
            "total": 1,
            "list": [movie]
        }
    
    def _empty_response(self, page: int = 1) -> Dict:
        """返回空响应"""
        return {
            "code": 1,
            "msg": "数据列表",
            "page": page,
            "pagecount": 0,
            "limit": 20,
            "total": 0,
            "list": []
        }
    
    def _empty_detail_response(self) -> Dict:
        """返回空详情响应"""
        return {
            "code": 0,
            "msg": "未找到数据",
            "page": 1,
            "pagecount": 0,
            "limit": 1,
            "total": 0,
            "list": []
        }


def test_adapter():
    """测试适配器"""
    adapter = K1KAdapter()
    
    print("="*80)
    print("测试k1k.cc适配器")
    print("="*80)
    
    # 测试1: 获取分类
    print("\n1. 获取分类:")
    categories = adapter.get_categories()
    for cat in categories:
        print(f"  {cat['type_id']}: {cat['type_name']}")
    
    # 测试2: 获取电影列表
    print("\n2. 获取电影列表:")
    result = adapter.get_movie_list(type_id=1, page=1, pagesize=5)
    print(f"  总数: {result['total']}")
    print(f"  返回数量: {len(result['list'])}")
    if result['list']:
        for movie in result['list'][:3]:
            print(f"    - {movie['vod_name']} ({movie['vod_remarks']})")
    
    # 测试3: 获取影片详情
    if result['list']:
        first_movie = result['list'][0]
        vod_id = first_movie['vod_id']
        print(f"\n3. 获取影片详情 (ID: {vod_id}):")
        detail = adapter.get_movie_detail(vod_id)
        if detail['list']:
            movie = detail['list'][0]
            print(f"  标题: {movie['vod_name']}")
            print(f"  播放源: {movie['vod_play_from']}")
            if movie['vod_play_url']:
                plays = movie['vod_play_url'].split('#')
                print(f"  播放集数: {len(plays)}")
                print(f"  示例: {plays[0][:100]}...")


if __name__ == "__main__":
    test_adapter()
