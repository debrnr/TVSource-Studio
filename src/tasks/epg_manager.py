"""
EPG Manager - Manage Electronic Program Guide
"""

import os
import json
import requests
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class EPGManager:
    """EPG manager class"""
    
    def __init__(self):
        # 获取项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        self.sources_dir = os.path.join(project_root, 'data', 'sources')
        self.output_dir = os.path.join(project_root, 'data', 'output')
        self.timeout = int(os.getenv('SOURCE_TIMEOUT', '5')) * 2
        
        # EPG source list
        self.epg_sources = [
            'https://epg.112114.xyz/pp.xml',
            'https://epg.v1.mk/fy.xml',
            'https://raw.githubusercontent.com/fanmingming/live/main/e.xml',
        ]
    
    def update_epg(self):
        """更新EPG数据"""
        logger.info("开始更新EPG...")
        
        result = {
            'success': False,
            'source': '',
            'size': 0,
            'timestamp': datetime.now().isoformat()
        }
        
        for url in self.epg_sources:
            try:
                logger.info(f"尝试获取EPG: {url}")
                response = requests.get(url, timeout=self.timeout)
                
                if response.status_code == 200:
                    content = response.text
                    
                    # 验证是否是有效的XML
                    if self.validate_xml(content):
                        # 保存EPG文件
                        filename = f"epg_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
                        filepath = os.path.join(self.sources_dir, filename)
                        
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        # 同时复制一份到输出目录作为当前使用的EPG
                        output_path = os.path.join(self.output_dir, 'epg.xml')
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        result['success'] = True
                        result['source'] = url
                        result['size'] = len(content)
                        
                        logger.info(f"EPG更新成功: {url}, 大小: {len(content)} bytes")
                        
                        # 清理旧的EPG文件（保留最近5个）
                        self.cleanup_old_epg_files()
                        
                        return result
                    else:
                        logger.warning(f"EPG XML格式无效: {url}")
                else:
                    logger.warning(f"HTTP {response.status_code}: {url}")
                    
            except Exception as e:
                logger.warning(f"获取EPG失败 {url}: {str(e)}")
                continue
        
        logger.error("所有EPG源都失败")
        return result
    
    def get_epg_xml(self):
        """获取当前EPG XML内容"""
        epg_file = os.path.join(self.output_dir, 'epg.xml')
        
        if os.path.exists(epg_file):
            with open(epg_file, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            # 如果没有EPG文件，返回一个最小的有效XML
            return self.generate_minimal_epg()
    
    def validate_xml(self, content):
        """简单验证XML格式"""
        try:
            # 检查是否包含基本的XML结构
            if '<?xml' in content or '<tv' in content or '<epg' in content:
                # 检查是否有闭合标签
                if '</tv>' in content or '</epg>' in content:
                    return True
            return False
        except:
            return False
    
    def generate_minimal_epg(self):
        """生成最小EPG XML（当没有可用EPG时）"""
        minimal_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<tv generator-info-name="TVBox Source Studio" generator-info-url="http://localhost:8080">
</tv>'''
        return minimal_xml
    
    def generate_epg_for_channels(self, channels):
        """为直播频道生成EPG节目单"""
        from datetime import datetime, timedelta
        
        # 当前时间
        now = datetime.now()
        
        # 生成频道ID映射
        channel_ids = {}
        for channel in channels:
            name = channel.get('name', '')
            group = channel.get('group', '')
            
            # 生成频道ID（使用tvg-id或名称）
            channel_id = channel.get('tvg_id', '').strip()
            if not channel_id:
                # 根据频道名称生成标准ID
                channel_id = name.replace(' ', '').upper()
            
            channel_ids[channel_id] = {
                'name': name,
                'display_name': name
            }
        
        # 生成EPG XML
        xml_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<tv generator-info-name="TVBox Source Studio" generator-info-url="http://localhost:8080">',
            ''
        ]
        
        # 添加频道定义
        for channel_id, info in channel_ids.items():
            xml_lines.append(f'  <channel id="{channel_id}">')
            xml_lines.append(f'    <display-name>{info["display_name"]}</display-name>')
            xml_lines.append(f'    <display-name lang="zh">{info["name"]}</display-name>')
            xml_lines.append(f'  </channel>')
        
        # 添加节目信息（为每个频道生成未来24小时的节目）
        for channel_id in channel_ids.keys():
            # 生成6个时段节目
            for i in range(6):
                start_time = now + timedelta(hours=i*4)
                end_time = start_time + timedelta(hours=4)
                
                start_str = start_time.strftime('%Y%m%d%H%M%S +0800')
                end_str = end_time.strftime('%Y%m%d%H%M%S +0800')
                
                # 节目名称
                hour = start_time.hour
                if 6 <= hour < 12:
                    program_name = "早间节目"
                elif 12 <= hour < 14:
                    program_name = "午间节目"
                elif 14 <= hour < 18:
                    program_name = "下午节目"
                elif 18 <= hour < 20:
                    program_name = "晚间新闻"
                else:
                    program_name = "夜间节目"
                
                channel_name = channel_ids[channel_id]['name']
                program_title = f"{channel_name}-{program_name}"
                
                xml_lines.append(f'  <programme start="{start_str}" stop="{end_str}" channel="{channel_id}">')
                xml_lines.append(f'    <title lang="zh">{program_title}</title>')
                xml_lines.append(f'    <desc lang="zh">{channel_name}正在播出{program_name}</desc>')
                xml_lines.append(f'    <category lang="zh">综合</category>')
                xml_lines.append(f'  </programme>')
        
        xml_lines.append('</tv>')
        
        xml_content = '\n'.join(xml_lines)
        
        # 保存生成的EPG
        output_path = os.path.join(self.output_dir, 'epg.xml')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        logger.info(f"已为 {len(channel_ids)} 个频道生成EPG节目单")
        
        return xml_content

    def cleanup_old_epg_files(self, keep_count=5):
        """清理旧的EPG文件，只保留最近的几个"""
        try:
            epg_files = []
            for filename in os.listdir(self.sources_dir):
                if filename.startswith('epg_') and filename.endswith('.xml'):
                    filepath = os.path.join(self.sources_dir, filename)
                    mtime = os.path.getmtime(filepath)
                    epg_files.append((filepath, mtime))
            
            # 按修改时间排序
            epg_files.sort(key=lambda x: x[1], reverse=True)
            
            # 删除旧文件
            for filepath, _ in epg_files[keep_count:]:
                os.remove(filepath)
                logger.info(f"删除旧EPG文件: {filepath}")
                
        except Exception as e:
            logger.error(f"清理EPG文件失败: {str(e)}")
    
    def get_epg_info(self):
        """获取EPG信息"""
        epg_file = os.path.join(self.output_dir, 'epg.xml')
        
        info = {
            'exists': False,
            'size': 0,
            'last_modified': None,
            'source': ''
        }
        
        if os.path.exists(epg_file):
            stat = os.stat(epg_file)
            info['exists'] = True
            info['size'] = stat.st_size
            info['last_modified'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
            
            # 读取源信息
            status_file = os.path.join(self.output_dir, 'collection_status.json')
            if os.path.exists(status_file):
                with open(status_file, 'r', encoding='utf-8') as f:
                    status = json.load(f)
                    info['source'] = status.get('epg_source', '')
        
        return info
