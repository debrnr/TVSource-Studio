# TVSource Studio 核心架构文档

## 📐 架构概览

TVSource Studio采用**适配器模式**设计,通过统一的接口抽象不同类型的视频数据源,实现灵活扩展和统一管理。

```
┌─────────────────────────────────────────────────────┐
│              Flask Web Service Layer                 │
│         (routes.py - HTTP API Endpoints)             │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│           SourceManager (配置管理器)                  │
│  - 加载/管理数据源配置                               │
│  - 创建适配器实例(带缓存)                             │
│  - 健康检查与统计                                    │
└──┬────────────┬──────────────┬──────────────────────┘
   │            │              │
┌──▼──────┐ ┌──▼────────┐ ┌──▼──────────┐
│MacCMSSrc│ │ XBPQSrc   │ │ DRPY2Src    │
│Type 0/1 │ │ Type 2/4  │ │ Type 3      │
└─────────┘ └───────────┘ └─────────────┘
   │            │              │
   └────────────┴──────────────┘
                │
     ┌──────────▼──────────┐
     │  VodSourceAdapter   │
     │  (统一接口抽象类)     │
     └─────────────────────┘
```

## 🎯 核心模块说明

### 1. VodSource接口 (`src/core/vod_source.py`)

**职责**: 定义所有数据源适配器必须实现的标准接口

**关键组件**:
- `VodSourceAdapter`: 抽象基类,定义5个核心方法
  - `get_categories()` - 获取分类列表
  - `get_vod_list()` - 获取影片列表
  - `get_vod_detail()` - 获取影片详情
  - `search_vod()` - 搜索影片
  - `clear_cache()` - 清除缓存

- **数据模型**:
  - `VodItem` - 影片条目(列表页)
  - `VodDetail` - 影片详情(详情页)
  - `Category` - 分类信息
  - `VodListResponse` - 列表响应(符合MacCMS标准)
  - `VodDetailResponse` - 详情响应

**设计原则**:
- ✅ 所有适配器返回统一的数据格式
- ✅ 支持异步操作(async/await)
- ✅ 内置缓存机制
- ✅ 标准化ID格式: `source_name$vod_id`

---

### 2. MacCMS API适配器 (`src/core/adapters/maccms_adapter.py`)

**类型**: Type 0/1

**功能**:
- 支持标准MacCMS API协议
- JSON/XML格式自动识别
- 完整的CRUD操作(分类/列表/详情/搜索)

**技术栈**:
- `aiohttp` - 异步HTTP客户端
- 自动处理URL拼接和参数编码

**使用示例**:
```python
adapter = MacCMSSource({
    'name': '三六零影视',
    'type': 0,
    'api': 'https://360zy.com/api.php/provide/vod/',
    'timeout': 10
})

categories = await adapter.get_categories()
vod_list = await adapter.get_vod_list(type_id=1, page=1)
```

**优势**:
- ✅ 最稳定,直接调用标准API
- ✅ 代码量少(~300行)
- ✅ 易于维护和调试

**限制**:
- ❌ 依赖第三方API可用性
- ❌ 不支持HTML解析

---

### 3. XBPQ规则引擎适配器 (`src/core/adapters/xbpq_adapter.py`)

**类型**: Type 2/4

**功能**:
- 通过配置化规则解析HTML页面
- 支持三种选择器语法:
  - `&&` - 正则表达式
  - `j:` - JSONPath
  - `p:` - CSS选择器 (BeautifulSoup)
- 支持高级过滤和工具函数

**核心技术**:
- `SelectorParser` - 选择器语法解析器
  - `_extract_regex()` - 正则提取(支持&&多段匹配)
  - `_extract_json()` - JSONPath提取(jsonpath-ng)
  - `_extract_css()` - CSS选择器提取(BeautifulSoup)

**规则配置示例**:
```json
{
  "title": "农民影视",
  "host": "https://www.nmddd.com",
  "class_name": "电影&电视剧&综艺",
  "class_url": "1&2&3",
  "一级": "div.vod-list&&li",
  "vod_name": "h3&&Text",
  "vod_pic": "img&&data-src",
  "vod_id": "a&&href"
}
```

**优势**:
- ✅ 无需编写代码,配置即可适配任意网站
- ✅ 覆盖80%以上的HTML站点
- ✅ 规则可热更新

**限制**:
- ❌ HTML结构变化需更新规则
- ❌ 复杂反爬需要额外处理

---

### 4. DRPY2 JS运行时适配器 (`src/core/adapters/drpy2_adapter.py`)

**类型**: Type 3

**功能**:
- 执行DRPY2格式的JavaScript爬虫脚本
- 模拟TVBox的JS运行时环境
- 支持复杂的动态渲染和加密逻辑

**技术选型**:
- **QuickJS** (推荐) - 轻量快速,无需Node.js
- **PyExecJS** (备选) - 需要安装Node.js

**当前状态**:
- ⚠️ 框架已搭建,完整实现待完善
- ✅ 支持加载JS文件
- ⚠️ 需要注入DRPY2全局API(request/fetch/pdfa等)

