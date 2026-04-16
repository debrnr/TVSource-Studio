"""
路由模块 - 定义所有API接口
"""

import os
import json
import logging
import sqlite3
from flask import jsonify, send_file, request, Response
from datetime import datetime, timedelta

# 获取项目根目录（src的父目录）
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 创建logger
logger = logging.getLogger(__name__)

# ==================== SQLite缓存初始化 ====================
CACHE_DB_PATH = os.path.join(project_root, 'data', 'maccms_cache.db')
CACHE_TTL = 3600  # 缓存有效期：1小时（秒）

def init_cache_db():
    """初始化SQLite缓存数据库"""
    try:
        os.makedirs(os.path.dirname(CACHE_DB_PATH), exist_ok=True)
        conn = sqlite3.connect(CACHE_DB_PATH)
        cursor = conn.cursor()
        
        # 创建缓存表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_cache (
                cache_key TEXT PRIMARY KEY,
                response_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                hit_count INTEGER DEFAULT 0
            )
        ''')
        
        # 创建索引加速查询
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_expires ON api_cache(expires_at)
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"[SUCCESS] SQLite缓存数据库初始化成功: {CACHE_DB_PATH}")
    except Exception as e:
        logger.error(f"[ERROR] SQLite缓存数据库初始化失败: {e}")


def get_cached_response(cache_key):
    """从缓存获取响应数据
    
    Args:
        cache_key: 缓存键
        
    Returns:
        dict or None: 缓存的响应数据，如果过期或不存在则返回None
    """
    try:
        conn = sqlite3.connect(CACHE_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT response_data, hit_count 
            FROM api_cache 
            WHERE cache_key = ? AND expires_at > CURRENT_TIMESTAMP
        ''', (cache_key,))
        
        result = cursor.fetchone()
        
        if result:
            response_data, hit_count = result
            # 更新命中次数
            cursor.execute('''
                UPDATE api_cache 
                SET hit_count = hit_count + 1 
                WHERE cache_key = ?
            ''', (cache_key,))
            conn.commit()
            
            logger.debug(f"[CACHE HIT] {cache_key} (命中{hit_count + 1}次)")
            return json.loads(response_data)
        else:
            logger.debug(f"[CACHE MISS] {cache_key}")
            return None
            
    except Exception as e:
        logger.warning(f"[CACHE ERROR] 读取缓存失败: {e}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()


def set_cached_response(cache_key, response_data, ttl=CACHE_TTL):
    """保存响应数据到缓存
    
    Args:
        cache_key: 缓存键
        response_data: 响应数据（dict）
        ttl: 有效期（秒），默认1小时
    """
    try:
        conn = sqlite3.connect(CACHE_DB_PATH)
        cursor = conn.cursor()
        
        expires_at = datetime.now() + timedelta(seconds=ttl)
        
        cursor.execute('''
            INSERT OR REPLACE INTO api_cache 
            (cache_key, response_data, expires_at, hit_count)
            VALUES (?, ?, ?, 0)
        ''', (
            cache_key,
            json.dumps(response_data, ensure_ascii=False),
            expires_at.isoformat()
        ))
        
        conn.commit()
        logger.debug(f"[CACHE SET] {cache_key} (TTL: {ttl}s)")
        
    except Exception as e:
        logger.warning(f"[CACHE ERROR] 写入缓存失败: {e}")
    finally:
        if 'conn' in locals():
            conn.close()


def cleanup_expired_cache():
    """清理过期的缓存记录"""
    try:
        conn = sqlite3.connect(CACHE_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM api_cache WHERE expires_at <= CURRENT_TIMESTAMP')
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        if deleted_count > 0:
            logger.info(f"[CLEANUP] 清理了 {deleted_count} 条过期缓存")
            
    except Exception as e:
        logger.warning(f"[CACHE ERROR] 清理缓存失败: {e}")


# 在模块加载时初始化缓存数据库
init_cache_db()
# =========================================================


def generate_mock_movies(type_id=None, page=1):
    """生成模拟影片数据
    
    Args:
        type_id: 分类ID（可选）
        page: 页码
        
    Returns:
        list: 模拟影片列表
    """
    # 完整的模拟影片数据库
    mock_movies_db = [
        # 电影 (type_id=1)
        {"vod_id": 1001, "vod_name": "流浪地球3", "type_id": 1, "type_name": "电影", "vod_pic": "https://via.placeholder.com/300x450.png?text=Movie1", "vod_remarks": "HD国语", "vod_year": "2026", "vod_area": "大陆", "vod_actor": "吴京,刘德华", "vod_director": "郭帆", "vod_content": "太阳危机升级，人类再次踏上流浪之旅。", "vod_play_from": "测试源", "vod_play_url": "正片$https://example.com/movie1.mp4"},
        {"vod_id": 1002, "vod_name": "封神第二部", "type_id": 1, "type_name": "电影", "vod_pic": "https://via.placeholder.com/300x450.png?text=Movie2", "vod_remarks": "TC国语", "vod_year": "2026", "vod_area": "大陆", "vod_actor": "费翔,李雪健", "vod_director": "乌尔善", "vod_content": "封神榜故事继续，姜子牙与纣王的终极对决。", "vod_play_from": "测试源", "vod_play_url": "正片$https://example.com/movie2.mp4"},
        {"vod_id": 1003, "vod_name": "唐人街探案4", "type_id": 1, "type_name": "电影", "vod_pic": "https://via.placeholder.com/300x450.png?text=Movie3", "vod_remarks": "HD国语", "vod_year": "2026", "vod_area": "大陆", "vod_actor": "王宝强,刘昊然", "vod_director": "陈思诚", "vod_content": "秦风和唐仁来到东京，卷入新的谜案。", "vod_play_from": "测试源", "vod_play_url": "正片$https://example.com/movie3.mp4"},
        {"vod_id": 1004, "vod_name": "复仇者联盟5", "type_id": 1, "type_name": "电影", "vod_pic": "https://via.placeholder.com/300x450.png?text=Movie4", "vod_remarks": "HD英语中字", "vod_year": "2026", "vod_area": "美国", "vod_actor": "小罗伯特·唐尼,克里斯·埃文斯", "vod_director": "罗素兄弟", "vod_content": "复仇者联盟面临前所未有的危机。", "vod_play_from": "测试源", "vod_play_url": "正片$https://example.com/movie4.mp4"},
        {"vod_id": 1005, "vod_name": "速度与激情11", "type_id": 1, "type_name": "电影", "vod_pic": "https://via.placeholder.com/300x450.png?text=Movie5", "vod_remarks": "HD英语中字", "vod_year": "2026", "vod_area": "美国", "vod_actor": "范·迪塞尔,杰森·斯坦森", "vod_director": "林诣彬", "vod_content": "飞车家族的最后一次冒险。", "vod_play_from": "测试源", "vod_play_url": "正片$https://example.com/movie5.mp4"},
        
        # 电视剧 (type_id=2)
        {"vod_id": 2001, "vod_name": "庆余年第三季", "type_id": 2, "type_name": "电视剧", "vod_pic": "https://via.placeholder.com/300x450.png?text=Drama1", "vod_remarks": "更新至第10集", "vod_year": "2026", "vod_area": "大陆", "vod_actor": "张若昀,李沁", "vod_director": "孙皓", "vod_content": "范闲继续他的权谋之路。", "vod_play_from": "测试源", "vod_play_url": "第01集$https://example.com/drama1e01.mp4#第02集$https://example.com/drama1e02.mp4#第03集$https://example.com/drama1e03.mp4"},
        {"vod_id": 2002, "vod_name": "赘婿第二季", "type_id": 2, "type_name": "电视剧", "vod_pic": "https://via.placeholder.com/300x450.png?text=Drama2", "vod_remarks": "更新至第8集", "vod_year": "2026", "vod_area": "大陆", "vod_actor": "郭麒麟,宋轶", "vod_director": "邓科", "vod_content": "宁毅的商战之路继续。", "vod_play_from": "测试源", "vod_play_url": "第01集$https://example.com/drama2e01.mp4#第02集$https://example.com/drama2e02.mp4"},
        {"vod_id": 2003, "vod_name": "权力的游戏前传", "type_id": 2, "type_name": "电视剧", "vod_pic": "https://via.placeholder.com/300x450.png?text=Drama3", "vod_remarks": "全10集", "vod_year": "2026", "vod_area": "美国", "vod_actor": "帕迪·康斯戴恩", "vod_director": "莱恩·康道尔", "vod_content": "坦格利安家族的兴衰史。", "vod_play_from": "测试源", "vod_play_url": "第01集$https://example.com/drama3e01.mp4#第02集$https://example.com/drama3e02.mp4"},
        
        # 综艺 (type_id=3)
        {"vod_id": 3001, "vod_name": "奔跑吧第十季", "type_id": 3, "type_name": "综艺", "vod_pic": "https://via.placeholder.com/300x450.png?text=Variety1", "vod_remarks": "更新至第5期", "vod_year": "2026", "vod_area": "大陆", "vod_actor": "李晨,Angelababy,郑恺", "vod_director": "", "vod_content": "跑男团继续带来欢乐。", "vod_play_from": "测试源", "vod_play_url": "第01期$https://example.com/variety1e01.mp4#第02期$https://example.com/variety1e02.mp4"},
        {"vod_id": 3002, "vod_name": "极限挑战第九季", "type_id": 3, "type_name": "综艺", "vod_pic": "https://via.placeholder.com/300x450.png?text=Variety2", "vod_remarks": "更新至第6期", "vod_year": "2026", "vod_area": "大陆", "vod_actor": "黄磊,孙红雷,黄渤", "vod_director": "", "vod_content": "极挑团的全新冒险。", "vod_play_from": "测试源", "vod_play_url": "第01期$https://example.com/variety2e01.mp4"},
        
        # 动漫 (type_id=4)
        {"vod_id": 4001, "vod_name": "斗罗大陆第二季", "type_id": 4, "type_name": "动漫", "vod_pic": "https://via.placeholder.com/300x450.png?text=Anime1", "vod_remarks": "更新至第50集", "vod_year": "2026", "vod_area": "大陆", "vod_actor": "", "vod_director": "", "vod_content": "唐三的修炼之路继续。", "vod_play_from": "测试源", "vod_play_url": "第01集$https://example.com/anime1e01.mp4#第02集$https://example.com/anime1e02.mp4"},
        {"vod_id": 4002, "vod_name": "海贼王", "type_id": 4, "type_name": "动漫", "vod_pic": "https://via.placeholder.com/300x450.png?text=Anime2", "vod_remarks": "更新至第1100集", "vod_year": "2026", "vod_area": "日本", "vod_actor": "", "vod_director": "", "vod_content": "路飞的海贼王之路。", "vod_play_from": "测试源", "vod_play_url": "第1098集$https://example.com/anime2e1098.mp4#第1099集$https://example.com/anime2e1099.mp4#第1100集$https://example.com/anime2e1100.mp4"},
    ]
    
    # 根据分类ID过滤
    if type_id:
        filtered_movies = [m for m in mock_movies_db if m['type_id'] == int(type_id)]
    else:
        filtered_movies = mock_movies_db
    
    # 分页
    page_size = 20
    start_idx = (int(page) - 1) * page_size
    end_idx = start_idx + page_size
    paginated_movies = filtered_movies[start_idx:end_idx]
    
    return paginated_movies


def register_routes(app):
    """注册所有路由"""
    
    @app.route('/')
    def index():
        """首页信息"""
        return jsonify({
            'name': 'TVBox Source Studio',
            'version': '1.0.0',
            'description': 'TVBox源聚合服务',
            'endpoints': {
                'tvbox_config': '/api/tvbox/config',
                'iptv_m3u': '/iptv/live.m3u',
                'iptv_txt': '/iptv/live.txt',
                'epg_xml': '/epg/epg.xml',
                'sources_list': '/api/sources',
                'health': '/api/health'
            }
        })
    
    @app.route('/api/health')
    def health_check():
        """健康检查"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat()
        })
    
    @app.route('/api/tvbox/config')
    def tvbox_config():
        """TVBox配置接口 - 返回JSON格式配置"""
        try:
            config = generate_tvbox_config()
            return jsonify(config)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/iptv/live.m3u')
    def iptv_m3u():
        """M3U格式的直播源"""
        try:
            m3u_content = generate_m3u_playlist()
            return Response(
                m3u_content,
                mimetype='application/x-mpegURL',
                headers={'Content-Disposition': 'attachment; filename=live.m3u'}
            )
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/iptv/live.txt')
    def iptv_txt():
        """TXT格式的直播源（TVBox传统格式）"""
        try:
            txt_content = generate_txt_playlist()
            return Response(
                txt_content,
                mimetype='text/plain',
                headers={'Content-Disposition': 'attachment; filename=live.txt'}
            )
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/epg/epg.xml')
    def epg_xml():
        """EPG节目单XML - 完全忽略查询参数，快速返回完整节目单"""
        try:
            from src.tasks.epg_manager import EPGManager
            epg_manager = EPGManager()
            
            xml_content = epg_manager.get_epg_xml()
            
            if not xml_content or '<?xml' not in xml_content:
                from src.tasks.source_collector import SourceCollector
                collector = SourceCollector()
                channels = collector.get_live_channels()
                xml_content = epg_manager.generate_epg_for_channels(channels)
            
            return Response(
                xml_content,
                mimetype='application/xml',
                headers={'Content-Disposition': 'attachment; filename=epg.xml'}
            )
        except Exception as e:
            logger.error(f"EPG服务错误: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/sources')
    def sources_list():
        """获取所有源的列表"""
        try:
            from src.tasks.source_collector import SourceCollector
            collector = SourceCollector()
            sources = collector.get_all_sources()
            return jsonify({
                'total': len(sources),
                'sources': sources
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/sources/refresh', methods=['POST'])
    def refresh_sources():
        """手动刷新源"""
        try:
            from src.tasks.source_collector import SourceCollector
            collector = SourceCollector()
            result = collector.collect_all_sources()
            return jsonify({
                'status': 'success',
                'message': '源刷新成功',
                'result': result
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/vod/<path:filename>')
    def vod_files(filename):
        """点播配置文件"""
        try:
            output_dir = os.path.join(project_root, 'data', 'output')
            file_path = os.path.join(output_dir, filename)
            
            if os.path.exists(file_path):
                return send_file(file_path)
            else:
                return jsonify({'error': '文件不存在'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/iptv/<path:filename>')
    def iptv_files(filename):
        """IPTV文件"""
        try:
            output_dir = os.path.join(project_root, 'data', 'output')
            file_path = os.path.join(output_dir, filename)
            
            if os.path.exists(file_path):
                return send_file(file_path)
            else:
                return jsonify({'error': '文件不存在'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/epg/<path:filename>')
    def epg_files(filename):
        """EPG文件"""
        try:
            output_dir = os.path.join(project_root, 'data', 'output')
            file_path = os.path.join(output_dir, filename)
            
            if os.path.exists(file_path):
                return send_file(file_path)
            else:
                return jsonify({'error': '文件不存在'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/maccms/vod')
    def maccms_api():
        """
        MacCMS API聚合服务
        
        从多个外部MacCMS API源聚合数据,提供故障转移。
        
        参数说明：
        - ac: 动作类型 (list=列表, detail=详情)
        - t: 分类ID
        - pg: 页码
        - wd: 搜索关键词
        - ids: 视频ID列表（逗号分隔）
        - h: 几小时内的数据
        """
        try:
            from flask import request
            import requests as req
            
            action = request.args.get('ac', 'list')
            page = int(request.args.get('pg', 1))
            type_id = request.args.get('t', '')
            keyword = request.args.get('wd', '')
            ids = request.args.get('ids', '')
            hours = request.args.get('h', '')
            
            logger.info(f"MacCMS API请求: ac={action}, t={type_id}, pg={page}, wd={keyword}")
            
            # ========== 分类列表 ==========
            if action == 'list' and not type_id and not keyword and not ids:
                classes = [
                    {"type_id": 1, "type_name": "电影"},
                    {"type_id": 2, "type_name": "电视剧"},
                    {"type_id": 3, "type_name": "综艺"},
                    {"type_id": 4, "type_name": "动漫"},
                    {"type_id": 5, "type_name": "纪录片"},
                    {"type_id": 6, "type_name": "短剧"}
                ]
                
                return jsonify({
                    "code": 1,
                    "msg": "数据列表",
                    "page": 1,
                    "pagecount": 1,
                    "limit": 20,
                    "total": len(classes),
                    "list": [],
                    "class": classes
                })
            
            # ========== 影片列表/搜索 ==========
            # 使用新添加的可用MacCMS API源
            api_sources = [
                "https://www.hongniuzy2.com/api.php/provide/vod/",
                "https://www.feisuzyapi.com/api.php/provide/vod/",
                "https://cj.lziapi.com/api.php/provide/vod/",
                "http://cj.ffzyapi.com/api.php/provide/vod/",
                "https://collect.wolongzyw.com/api.php/provide/vod/",
            ]
            
            params = {
                'ac': action,
                'pg': page,
                'pagesize': 20
            }
            
            if type_id:
                params['t'] = type_id
            if keyword:
                params['wd'] = keyword
            if ids:
                params['ids'] = ids
            if hours:
                params['h'] = hours
            
            # 尝试从多个源获取数据
            for source_url in api_sources:
                try:
                    response = req.get(source_url, params=params, timeout=8)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if data.get('code') == 1 and data.get('list'):
                            logger.info(f"[SUCCESS] 从 {source_url} 获取 {len(data['list'])} 条数据")
                            return jsonify(data)
                            
                except Exception as e:
                    logger.warning(f"源失败 [{source_url}]: {e}")
                    continue
            
            # 所有源都失败
            logger.error("所有MacCMS API源均失败")
            return jsonify({
                "code": 0,
                "msg": "所有数据源暂时不可用,请稍后重试",
                "list": []
            })
                
        except Exception as e:
            logger.error(f"MacCMS API错误: {e}", exc_info=True)
            return jsonify({
                "code": 0,
                "msg": f"服务器错误: {str(e)}",
                "list": []
            }), 500
    
    @app.route('/api/k1k/vod')
    def k1k_api():
        """
        k1k.cc网站数据代理 - 将网页数据转换为MacCMS API格式
        
        注意：此接口仅供个人学习研究使用，请遵守robots.txt协议
        """
        try:
            from flask import request
            from tools.k1k_adapter import K1KAdapter
            
            action = request.args.get('ac', 'list')
            page = int(request.args.get('pg', 1))
            type_id = request.args.get('t', '')
            keyword = request.args.get('wd', '')
            ids = request.args.get('ids', '')
            
            logger.info(f"k1k API请求: ac={action}, t={type_id}, pg={page}, wd={keyword}")
            
            # 创建适配器实例
            adapter = K1KAdapter()
            
            # ========== 分类列表 ==========
            if action == 'list' and not type_id and not keyword and not ids:
                classes = adapter.get_categories()
                
                return jsonify({
                    "code": 1,
                    "msg": "数据列表",
                    "page": 1,
                    "pagecount": 1,
                    "limit": 20,
                    "total": len(classes),
                    "list": [],
                    "class": classes
                })
            
            # ========== 影片列表（按分类或搜索）==========
            elif action == 'list':
                # 生成缓存键
                cache_key = f"k1k_list_t{type_id}_pg{page}"
                
                # 1. 尝试从缓存获取
                cached_data = get_cached_response(cache_key)
                if cached_data:
                    logger.info(f"[CACHE HIT] 使用k1k缓存数据: {cache_key}")
                    return jsonify(cached_data)
                
                # 2. 缓存未命中，爬取网页
                type_id_int = int(type_id) if type_id else 1
                
                # 限制分类范围（k1k只有4个分类）
                if type_id_int > 4:
                    type_id_int = 1
                
                result = adapter.get_movie_list(
                    type_id=type_id_int,
                    page=page,
                    pagesize=20
                )
                
                # 3. 保存到缓存（k1k数据缓存时间较短，因为网页可能频繁更新）
                set_cached_response(cache_key, result, ttl=1800)  # 30分钟
                
                return jsonify(result)
            
            # ========== 影片详情 ==========
            elif action == 'detail':
                # 生成缓存键
                cache_key = f"k1k_detail_{ids}"
                
                # 1. 尝试从缓存获取
                cached_data = get_cached_response(cache_key)
                if cached_data:
                    logger.info(f"[CACHE HIT] 使用k1k详情缓存: {cache_key}")
                    return jsonify(cached_data)
                
                # 2. 缓存未命中，爬取详情页
                vod_id = ids.split(',')[0] if ',' in ids else ids
                result = adapter.get_movie_detail(vod_id)
                
                # 3. 保存到缓存（详情数据缓存时间较长）
                set_cached_response(cache_key, result, ttl=3600)  # 1小时
                
                return jsonify(result)
            
            # ========== 未知动作 ==========
            else:
                return jsonify({
                    "code": 0,
                    "msg": f"不支持的动作: {action}",
                    "page": 0,
                    "pagecount": 0,
                    "limit": 0,
                    "total": 0,
                    "list": []
                })
        
        except Exception as e:
            logger.error(f"k1k API错误: {e}", exc_info=True)
            return jsonify({
                "code": 0,
                "msg": f"服务器错误: {str(e)}",
                "page": 0,
                "pagecount": 0,
                "limit": 0,
                "total": 0,
                "list": []
            }), 500


    @app.route('/api/cache/info')
    def cache_info():
        """查看缓存统计信息"""
        try:
            conn = sqlite3.connect(CACHE_DB_PATH)
            cursor = conn.cursor()
            
            # 总缓存数
            cursor.execute('SELECT COUNT(*) FROM api_cache')
            total_count = cursor.fetchone()[0]
            
            # 有效缓存数
            cursor.execute('SELECT COUNT(*) FROM api_cache WHERE expires_at > CURRENT_TIMESTAMP')
            valid_count = cursor.fetchone()[0]
            
            # 过期缓存数
            expired_count = total_count - valid_count
            
            # 总命中次数
            cursor.execute('SELECT COALESCE(SUM(hit_count), 0) FROM api_cache')
            total_hits = cursor.fetchone()[0]
            
            # 数据库文件大小
            db_size = os.path.getsize(CACHE_DB_PATH) if os.path.exists(CACHE_DB_PATH) else 0
            
            conn.close()
            
            return jsonify({
                "status": "success",
                "cache_db": CACHE_DB_PATH,
                "db_size_mb": round(db_size / 1024 / 1024, 2),
                "total_entries": total_count,
                "valid_entries": valid_count,
                "expired_entries": expired_count,
                "total_hits": total_hits,
                "hit_rate": f"{total_hits/(total_hits + max(1, total_count-valid_count))*100:.1f}%" if total_count > 0 else "0%"
            })
        
        except Exception as e:
            logger.error(f"缓存信息查询失败: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/cache/cleanup', methods=['POST'])
    def cache_cleanup():
        """手动清理过期缓存"""
        try:
            cleanup_expired_cache()
            
            conn = sqlite3.connect(CACHE_DB_PATH)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM api_cache')
            remaining = cursor.fetchone()[0]
            conn.close()
            
            return jsonify({
                "status": "success",
                "message": "过期缓存已清理",
                "remaining_entries": remaining
            })
        
        except Exception as e:
            logger.error(f"缓存清理失败: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/cache/clear', methods=['POST'])
    def cache_clear():
        """清空所有缓存（包括未过期的）"""
        try:
            conn = sqlite3.connect(CACHE_DB_PATH)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM api_cache')
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"[CLEANUP] 清空了 {deleted} 条缓存")
            
            return jsonify({
                "status": "success",
                "message": f"已清空 {deleted} 条缓存",
                "deleted_entries": deleted
            })
        
        except Exception as e:
            logger.error(f"缓存清空失败: {e}")
            return jsonify({"error": str(e)}), 500


def generate_tvbox_config():
    """生成TVBox配置JSON - 使用自制MacCMS API聚合服务"""
    from src.tasks.source_collector import SourceCollector
    
    collector = SourceCollector()
    
    # 获取基础URL
    # 优先使用环境变量 EXTERNAL_HOST，否则使用请求的host
    external_host = os.environ.get('EXTERNAL_HOST', '')
    if external_host:
        host = external_host.rstrip('/')
        logger.info(f"使用外部配置的HOST: {host}")
    else:
        host = request.host_url.rstrip('/')
        logger.warning(f"使用请求HOST（可能不适用于TVBox）: {host}")
        logger.warning("提示: 如需正确配置TVBox，请设置环境变量 EXTERNAL_HOST=http://192.168.0.88:8080")
    
    logger.info("生成TVBox配置（使用自制MacCMS API）...")
    
    # ========== 从SourceManager加载所有启用的数据源 ==========
    from src.core import SourceManager
    source_manager = SourceManager("data/sources/source_config.json")
    
    video_sites = []
    
    # 为每个启用的数据源生成TVBox站点配置
    for name, source_config in source_manager.sources.items():
        try:
            if source_config.type == 0 or source_config.type == 1:
                # MacCMS API类型
                video_sites.append({
                    "key": f"tvsource_{name.replace(' ', '_')}",
                    "name": f"🎬 {name}",
                    "type": 1,  # Type 1 = MacCMS API
                    "api": source_config.api,
                    "searchable": 1,
                    "quickSearch": 1,
                    "filterable": 1,
                    "changeable": 1
                })
            elif source_config.type == 2:
                # XBPQ规则引擎 - 通过我们的代理API访问
                video_sites.append({
                    "key": f"tvsource_xbpq_{name.replace(' ', '_')}",
                    "name": f"📜 {name}(XBPQ)",
                    "type": 1,  # 仍然使用Type 1,通过我们的API代理
                    "api": f"{host}/api/vod",  # 使用新的统一API
                    "searchable": 1,
                    "quickSearch": 0,
                    "filterable": 0,
                    "changeable": 1,
                    "ext": source_config.ext  # XBPQ规则文件路径
                })
            elif source_config.type == 3:
                # DRPY2 JS脚本
                video_sites.append({
                    "key": f"tvsource_drpy2_{name.replace(' ', '_')}",
                    "name": f"⚙️ {name}(DRPY2)",
                    "type": 3,  # Type 3 = JS脚本
                    "api": f"{host}/api/vod",  # 通过我们的API代理
                    "searchable": 1,
                    "quickSearch": 0,
                    "filterable": 0,
                    "changeable": 1,
                    "ext": source_config.api  # JS文件路径
                })
        except Exception as e:
            logger.warning(f"跳过数据源 [{name}]: {e}")
    
    # 如果没有任何数据源,至少保留聚合API
    if not video_sites:
        video_sites.append({
            "key": "tvsource_vod",
            "name": "🎬 TVSOURCE聚合",
            "type": 1,
            "api": f"{host}/api/maccms/vod",
            "searchable": 1,
            "quickSearch": 1,
            "filterable": 1,
            "changeable": 1
        })
    
    logger.info(f"✓ 配置站点数: {len(video_sites)} (从SourceManager加载)")
    
    # 构建直播配置（使用我们自己的服务）
    live_channels = collector.get_live_channels()
    live_config = []
    
    if live_channels:
        live_config = [
            {
                "name": "📺 TVSOURCE直播",
                "type": 0,
                "url": f"{host}/iptv/live.m3u",
                "playerType": 2,
                "epg": f"{host}/epg/epg.xml",
                "logo": "https://epg.112114.xyz/logo/{{name}}.png"
            }
        ]
    
    # 构建解析配置
    parse_config = [
        {
            "name": "聚合解析",
            "type": 3,
            "url": "Demo"
        },
        {
            "name": "Web解析",
            "type": 0,
            "url": "https://jx.xmflv.com/?url="
        }
    ]
    
    # 构建完整配置
    config = {
        "wallpaper": "https://bing.img.run/uhd.php",
        "homepage": "https://github.com/CatVodTVOfficial/TVBoxOSC",
        "warningText": "请勿相信视频中的广告，如有卡顿请切换线路或数据源",
        
        # 关键：不再需要spider字段！
        # 因为我们使用的是Type 1 MacCMS API，不需要jar包
        
        # 使用自制的MacCMS API站点
        "sites": video_sites,
        
        "lives": live_config,
        "parses": parse_config,
        "flags": [
            "youku",
            "qq",
            "iqiyi",
            "qiyi",
            "letv",
            "sohu",
            "tudou",
            "pptv",
            "mgtv",
            "wasu",
            "bilibili",
            "renrenmi"
        ],
        "ijk": [
            {
                "group": "软解码",
                "options": [
                    {"category": 4, "name": "opensles", "value": "0"},
                    {"category": 4, "name": "overlay-format", "value": "842225234"},
                    {"category": 4, "name": "framedrop", "value": "1"},
                    {"category": 4, "name": "soundtouch", "value": "1"},
                    {"category": 4, "name": "start-on-prepared", "value": "1"},
                    {"category": 1, "name": "http-detect-range-support", "value": "0"},
                    {"category": 1, "name": "fflags", "value": "fastseek"},
                    {"category": 2, "name": "skip_loop_filter", "value": "48"},
                    {"category": 4, "name": "reconnect", "value": "1"},
                    {"category": 4, "name": "enable-accurate-seek", "value": "0"},
                    {"category": 4, "name": "mediacodec", "value": "0"},
                    {"category": 4, "name": "mediacodec-auto-rotate", "value": "0"},
                    {"category": 4, "name": "mediacodec-handle-resolution-change", "value": "0"},
                    {"category": 4, "name": "mediacodec-hevc", "value": "0"},
                    {"category": 1, "name": "dns_cache_timeout", "value": "600000000"}
                ]
            }
        ],
        "ads": [
            "mimg.0c1q0l.cn",
            "www.googletagmanager.com",
            "www.google-analytics.com"
        ]
    }
    
    logger.info(f"配置生成完成: {len(video_sites)}个站点, {len(live_config)}个直播源")
    return config


def generate_m3u_playlist():
    """生成M3U播放列表 - 支持EPG节目单和回看功能"""
    from src.tasks.source_collector import SourceCollector
    
    collector = SourceCollector()
    channels = collector.get_live_channels()
    
    m3u_lines = [
        '#EXTM3U x-tvg-url="http://epg.112114.xyz/pp.xml"',
        ''
    ]
    
    for channel in channels:
        if channel.get('valid', True):
            name = channel.get('name', '未知频道')
            url = channel.get('url', '')
            group = channel.get('group', '默认')
            logo = channel.get('logo', '')
            
            # 生成tvg-id（用于EPG匹配）
            tvg_id = name.replace(' ', '').replace('-', '').upper()
            
            # 构建EXTINF行，包含EPG和回看支持
            extinf = (
                f'#EXTINF:-1 '
                f'tvg-id="{tvg_id}" '
                f'tvg-name="{name}" '
                f'tvg-logo="{logo}" '
                f'group-title="{group}" '
                f'catchup="default" '
                f'catchup-days="7" '
                f'timeshift="1",'
                f'{name}'
            )
            m3u_lines.append(extinf)
            m3u_lines.append(url)
    
    return '\n'.join(m3u_lines)


def generate_txt_playlist():
    """生成TXT播放列表（TVBox传统格式）- 简洁格式"""
    from src.tasks.source_collector import SourceCollector
    
    collector = SourceCollector()
    channels = collector.get_live_channels()
    
    # 按分组整理
    groups = {}
    for channel in channels:
        if channel.get('valid', True):
            # 清理URL，移除可能导致解析失败的特殊字符
            url = channel.get('url', '').strip()
            if not url or url.startswith('#'):
                continue
            
            group = channel.get('group', '默认')
            if group not in groups:
                groups[group] = []
            groups[group].append({
                'name': channel.get('name', '未知频道'),
                'url': url
            })
    
    lines = []
    for group_name, group_channels in groups.items():
        if not group_channels:
            continue
        lines.append(f'{group_name},#genre#')
        for channel in group_channels:
            name = channel['name']
            url = channel['url']
            # 确保格式正确：名称,URL
            lines.append(f'{name},{url}')
        lines.append('')
    
    return '\n'.join(lines)
