"""
TVSource Studio - GitHub/Gitee 上传助手

此脚本帮助您将项目推送到GitHub和Gitee。
使用前请确保:
1. 已安装Git
2. 已配置SSH密钥或HTTPS凭据
3. 已在GitHub/Gitee创建空仓库
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """执行命令并显示结果"""
    print(f"\n🔄 {description}...")
    print(f"   命令: {cmd}")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        print(f"   ✅ 成功")
        if result.stdout:
            print(f"   输出: {result.stdout[:200]}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ 失败: {e.stderr[:200] if e.stderr else str(e)}")
        return False

def setup_git():
    """初始化Git仓库"""
    project_root = Path(__file__).parent
    
    print("=" * 60)
    print("🚀 TVSource Studio - Git上传助手".center(50))
    print("=" * 60)
    print()
    
    # 检查是否已初始化Git
    git_dir = project_root / ".git"
    if not git_dir.exists():
        print("📝 步骤1: 初始化Git仓库")
        if not run_command("git init", "初始化Git仓库"):
            return False
    else:
        print("✅ Git仓库已存在,跳过初始化")
    
    # 添加所有文件
    print("\n📝 步骤2: 添加文件到暂存区")
    if not run_command("git add .", "添加所有文件"):
        return False
    
    # 提交
    print("\n📝 步骤3: 提交更改")
    commit_msg = input("请输入提交信息 (默认: Initial commit): ").strip()
    if not commit_msg:
        commit_msg = "Initial commit"
    
    if not run_command(f'git commit -m "{commit_msg}"', "提交更改"):
        print("   ⚠️  如果没有更改,这是正常的")
    
    return True

def add_remote():
    """添加远程仓库"""
    print("\n" + "=" * 60)
    print("🔗 配置远程仓库")
    print("=" * 60)
    print()
    
    # GitHub
    github_url = input("请输入GitHub仓库URL (例如: https://github.com/username/TVSource-Studio.git): ").strip()
    if github_url:
        # 先删除已存在的origin
        run_command("git remote remove origin", "删除旧的origin远程")
        if run_command(f"git remote add origin {github_url}", "添加GitHub远程仓库"):
            print("   ✅ GitHub远程仓库已添加")
        else:
            print("   ⚠️  可以稍后手动添加")
    
    # Gitee
    gitee_url = input("\n请输入Gitee仓库URL (例如: https://gitee.com/username/TVSource-Studio.git): ").strip()
    if gitee_url:
        if run_command(f"git remote add gitee {gitee_url}", "添加Gitee远程仓库"):
            print("   ✅ Gitee远程仓库已添加")
        else:
            print("   ⚠️  可以稍后手动添加")

def push_to_remotes():
    """推送到远程仓库"""
    print("\n" + "=" * 60)
    print("📤 推送到远程仓库")
    print("=" * 60)
    print()
    
    branch = input("请输入分支名 (默认: main): ").strip() or "main"
    
    # 推送到GitHub
    push_github = input("\n是否推送到GitHub? (y/n, 默认: y): ").strip().lower()
    if push_github != 'n':
        print("\n📤 推送到GitHub...")
        if run_command(f"git push -u origin {branch}", "推送到GitHub"):
            print("   🎉 GitHub推送成功!")
        else:
            print("   ⚠️  推送失败,请检查:")
            print("      1. 仓库URL是否正确")
            print("      2. 是否有推送权限")
            print("      3. 是否需要认证(用户名/密码或SSH密钥)")
    
    # 推送到Gitee
    push_gitee = input("\n是否推送到Gitee? (y/n, 默认: y): ").strip().lower()
    if push_gitee != 'n':
        print("\n📤 推送到Gitee...")
        if run_command(f"git push -u gitee {branch}", "推送到Gitee"):
            print("   🎉 Gitee推送成功!")
        else:
            print("   ⚠️  推送失败,请检查:")
            print("      1. 仓库URL是否正确")
            print("      2. 是否有推送权限")
            print("      3. 是否需要认证")

def show_summary():
    """显示总结"""
    print("\n" + "=" * 60)
    print("✅ 完成!".center(50))
    print("=" * 60)
    print()
    print("💡 后续操作:")
    print("  1. 访问您的GitHub/Gitee仓库查看代码")
    print("  2. 更新README.md中的仓库链接")
    print("  3. 添加LICENSE文件(如需要)")
    print("  4. 配置GitHub Actions/Gitee Go进行CI/CD")
    print()
    print("📝 常用Git命令:")
    print("  git status          - 查看状态")
    print("  git add .           - 添加所有更改")
    print("  git commit -m 'msg' - 提交更改")
    print("  git push            - 推送到远程")
    print("  git pull            - 拉取最新更改")
    print()

def main():
    """主函数"""
    try:
        # 步骤1: 初始化Git
        if not setup_git():
            print("\n❌ Git初始化失败")
            return
        
        # 步骤2: 添加远程仓库
        add_remote()
        
        # 步骤3: 推送
        push_to_remotes()
        
        # 步骤4: 显示总结
        show_summary()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  操作被用户中断")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