**下一步优化**:
1. 实现完整的DRPY2全局函数注入
2. 支持异步HTTP请求
3. 集成加密解密库(Crypto/RSA)

---

### 5. 配置管理器 (`src/core/source_manager.py`)

**职责**:
- 统一管理所有数据源配置
- 懒加载适配器实例(带缓存)
- 支持动态添加/删除数据源
- 提供健康检查和统计功能

**配置文件格式** (`data/sources/source_config.json`):
```json
{
  "version": "1.0",
  "sources": [
    {
      "name": "三六零影视",
      "type": 0,
      "api": "https://360zy.com/api.php/provide/vod/",
      "timeout": 10,
      "enabled": true
    }
  ]
}
```

**核心方法**:
- `load_config()` - 从JSON加载配置
- `get_adapter(name)` - 获取适配器实例(带缓存)
- `add_source(config)` - 动态添加数据源
- `health_check(name)` - 健康检查
- `get_stats()` - 获取统计信息

---

## 🔧 依赖管理

### 核心依赖
```txt
aiohttp==3.9.1          # 异步HTTP客户端
beautifulsoup4==4.12.3  # HTML解析
jsonpath-ng==1.6.1      # JSONPath支持
pydantic==2.5.3         # 数据验证
```

### 可选依赖 (DRPY2支持)
```txt
quickjs==1.19.2         # 推荐: 轻量JS运行时
# 或
PyExecJS==1.5.1         # 备选: 需要Node.js
```

### 安装命令
```bash
pip install aiohttp jsonpath-ng pydantic beautifulsoup4 lxml
pip install quickjs  # 如需DRPY2支持
```

---

## 📊 测试验证

运行测试脚本验证核心功能:
```bash
python test/test_core_architecture.py
```

**测试结果**:
- ✅ 配置管理器加载成功
- ✅ XBPQ选择器解析器工作正常
  - CSS选择器: ✓
  - JSONPath: ✓
  - 正则表达式: ✓ (已优化)
- ⚠️ MacCMS API (网络依赖,可能超时)
- ⚠️ DRPY2运行时 (待完善)

---

## 🚀 下一步开发计划

### Phase 1 - 基础功能 (已完成✅)
- [x] 统一VodSource接口
- [x] MacCMS API适配器
- [x] XBPQ规则解析器核心
- [x] 配置管理系统
- [x] DRPY2框架搭建

### Phase 2 - 增强功能 (进行中🔄)
- [ ] 完善DRPY2 JS运行时
  - [ ] 注入全局API (request/fetch/pdfh/pdfa)
  - [ ] 支持异步HTTP
  - [ ] 集成加密库
- [ ] 实现批量请求优化 (batchFetch)
- [ ] 添加请求重试和熔断机制
- [ ] 完善错误处理和日志

### Phase 3 - Web集成
- [ ] 创建Flask路由整合适配器
- [ ] 实现TVBox标准API端点
- [ ] 添加CORS支持
- [ ] 实现配置管理Web界面

### Phase 4 - 高级特性
- [ ] 自动健康检查和故障转移
- [ ] 数据缓存策略 (Redis/Memory)
- [ ] 定时任务自动更新源
- [ ] 性能监控和告警

---

## 📝 最佳实践

### 1. 添加新数据源
```python
# 在 source_config.json 中添加
{
  "name": "新数据源",
  "type": 0,  # 或 2, 3
  "api": "https://example.com/api",
  "enabled": true
}

# 配置管理器会自动加载
manager = SourceManager()
adapter = manager.get_adapter("新数据源")
```

### 2. 自定义XBPQ规则
```json
{
  "host": "https://example.com",
  "class_name": "电影&电视剧",
  "class_url": "1&2",
  "一级": "div.list-item",
  "vod_name": "p:span.title",
  "vod_pic": "p:img&&src",
  "vod_id": "p:a&&href"
}
```

### 3. 性能优化建议
- 启用适配器缓存 (`manager.get_adapter()` 自动缓存)
- 设置合理的timeout (10-15秒)
- 定期清理无效源 (`health_check()`)
- 使用连接池 (aiohttp自动管理)

---

## 🐛 常见问题

### Q1: MacCMS API连接超时?
**A**: 检查网络连接,确认API地址可用。某些API可能需要代理。

### Q2: XBPQ规则不生效?
**A**: 
1. 检查规则JSON格式是否正确
2. 使用浏览器开发者工具验证CSS选择器
3. 查看日志中的详细错误信息

### Q3: DRPY2 JS执行失败?
**A**: 
1. 确认已安装quickjs或execjs
2. 检查JS文件路径是否正确
3. 查看是否缺少DRPY2全局函数

---

## 📚 参考资料

- [TVBox开源项目](https://github.com/CatVodTVOfficial/TVBoxOSC)
- [DRPY2框架文档](https://github.com/hjdhnx/dr_py)
- [XBPQ规则详解](demo/Box系列/本地包/XBPQ_20250816/XBPQ详细说明.json)
- [MacCMS API规范](http://www.maccms.la/doc/)

---

**文档版本**: v1.0  
**最后更新**: 2026-04-16  
**维护者**: TVSource Studio Team
