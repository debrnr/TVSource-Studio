"""
TVBox标准API路由

实现TVBox客户端期望的标准MacCMS API接口:
- /api/vod - 视频列表/详情/搜索
- /api/live - 直播源
- /api/config - 配置信息

支持CORS跨域访问
"""

import logging
from flask import Blueprint, jsonify, request, Response
from .core import SourceManager, MultiSourceAggregator
from flask_cors import CORS

logger = logging.getLogger(__name__)

# 创建Blueprint
tvbox_bp = Blueprint('tvbox', __name__, url_prefix='/api')

# 启用CORS
CORS(tvbox_bp)

# 全局管理器实例
source_manager = None
aggregator = None


def init_tvbox_routes(manager: SourceManager):
    """
    初始化TVBox路由
    
    Args:
        manager: SourceManager实例
    """
    global source_manager, aggregator
    source_manager = manager
    aggregator = MultiSourceAggregator(max_concurrency=5)
    
    logger.info("✓ TVBox API路由初始化完成")


@tvbox_bp.route('/vod', methods=['GET'])
async def vod_api():
    """
    MacCMS标准视频API
    
    参数:
        ac: 动作类型 (list/detail)
        t: 分类ID
        pg: 页码
        wd: 搜索关键词
        ids: 影片ID列表(逗号分隔)
    
    返回:
        标准MacCMS JSON格式
    """
    try:
        action = request.args.get('ac', 'list')
        
        if action == 'detail':
            return await handle_vod_detail()
        elif action == 'list':
            return await handle_vod_list()
        else:
            return jsonify({
                'code': 0,
                'msg': f'不支持的动作: {action}'
            }), 400
            
    except Exception as e:
        logger.error(f"VOD API错误: {e}", exc_info=True)
        return jsonify({
            'code': 0,
            'msg': f'服务器错误: {str(e)}'
        }), 500


async def handle_vod_list():
    """处理影片列表请求"""
    type_id = request.args.get('t', type=int, default=1)
    page = request.args.get('pg', type=int, default=1)
    keyword = request.args.get('wd', '')
    
    # 搜索模式
    if keyword:
        return await handle_search(keyword, page)
    
    # 列表模式 - 从所有数据源聚合
    adapters = source_manager.get_all_adapters()
    
    if not adapters:
        return jsonify({
            'code': 0,
            'msg': '没有可用的数据源',
            'list': [],
            'class': []
        })
    
    # 从第一个适配器获取分类
    first_adapter = list(adapters.values())[0]
    try:
        categories = await first_adapter.get_categories()
        class_list = [
            {
                'type_id': cat.type_id,
                'type_name': cat.type_name,
                'type_flag': cat.type_flag
            }
            for cat in categories
        ]
    except Exception as e:
        logger.warning(f"获取分类失败: {e}")
        class_list = []
    
    # 从所有适配器获取影片列表并合并
    all_vods = []
    
    for name, adapter in adapters.items():
        try:
            vod_response = await adapter.get_vod_list(type_id, page)
            
            if vod_response.code == 1 and vod_response.list:
                # 转换VodItem为字典
                for item in vod_response.list:
                    all_vods.append({
                        'vod_id': item.vod_id,
                        'vod_name': item.vod_name,
                        'vod_pic': item.vod_pic,
                        'vod_remarks': item.vod_remarks,
                        'vod_year': item.vod_year,
                        'vod_area': item.vod_area,
                        'type_name': item.vod_type
                    })
        except Exception as e:
            logger.error(f"数据源 [{name}] 获取列表失败: {e}")
            continue
    
    # 如果没有数据,返回空列表但包含分类
    if not all_vods:
        return jsonify({
            'code': 1,
            'msg': 'success',
            'page': page,
            'pagecount': 0,
            'limit': 20,
            'total': 0,
            'list': [],
            'class': class_list
        })
    
    # 分页处理
    limit = 20
    total = len(all_vods)
    pagecount = (total + limit - 1) // limit
    
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    page_vods = all_vods[start_idx:end_idx]
    
    return jsonify({
        'code': 1,
        'msg': 'success',
        'page': page,
        'pagecount': pagecount,
        'limit': limit,
        'total': total,
        'list': page_vods,
        'class': class_list
    })


