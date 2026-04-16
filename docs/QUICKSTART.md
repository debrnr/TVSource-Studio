# TVSource Studio 快速开始指南

## 🎯 5分钟快速上手

### 1. 安装依赖

```bash
# 激活虚拟环境
.\venv\Scripts\activate

# 安装核心依赖
pip install aiohttp jsonpath-ng pydantic beautifulsoup4 lxml

# (可选) 如需DRPY2支持
pip install quickjs
```

### 2. 配置数据源

编辑 `data/sources/source_config.json`:

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

**数据源类型说明**:
- `type: 0` - MacCMS JSON API (推荐)
- `type: 2` - XBPQ规则引擎
- `type: 3` - DRPY2 JS爬虫

### 3. 运行测试

```bash
python test/test_core_architecture.py
```

预期输出:
```
🧪 TVSource Studio 核心架构测试
============================================================
✓ 加载成功!
  总数据源: 1
  活跃适配器: 0
✓ 选择器解析器测试通过!
✅ 所有测试完成!
```

### 4. 在代码中使用

```python
import asyncio
from src.core import SourceManager

async def main():
    # 创建配置管理器
    manager = SourceManager("data/sources/source_config.json")
    
    # 获取适配器
    adapter = manager.get_adapter("三六零影视")
    
    # 获取分类
    categories = await adapter.get_categories()
    print(f"分类数量: {len(categories)}")
    
    # 获取影片列表
    if categories:
        vod_list = await adapter.get_vod_list(
            type_id=categories[0].type_id,
            page=1
        )
        print(f"影片数量: {len(vod_list.list)}")
        
        # 显示第一部影片
        if vod_list.list:
            first = vod_list.list[0]
            print(f"影片名称: {first.vod_name}")
            print(f"封面图片: {first.vod_pic}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📚 完整示例

### 示例1: 批量获取多个数据源

```python
from src.core import SourceManager

manager = SourceManager()

# 获取所有适配器
adapters = manager.get_all_adapters()

for name, adapter in adapters.items():
    print(f"\n数据源: {name}")
    try:
        categories = await adapter.get_categories()
        print(f"  分类数: {len(categories)}")
    except Exception as e:
        print(f"  错误: {e}")
```

### 示例2: 动态添加数据源

```python
manager = SourceManager()

# 添加新数据源
manager.add_source({
    "name": "采集之王",
    "type": 0,
    "api": "https://cjhwba.com/api.php/provide/vod/",
    "timeout": 15,
    "enabled": True
})

# 立即使用
adapter = manager.get_adapter("采集之王")
```

### 示例3: 健康检查

```python
manager = SourceManager()

# 检查所有数据源
for name in manager.sources.keys():
    is_healthy = await manager.health_check(name)
    status = "✓ 正常" if is_healthy else "✗ 异常"
    print(f"{name}: {status}")

# 查看统计
stats = manager.get_stats()
print(f"总数据源: {stats['total_sources']}")
print(f"按类型: {stats['sources_by_type']}")
```

### 示例4: XBPQ规则引擎

```python
# 配置XBPQ数据源
manager.add_source({
    "name": "农民影视",
    "type": 2,
    "api": "",
    "ext": "demo/Box系列/本地包/奇奇，20260414/tvboxqq/南风/json/农民影视.json",
    "enabled": True
})

adapter = manager.get_adapter("农民影视")
categories = await adapter.get_categories()
```

---

## 🔍 调试技巧

### 1. 启用详细日志

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 2. 查看原始API响应

```python
# 在 MacCMSSource 中添加
import json
data = await self._request(params)
print(json.dumps(data, ensure_ascii=False, indent=2))
```

### 3. 测试XBPQ选择器

```python
from src.core.adapters.xbpq_adapter import SelectorParser

html = '<div class="item"><a href="/1.html">影片</a></div>'

# 测试CSS选择器
result = SelectorParser.extract(html, 'p:a', 'https://example.com')
print(result)  # ['https://example.com/1.html']

# 测试正则
result = SelectorParser.extract(html, 'href="([^"]+)"')
print(result)  # ['/1.html']
```

---

## ❓ 常见问题

### Q: 如何添加新的MacCMS数据源?

**A**: 只需在配置文件中添加:
```json
{
  "name": "我的数据源",
  "type": 0,
  "api": "https://example.com/api.php/provide/vod/",
  "enabled": true
}
```

### Q: XBPQ规则怎么写?

**A**: 参考现有规则文件:
- `demo/Box系列/本地包/奇奇，20260414/tvboxqq/南风/json/农民影视.json`
- `demo/Box系列/本地包/奇奇，20260414/tvboxqq/南风/json/低端影视.json`

### Q: 如何提高性能?

**A**: 
1. 启用缓存 (已自动启用)
2. 设置合理的timeout (10-15秒)
3. 定期清理无效源
4. 使用连接池 (aiohttp自动管理)

### Q: DRPY2 JS爬虫为什么不能用?

**A**: 当前DRPY2适配器是框架版本,需要:
1. 安装quickjs: `pip install quickjs`
2. 完善全局API注入 (待开发)
3. 或者先用MacCMS/XBPQ替代

---

## 📖 延伸阅读

- [核心架构文档](CORE_ARCHITECTURE.md) - 详细的架构设计
- [TVBox配置规范](../demo/Box系列/) - 完整的TVBox资料
- [XBPQ规则详解](../demo/Box系列/本地包/XBPQ_20250816/XBPQ详细说明.json)

---

**祝您使用愉快!** 🎉

如有问题,请查看日志或提交Issue。
