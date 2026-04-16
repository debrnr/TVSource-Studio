"""
配置管理Web界面路由

提供数据源配置的可视化管理:
- 查看/添加/编辑/删除数据源
- 健康检查
- 统计信息展示
"""

import logging
from flask import Blueprint, render_template, jsonify, request
from .core import SourceManager

logger = logging.getLogger(__name__)

# 创建Blueprint
config_bp = Blueprint('config', __name__, url_prefix='/admin')

# 全局管理器实例
source_manager = None


def init_config_routes(manager: SourceManager):
    """
    初始化配置管理路由
    
    Args:
        manager: SourceManager实例
    """
    global source_manager
    source_manager = manager
    logger.info("✓ 配置管理路由初始化完成")


@config_bp.route('/')
def admin_dashboard():
    """管理后台首页"""
    return render_template('admin/dashboard.html')


@config_bp.route('/api/sources', methods=['GET'])
def get_sources():
    """获取所有数据源列表"""
    try:
        sources = []
        for name, config in source_manager.sources.items():
            sources.append({
                'name': config.name,
                'type': config.type,
                'api': config.api,
                'enabled': config.enabled,
                'timeout': config.timeout
            })
        
        stats = source_manager.get_stats()
        
        return jsonify({
            'code': 1,
            'msg': 'success',
            'data': {
                'sources': sources,
                'stats': stats
            }
        })
    except Exception as e:
        logger.error(f"获取数据源列表失败: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500


@config_bp.route('/api/sources', methods=['POST'])
def add_source():
    """添加新数据源"""
    try:
        data = request.json
        
        # 验证必填字段
        if not data.get('name'):
            return jsonify({'code': 0, 'msg': '缺少name字段'}), 400
        
        if 'type' not in data:
            return jsonify({'code': 0, 'msg': '缺少type字段'}), 400
        
        # 添加数据源
        source_manager.add_source(data)
        
        return jsonify({
            'code': 1,
            'msg': '添加成功',
            'data': {'name': data['name']}
        })
    except Exception as e:
        logger.error(f"添加数据源失败: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500


@config_bp.route('/api/sources/<source_name>', methods=['DELETE'])
def delete_source(source_name):
    """删除数据源"""
    try:
        source_manager.remove_source(source_name)
        
        return jsonify({
            'code': 1,
            'msg': '删除成功'
        })
    except Exception as e:
        logger.error(f"删除数据源失败: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500


@config_bp.route('/api/sources/<source_name>/toggle', methods=['POST'])
def toggle_source(source_name):
    """启用/禁用数据源"""
    try:
        if source_name not in source_manager.sources:
            return jsonify({'code': 0, 'msg': '数据源不存在'}), 404
        
        config = source_manager.sources[source_name]
        config.enabled = not config.enabled
        
        # 保存配置
        source_manager.save_config()
        
        # 清除缓存
        source_manager.clear_cache(source_name)
        
        return jsonify({
            'code': 1,
            'msg': 'success',
            'data': {
                'name': source_name,
                'enabled': config.enabled
            }
        })
    except Exception as e:
        logger.error(f"切换数据源状态失败: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500


@config_bp.route('/api/health', methods=['GET'])
async def check_health():
    """健康检查所有数据源"""
    try:
        results = {}
        
        for name in source_manager.sources.keys():
            is_healthy = await source_manager.health_check(name)
            results[name] = {
                'status': 'healthy' if is_healthy else 'unhealthy',
                'enabled': source_manager.sources[name].enabled
            }
        
        return jsonify({
            'code': 1,
            'msg': 'success',
            'data': results
        })
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500


@config_bp.route('/api/stats', methods=['GET'])
def get_stats():
    """获取统计信息"""
    try:
        stats = source_manager.get_stats()
        
        # 添加熔断器统计
        circuit_stats = {}
        for name, adapter in source_manager.adapters.items():
            if hasattr(adapter, 'http_client'):
                cb_stats = adapter.http_client.get_stats()
                circuit_stats[name] = cb_stats
        
        stats['circuit_breakers'] = circuit_stats
        
        return jsonify({
            'code': 1,
            'msg': 'success',
            'data': stats
        })
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500


@config_bp.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """清除所有缓存"""
    try:
        source_manager.clear_cache()
        
        return jsonify({
            'code': 1,
            'msg': '缓存已清除'
        })
    except Exception as e:
        logger.error(f"清除缓存失败: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500
