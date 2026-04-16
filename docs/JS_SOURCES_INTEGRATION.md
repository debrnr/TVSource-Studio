# 📚 JS爬虫集成指南

> 如何将demo目录中的XBPQ规则和DRPY2脚本集成到TVSource Studio

---

## 🎯 集成概览

TVSource Studio支持三种数据源类型:

| 类型 | 名称 | 说明 | 难度 |
|------|------|------|------|
| Type 0/1 | MacCMS API | 标准API接口,最稳定 | ⭐ |
| **Type 2** | **XBPQ规则引擎** | **JSON配置化解析HTML** | **⭐⭐⭐** |
| **Type 3** | **DRPY2 JS运行时** | **JavaScript爬虫脚本** | **⭐⭐⭐⭐** |

---

## 🚀 快速集成(推荐)

### 方法1: 自动导入工具(最简单)

```bash
# 1. 运行导入工具,扫描demo目录
python scripts/import_js_sources.py

# 2. 合并配置
python scripts/merge_configs.py

# 3. 重启服务
python src/app.py
```

**效果**: 自动发现4个JS爬虫资源并生成配置

---

### 方法2: 手动配置

#### 步骤1: 编辑配置文件

打开 `data/sources/source_config.json`,添加数据源:

##### XBPQ规则示例 (Type 2)

```json
{
  "name": "农民影视",
  "type": 2,
  "api": "",
  "ext": "demo/Box系列/本地包/奇奇，20260414/tvboxqq/南风/json/农民影视.json",
  "timeout": 15,
  "enabled": true
}
```

**关键字段**:
- `type`: 固定为 `2` (XBPQ规则引擎)
- `api`: 留空 (不需要API地址)
- `ext`: JSON规则文件路径(**相对路径或绝对路径**)
- `enabled`: 设为 `true` 启用

##### DRPY2脚本示例 (Type 3)

```json
{
  "name": "虎牙直播",
  "type": 3,
  "api": "demo/Box系列/本地包/奇奇，20260414/tvboxqq/南风/js/虎牙.js",
  "timeout": 20,
  "enabled": true
}
```

**关键字段**:
- `type`: 固定为 `3` (DRPY2 JS运行时)
- `api`: JS脚本文件路径
- `timeout`: 建议20秒(JS执行较慢)

---

## 📋 已发现的JS爬虫资源

### XBPQ规则引擎 (Type 2)

| 名称 | 分类 | 作者 | 状态 |
|------|------|------|------|
| 农民影视 | 电影/电视剧/综艺/动漫/短剧 | 香雅情 | ✗ 禁用 |
| jianpian | - | - | ✗ 禁用 |
| ~~低端影视~~ | - | - | ⚠️ 格式错误 |
| ~~嗷呜动漫~~ | - | - | ⚠️ 格式错误 |

**注意**: 低端影视和嗷呜动漫的JSON格式有误,需要手动修复后才能使用。

### DRPY2脚本 (Type 3)

| 名称 | 类型 | 大小 | 状态 |
|------|------|------|------|
| 斗鱼直播 | 直播爬虫 | 76.91 KB | ✗ 禁用 |
| 虎牙 | 直播爬虫 | 44.97 KB | ✗ 禁用 |

---

## 🔧 启用JS爬虫

### 方式1: 编辑配置文件

在 `data/sources/source_config.json` 中找到对应的数据源,将 `"enabled": false` 改为 `"enabled": true`:

```json
{
  "name": "农民影视",
  "type": 2,
  "enabled": true  // ← 改为true
}
```

### 方式2: 管理后台

1. 启动服务: `python src/app.py`
2. 浏览器访问: `http://localhost:8080/admin/`
3. 找到对应的数据源,点击"启用"按钮

---

## ⚙️ 工作原理

### XBPQ规则引擎 (Type 2)

```
用户请求 → XBPQAdapter加载JSON规则 → HTTP请求目标网站 
       → 根据规则提取HTML元素 → 转换为标准MacCMS格式 → 返回结果
```

**规则字段说明**:
- `分类链接`: 定义如何构建分类URL
- `分类列表数组规则`: CSS选择器提取影片列表
- `搜索片单标题`: 提取影片标题
- `选集链接`: 提取播放地址

**优势**:
- ✅ 配置化,无需编写代码
- ✅ 规则可复用
- ✅ 易于维护和更新

### DRPY2 JS运行时 (Type 3)

```
用户请求 → DRPY2Adapter加载JS文件 → QuickJS/ExecJS执行 
       → 调用JS中的category/search/detail函数 → 返回结果
```

**JS脚本要求**:
- 必须导出 `rule` 对象
- 实现 `category()`, `search()`, `detail()` 等函数
- 返回标准JSON格式

**优势**:
- ✅ 支持复杂逻辑(签名/加密)
- ✅ 可直接复用现有DRPY2脚本
- ⚠️ 性能较低(JS执行开销)

---

## 🐛 常见问题

### Q1: XBPQ规则解析失败?

**症状**: 日志显示 "JSON解析错误"

**原因**: JSON文件格式不正确(注释/尾随逗号)

