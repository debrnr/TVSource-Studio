# 🎬 TVSource Studio

> 强大的TVBox数据源聚合服务,部署在群晖NAS上,提供标准化的MacCMS API接口

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## ✨ 核心特性

### 🚀 高性能
- **异步IO** - 基于aiohttp的高并发请求
- **连接池** - TCP连接复用,降低延迟
- **批量处理** - 多数据源并行聚合,提升3-5倍速度
- **智能缓存** - 适配器实例自动缓存

### 🛡️ 高可用
- **自动重试** - 指数退避策略,应对网络波动
- **熔断保护** - Circuit Breaker模式,防止雪崩
- **健康检查** - 实时监控数据源状态
- **故障转移** - 单点故障不影响整体服务

### 🎯 标准化
- **MacCMS协议** - 完全兼容TVBox客户端
- **RESTful API** - 标准HTTP接口
- **CORS支持** - 跨域访问无忧
- **统一数据模型** - 内部一致性强

### 🎨 易用性
- **Web管理后台** - 可视化配置管理
- **热更新** - JSON配置即时生效
- **模块化设计** - 易于扩展新适配器
- **完善文档** - 快速上手指南

---

## 📦 支持的數據源类型

| 类型 | 名称 | 难度 | 稳定性 | 说明 |
|------|------|------|--------|------|
| Type 0/1 | MacCMS API | ⭐ | ⭐⭐⭐⭐⭐ | 标准API,最稳定 |
| Type 2/4 | XBPQ规则引擎 | ⭐⭐⭐ | ⭐⭐⭐⭐ | 配置化解析HTML |
| Type 3 | DRPY2 JS爬虫 | ⭐⭐⭐⭐ | ⭐⭐⭐ | JavaScript运行时 |

---

## 🚀 快速开始

### 1. 安装依赖

```bash
# 激活虚拟环境
.\venv\Scripts\activate

# 安装核心依赖
pip install aiohttp jsonpath-ng pydantic beautifulsoup4 lxml flask-cors
```

### 2. 配置数据源

编辑 `data/sources/source_config.json`:

```json
{
  "sources": [
    {
      "name": "三六零影视",
      "type": 0,
      "api": "https://360zy.com/api.php/provide/vod",
      "timeout": 10,
      "enabled": true
    }
  ]
}
```

### 3. 启动服务

```bash
# Windows
start_server.bat

# Linux/Mac
python src/app.py
```

### 4. 访问服务

- **TVBox API**: `http://localhost:8080/api/vod`
- **管理后台**: `http://localhost:8080/admin/`
- **健康检查**: `http://localhost:8080/api/health`

### 5. TVBox配置

在TVBox客户端中输入接口地址:
```
http://192.168.0.88:8080/api/vod
```

---

## 📚 API文档

### TVBox标准API

#### 获取影片列表
```
GET /api/vod?ac=list&t=1&pg=1
```

**参数**:
- `ac`: 动作类型 (`list`/`detail`)
- `t`: 分类ID
- `pg`: 页码
- `wd`: 搜索关键词

**响应**:
```json
{
  "code": 1,
  "msg": "success",
  "page": 1,
  "pagecount": 10,
  "limit": 20,
  "total": 200,
  "list": [...],
  "class": [...]
}
```

#### 获取影片详情
```
GET /api/vod?ac=detail&ids=source_name$12345
```

#### 搜索影片
```
GET /api/vod?ac=list&wd=复仇者联盟&pg=1
```

### 管理后台API

| 端点 | 方法 | 功能 |
|------|------|------|
| `/admin/api/sources` | GET | 获取数据源列表 |
| `/admin/api/sources` | POST | 添加数据源 |
| `/admin/api/sources/{name}` | DELETE | 删除数据源 |
| `/admin/api/health` | GET | 健康检查 |
| `/admin/api/stats` | GET | 统计信息 |

---

## 🏗️ 架构设计

```
┌─────────────────────────────────────┐
│      Flask Web Server               │
│  - TVBox API Blueprint              │
│  - Admin Panel Blueprint            │
│  - Global CORS                      │
└──────────┬──────────────────────────┘
           │
    ┌──────▼───────┐
    │SourceManager │
    │ - Config Mgmt│
    │ - Adapter    │
    │   Factory    │
    └──────┬───────┘
           │
    ┌──────┼──────────┐
    │      │          │
 ┌──▼──┐ ┌─▼───┐ ┌───▼────┐
 │Mac  │ │XBPQ │ │ DRPY2  │
 │CMS  │ │Eng  │ │Runtime │
 └──┬──┘ └─┬───┘ └───┬────┘
    │      │         │
    └──────┼─────────┘
           │
    ┌──────▼────────┐
    │ HTTPClient    │
    │ - Retry       │
    │ - Circuit     │
    │   Breaker     │
    └───────────────┘
```

---

## 📖 详细文档

- [核心架构文档](docs/CORE_ARCHITECTURE.md) - 详细的模块设计
- [快速开始指南](docs/QUICKSTART.md) - 5分钟上手
- [Phase 2&3完成报告](docs/PHASE2_3_COMPLETION.md) - 新增功能说明

---

## 🧪 测试

```bash
# 核心架构测试
python test/test_core_architecture.py

# 完整功能测试
python test/test_full_features.py
```

---

## 🛠️ 技术栈

### 后端框架
- **Flask** - Web框架
- **aiohttp** - 异步HTTP客户端
- **APScheduler** - 定时任务调度

### 数据处理
- **BeautifulSoup4** - HTML解析
- **jsonpath-ng** - JSONPath查询
- **pydantic** - 数据验证

### 前端
- **原生HTML/CSS/JS** - 管理后台界面
- **Flask-CORS** - 跨域支持

---

## 📝 项目结构

```
TVSource Studio/
├── src/
│   ├── core/                  # 核心模块
│   │   ├── vod_source.py      # 统一接口
│   │   ├── source_manager.py  # 配置管理器
│   │   ├── http_client.py     # HTTP客户端
│   │   ├── batch_processor.py # 批量处理器
│   │   └── adapters/          # 适配器实现
│   │       ├── maccms_adapter.py
│   │       ├── xbpq_adapter.py
│   │       └── drpy2_adapter.py
│   ├── tvbox_routes.py        # TVBox API路由
│   ├── admin_routes.py        # 管理后台路由
│   ├── app.py                 # Flask应用入口
│   └── templates/             # HTML模板
│       └── admin/
│           └── dashboard.html
├── data/
│   └── sources/
│       └── source_config.json # 数据源配置
├── test/                      # 测试脚本
├── docs/                      # 文档
├── demo/                      # TVBox参考资料
└── start_server.bat           # 启动脚本
```

---

## 🤝 贡献指南

欢迎提交Issue和Pull Request!

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

---

## 📄 许可证

本项目采用MIT许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🌐 代码仓库

- **GitHub**: [https://github.com/YOUR_USERNAME/TVSource-Studio](https://github.com/YOUR_USERNAME/TVSource-Studio)
- **Gitee**: [https://gitee.com/YOUR_USERNAME/TVSource-Studio](https://gitee.com/YOUR_USERNAME/TVSource-Studio)

> 💡 提示: 请将 `YOUR_USERNAME` 替换为您的实际用户名

---

## 🙏 致谢

- [TVBox开源项目](https://github.com/CatVodTVOfficial/TVBoxOSC)
- [DRPY2框架](https://github.com/hjdhnx/dr_py)
- [MacCMS](http://www.maccms.la/)

---

## 📮 联系方式

如有问题或建议,请提交Issue或联系维护团队。

**祝您使用愉快!** 🎉
