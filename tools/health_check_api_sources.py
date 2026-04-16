#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MacCMS API源健康检查与自动发现工具

功能：
1. 批量测试已知的MacCMS API源
2. 记录每个源的响应时间、数据量、成功率
3. 自动生成可用源列表
4. 支持从GitHub/Gitee仓库自动发现新源
"""

import requests
import json
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# 已知的高质量MacCMS API源列表（持续更新）
KNOWN_SOURCES = [
    # 国内稳定源
    "https://subocaiji.com/api.php/provide/vod/",
    "https://api.apibdzy.com/api.php",
    "http://zy.yilans.net:8090/api.php",
    
    # 传统资源站
    "https://api.1080zyku.com/inc/apijson.php",
    "https://wujinzy.com/api.php/provide/vod/",
    "https://vipcj.timizy.top/api.php/provide/vod/",
    "https://ziyuan.smdyy.cc/api.php/provide/vod/",
    "https://cj.vodimg.top/api.php/provide/vod/",
    "https://json.777up.cc/api.php/provide/vod/",
    
    # 其他可能的源
    "https://collect.wolongzyw.com/api.php/provide/vod/",
    "https://collect.kuyun.pro/api.php/provide/vod/",
    "https://m3u8.feisuzyapi.com/api.php",
    "http://api.fqzy.cc/api.php",
    "https://app.linzhiyuan.xyz/api.php",
    "https://www.39kan.com/api.php",
    "https://app.feiyu5.com/api.php",
]

# GitHub/Gitee上的TVBox配置仓库（用于自动发现新源）
CONFIG_REPOS = [
    "https://raw.githubusercontent.com/FongMi/Release/main/api.json",
    "https://raw.githubusercontent.com/gaotianliuyun/gao/master/api.json",
    "https://raw.githubusercontent.com/CatVodTVOfficial/TVBoxOSC/master/api.json",
    "https://raw.githubusercontent.com/qist/tvbox/master/json/config.json",
]


def test_api_source(url, timeout=5):
    """测试单个API源的健康状态"""
    result = {
        'url': url,
        'status': 'UNKNOWN',
        'response_time': 0,
        'data_count': 0,
        'sample_movie': '',
        'error': ''
    }
    
    try:
        start_time = time.time()
        
        # 测试分类列表接口
        response = requests.get(
            f"{url}?ac=list&t=1&pg=1",
            timeout=timeout,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        
        elapsed = time.time() - start_time
        result['response_time'] = round(elapsed * 1000, 2)  # 毫秒
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('code') == 1 and data.get('list'):
                result['status'] = 'HEALTHY'
                result['data_count'] = len(data['list'])
                if data['list']:
                    result['sample_movie'] = data['list'][0].get('vod_name', '')
            else:
                result['status'] = 'EMPTY_DATA'
                result['error'] = data.get('msg', '返回空数据')
        else:
            result['status'] = 'HTTP_ERROR'
            result['error'] = f"HTTP {response.status_code}"
            
    except requests.exceptions.Timeout:
        result['status'] = 'TIMEOUT'
        result['error'] = f"超时({timeout}s)"
    except requests.exceptions.ConnectionError as e:
        result['status'] = 'CONNECTION_ERROR'
        result['error'] = str(e)[:50]
    except Exception as e:
        result['status'] = 'ERROR'
        result['error'] = str(e)[:50]
    
    return result


def extract_type1_sources_from_config(config_url):
    """从TVBox配置文件中提取Type 1 MacCMS API源"""
    sources = []
    try:
        response = requests.get(config_url, timeout=10)
        if response.status_code == 200:
            config = response.json()
            sites = config.get('sites', [])
            
            for site in sites:
                if site.get('type') == 1:
                    api_url = site.get('api', '')
                    if api_url and 'api.php' in api_url or 'vod' in api_url:
                        sources.append(api_url)
    except Exception as e:
        print(f"  ❌ 解析配置失败: {str(e)[:50]}")
    
    return sources


def discover_new_sources():
    """从GitHub/Gitee仓库中发现新的API源"""
    print("\n" + "="*80)
    print("正在从开源仓库发现新的API源...")
    print("="*80)
    
    discovered_sources = []
    
    for repo_url in CONFIG_REPOS:
        try:
            print(f"\n检查: {repo_url.split('/')[-1]}")
            sources = extract_type1_sources_from_config(repo_url)
            if sources:
                print(f"  ✅ 发现 {len(sources)} 个Type 1源")
                discovered_sources.extend(sources)
            else:
                print(f"  ⚠️  未发现Type 1源")
        except Exception as e:
            print(f"  ❌ 访问失败: {str(e)[:50]}")
    
    # 去重
    unique_sources = list(set(discovered_sources))
    print(f"\n总计发现 {len(unique_sources)} 个唯一源")
    
    return unique_sources


def run_health_check():
    """执行完整的健康检查"""
    print("="*80)
    print("MacCMS API源健康检查工具")
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # 第一步：发现新源
    new_sources = discover_new_sources()
    all_sources = list(set(KNOWN_SOURCES + new_sources))
    
    print(f"\n总共需要测试 {len(all_sources)} 个API源")
    print("="*80)
    
    # 第二步：批量测试
    results = []
    healthy_count = 0
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {
            executor.submit(test_api_source, url): url 
            for url in all_sources
        }
        
        for future in as_completed(future_to_url):
            result = future.result()
            results.append(result)
            
            # 实时显示结果
            status_icon = {
                'HEALTHY': '✅',
                'EMPTY_DATA': '⚠️ ',
                'TIMEOUT': '⏱️ ',
                'HTTP_ERROR': '❌',
                'CONNECTION_ERROR': '❌',
                'ERROR': '❌'
            }.get(result['status'], '?')
            
            url_short = result['url'].split('/')[2][:25]
            print(f"{status_icon} {url_short:<30} | {result['status']:<15} | {result['response_time']}ms")
            
            if result['status'] == 'HEALTHY':
                healthy_count += 1
                if result['data_count'] > 0:
                    print(f"   └─ 数据: {result['data_count']}条 | 示例: {result['sample_movie']}")
    
    # 第三步：生成报告
    print("\n" + "="*80)
    print("健康检查报告")
    print("="*80)
    print(f"总测试数: {len(results)}")
    print(f"健康源: {healthy_count}")
    print(f"失败源: {len(results) - healthy_count}")
    print(f"成功率: {healthy_count/len(results)*100:.1f}%")
    
    # 第四步：保存结果
    healthy_sources = [r for r in results if r['status'] == 'HEALTHY']
    healthy_sources.sort(key=lambda x: x['data_count'], reverse=True)
    
    if healthy_sources:
        output_file = 'healthy_maccms_sources.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'check_time': datetime.now().isoformat(),
                'total_tested': len(results),
                'healthy_count': healthy_count,
                'sources': healthy_sources
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 健康源列表已保存到: {output_file}")
        
        # 生成Python代码格式
        print("\n可直接使用的Python代码:")
        print("\napi_sources = [")
        for src in healthy_sources[:10]:  # 只显示前10个
            print(f'    "{src["url"]}",  # {src["data_count"]}条数据, {src["response_time"]}ms')
        print("]")
    
    return healthy_sources


if __name__ == "__main__":
    run_health_check()
