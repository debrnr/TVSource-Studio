# 🤝 TVSource Studio 贡献者指南

欢迎为TVSource Studio项目做出贡献!本指南将帮助您快速上手。

---

## 📋 目录

- [项目概述](#项目概述)
- [开发环境搭建](#开发环境搭建)
- [代码规范](#代码规范)
- [提交PR流程](#提交pr流程)
- [待完成任务清单](#待完成任务清单)
- [常见问题](#常见问题)

---

## 🎯 项目概述

**TVSource Studio** 是一个TVBox数据源聚合服务,目标是提供统一的标准接口,让TVBox客户端能够访问多个数据源。

### 当前状态
- ✅ **核心架构完成** - SourceManager、适配器模式、HTTP客户端
- ✅ **MacCMS API可用** - Type 0/1数据源完全支持
- ⚠️ **XBPQ/DRPY2待完善** - 框架已搭建,核心逻辑需实现

### 技术栈
- **后端**: Python 3.8+ + Flask 3.0
- **异步**: aiohttp
- **HTML解析**: BeautifulSoup4 (待集成)
- **JS运行**: quickjs/PyExecJS (待集成)
- **数据库**: SQLite (缓存)
- **定时任务**: APScheduler

---

## 💻 开发环境搭建

### 1. 克隆仓库
```bash
git clone https://github.com/debrnr/TVSource-Studio.git
cd TVSource-Studio
```

### 2. 创建虚拟环境
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. 安装依赖
```bash
pip install -r config/requirements.txt
```

### 4. 运行测试
```bash
python -m pytest test/ -v
```

### 5. 启动开发服务器
```bash
python src/app.py
```

访问 http://localhost:8080 查看服务是否正常运行。

---

## 📝 代码规范

### Python代码风格
遵循 [PEP 8](https://peps.python.org/pep-0008/) 规范:

```python
# ✅ 好的写法
def get_vod_list(self, category_id: str, page: int = 1) -> Dict:
    """获取影片列表
    
    Args:
        category_id: 分类ID
        page: 页码,默认1
        
    Returns:
        包含影片列表的字典
    """
    pass

# ❌ 不好的写法
def getVodList(self,id,page=1):
    pass
```

### 命名规范
- **类名**: PascalCase (`XBPQAdapter`, `SourceManager`)
- **函数/变量**: snake_case (`get_vod_list`, `source_config`)
- **常量**: UPPER_SNAKE_CASE (`MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT`)
- **私有方法**: 前缀下划线 (`_parse_html`, `_init_runtime`)

### 注释要求
- 所有公共方法必须有docstring
- 复杂逻辑需要行内注释说明
- TODO标记待完成事项

```python
async def parse_categories(self, html: str) -> List[Dict]:
    """解析分类页面
    
    Args:
        html: HTML内容
        
    Returns:
        分类列表,每个分类包含id和name
        
    Raises:
        ParseError: HTML解析失败
    """
    # TODO: 使用BeautifulSoup解析
    pass
```

### 类型注解
强烈建议使用类型注解:

```python
from typing import List, Dict, Optional, Any

async def search(self, keyword: str, page: int = 1) -> Dict[str, Any]:
    """搜索影片"""
    pass
```

---

## 🔄 提交PR流程

### 1. Fork仓库
在GitHub或Gitee上点击"Fork"按钮

### 2. 创建功能分支
```bash
git checkout -b feature/your-feature-name
# 例如: feature/xbpq-html-parser
```

### 3. 开发并测试
```bash
# 编写代码
# ...

# 运行测试确保不破坏现有功能
python -m pytest test/ -v

# 本地测试新功能
python src/app.py
```

### 4. 提交更改
```bash
git add .
git commit -m "feat: 添加XBPQ HTML解析器

- 实现CSS选择器提取
- 实现XPath提取
- 添加单元测试

Closes #123"
```

**提交信息格式**:
- `feat:` 新功能
- `fix:` Bug修复
- `docs:` 文档更新
- `style:` 代码格式(不影响功能)
- `refactor:` 重构
- `test:` 测试相关
- `chore:` 构建过程或辅助工具变动

### 5. 推送到您的Fork
```bash
git push origin feature/your-feature-name
```

### 6. 创建Pull Request
- 访问原仓库
- 点击"Compare & pull request"
- 填写PR描述
- 等待审核

---

## ✅ 待完成任务清单

### 🔥 高优先级

#### 1. XBPQ适配器核心方法
**文件**: `src/core/adapters/xbpq_adapter.py`  
**进度**: 30%  
**难度**: ⭐⭐⭐

**需要实现**:
```python
class XBPQAdapter(VodSourceAdapter):
    async def get_categories(self) -> List[Dict]:
        """从XBPQ规则解析分类列表"""
        # 1. 读取规则文件
        # 2. 请求首页URL
        # 3. 使用BeautifulSoup提取分类链接
        # 4. 返回标准格式
        
    async def get_vod_list(self, category_id: str, page: int) -> Dict:
        """解析分类下的影片列表"""
        # 1. 构造列表页URL
        # 2. 请求并解析HTML
        # 3. 提取影片封面、标题、ID等
        # 4. 返回分页数据
        
    async def get_vod_detail(self, vod_id: str) -> Dict:
        """解析影片详情"""
        # 1. 请求详情页URL
        # 2. 提取简介、演员、导演
        # 3. 提取播放地址(可能有多个线路)
        # 4. 返回完整详情
```

**技术要点**:
- 使用 `BeautifulSoup4` 解析HTML
- 支持CSS选择器和正则表达式
- 处理相对路径转绝对路径
- 异常处理和重试机制

**参考资源**:
- [BeautifulSoup文档](https://beautiful-soup-4.readthedocs.io/)
- XBPQ规则示例: `data/rules/xbpq/*.json`

---

#### 2. DRPY2 JS运行时集成
**文件**: `src/core/adapters/drpy2_adapter.py`  
**进度**: 20%  
**难度**: ⭐⭐⭐⭐

**需要实现**:
```python
class DRPY2Adapter(VodSourceAdapter):
    def _init_js_runtime(self):
        """初始化JS执行环境"""
        # 方案1: 使用quickjs
        import quickjs
        self.context = quickjs.Context()
        
        # 注入全局API
        self.context.set("request", self._js_request)
        self.context.set("pdfh", self._js_pdfh)
        self.context.set("pd", self._js_pd)
        self.context.set("log", self._js_log)
        
    async def execute_script(self, script_path: str, function_name: str, **kwargs) -> Any:
        """执行DRPY2脚本"""
        # 1. 读取JS文件
        # 2. 在JS上下文中执行
        # 3. 调用指定函数
        # 4. 返回Python对象
```

**技术方案选择**:
1. **quickjs** (推荐) - 轻量级,纯Python,无外部依赖
2. **PyExecJS** - 支持多种JS引擎,但需要node.js
3. **subprocess调用node** - 最灵活,但性能较差

**技术要点**:
- JS与Python数据类型转换
- 异步HTTP请求封装
- DOM操作模拟(pdfh/pd函数)
- 错误捕获和日志输出

**参考资源**:
- [quickjs-python](https://pypi.org/project/quickjs/)
- DRPY2脚本示例: `data/rules/drpy2/*.js`

---

#### 3. 通用HTML解析引擎
**文件**: `src/core/html_parser.py` (新建)  
**进度**: 0%  
**难度**: ⭐⭐

**需要实现**:
```python
class HTMLParser:
    """通用HTML解析器"""
    
    @staticmethod
    def extract_by_css(html: str, selector: str, attr: str = None) -> List[str]:
        """CSS选择器提取
        
        Args:
            html: HTML内容
            selector: CSS选择器,如 'div.item > a.title'
            attr: 提取属性(None提取文本),如 'href', 'src'
            
        Returns:
            提取结果列表
        """
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')
        elements = soup.select(selector)
        
        if attr:
            return [elem.get(attr, '') for elem in elements]
        else:
            return [elem.get_text(strip=True) for elem in elements]
    
    @staticmethod
    def extract_by_xpath(html: str, xpath: str) -> List[str]:
        """XPath提取"""
        from lxml import etree
        tree = etree.HTML(html)
        return tree.xpath(xpath)
    
    @staticmethod
    def extract_by_regex(html: str, pattern: str, group: int = 0) -> List[str]:
        """正则表达式提取"""
        import re
        matches = re.finditer(pattern, html, re.DOTALL)
        return [m.group(group) for m in matches]
```

**技术要点**:
- 统一三种提取方式的接口
- 处理编码问题
- 性能优化(缓存解析结果)
- 错误容错

---

### 🎯 中优先级

#### 4. 智能缓存策略
**文件**: `src/core/cache_manager.py` (新建)  
**进度**: 50%  
**难度**: ⭐⭐⭐

**需要实现**:
- LRU缓存淘汰算法
- TTL自动过期
- 缓存预热机制
- 缓存命中率统计

#### 5. 性能监控面板
**文件**: `src/monitoring/` (新建目录)  
**进度**: 0%  
**难度**: ⭐⭐⭐⭐

**需要实现**:
- Prometheus指标暴露
- Grafana看板配置
- 实时请求统计
- 慢查询告警

#### 6. 补充单元测试
**文件**: `test/test_adapters.py` (新建)  
**进度**: 40%  
**难度**: ⭐⭐

**需要测试**:
- XBPQ适配器各种规则解析
- DRPY2脚本执行
- HTTP客户端重试逻辑
- 边界条件和异常情况

---

### 📚 低优先级

#### 7. Docker部署优化
**文件**: `deploy/Dockerfile`  
**进度**: 60%  
**难度**: ⭐⭐

**需要优化**:
- 多阶段构建减小镜像体积
- 健康检查端点
- Volume挂载配置
- docker-compose编排

#### 8. 前端UI优化
**文件**: `src/templates/admin/dashboard.html`  
**进度**: 70%  
**难度**: ⭐⭐

**需要优化**:
- 响应式布局
- 实时数据刷新
- 图表可视化
- 暗色主题

---

## ❓ 常见问题

### Q1: 如何调试XBPQ规则解析?

**A**: 使用浏览器开发者工具查看目标网站的HTML结构,然后编写对应的CSS选择器。

```python
# 调试示例
import requests
from bs4 import BeautifulSoup

html = requests.get('https://example.com').text
soup = BeautifulSoup(html, 'lxml')

# 在浏览器控制台测试选择器
# document.querySelectorAll('div.item > a.title')

# 在Python中测试
items = soup.select('div.item > a.title')
for item in items:
    print(item.get_text(), item.get('href'))
```

### Q2: DRPY2脚本如何测试?

**A**: 可以先用node.js单独运行JS脚本,验证逻辑正确性。

```bash
# 安装node.js
# 然后运行
node data/rules/drpy2/斗鱼直播.js
```

### Q3: 遇到依赖冲突怎么办?

**A**: 使用虚拟环境隔离依赖。

```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r config/requirements.txt
```

### Q4: 如何联系维护者?

**A**: 
- GitHub Issues: https://github.com/debrnr/TVSource-Studio/issues
- Gitee Issues: https://gitee.com/debrnr/tvsource-studio/issues
- 直接在PR中@debrnr

---

## 🎁 贡献者福利

- ✅ 您的名字将出现在 CONTRIBUTORS.md
- ✅ 获得项目维护者的技术指导
- ✅ 参与开源项目,积累实战经验
- ✅ 结识志同道合的开发者

---

## 📞 需要帮助?

如果您在贡献过程中遇到任何问题:

1. 查看现有Issues是否有类似问题
2. 创建新Issue详细描述问题
3. 在PR中请求Code Review
4. 加入社区讨论(如有)

---

**感谢您的贡献!** 🎉

每一行代码都将帮助更多人享受更好的观影体验!
