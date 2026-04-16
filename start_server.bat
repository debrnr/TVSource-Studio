@echo off
chcp 65001 >nul
echo ========================================
echo   TVSource Studio - 启动服务
echo ========================================
echo.

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 检查依赖
echo [1/3] 检查依赖...
pip list | findstr "aiohttp" >nul
if errorlevel 1 (
    echo 安装缺失的依赖...
    pip install aiohttp jsonpath-ng pydantic beautifulsoup4 lxml flask-cors
)

REM 启动Flask应用
echo [2/3] 启动Flask应用...
echo.
echo ✓ TVBox API端点: http://localhost:8080/api/vod
echo ✓ 管理后台:      http://localhost:8080/admin/
echo ✓ 健康检查:      http://localhost:8080/api/health
echo.
echo [3/3] 服务运行中... (按Ctrl+C停止)
echo ========================================
echo.

python src/app.py

pause
