# 🎉 TVSource Studio 项目发布成功!

## 📊 发布信息

**发布时间**: 2026-04-16  
**版本**: v1.0.0 (Initial Release)  
**代码量**: 89,771行  
**文件数**: 85个对象

---

## 🔗 仓库地址

### 主要仓库
- **GitHub**: https://github.com/debrnr/TVSource-Studio ⭐
- **Gitee**: https://gitee.com/debrnr/tvsource-studio ⭐

### 快速访问
```bash
# 克隆GitHub仓库
git clone https://github.com/debrnr/TVSource-Studio.git

# 克隆Gitee仓库(国内更快)
git clone https://gitee.com/debrnr/tvsource-studio.git
```

---

## 📦 项目简介

**TVSource Studio** 是一个强大的TVBox数据源聚合服务,部署在群晖NAS上,提供标准化的MacCMS API接口。

### 核心功能
✅ **多源聚合** - 支持MacCMS API、XBPQ规则、DRPY2脚本等多种数据源  
✅ **自动更新** - 定时任务自动收集和验证源可用性  
✅ **Web管理** - 可视化后台管理所有数据源配置  
✅ **标准接口** - 完全兼容TVBox客户端的MacCMS协议  
✅ **高可用** - 自动重试、熔断保护、故障转移机制  

### 技术栈
- **后端**: Python 3.8+ + Flask 3.0
- **异步IO**: aiohttp
- **数据库**: SQLite (缓存)
- **定时任务**: APScheduler
- **前端**: HTML + CSS + JavaScript (管理后台)

---

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone https://gitee.com/debrnr/tvsource-studio.git
cd tvsource-studio
```

### 2. 安装依赖
```bash
pip install -r config/requirements.txt
```

### 3. 启动服务
```bash
python src/app.py
```

### 4. 访问服务
- **主页**: http://localhost:8080
- **管理后台**: http://localhost:8080/admin/
- **TVBox配置**: http://localhost:8080/api/tvbox/config

---

## 📁 项目结构

```
TVSource-Studio/
├── src/                    # 源代码
│   ├── core/              # 核心模块
│   │   ├── adapters/      # 数据源适配器
│   │   ├── source_manager.py
│   │   └── ...
│   ├── routes.py          # API路由
│   ├── app.py             # 应用入口
│   └── ...
├── data/                   # 数据目录
│   ├── sources/           # 配置文件
│   ├── output/            # 输出文件
│   └── rules/             # 规则文件(不提交)
├── scripts/                # 工具脚本
├── docs/                   # 文档
├── config/                 # 配置文件
└── README.md
```

---

## 📝 已上传内容

### ✅ 包含的文件
- 所有Python源代码 (`src/`)
- 配置文件模板 (`config/`, `.env.example`)
- 完整文档 (`docs/`)
- 工具脚本 (`scripts/`)
- HTML模板 (`templates/`)
- 测试文件 (`test/`)
- 部署配置 (`deploy/`)

### ❌ 排除的文件(.gitignore)
- `demo/` - DEMO目录(外部资源,太大)
- `venv/` - Python虚拟环境
- `logs/` - 日志文件
- `data/sources/*.json` - 运行时配置
- `data/rules/` - 规则文件
- `.env` - 环境变量(含敏感信息)

---

## 💡 使用建议

### 对于开发者
1. **Fork项目** - 创建自己的分支进行开发
2. **阅读文档** - 查看 `docs/` 目录了解架构设计
3. **提交Issue** - 发现问题或建议随时反馈
4. **Pull Request** - 欢迎贡献代码

### 对于使用者
1. **克隆仓库** - 获取最新代码
2. **配置环境** - 修改 `.env` 文件设置参数
3. **添加数据源** - 通过管理后台或编辑JSON配置
4. **定期更新** - `git pull` 获取最新功能和修复

---

## 🔄 后续更新流程

### 本地修改后推送
```bash
# 1. 查看更改
git status

# 2. 添加更改
git add .

# 3. 提交
git commit -m "描述您的更改"

# 4. 推送到两个平台
git push origin master
git push gitee master
```

### 从远程拉取更新
```bash
git pull origin master
git pull gitee master
```

---

## 📞 联系方式

- **GitHub Issues**: https://github.com/debrnr/TVSource-Studio/issues
- **Gitee Issues**: https://gitee.com/debrnr/tvsource-studio/issues
- **Email**: (待补充)

---

## 🙏 致谢

感谢以下开源项目:
- [TVBox](https://github.com/CatVodTVOfficial/TVBoxOSC)
- [DRPY2](https://github.com/hjdhnx/dr_py)
- [MacCMS](http://www.maccms.la/)
- [Flask](https://flask.palletsprojects.com/)

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

**祝您使用愉快!** 🎉

如有任何问题,欢迎提交Issue或联系维护者。