**解决**:
```bash
# 检查JSON格式
python -m json.tool demo/xxx/规则.json

# 或使用在线工具验证
# https://jsonlint.com/
```

**修复示例**:
```json
// ❌ 错误: JSON不支持注释
{
  "规则名": "测试",  // ❌ 错误: 尾随逗号
}

// ✅ 正确
{
  "规则名": "测试"
}
```

### Q2: DRPY2脚本执行超时?

**症状**: 请求超过20秒无响应

**解决**:
1. 增加超时时间:
```json
{
  "name": "虎牙直播",
  "type": 3,
  "timeout": 30  // ← 增加到30秒
}
```

2. 检查JS脚本是否有死循环或网络请求阻塞

### Q3: 路径找不到?

**症状**: "FileNotFoundError: xxx.json"

**解决**:
- 使用**相对路径**(相对于项目根目录):
  ```json
  "ext": "demo/Box系列/本地包/奇奇，20260414/tvboxqq/南风/json/农民影视.json"
  ```

- 或使用**绝对路径**:
  ```json
  "ext": "D:/DEBRNR_PYTHON/Project/TVSource Studio/demo/..."
  ```

### Q4: 如何调试XBPQ规则?

**方法**:
1. 在浏览器中打开规则中的 `首页推荐链接`
2. 按F12打开开发者工具
3. 使用Console测试CSS选择器:
   ```javascript
   document.querySelectorAll('.globalPicList li')
   ```
4. 验证选择器是否能正确提取元素

---

## 📊 性能对比

| 指标 | MacCMS API | XBPQ规则 | DRPY2脚本 |
|------|-----------|---------|----------|
| 响应速度 | ⭐⭐⭐⭐⭐ (快) | ⭐⭐⭐ (中) | ⭐⭐ (慢) |
| 稳定性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| 维护成本 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| 数据丰富度 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

**建议**:
- 优先使用 **MacCMS API** (Type 0/1)
- 补充使用 **XBPQ规则** (Type 2)
- 仅在必要时使用 **DRPY2脚本** (Type 3)

---

## 🔄 批量管理JS爬虫

### 查看所有JS资源

```bash
# Windows PowerShell
Get-ChildItem "demo\Box系列\本地包\奇奇，20260414\tvboxqq\南风" -Recurse -Include *.json,*.js | 
  Select-Object FullName, @{Name="SizeKB";Expression={[Math]::Round($_.Length/1KB, 2)}}
```

### 批量启用/禁用

编辑 `data/sources/source_config.json`,批量修改 `enabled` 字段:

```json
// 全部启用
"enabled": true

// 全部禁用
"enabled": false
```

---

## 💡 最佳实践

### 1. 优先级策略

```
第一梯队 (主力): MacCMS API (2-3个高可用源)
第二梯队 (补充): XBPQ规则 (3-5个优质站点)  
第三梯队 (备选): DRPY2脚本 (仅特殊需求)
```

### 2. 健康检查

定期运行健康检查,剔除失效源:

```bash
# 访问健康检查API
curl http://localhost:8080/api/health

# 或在管理后台点击"健康检查"按钮
```

### 3. 备份配置

```bash
# 备份当前配置
Copy-Item data/sources/source_config.json data/sources/source_config.backup.json
```

### 4. 逐步启用

不要一次性启用所有JS爬虫,建议:
1. 先启用1-2个XBPQ规则测试
2. 验证功能正常后再添加更多
3. DRPY2脚本最后考虑(性能较差)

---

## 🎓 进阶: 自定义XBPQ规则

如果想自己编写XBPQ规则,参考以下模板:

```json
{
  "规则名": "我的影视站",
  "请求头参数": "User-Agent$手机",
  "首页推荐链接": "https://example.com",
  
  // 分类配置
  "分类名称": "电影&电视剧",
  "分类名称替换词": "1&2",
  "分类链接": "https://example.com/vod/{cateId}/pg/{catePg}.html",
  
  // 列表提取规则
  "分类列表数组规则": ".vod-list&&li",
  "分类片单标题": ".title&&Text",
  "分类片单链接": "a&&href",
  "分类片单图片": "img&&src",
  
  // 详情提取规则
  "详情是否Jsoup写法": "1",
  "演员详情": ".actor&&Text",
  "简介详情": ".desc&&Text",
  
  // 播放地址提取
  "线路列表数组规则": ".tab-content&&li",
  "播放列表数组规则": ".playlist&&li",
  "选集标题": "a&&Text",
  "选集链接": "a&&href"
}
```

**学习资源**:
- [XBPQ规则语法详解](https://github.com/qist/tvbox/blob/master/xbpq.md)
- [CSS选择器参考](https://www.w3school.com.cn/cssref/css_selectors.asp)

---

## 📞 获取帮助

如遇到问题:
1. 查看日志文件: `logs/tvsource.log`
2. 检查配置文件格式: `python -m json.tool data/sources/source_config.json`
3. 在管理后台查看数据源状态
4. 提交Issue并提供错误日志

---

**祝您集成顺利!** 🎉
