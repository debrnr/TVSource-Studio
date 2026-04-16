# 🚀 5分钟快速上传到GitHub/Gitee

## ⚡ 最快方式(推荐)

### Windows用户

**双击运行**: [`upload_to_git.bat`](upload_to_git.bat)

脚本会自动:
1. ✅ 检查Git是否安装
2. ✅ 初始化仓库
3. ✅ 添加所有文件
4. ✅ 提交更改
5. ✅ 配置远程仓库
6. ✅ 推送到GitHub和Gitee

### Python用户(跨平台)

```bash
python upload_to_git.py
```

---

## 📝 手动操作(3步完成)

### 第1步: 在GitHub和Gitee创建仓库

**GitHub**:
1. 访问 https://github.com/new
2. 仓库名: `TVSource-Studio`
3. ❌ **不要**勾选"Initialize with README"
4. 点击 "Create repository"
5. 复制URL (类似: `https://github.com/你的用户名/TVSource-Studio.git`)

**Gitee**:
1. 访问 https://gitee.com/projects/new
2. 仓库名: `TVSource-Studio`
3. ❌ **不要**勾选"使用Readme文件初始化"
4. 点击 "创建"
5. 复制URL (类似: `https://gitee.com/你的用户名/TVSource-Studio.git`)

---

### 第2步: 打开PowerShell/CMD执行命令

```powershell
# 进入项目目录
cd "d:\DEBRNR_PYTHON\Project\TVSource Studio"

# 初始化Git
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit"

# 添加GitHub远程仓库 (替换YOUR_USERNAME为你的用户名)
git remote add origin https://github.com/YOUR_USERNAME/TVSource-Studio.git

# 添加Gitee远程仓库
git remote add gitee https://gitee.com/YOUR_USERNAME/TVSource-Studio.git

# 推送到GitHub (首次需要输入用户名和密码/token)
git push -u origin main

# 推送到Gitee
git push -u gitee main
```

---

### 第3步: 验证

访问您的仓库页面,确认文件已上传:
- GitHub: https://github.com/YOUR_USERNAME/TVSource-Studio
- Gitee: https://gitee.com/YOUR_USERNAME/TVSource-Studio

---

## 🔐 认证问题?

### GitHub需要使用Token而非密码

1. 访问: https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 选择权限: `repo`
4. 生成并复制token
5. 推送时:
   - Username: 你的GitHub用户名
   - Password: 粘贴刚才生成的token

### Gitee可以直接用密码

直接使用您的Gitee账号密码即可。

---

## ❓ 遇到问题?

查看详细指南: [`docs/GIT_UPLOAD_GUIDE.md`](docs/GIT_UPLOAD_GUIDE.md)

常见错误解决:
- **推送被拒绝**: `git pull --allow-unrelated-histories` 然后重新推送
- **大文件失败**: demo目录已被排除,不会上传
- **中文乱码**: `git config core.quotepath false`

---

**就这么简单!** 🎉
