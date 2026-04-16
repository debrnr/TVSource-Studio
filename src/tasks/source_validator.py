"""
Source Validator - Validate source availability
"""

import os
import json
import requests
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class SourceValidator:
    """Source validator class"""
    
    def __init__(self):
        # 获取项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        self.sources_dir = os.path.join(project_root, 'data', 'sources')
        self.timeout = int(os.getenv('SOURCE_TIMEOUT', '5'))
        self.max_workers = 10  # Concurrent validation count
    
    def validate_all_sources(self):
        """Validate all sources"""
        logger.info("Start validating all sources...")
        
        result = {
            'video_validated': 0,
            'live_validated': 0,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Validate video sources
            video_count = self.validate_video_sources()
            result['video_validated'] = video_count
            
            # Validate live channels
            live_count = self.validate_live_channels()
            result['live_validated'] = live_count
            
            logger.info(f"Source validation completed: video sources={video_count}, live channels={live_count}")
            return result
            
        except Exception as e:
            logger.error(f"Source validation failed: {str(e)}", exc_info=True)
            return result
    
    def validate_video_sources(self):
        """Validate video sources"""
        logger.info("Validating video sources...")
        
        video_file = os.path.join(self.sources_dir, 'video_sources.json')
        if not os.path.exists(video_file):
            logger.warning("Video source file does not exist")
            return 0
        
        with open(video_file, 'r', encoding='utf-8') as f:
            sources = json.load(f)
        
        validated_count = 0
        
        # Use thread pool for concurrent validation
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_source = {
                executor.submit(self.validate_single_video_source, source): source
                for source in sources
            }
            
            for future in as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    is_valid = future.result()
                    source['valid'] = is_valid
                    source['validated_at'] = datetime.now().isoformat()
                    validated_count += 1
                except Exception as e:
                    logger.error(f"Failed to validate video source {source.get('name', '')}: {str(e)}")
                    source['valid'] = False
        
        # Save validation results
        with open(video_file, 'w', encoding='utf-8') as f:
            json.dump(sources, f, ensure_ascii=False, indent=2)
        
        valid_count = sum(1 for s in sources if s.get('valid', False))
        logger.info(f"Video source validation completed: {valid_count}/{len(sources)} valid")
        return validated_count
    
    def validate_live_channels(self):
        """Validate live channels"""
        logger.info("Validating live channels...")
        
        live_file = os.path.join(self.sources_dir, 'live_channels.json')
        if not os.path.exists(live_file):
            logger.warning("Live source file does not exist")
            return 0
        
        with open(live_file, 'r', encoding='utf-8') as f:
            channels = json.load(f)
        
        validated_count = 0
        
        # Use thread pool for concurrent validation (limit concurrency to avoid too many requests)
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_channel = {
                executor.submit(self.validate_single_channel, channel): channel
                for channel in channels[:200]  # Only validate the first 200 to avoid long processing time
            }
            
            for future in as_completed(future_to_channel):
                channel = future_to_channel[future]
                try:
                    is_valid = future.result()
                    channel['valid'] = is_valid
                    channel['validated_at'] = datetime.now().isoformat()
                    validated_count += 1
                except Exception as e:
                    logger.error(f"Failed to validate channel {channel.get('name', '')}: {str(e)}")
                    channel['valid'] = False
        
        # Save validation results
        with open(live_file, 'w', encoding='utf-8') as f:
            json.dump(channels, f, ensure_ascii=False, indent=2)
        
        valid_count = sum(1 for c in channels if c.get('valid', False))
        logger.info(f"Live channel validation completed: {valid_count}/{len(channels)} valid")
        return validated_count
    
    def validate_single_video_source(self, source):
        """Validate a single video source"""
        try:
            api_url = source.get('api', '')
            if not api_url:
                return False
            
            # Try accessing the API
            response = requests.get(api_url, timeout=self.timeout)
            
            # If the response is 200 and JSON format, consider it valid
            if response.status_code == 200:
                try:
                    response.json()
                    return True
                except:
                    return False
            return False
            
        except Exception as e:
            logger.debug(f"Failed to validate video source {source.get('name', '')}: {str(e)}")
            return False
    
    def validate_single_channel(self, channel):
        """Validate a single live channel"""
        try:
            url = channel.get('url', '')
            if not url:
                return False
            
            # For live streams, we only do a HEAD request to check if it's accessible
            # Some streams may require special handling, here we do a simple check
            response = requests.head(url, timeout=self.timeout, allow_redirects=True)
            
            # Status codes in the range 200-399 are considered valid
            return 200 <= response.status_code < 400
            
        except Exception as e:
            logger.debug(f"Failed to validate channel {channel.get('name', '')}: {str(e)}")
            return False
    
    def get_validation_report(self):
        """Get validation report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'video_sources': {},
            'live_channels': {}
        }
        
        # Count video sources
        video_file = os.path.join(self.sources_dir, 'video_sources.json')
        if os.path.exists(video_file):
            with open(video_file, 'r', encoding='utf-8') as f:
                sources = json.load(f)
                total = len(sources)
                valid = sum(1 for s in sources if s.get('valid', False))
                report['video_sources'] = {
                    'total': total,
                    'valid': valid,
                    'invalid': total - valid,
                    'valid_rate': f"{(valid/total*100) if total > 0 else 0:.1f}%"
                }
        
        # Count live channels
        live_file = os.path.join(self.sources_dir, 'live_channels.json')
        if os.path.exists(live_file):
            with open(live_file, 'r', encoding='utf-8') as f:
                channels = json.load(f)
                total = len(channels)
                valid = sum(1 for c in channels if c.get('valid', False))
                report['live_channels'] = {
                    'total': total,
                    'valid': valid,
                    'invalid': total - valid,
                    'valid_rate': f"{(valid/total*100) if total > 0 else 0:.1f}%"
                }
        
        return report
