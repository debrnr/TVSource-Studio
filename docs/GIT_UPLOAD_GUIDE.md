# 🚀 TVSource Studio - GitHub/Gitee 上传指南

## 📋 前置准备

### 1. 安装Git
- **Windows**: 从 [git-scm.com](https://git-scm.com/download/win) 下载并安装
- 验证安装: `git --version`

### 2. 创建仓库

#### GitHub
1. 访问 [github.com](https://github.com)
2. 点击右上角 "+" → "New repository"
3. 填写信息:
   - Repository name: `TVSource-Studio`
   - Description: `TVBox数据源聚合服务`
   - Public/Private: 根据需要选择
   - ❌ **不要**初始化README/.gitignore(我们已有)
4. 点击 "Create repository"
5. 复制仓库URL (例如: `https://github.com/yourusername/TVSource-Studio.git`)

#### Gitee
1. 访问 [gitee.com](https://gitee.com)
2. 点击右上角 "+" → "新建仓库"
3. 填写信息:
   - 仓库名称: `TVSource-Studio`
   - 介绍: `TVBox数据源聚合服务`
   - 公开/私有: 根据需要选择
   - ❌ **不要**勾选"使用Readme文件初始化这个仓库"
4. 点击 "创建"
5. 复制仓库URL (例如: `https://gitee.com/yourusername/TVSource-Studio.git`)

---

## 🎯 方法一: 使用自动化脚本(推荐)

### 步骤1: 运行上传脚本

```bash
python upload_to_git.py
```

### 步骤2: 按提示操作

脚本会引导您完成:
1. ✅ 初始化Git仓库
2. ✅ 添加所有文件
3. ✅ 提交更改
4. ✅ 配置GitHub远程仓库
5. ✅ 配置Gitee远程仓库
6. ✅ 推送到远程

### 步骤3: 输入认证信息

首次推送时需要:
- **HTTPS方式**: 输入GitHub/Gitee用户名和密码
- **SSH方式**: 确保已配置SSH密钥

---

## 🎯 方法二: 手动命令行操作

### 步骤1: 初始化Git

```bash
cd "d:\DEBRNR_PYTHON\Project\TVSource Studio"
git init
```

### 步骤2: 添加文件

```bash
git add .
```

### 步骤3: 提交

```bash
git commit -m "Initial commit: TVSource Studio project"
```

### 步骤4: 添加远程仓库

```bash
# 添加GitHub
git remote add origin https://github.com/YOUR_USERNAME/TVSource-Studio.git

# 添加Gitee
git remote add gitee https://gitee.com/YOUR_USERNAME/TVSource-Studio.git
```

> ⚠️ 将 `YOUR_USERNAME` 替换为您的实际用户名

### 步骤5: 推送

```bash
# 推送到GitHub
git push -u origin main

# 推送到Gitee
git push -u gitee main
```

如果分支名是 `master` 而不是 `main`:
```bash
git push -u origin master
git push -u gitee master
```

---

## 🔐 认证方式

### 方式1: HTTPS + 用户名密码(简单)

首次推送时会提示输入:
```
Username for 'https://github.com': your_username
Password for 'https://your_username@github.com': your_password
```

**注意**: 
- GitHub需要使用**Personal Access Token**代替密码
- Gitee可以直接使用密码

#### 生成GitHub Personal Access Token
1. 访问: https://github.com/settings/tokens
2. 点击 "Generate new token"
3. 选择权限: `repo` (完整仓库访问)
4. 生成并复制token
5. 推送时使用token作为密码

### 方式2: SSH密钥(推荐,更安全)

#### 生成SSH密钥
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

#### 添加公钥到GitHub
1. 复制公钥内容: `cat ~/.ssh/id_ed25519.pub`
2. 访问: https://github.com/settings/keys
3. 点击 "New SSH key"
4. 粘贴公钥并保存

#### 添加公钥到Gitee
1. 复制公钥内容
2. 访问: https://gitee.com/profile/sshkeys
3. 点击 "添加公钥"
4. 粘贴并保存

#### 使用SSH URL
```bash
# GitHub
git remote add origin git@github.com:YOUR_USERNAME/TVSource-Studio.git

# Gitee
git remote add gitee git@gitee.com:YOUR_USERNAME/TVSource-Studio.git
```

---

## ⚠️ 常见问题

### Q1: 推送被拒绝(non-fast-forward)

**原因**: 远程仓库已有内容

**解决**:
```bash
# 强制推送(谨慎使用,会覆盖远程历史)
git push -f origin main

# 或者先拉取再合并
git pull origin main --allow-unrelated-histories
git push origin main
```

### Q2: 大文件上传失败

**原因**: Git有文件大小限制

**解决**:
```bash
# 检查大文件
git ls-files | xargs du -h | sort -rh | head -20

# 如果demo目录太大,已在.gitignore中排除
# 如需上传,使用Git LFS
git lfs install
git lfs track "*.large_file"
```

### Q3: 中文文件名乱码

**解决**:
```bash
git config core.quotepath false
```

### Q4: 推送速度慢

**优化**:
```bash
# 增加缓冲区大小
git config http.postBuffer 524288000

# 或使用SSH而非HTTPS
```

### Q5: 忘记添加某些文件

**解决**:
```bash
git add forgotten_file.py
git commit --amend --no-edit
git push -f origin main
```

---

## 📊 上传后检查清单

- [ ] 访问GitHub仓库,确认所有文件已上传
- [ ] 访问Gitee仓库,确认所有文件已上传
- [ ] README.md中的仓库链接已更新
- [ ] LICENSE文件已添加(如需要)
- [ ] .gitignore正确排除了敏感文件
- [ ] 可以克隆仓库并正常运行

---

## 🔄 后续更新

每次修改代码后:

```bash
# 1. 查看更改
git status

# 2. 添加更改
git add .

# 3. 提交
git commit -m "描述您的更改"

# 4. 推送到两个平台
git push origin main
git push gitee main
```

---

## 💡 最佳实践

1. **频繁提交**: 每完成一个小功能就提交
2. **清晰的提交信息**: 说明做了什么,为什么
3. **分支管理**: 新功能在独立分支开发
4. **定期推送**: 避免本地丢失
5. **保护敏感信息**: 不要在代码中硬编码密码/API密钥

---

## 📞 需要帮助?

- [GitHub官方文档](https://docs.github.com/)
- [Gitee官方文档](https://gitee.com/help)
- [Git官方教程](https://git-scm.com/book/zh/v2)

---

**祝您上传顺利!** 🎉