async def handle_vod_detail():
    """处理影片详情请求"""
    ids = request.args.get('ids', '')
    
    if not ids:
        return jsonify({
            'code': 0,
            'msg': '缺少影片ID参数'
        }), 400
    
    # 提取第一个ID (支持多个ID,但通常只查一个)
    vod_id = ids.split(',')[0].strip()
    
    # 解析源名称和真实ID
    if '$' in vod_id:
        source_name, real_id = vod_id.split('$', 1)
    else:
        # 尝试从所有源查找
        source_name = None
        real_id = vod_id
    
    try:
        if source_name:
            # 从指定源获取
            adapter = source_manager.get_adapter(source_name)
            detail_response = await adapter.get_vod_detail(vod_id)
        else:
            # 从所有源查找
            detail_response = await search_all_sources_for_detail(real_id)
        
        if detail_response.code != 1 or not detail_response.list:
            return jsonify({
                'code': 0,
                'msg': '未找到影片详情',
                'list': []
            })
        
        # 转换VodDetail为字典
        detail = detail_response.list[0]
        result = {
            'vod_id': detail.vod_id,
            'vod_name': detail.vod_name,
            'vod_pic': detail.vod_pic,
            'vod_content': detail.vod_content,
            'vod_year': detail.vod_year,
            'vod_area': detail.vod_area,
            'vod_director': detail.vod_director,
            'vod_actor': detail.vod_actor,
            'vod_play_from': '$$$'.join(detail.vod_play_from),
            'vod_play_url': '#'.join(['#'.join(episodes) for episodes in detail.vod_play_url])
        }
        
        return jsonify({
            'code': 1,
            'msg': 'success',
            'page': 1,
            'pagecount': 1,
            'limit': 1,
            'total': 1,
            'list': [result]
        })
        
    except KeyError:
        return jsonify({
            'code': 0,
            'msg': f'数据源不存在: {source_name}',
            'list': []
        })
    except Exception as e:
        logger.error(f"获取详情失败: {e}", exc_info=True)
        return jsonify({
            'code': 0,
            'msg': f'获取详情失败: {str(e)}',
            'list': []
        })


async def search_all_sources_for_detail(real_id: str):
    """在所有源中搜索影片详情"""
    adapters = source_manager.get_all_adapters()
    
    for name, adapter in adapters.items():
        try:
            vod_id = f"{name}${real_id}"
            response = await adapter.get_vod_detail(vod_id)
            if response.code == 1 and response.list:
                return response
        except:
            continue
    
    from .core import VodDetailResponse
    return VodDetailResponse(code=0, msg='not found', list=[])


async def handle_search(keyword: str, page: int):
    """处理搜索请求"""
    adapters = source_manager.get_all_adapters()
    
    if not adapters:
        return jsonify({
            'code': 0,
            'msg': '没有可用的数据源',
            'list': []
        })
    
    # 从所有源并行搜索
    all_results = []
    
    for name, adapter in adapters.items():
        try:
            search_response = await adapter.search_vod(keyword, page)
            
            if search_response.code == 1 and search_response.list:
                for item in search_response.list:
                    all_results.append({
                        'vod_id': item.vod_id,
                        'vod_name': item.vod_name,
                        'vod_pic': item.vod_pic,
                        'vod_remarks': item.vod_remarks,
                        'vod_year': item.vod_year,
                        'vod_area': item.vod_area,
                        'type_name': item.vod_type
                    })
        except Exception as e:
            logger.error(f"数据源 [{name}] 搜索失败: {e}")
            continue
    
    # 分页
    limit = 20
    total = len(all_results)
    pagecount = (total + limit - 1) // limit if total > 0 else 0
    
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    page_results = all_results[start_idx:end_idx]
    
    return jsonify({
        'code': 1,
        'msg': 'success',
        'page': page,
        'pagecount': pagecount,
        'limit': limit,
        'total': total,
        'list': page_results
    })


