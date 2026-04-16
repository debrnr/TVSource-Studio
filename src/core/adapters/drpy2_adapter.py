"""
DRPY2 JavaScript运行时适配器

实现Type 3 DRPY2 JS爬虫执行引擎,支持:
- 直接执行JavaScript爬虫脚本
- 提供DRPY2框架的全局API
- 异步HTTP请求支持
"""

import json
import logging
import os
import re
from typing import List, Dict, Optional, Any
from ..vod_source import (
    VodSourceAdapter,
    VodItem,
    VodDetail,
    Category,
    VodListResponse,
    VodDetailResponse,
    SourceType
)

logger = logging.getLogger(__name__)


class DRPY2Runtime:
    """
    DRPY2 JavaScript运行时环境
    
    使用PyExecJS或QuickJS执行JavaScript代码,
    模拟TVBox的DRPY2框架环境。
    """
    
    def __init__(self):
        self.ctx = None
        self.runtime_type = None
        self._init_runtime()
    
    def _init_runtime(self):
        """初始化JavaScript运行时"""
        try:
            # 尝试使用quickjs (更快,更轻量)
            import quickjs
            self.ctx = quickjs.Context()
            self.runtime_type = 'quickjs'
            logger.info("✓ 使用QuickJS运行时")
            
            # 注入全局函数
            self._inject_globals_quickjs()
            
        except ImportError:
            try:
                # 降级到execjs (需要Node.js)
                import execjs
                self.ctx = execjs.get()
                self.runtime_type = 'execjs'
                logger.info("✓ 使用ExecJS运行时 (需要Node.js)")
                
                # 注入全局函数
                self._inject_globals_execjs()
                
            except ImportError:
                raise RuntimeError(
                    "未找到JavaScript运行时环境!\n"
                    "请安装以下任一依赖:\n"
                    "1. pip install quickjs (推荐,无需Node.js)\n"
                    "2. pip install PyExecJS + 安装Node.js"
                )
    
    def _inject_globals_quickjs(self):
        """注入DRPY2全局API (QuickJS)"""
        # HTTP请求函数
        self.ctx.eval("""
        // 同步HTTP请求
        function request(url, options) {
            // QuickJS中无法直接发起HTTP请求,需要在Python层处理
            return {};
        }
        
        // fetch别名
        var fetch = request;
        
        // PDF解析函数 (Jsoup封装)
        function pdfa(html, selector) {
            // CSS选择器提取多个元素
            return [];
        }
        
        function pdfh(html, selector) {
            // CSS选择器提取单个元素
            return '';
        }
        
        // 工具函数
        function base64Encode(text) {
            return text; // 占位
        }
        
        function base64Decode(text) {
            return text; // 占位
        }
        
        function log(msg) {
            console.log(msg);
        }
        
        // URL处理
        function joinUrl(base, url) {
            if (url.startsWith('http')) return url;
            if (url.startsWith('/')) return base.replace(/\\/[^/]*$/, '') + url;
            return base + '/' + url;
        }
        """)
    
    def _inject_globals_execjs(self):
        """注入DRPY2全局API (ExecJS)"""
        # ExecJS需要通过上下文注入
        pass
    
    def execute_script(self, js_code: str, function_name: str, *args) -> Any:
        """
        执行JavaScript代码
        
        Args:
            js_code: JavaScript代码
            function_name: 要调用的函数名
            *args: 函数参数
        
        Returns:
            执行结果
        """
        try:
            if self.runtime_type == 'quickjs':
                # QuickJS执行
                self.ctx.eval(js_code)
                func = self.ctx.get(function_name)
                if callable(func):
                    result = func(*args)
                    # 转换结果为Python对象
                    return self._convert_result(result)
                else:
                    raise AttributeError(f"函数 {function_name} 不存在或不可调用")
            else:
                # ExecJS执行
                result = self.ctx.call(function_name, *args)
                return result
        except Exception as e:
            logger.error(f"JavaScript执行失败 [{function_name}]: {e}")
            raise
    
    def _convert_result(self, js_value) -> Any:
        """转换JavaScript结果为Python对象"""
        # QuickJS返回的结果需要特殊处理
        if hasattr(js_value, 'to_dict'):
            return js_value.to_dict()
        elif hasattr(js_value, '__iter__') and not isinstance(js_value, str):
            return list(js_value)
        return js_value


