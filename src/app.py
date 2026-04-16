"""
TVBox Source Studio - 主应用入口
TVBox源聚合服务
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载配置文件（从config目录）
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
config_dir = os.path.join(project_root, 'config')
env_file = os.path.join(config_dir, '.env')
if os.path.exists(env_file):
    load_dotenv(env_file)
else:
    # 兼容旧版本
    load_dotenv()

# 配置日志
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.getenv('LOG_FILE', './logs/tvsource.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 设置StreamHandler的编码为UTF-8
for handler in logging.root.handlers:
    if isinstance(handler, logging.StreamHandler):
        import sys
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')

logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# 全局CORS配置 (允许所有来源)
CORS(app, resources={r"/*": {"origins": "*"}})

# 导入路由和任务
from src.routes import register_routes
from src.tasks.source_collector import SourceCollector
from src.tasks.source_validator import SourceValidator
from src.tasks.epg_manager import EPGManager

# 导入新的TVBox API路由
from src.core import SourceManager
from src.tvbox_routes import tvbox_bp, init_tvbox_routes
from src.admin_routes import config_bp, init_config_routes

register_routes(app)

# 初始化数据源管理器
source_manager = SourceManager("data/sources/source_config.json")

# 注册TVBox API蓝图
app.register_blueprint(tvbox_bp)
init_tvbox_routes(source_manager)

# 注册管理后台蓝图
app.register_blueprint(config_bp)
init_config_routes(source_manager)

logger.info("✓ TVBox API蓝图已注册")
logger.info("✓ 管理后台蓝图已注册")

# 初始化任务调度器
scheduler = BackgroundScheduler()
source_collector = SourceCollector()
source_validator = SourceValidator()
epg_manager = EPGManager()


def init_directories():
    """初始化必要的目录"""
    dirs = [
        os.getenv('DATA_DIR', './data'),
        os.getenv('SOURCES_DIR', './data/sources'),
        os.getenv('OUTPUT_DIR', './data/output'),
        './logs'
    ]
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
        logger.info(f"确保目录存在: {dir_path}")


def start_scheduler():
    """启动定时任务"""
    if os.getenv('AUTO_UPDATE', 'true').lower() == 'true':
        interval = int(os.getenv('UPDATE_INTERVAL_HOURS', '6'))
        
        # 定时收集源
        scheduler.add_job(
            source_collector.collect_all_sources,
            'interval',
            hours=interval,
            id='collect_sources',
            name='收集影视源和直播源'
        )
        
        # 定时验证源
        scheduler.add_job(
            source_validator.validate_all_sources,
            'interval',
            hours=interval,
            id='validate_sources',
            name='验证源可用性'
        )
        
        # 定时更新EPG
        scheduler.add_job(
            epg_manager.update_epg,
            'interval',
            hours=12,
            id='update_epg',
            name='更新EPG节目单'
        )
        
        scheduler.start()
        logger.info(f"定时任务已启动，更新间隔: {interval}小时")


@app.before_request
def before_request():
    """请求前处理"""
    logger.info(f"收到请求: {request.method} {request.path}")


@app.after_request
def after_request(response):
    """请求后处理"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    return response


if __name__ == '__main__':
    try:
        # 初始化目录
        init_directories()
        
        # 启动定时任务（后台运行，不阻塞服务启动）
        start_scheduler()
        
        # 在后台线程中执行首次源收集
        import threading
        def initial_collect():
            try:
                logger.info("开始后台源收集...")
                source_collector.collect_all_sources()
                logger.info("后台源收集完成")
            except Exception as e:
                logger.error(f"后台源收集失败: {str(e)}")
        
        collect_thread = threading.Thread(target=initial_collect, daemon=True)
        collect_thread.start()
        
        # 启动Web服务
        host = os.getenv('HOST', '0.0.0.0')
        port = int(os.getenv('PORT', '8080'))
        logger.info(f"TVBox Source Studio 启动成功！")
        logger.info(f"访问地址: http://{host}:{port}")
        logger.info(f"TVBox配置接口: http://{host}:{port}/api/tvbox/config")
        logger.info(f"M3U直播源: http://{host}:{port}/iptv/live.m3u")
        logger.info(f"提示: 源正在后台收集中，请稍候访问...")
        
        app.run(host=host, port=port, debug=False, use_reloader=False)
        
    except KeyboardInterrupt:
        logger.info("服务停止中...")
        scheduler.shutdown()
        sys.exit(0)
    except Exception as e:
        logger.error(f"服务启动失败: {str(e)}", exc_info=True)
        sys.exit(1)
