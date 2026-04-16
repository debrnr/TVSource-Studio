@echo off
chcp 65001 >nul
echo ============================================================
echo    TVSource Studio - GitHub/Gitee 快速上传
echo ============================================================
echo.

REM 检查Git是否安装
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Git,请先安装Git
    echo 下载地址: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo [步骤1/4] 初始化Git仓库...
if not exist ".git" (
    git init
    if %errorlevel% neq 0 (
        echo [失败] Git初始化失败
        pause
        exit /b 1
    )
    echo [成功] Git仓库已创建
) else (
    echo [跳过] Git仓库已存在
)
echo.

echo [步骤2/4] 添加文件到暂存区...
git add .
if %errorlevel% neq 0 (
    echo [失败] 文件添加失败
    pause
    exit /b 1
)
echo [成功] 文件已添加
echo.

echo [步骤3/4] 提交更改...
set /p commit_msg="请输入提交信息 (直接回车使用默认信息): "
if "%commit_msg%"=="" set commit_msg=Initial commit

git commit -m "%commit_msg%"
if %errorlevel% neq 0 (
    echo [提示] 如果没有更改,这是正常的
)
echo.

echo [步骤4/4] 配置远程仓库并推送
echo.
echo 请准备以下信息:
echo   1. GitHub仓库URL (例如: https://github.com/username/TVSource-Studio.git)
echo   2. Gitee仓库URL (例如: https://gitee.com/username/TVSource-Studio.git)
echo.
pause

echo.
set /p github_url="请输入GitHub仓库URL (直接回车跳过): "
if not "%github_url%"=="" (
    git remote remove origin 2>nul
    git remote add origin %github_url%
    echo [成功] GitHub远程仓库已添加
    
    set /p push_github="是否推送到GitHub? (y/n, 默认y): "
    if /i not "%push_github%"=="n" (
        echo.
        echo 正在推送到GitHub...
        git push -u origin main
        if %errorlevel% equ 0 (
            echo [成功] GitHub推送完成!
        ) else (
            echo [失败] 推送失败,请检查URL和认证信息
        )
    )
)

echo.
set /p gitee_url="请输入Gitee仓库URL (直接回车跳过): "
if not "%gitee_url%"=="" (
    git remote remove gitee 2>nul
    git remote add gitee %gitee_url%
    echo [成功] Gitee远程仓库已添加
    
    set /p push_gitee="是否推送到Gitee? (y/n, 默认y): "
    if /i not "%push_gitee%"=="n" (
        echo.
        echo 正在推送到Gitee...
        git push -u gitee main
        if %errorlevel% equ 0 (
            echo [成功] Gitee推送完成!
        ) else (
            echo [失败] 推送失败,请检查URL和认证信息
        )
    )
)

echo.
echo ============================================================
echo    ✅ 上传流程完成!
echo ============================================================
echo.
echo 提示:
echo   1. 访问您的GitHub/Gitee仓库查看代码
echo   2. 更新README.md中的仓库链接
echo   3. 后续更新使用: git add . ^&^& git commit -m "msg" ^&^& git push
echo.
pause
