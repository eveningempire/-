#!/bin/bash

echo "========================================"
echo "  CMG健康管理平台 - 系统启动"
echo "========================================"
echo

echo "正在启动系统..."
echo

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python未安装或不在PATH中"
    echo "请先安装Python 3.10+"
    exit 1
fi

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "❌ 虚拟环境不存在"
    echo "请先运行: python scripts/migration_setup.py"
    exit 1
fi

# 激活虚拟环境并启动系统
echo "🚀 启动CMG健康管理平台..."
echo

source .venv/bin/activate
python scripts/start_system.py

echo
echo "系统已停止运行"
