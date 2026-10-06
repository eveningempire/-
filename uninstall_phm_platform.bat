@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
echo 重复使用运载器健康管理原型系统 - 一键卸载
choice /C YN /N /M "确认删除项目创建的 .venv 和 runtime\python310 吗?[Y/N] "
if errorlevel 2 exit /b 0
call "%~dp0stop_phm_platform.bat"
if exist ".venv" rmdir /s /q ".venv"
if exist "runtime\python310" rmdir /s /q "runtime\python310"
echo 已删除项目虚拟环境和包内 Python 运行时。
echo db.sqlite3、media、config 和用户数据未删除;如需彻底移除,请手动删除整个项目目录。
pause
