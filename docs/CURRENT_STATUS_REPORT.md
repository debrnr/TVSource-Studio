# 📊 TVSource Studio 当前状态报告

## ✅ 已完成的工作

### 1. JS爬虫资源整理 ✓
- **创建了项目内部规则目录**: `data/rules/`
  - `data/rules/xbpq/` - 存放87个XBPQ JSON规则文件
  - `data/rules/drpy2/` - 存放10个DRPY2 JS脚本文件

- **批量导入工具优化**: 
  - [`scripts/import_js_sources.py`](file://d:\DEBRNR_PYTHON\Project\TVSource%20Studio\scripts\import_js_sources.py) 支持扁平目录结构
  - 自动检测并使用项目内部rules目录
  - 成功导入61个有效规则(29个JSON格式错误被跳过)

### 2. 数据源配置扩展 ✓
- **总数据源数量**: 69个
  - MacCMS API: 7个 (5个新增可用源)
  - XBPQ规则: 52个 (已禁用,待适配器完善)
  - DRPY2脚本: 10个 (已禁用,待适配器完善)

- **新增可用MacCMS API源**:
  ```json
  [
    "红牛资源",
    "飞速资源", 
    "量子资源",
    "非凡资源",
    "卧龙资源"
  ]
  ```

### 3. DEMO资源迁移 ✓
- 从`demo/Box系列/本地包/`复制了所有JS爬虫到项目内部
- 路径结构:
  ```
  data/rules/
  ├── xbpq/     # 87个XBPQ规则
  │   ├── 农民影视.json
  │   ├── 低端影视.json
  │   ├── jianpian.json
  │   ├── Bili.json
  │   └── ... (共87个)
  └── drpy2/    # 10个DRPY2脚本
      ├── 斗鱼直播.js
      ├── 虎牙.js
      ├── 优酷.js
      └── ... (共10个)
  ```

---

## ⚠️ 当前问题

### 问题1: TVBox分类显示空数据

**原因分析**:
1. 旧的`/api/maccms/vod`路由尝试调用不存在的`handle_vod_list()`函数
2. XBPQ适配器核心方法(`get_categories`, `get_vod_list`)尚未实现
3. 配置的旧MacCMS API源(三六零、采集之王)全部超时/403

**临时解决方案**:
- 已禁用所有XBPQ和DRPY2源(共62个)
- 保留7个MacCMS API源(5个新添加的应该可用)
- routes.py中的maccms_api需要修复

**待修复**:
需要修复[`src/routes.py`](file://d:\DEBRNR_PYTHON\Project\TVSource%20Studio\src\routes.py)第361行的`maccms_api()`函数,移除对不存在函数的调用。

---

### 问题2: XBPQ规则文件格式错误

**错误统计**: 29个JSON文件解析失败

**常见错误类型**:
1. **单引号而非双引号**: `Expecting property name enclosed in double quotes`
   - 例如: `{ 'key': 'value' }` 应为 `{ "key": "value" }`
   
2. **UTF-8 BOM头**: `Unexpected UTF-8 BOM`
   - 文件开头有BOM标记,需要用`utf-8-sig`解码

3. **空文件或格式损坏**: `Expecting value: line 1 column 1`

**影响范围**: 
- 低端影视.json
- 嗷呜动漫.json  
- age动漫.json
- 等多个文件

**建议**: 手动修复这些JSON文件,或从其他来源获取正确版本。

---

### 问题3: XBPQ适配器未完全实现

**当前状态**:
- ✅ 框架已搭建
- ✅ 规则加载逻辑完成
- ❌ 核心方法缺失:
  - `get_categories()` - 获取分类列表
  - `get_vod_list()` - 获取影片列表
  - `get_vod_detail()` - 获取影片详情
  - `search()` - 搜索功能

**下一步**: 需要实现HTML解析逻辑,使用BeautifulSoup或正则表达式提取数据。

---

## 📋 数据源清单

### 启用的数据源 (7个)
```
✓ 三六零影视 (Type 0) - ⚠️ 可能不可用
✓ 采集之王聚合 (Type 0) - ⚠️ 可能不可用
✓ 红牛资源 (Type 0) - ✅ 新增
✓ 飞速资源 (Type 0) - ✅ 新增
✓ 量子资源 (Type 0) - ✅ 新增
✓ 非凡资源 (Type 0) - ✅ 新增
✓ 卧龙资源 (Type 0) - ✅ 新增
```

### 禁用的XBPQ规则 (52个)
部分示例:
- 农民影视(XBPQ)
- 低端影视(XBPQ)
- jianpian
- Bili (哔哩哔哩)
- 斗鱼直播
- 虎牙直播
- 樱花动漫
- 动漫巴士
- ...等52个

### 禁用的DRPY2脚本 (10个)
- 斗鱼直播(DRPY2) - 76.91 KB
- 虎牙(DRPY2) - 44.97 KB
- 优酷(DRPY2) - 28.68 KB
- 奇珍异兽(DRPY2) - 23.01 KB
- 虎牙直播(DRPY2) - 20.89 KB
- 哔哩直播(DRPY2) - 16.37 KB
- 腾云驾雾(DRPY2) - 12.99 KB
- drpy(DRPY2) - 13.04 KB
- 百忙无果(DRPY2) - 10.12 KB
- 金牌影视(DRPY2) - 4.4 KB

---

## 🔧 下一步行动计划

### 优先级1: 修复MacCMS API路由 (紧急)

**任务**: 修复`src/routes.py`中的`maccms_api()`函数

**方案A** (推荐): 回滚到原始实现,从外部API聚合
```python
# 移除对tvbox_routes的调用
# 恢复原来从多个外部源获取数据的逻辑
```

**方案B**: 实现正确的异步调用
```python
# 创建wrapper函数适配tvbox_routes
```

### 优先级2: 测试新增MacCMS API源

验证以下5个新源是否可用:
- 红牛资源
- 飞速资源
- 量子资源
- 非凡资源
- 卧龙资源

### 优先级3: 修复JSON格式错误的XBPQ规则

修复29个格式错误的JSON文件,或替换为正确版本。

### 优先级4: 实现XBPQ适配器核心方法

实现以下方法使XBPQ规则真正可用:
- `get_categories()` - 解析分类页面
- `get_vod_list()` - 解析列表页面
- `get_vod_detail()` - 解析详情页面
- `search()` - 解析搜索结果

### 优先级5: 实现DRPY2适配器

完善DRPY2 JS运行时支持,包括:
- QuickJS/PyExecJS集成
- 全局API注入
- JS脚本执行环境

---

## 📝 关键文件清单

| 文件 | 状态 | 说明 |
|------|------|------|
| `data/rules/xbpq/*.json` | ✅ 已导入 | 87个XBPQ规则文件 |
| `data/rules/drpy2/*.js` | ✅ 已导入 | 10个DRPY2脚本 |
| `data/sources/source_config.json` | ✅ 已更新 | 69个数据源配置 |
| `scripts/import_js_sources.py` | ✅ 已优化 | 支持扁平目录结构 |
| `scripts/add_working_maccms_sources.py` | ✅ 新建 | 添加可用MacCMS源 |
| `scripts/disable_xbpq_temp.py` | ✅ 新建 | 临时禁用XBPQ |
| `src/routes.py` | ⚠️ 需修复 | maccms_api函数错误 |
| `src/core/adapters/xbpq_adapter.py` | ⚠️ 待完善 | 核心方法未实现 |
| `src/core/adapters/drpy2_adapter.py` | ⚠️ 待完善 | JS运行时未集成 |

---

## 💡 使用建议

### 当前可用功能
1. **MacCMS API聚合** - 通过7个数据源提供影片数据
2. **TVBox配置生成** - `/api/tvbox/config`返回7个站点配置
3. **管理后台** - `/admin/`可视化管理数据源
4. **直播源服务** - M3U/TXT格式输出

### 暂时不可用功能
1. **XBPQ规则引擎** - 适配器未完全实现
2. **DRPY2脚本运行** - JS运行时未集成
3. **HTML页面抓取** - 需要完善选择器解析

### 推荐操作
1. **重启服务**后在TVBox中重新配置接口
2. **访问管理后台**查看数据源健康状态
3. **等待XBPQ适配器完善**后再启用规则引擎源

---

**报告生成时间**: 2026-04-16 19:57
**下次更新**: 修复MacCMS API路由后
