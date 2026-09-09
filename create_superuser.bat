@echo off
chcp 65001 >nul
REM 基于模型的寿命预测系统 - 管理员创建工具 (Windows批处理版本)

echo ======================================================================
echo                  基于模型的寿命预测系统
echo                     管理员账户创建工具
echo ======================================================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未检测到Python
    echo 请先安装Python 3.8或更高版本
    pause
    exit /b 1
)

echo ℹ️  使用方法:
echo    - 交互式创建: 直接运行此脚本
echo    - 快速创建:   运行 create_superuser.bat quick
echo.

REM 检查是否传入了quick参数
if "%1"=="quick" (
    python create_superuser.py --quick
) else if "%1"=="-q" (
    python create_superuser.py --quick
) else (
    python create_superuser.py
)

if errorlevel 1 (
    echo.
    echo ❌ 创建失败，请检查错误信息
    pause
    exit /b 1
)

echo.
pause