@tvbox_bp.route('/live', methods=['GET'])
def live_api():
    """
    直播源API
    
    返回M3U或TXT格式的直播源
    """
    format_type = request.args.get('format', 'txt')
    
    # TODO: 从配置文件加载直播源
    # 这里先返回示例数据
    
    if format_type == 'm3u':
        return generate_m3u_playlist()
    else:
        return generate_txt_playlist()


def generate_m3u_playlist():
    """生成M3U格式播放列表"""
    m3u_content = "#EXTM3U\n"
    
    # 示例频道
    channels = [
        ("CCTV-1", "http://example.com/cctv1.m3u8"),
        ("CCTV-5", "http://example.com/cctv5.m3u8"),
        ("湖南卫视", "http://example.com/hunan.m3u8"),
    ]
    
    for name, url in channels:
        m3u_content += f'#EXTINF:-1,{name}\n{url}\n'
    
    return Response(
        m3u_content,
        mimetype='application/x-mpegURL',
        headers={'Content-Disposition': 'attachment; filename=live.m3u'}
    )


def generate_txt_playlist():
    """生成TXT格式播放列表"""
    txt_content = ""
    
    # 示例分组
    groups = {
        "央视频道": [
            ("CCTV-1", "http://example.com/cctv1.m3u8"),
            ("CCTV-5", "http://example.com/cctv5.m3u8"),
        ],
        "地方卫视": [
            ("湖南卫视", "http://example.com/hunan.m3u8"),
            ("浙江卫视", "http://example.com/zhejiang.m3u8"),
        ]
    }
    
    for group_name, channels in groups.items():
        txt_content += f"{group_name},#genre#\n"
        for name, url in channels:
            txt_content += f"{name},{url}\n"
        txt_content += "\n"
    
    return Response(
        txt_content,
        mimetype='text/plain',
        headers={'Content-Disposition': 'attachment; filename=live.txt'}
    )


@tvbox_bp.route('/config', methods=['GET'])
def config_api():
    """
    配置信息API
    
    返回数据源统计和健康状态
    """
    try:
        stats = source_manager.get_stats()
        
        # 检查熔断器状态
        circuit_stats = {}
        for name, adapter in source_manager.adapters.items():
            if hasattr(adapter, 'http_client'):
                cb_stats = adapter.http_client.get_stats()
                circuit_stats[name] = cb_stats
        
        return jsonify({
            'code': 1,
            'msg': 'success',
            'data': {
                'stats': stats,
                'circuit_breakers': circuit_stats,
                'timestamp': __import__('datetime').datetime.now().isoformat()
            }
        })
    except Exception as e:
        logger.error(f"配置API错误: {e}")
        return jsonify({
            'code': 0,
            'msg': str(e)
        }), 500


@tvbox_bp.route('/health', methods=['GET'])
async def health_check():
    """
    健康检查API
    
    检查所有数据源的可用性
    """
    results = {}
    
    for name in source_manager.sources.keys():
        is_healthy = await source_manager.health_check(name)
        results[name] = {
            'status': 'healthy' if is_healthy else 'unhealthy',
            'enabled': source_manager.sources[name].enabled
        }
    
    healthy_count = sum(1 for r in results.values() if r['status'] == 'healthy')
    total_count = len(results)
    
    return jsonify({
        'code': 1,
        'msg': 'success',
        'data': {
            'overall': 'healthy' if healthy_count > 0 else 'unhealthy',
            'healthy_sources': healthy_count,
            'total_sources': total_count,
            'sources': results
        }
    })