class DRPY2Source(VodSourceAdapter):
    """
    DRPY2 JavaScript爬虫适配器
    
    加载并执行DRPY2格式的JS爬虫脚本,
    通过rule对象获取数据。
    """
    
    def __init__(self, source_config: Dict[str, Any]):
        super().__init__(source_config)
        
        # 加载JS文件
        self.js_code = self._load_js_file()
        
        # 初始化运行时
        self.runtime = DRPY2Runtime()
        
        # 解析rule对象
        self.rule = self._parse_rule()
        
        logger.info(f"✓ DRPY2适配器初始化成功: {self.name}")
    
    def _load_js_file(self) -> str:
        """加载JavaScript文件"""
        js_path = self.api_url
        
        # 如果是相对路径,转换为绝对路径
        if not os.path.isabs(js_path):
            # 从demo目录查找
            base_dirs = [
                "demo/Box系列/本地包",
                "demo/Box系列"
            ]
            
            for base_dir in base_dirs:
                full_path = os.path.join(base_dir, js_path)
                if os.path.exists(full_path):
                    js_path = full_path
                    break
        
        if not os.path.exists(js_path):
            raise FileNotFoundError(f"JS文件不存在: {js_path}")
        
        with open(js_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _parse_rule(self) -> Dict:
        """
        解析JS中的rule对象
        
        通过正则提取rule对象的JSON表示
        """
        try:
            # 提取rule对象 (简单的正则匹配)
            match = re.search(r'var\s+rule\s*=\s*(\{[\s\S]*?\});', self.js_code)
            
            if match:
                rule_str = match.group(1)
                
                # 尝试清理JS注释和单引号
                rule_str = re.sub(r'//.*$', '', rule_str, flags=re.MULTILINE)
                rule_str = rule_str.replace("'", '"')
                
                # 移除末尾逗号
                rule_str = re.sub(r',(\s*[}\]])', r'\1', rule_str)
                
                try:
                    rule = json.loads(rule_str)
                    logger.info(f"✓ 成功解析rule对象,包含 {len(rule)} 个字段")
                    return rule
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON解析失败: {e}, 返回空规则")
                    return {}
            else:
                logger.warning("未找到rule对象定义")
                return {}
        except Exception as e:
            logger.error(f"解析rule对象失败: {e}")
            return {}
    
    async def get_categories(self) -> List[Category]:
        """获取分类列表"""
        if self.is_cache_valid():
            return self._categories_cache
        
        try:
            # 检查是否有home接口
            if 'home' not in self.rule:
                logger.warning(f"DRPY2源 [{self.name}] 未定义home接口")
                return []
            
            # TODO: 执行JS的home()函数
            # 目前先返回空,待完整实现JS运行时后启用
            
            categories = []
            self._categories_cache = categories
            return categories
            
        except Exception as e:
            logger.error(f"DRPY2获取分类失败 [{self.name}]: {e}")
            raise
    
    async def get_vod_list(
        self, 
        type_id: int, 
        page: int = 1,
        filters: Optional[Dict[str, str]] = None
    ) -> VodListResponse:
        """获取影片列表"""
        try:
            # 检查是否有category接口
            if 'category' not in self.rule:
                return VodListResponse(code=0, msg="未定义category接口", list=[])
            
            # TODO: 执行JS的category(tid, pg, filter, extend)函数
            
            return VodListResponse(code=0, msg="DRPY2 category接口待实现", list=[])
            
        except Exception as e:
            logger.error(f"DRPY2获取列表失败 [{self.name}]: {e}")
            raise
    
    async def get_vod_detail(self, vod_id: str) -> VodDetailResponse:
        """获取影片详情"""
        try:
            # 检查是否有detail接口
            if 'detail' not in self.rule:
                return VodDetailResponse(code=0, msg="未定义detail接口", list=[])
            
            # TODO: 执行JS的detail(ids)函数
            
            return VodDetailResponse(code=0, msg="DRPY2 detail接口待实现", list=[])
            
        except Exception as e:
            logger.error(f"DRPY2获取详情失败 [{self.name}]: {e}")
            raise
    
    async def search_vod(self, keyword: str, page: int = 1) -> VodListResponse:
        """搜索影片"""
        try:
            # 检查是否有search接口
            if 'search' not in self.rule:
                return VodListResponse(code=0, msg="不支持搜索", list=[])
            
            # TODO: 执行JS的search(wd, quick, pg)函数
            
            return VodListResponse(code=0, msg="DRPY2 search接口待实现", list=[])
            
        except Exception as e:
            logger.error(f"DRPY2搜索失败 [{self.name}]: {e}")
            raise
