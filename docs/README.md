# 🎬 TVBox Source Studio

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Docker](https://img.shields.io/badge/Docker-Supported-orange.svg)

**TVBox源聚合服务 - 自动收集、验证和生成TVBox可用源**

[快速开始](#-快速开始) • [使用说明](docs/GUIDE.md) • [Docker部署](deploy/) • [问题反馈](../../issues)

</div>

---

## 📺 项目简介

TVBox Source Studio 是一个运行在本地或NAS上的TVBox源聚合服务，能够：

- 🎬 **自动收集影视源** - 从多个优质源聚合影视内容
- 📡 **自动收集直播源** - 整合国内外IPTV直播源
- 📋 **EPG节目单管理** - 自动生成和更新电子节目指南
- 🔄 **定时自动更新** - 无需手动维护
- 🌐 **HTTP服务提供** - 通过局域网访问

## ✨ 功能特性

- ✅ 支持多种影视源API（MacCMS标准）
- ✅ 支持M3U/TXT格式直播源
- ✅ 完整的EPG节目单支持
- ✅ TVBox/影视仓完全兼容
- ✅ Docker一键部署
- ✅ Web界面管理
- ✅ 自动源验证和清洗
- ✅ 多线路解析支持

## 🚀 快速开始

### 方式一：Windows直接运行（推荐新手）

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/tvsource-studio.git
cd tvsource-studio

# 2. 初始化环境
activate_env.bat

# 3. 启动服务
start.bat
```

### 方式二：Docker部署（推荐生产环境）

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/tvsource-studio.git
cd tvsource-studio

# 2. 启动服务
cd deploy
docker-compose up -d
```

### 访问服务

服务启动后，访问：
- **主页**: http://localhost:8080
- **健康检查**: http://localhost:8080/api/health

## 📱 TVBox配置

在TVBox/影视仓中输入配置地址：

```
http://你的IP:8080/api/tvbox/config
```

例如：
```
http://192.168.0.88:8080/api/tvbox/config
```

配置成功后，TVBox首页会显示：
- 🎬 电影
- 📺 电视剧
- 🎭 综艺
- 🎨 动漫

## 📡 直播源地址

- **M3U格式**: `http://你的IP:8080/iptv/live.m3u`
- **TXT格式**: `http://你的IP:8080/iptv/live.txt`
- **EPG节目单**: `http://你的IP:8080/epg/epg.xml`

## 📖 详细文档

完整的使用说明、配置教程、常见问题等，请查看：

👉 **[完整使用指南](docs/GUIDE.md)**

## 🏗️ 项目结构

```
TVSource Studio/
├── activate_env.bat          # 环境激活脚本
├── start.bat                 # 服务启动脚本
├── README.md                 # 项目说明
├── .gitignore                # Git忽略配置
│
├── config/                   # 配置文件
│   ├── .env                  # 环境配置
│   ├── .env.example          # 配置示例
│   └── requirements.txt      # Python依赖
│
├── src/                      # 核心代码
│   ├── app.py                # Flask应用入口
│   ├── routes.py             # API路由定义
│   └── tasks/                # 任务模块
│       ├── source_collector.py
│       ├── source_validator.py
│       └── epg_manager.py
│
├── deploy/                   # 部署配置
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── docs/                     # 文档
│   └── GUIDE.md              # 完整使用指南
│
├── data/                     # 运行时数据
├── logs/                     # 日志文件
└── venv/                     # 虚拟环境
```

## ⚙️ 配置说明

编辑 `config/.env` 文件：

```env
# 服务器配置
HOST=0.0.0.0
PORT=8080

# 更新间隔（小时）
UPDATE_INTERVAL=6

# 日志级别
LOG_LEVEL=INFO
```

## 🔧 技术栈

- **后端框架**: Flask 2.0+
- **定时任务**: APScheduler
- **HTTP客户端**: Requests
- **数据处理**: JSON
- **容器化**: Docker & Docker Compose

## 📊 系统要求

- Python 3.8+
- 内存: 512MB+
- 磁盘: 100MB+
- 网络: 需要访问GitHub/Gitee

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目仅供学习和个人使用，请勿用于商业用途。

## 🌟 致谢

感谢以下开源项目：

- [TVBox](https://github.com/CatVodTVOfficial/TVBoxOSC)
- [iptv-org](https://github.com/iptv-org/iptv)
- [fanmingming/live](https://github.com/fanmingming/live)
- 所有贡献者

## 📮 联系方式

- 问题反馈: [Issues](../../issues)
- 功能建议: [Discussions](../../discussions)

---

<div align="center">

**如果这个项目对你有帮助，请给个⭐ Star！**

Made with ❤️ by TVBox Source Studio Team

</div>
