"""
Source Collector - Collect video and live sources from the internet
"""

import os
import json
import requests
from datetime import datetime
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class SourceCollector:
    """Source collector class"""
    
    def __init__(self):
        # 获取项目根目录（src/tasks的祖父目录）
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        self.sources_dir = os.path.join(project_root, 'data', 'sources')
        self.output_dir = os.path.join(project_root, 'data', 'output')
        self.timeout = int(os.getenv('SOURCE_TIMEOUT', '10'))
        self.max_retry = int(os.getenv('MAX_RETRY', '2'))
        
        # GitHub proxy list (sorted by priority)
        self.github_proxies = [
            'https://ghfast.top',  # Currently available
            'https://ghproxy.net',
            'https://gh-proxy.com',
            'https://mirror.ghproxy.com',
        ]
        
        # Raw GitHub source URLs
        raw_github_sources = {
            'video': [
                'https://raw.githubusercontent.com/FongMi/Release/main/api.json',
                'https://raw.githubusercontent.com/gaotianliuyun/gao/master/api.json',
                'https://raw.githubusercontent.com/CatVodTVOfficial/TVBoxOSC/master/api.json',
                'https://raw.githubusercontent.com/qist/tvbox/master/json/config.json',
            ],
            'live': [
                # GitHub high-quality live sources
                'https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/ipv6.m3u',
                'https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/ipv4.m3u',
                'https://raw.githubusercontent.com/YueChan/Live/main/APTV.m3u',
                'https://raw.githubusercontent.com/YueChan/Live/main/IPTV.m3u',
                'https://raw.githubusercontent.com/vbskycn/iptv/master/tv/iptv4.m3u',
                'https://raw.githubusercontent.com/vbskycn/iptv/master/tv/iptv6.m3u',
                'https://raw.githubusercontent.com/wwb521/live/main/tv.m3u',
                'https://raw.githubusercontent.com/0047ol/China-TV-Live-M3U8/main/China-TV.m3u',
                'https://raw.githubusercontent.com/suxuang/myIPTV/main/ipv4.m3u',
                'https://raw.githubusercontent.com/lylehust/Chinese-IPTV/master/TV-SXYD.m3u',
                # iptv-org global sources
                'https://iptv-org.github.io/iptv/countries/cn.m3u',
                'https://iptv-org.github.io/iptv/index.m3u',
            ],
            'epg': [
                'https://raw.githubusercontent.com/fanmingming/live/main/e.xml',
            ]
        }
        
        # 主流平台免费资源（B站、爱奇艺、优酷、腾讯等）
        mainstream_platforms = [
            {
                "key": "bili",
                "name": "🅱️ B站视频",
                "type": 3,
                "api": "csp_Bili",
                "searchable": 1,
                "quickSearch": 1,
                "changeable": 0,
                "ext": "https://gh-proxy.com/https://raw.githubusercontent.com/FongMi/TV/release/json/bili.json"
            },
            {
                "key": "iqiyi",
                "name": "🥝 爱奇艺",
                "type": 3,
                "api": "csp_IQIYI",
                "searchable": 1,
                "quickSearch": 1,
                "changeable": 0
            },
            {
                "key": "youku",
                "name": "👑 优酷",
                "type": 3,
                "api": "csp_Youku",
                "searchable": 1,
                "quickSearch": 1,
                "changeable": 0
            },
            {
                "key": "qq",
                "name": "🐧 腾讯视频",
                "type": 3,
                "api": "csp_QQ",
                "searchable": 1,
                "quickSearch": 1,
                "changeable": 0
            },
            {
                "key": "mgtv",
                "name": "📺 芒果TV",
                "type": 3,
                "api": "csp_MGTV",
                "searchable": 1,
                "quickSearch": 1,
                "changeable": 0
            },
            {
                "key": "cntv",
                "name": "📡 央视影音",
                "type": 3,
                "api": "csp_Cntv",
                "searchable": 1,
                "quickSearch": 1,
                "changeable": 0
            }
        ]
        
        # Domestically accessible sources (no GitHub proxy)
        domestic_sources = {
            'live': [
                # Domestically maintained live sources
                'https://live.zbds.top/tv/iptv4.txt',
                'https://live.zbds.top/tv/iptv4.m3u',
                'https://live.freetv.top/huyayqk.m3u',
                'https://live.freetv.top/douyuyqk.m3u',
                # Gitee sources (fast access in China)
                'https://gitee.com/boydqz/iptv-source/raw/master/cn.m3u',
                'https://gitee.com/boydqz/iptv-source/raw/master/iptv-all.m3u',
                'https://gitee.com/boydqz/iptv-source/raw/master/IPTV.m3u',
                # ⭐ Latest hotel source project in 2026
                'https://gitee.com/wangyaning001_admin/tv/raw/master/tv.txt',
                'https://gitee.com/wangyaning001_admin/tv/raw/master/tv.m3u',
            ],
            'epg': [
                'https://epg.112114.xyz/pp.xml',
                'https://epg.v1.mk/fy.xml',
                'https://epg.cdsb.net/epg.xml',
            ]
        }
        
        # Build URL list with proxies
        self.source_urls = {
            'video': [],
            'live': [],
            'epg': []
        }
        
        # Add proxy versions for each raw URL
        for source_type, urls in raw_github_sources.items():
            # First try direct access (if network is normal)
            self.source_urls[source_type].extend(urls)
            
            # Then add proxy versions
            for url in urls:
                for proxy in self.github_proxies:
                    # Convert URL format: raw.githubusercontent.com -> proxy/raw.githubusercontent.com
                    if 'raw.githubusercontent.com' in url:
                        proxy_url = url.replace('https://raw.githubusercontent.com', f'{proxy}/https://raw.githubusercontent.com')
                        self.source_urls[source_type].append(proxy_url)
        
        # Add domestic sources
        for source_type, urls in domestic_sources.items():
            self.source_urls[source_type].extend(urls)

    def collect_all_sources(self):
        """Collect all types of sources"""
        logger.info("Starting source collection...")
        
        result = {
            'video_sources': 0,
            'live_channels': 0,
            'epg_sources': 0,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Collect video sources
            video_count = self.collect_video_sources()
            result['video_sources'] = video_count
            
            # Collect live sources
            live_count = self.collect_live_sources()
            result['live_channels'] = live_count
            
            # Collect EPG
            epg_count = self.collect_epg_sources()
            result['epg_sources'] = epg_count
            
            # Save collection status
            self.save_collection_status(result)
            
            logger.info(f"Source collection completed: Video sources={video_count}, Live channels={live_count}, EPG={epg_count}")
            return result
            
        except Exception as e:
            logger.error(f"Source collection failed: {str(e)}", exc_info=True)
            return result
    
    def collect_video_sources(self):
        """Collect video on-demand sources"""
        logger.info("Collecting video sources...")
        valid_sources = []
        
        for url in self.source_urls['video']:
            try:
                logger.info(f"Attempting to get video source: {url}")
                response = requests.get(url, timeout=self.timeout)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if 'sites' in data:
                            for site in data['sites']:
                                source = {
                                    'name': site.get('name', ''),
                                    'type': site.get('type', 0),
                                    'api': site.get('api', ''),
                                    'url': site.get('api', ''),
                                    'searchable': site.get('searchable', 0),
                                    'source_url': url,
                                    'collected_at': datetime.now().isoformat(),
                                    'valid': True
                                }
                                valid_sources.append(source)
                    except json.JSONDecodeError:
                        logger.warning(f"JSON decoding failed: {url}")
                else:
                    logger.warning(f"HTTP {response.status_code}: {url}")
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed {url}: {str(e)}")
                continue
        
        # Save video sources
        self.save_sources('video_sources.json', valid_sources)
        logger.info(f"Collected {len(valid_sources)} video sources")
        return len(valid_sources)
    
    def collect_live_sources(self):
        """Collect live sources"""
        logger.info("Collecting live sources...")
        all_channels = []
        
        for url in self.source_urls['live']:
            try:
                logger.info(f"Attempting to get live source: {url}")
                response = requests.get(url, timeout=self.timeout)
                
                if response.status_code == 200:
                    content = response.text
                    
                    # Determine if M3U or TXT format
                    if content.startswith('#EXTM3U'):
                        channels = self.parse_m3u(content, url)
                    else:
                        channels = self.parse_txt(content, url)
                    
                    all_channels.extend(channels)
                else:
                    logger.warning(f"HTTP {response.status_code}: {url}")
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed {url}: {str(e)}")
                continue
        
        # Deduplicate
        unique_channels = self.deduplicate_channels(all_channels)
        
        # Save live sources
        self.save_sources('live_channels.json', unique_channels)
        logger.info(f"Collected {len(unique_channels)} live channels")
        return len(unique_channels)
    
    def collect_epg_sources(self):
        """Collect EPG sources"""
        logger.info("Collecting EPG sources...")
        valid_epgs = []
        
        for url in self.source_urls['epg']:
            try:
                logger.info(f"Attempting to get EPG: {url}")
                response = requests.get(url, timeout=self.timeout * 2)  # EPG files are larger, increase timeout
                
                if response.status_code == 200:
                    epg = {
                        'url': url,
                        'size': len(response.content),
                        'collected_at': datetime.now().isoformat(),
                        'valid': True
                    }
                    valid_epgs.append(epg)
                    
                    # Save EPG content
                    filename = f"epg_{datetime.now().strftime('%Y%m%d')}.xml"
                    epg_path = os.path.join(self.sources_dir, filename)
                    with open(epg_path, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                else:
                    logger.warning(f"HTTP {response.status_code}: {url}")
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed {url}: {str(e)}")
                continue
        
        # Save EPG source information
        self.save_sources('epg_sources.json', valid_epgs)
        logger.info(f"Collected {len(valid_epgs)} EPG sources")
        return len(valid_epgs)
    
    def parse_m3u(self, content, source_url):
        """Parse M3U format"""
        channels = []
        lines = content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith('#EXTINF'):
                # Parse EXTINF line
                channel_info = self.parse_extinf(line)
                
                # Next line should be URL
                if i + 1 < len(lines):
                    url = lines[i + 1].strip()
                    
                    # Clean URL, remove special characters and parameters
                    url = self.clean_url(url)
                    
                    if url and not url.startswith('#'):
                        channel = {
                            'name': channel_info.get('name', 'Unknown channel'),
                            'url': url,
                            'group': channel_info.get('group', 'Default'),
                            'logo': channel_info.get('logo', ''),
                            'tvg_id': channel_info.get('tvg_id', ''),
                            'source_url': source_url,
                            'collected_at': datetime.now().isoformat(),
                            'valid': True
                        }
                        channels.append(channel)
                    i += 2
                    continue
            i += 1
        
        return channels
    
    def clean_url(self, url):
        """Clean URL, remove special characters that may cause parsing issues"""
        if not url:
            return ''
        
        # Remove comments
        if '#' in url:
            url = url.split('#')[0]
        
        # Remove trailing spaces
        url = url.strip()
        
        # Remove common special character markers (these are usually source website markers, not part of the URL)
        # Example: $LR•IPV4『线路156』
        special_markers = [
            '$LR', '$IPV4', '$IPV6', '$线路',
            '『', '』', '【', '】',
            '•', '|', '\\',
        ]
        
        for marker in special_markers:
            if marker in url:
                # If URL contains these markers, split at the marker and take the part before it
                url = url.split(marker)[0].strip()
        
        # Ensure URL is valid
        if url and not url.startswith(('http://', 'https://', 'rtmp://', 'rtsp://', 'mms://')):
            # If URL does not start with a protocol, it may not be a valid URL
            # But still return it for further validation
            pass
        
        return url
    
    def parse_extinf(self, line):
        """Parse EXTINF line"""
        info = {}
        
        # Extract name (part after comma)
        if ',' in line:
            name_part = line.split(',', 1)[1].strip()
            info['name'] = name_part
        
        # Extract attributes
        if 'tvg-name=' in line:
            info['tvg_name'] = self.extract_attribute(line, 'tvg-name')
        if 'tvg-logo=' in line:
            info['logo'] = self.extract_attribute(line, 'tvg-logo')
        if 'tvg-id=' in line:
            info['tvg_id'] = self.extract_attribute(line, 'tvg-id')
        if 'group-title=' in line:
            info['group'] = self.extract_attribute(line, 'group-title')
        
        return info
    
    def extract_attribute(self, line, attr_name):
        """Extract attribute value from EXTINF line"""
        start = line.find(f'{attr_name}="')
        if start == -1:
            return ''
        start += len(attr_name) + 2
        end = line.find('"', start)
        if end == -1:
            return ''
        return line[start:end]
    
    def parse_txt(self, content, source_url):
        """Parse TXT format (TVBox traditional format)"""
        channels = []
        lines = content.split('\n')
        current_group = 'Default'
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Check if it's a group marker
            if ',#genre#' in line:
                current_group = line.split(',')[0].strip()
                continue
            
            # Parse channel
            if ',' in line:
                parts = line.split(',', 1)
                if len(parts) == 2:
                    name = parts[0].strip()
                    url = parts[1].strip()
                    
                    # Clean URL
                    url = self.clean_url(url)
                    
                    if url:  # Only add if URL is valid
                        channel = {
                            'name': name,
                            'url': url,
                            'group': current_group,
                            'logo': '',
                            'tvg_id': '',
                            'source_url': source_url,
                            'collected_at': datetime.now().isoformat(),
                            'valid': True
                        }
                        channels.append(channel)
        
        return channels
    
    def deduplicate_channels(self, channels):
        """Deduplicate channels (based on name and URL)"""
        seen = set()
        unique = []
        
        for channel in channels:
            key = f"{channel['name']}_{channel['url']}"
            if key not in seen:
                seen.add(key)
                unique.append(channel)
        
        return unique
    
    def save_sources(self, filename, sources):
        """Save source data"""
        filepath = os.path.join(self.sources_dir, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(sources, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved source data: {filepath}")
        except Exception as e:
            logger.error(f"Failed to save source data: {str(e)}")
    
    def save_collection_status(self, status):
        """Save collection status"""
        filepath = os.path.join(self.output_dir, 'collection_status.json')
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(status, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save collection status: {str(e)}")
    
    def get_all_sources(self):
        """Get all sources"""
        sources = {
            'video': [],
            'live': [],
            'epg': []
        }
        
        # Read video sources
        video_file = os.path.join(self.sources_dir, 'video_sources.json')
        if os.path.exists(video_file):
            with open(video_file, 'r', encoding='utf-8') as f:
                sources['video'] = json.load(f)
        
        # Read live sources
        live_file = os.path.join(self.sources_dir, 'live_channels.json')
        if os.path.exists(live_file):
            with open(live_file, 'r', encoding='utf-8') as f:
                sources['live'] = json.load(f)
        
        # Read EPG sources
        epg_file = os.path.join(self.sources_dir, 'epg_sources.json')
        if os.path.exists(epg_file):
            with open(epg_file, 'r', encoding='utf-8') as f:
                sources['epg'] = json.load(f)
        
        return sources
    
    def get_video_sources(self):
        """Get video sources"""
        video_file = os.path.join(self.sources_dir, 'video_sources.json')
        if os.path.exists(video_file):
            with open(video_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def get_live_channels(self):
        """Get live channels"""
        live_file = os.path.join(self.sources_dir, 'live_channels.json')
        if os.path.exists(live_file):
            with open(live_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def get_mainstream_platforms(self):
        """获取主流平台免费资源配置（B站、爱奇艺、优酷、腾讯等）"""
        mainstream_platforms = [
            {
                "key": "bili",
                "name": "🅱️ B站视频",
                "type": 3,
                "api": "csp_Bili",
                "searchable": 1,
                "quickSearch": 1,
                "changeable": 0,
                "ext": "https://gh-proxy.com/https://raw.githubusercontent.com/FongMi/TV/release/json/bili.json"
            },
            {
                "key": "iqiyi",
                "name": "🥝 爱奇艺",
                "type": 3,
                "api": "csp_IQIYI",
                "searchable": 1,
                "quickSearch": 1,
                "changeable": 0
            },
            {
                "key": "youku",
                "name": "👑 优酷",
                "type": 3,
                "api": "csp_Youku",
                "searchable": 1,
                "quickSearch": 1,
                "changeable": 0
            },
            {
                "key": "qq",
                "name": "🐧 腾讯视频",
                "type": 3,
                "api": "csp_QQ",
                "searchable": 1,
                "quickSearch": 1,
                "changeable": 0
            },
            {
                "key": "mgtv",
                "name": "📺 芒果TV",
                "type": 3,
                "api": "csp_MGTV",
                "searchable": 1,
                "quickSearch": 1,
                "changeable": 0
            },
            {
                "key": "cntv",
                "name": "📡 央视影音",
                "type": 3,
                "api": "csp_Cntv",
                "searchable": 1,
                "quickSearch": 1,
                "changeable": 0
            }
        ]
        return mainstream_platforms
