#!/usr/bin/env python
"""
整理主路径下的文件
将测试脚本、临时文件等移动到合适的目录
"""

import os
import shutil
import glob
from datetime import datetime

def create_directory_if_not_exists(directory):
    """创建目录（如果不存在）"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"✅ 创建目录: {directory}")

def move_files_by_pattern():
    """根据文件模式移动文件"""
    
    # 创建整理目录
    cleanup_dirs = {
        'temp_scripts': '临时脚本',
        'test_files': '测试文件', 
        'debug_files': '调试文件',
        'docs_temp': '临时文档',
        'json_backups': 'JSON备份'
    }
    
    for dir_name, description in cleanup_dirs.items():
        create_directory_if_not_exists(dir_name)
    
    # 定义文件移动规则
    move_rules = [
        # 测试脚本
        {
            'pattern': 'test_*.py',
            'target_dir': 'temp_scripts',
            'description': '测试脚本'
        },
        {
            'pattern': 'debug_*.py', 
            'target_dir': 'debug_files',
            'description': '调试脚本'
        },
        {
            'pattern': 'check_*.py',
            'target_dir': 'debug_files', 
            'description': '检查脚本'
        },
        {
            'pattern': 'fix_*.py',
            'target_dir': 'temp_scripts',
            'description': '修复脚本'
        },
        {
            'pattern': 'analyze_*.py',
            'target_dir': 'debug_files',
            'description': '分析脚本'
        },
        {
            'pattern': 'extract_*.py',
            'target_dir': 'temp_scripts',
            'description': '提取脚本'
        },
        {
            'pattern': 'suggest_*.py',
            'target_dir': 'temp_scripts',
            'description': '建议脚本'
        },
        {
            'pattern': 'cleanup_*.py',
            'target_dir': 'temp_scripts',
            'description': '清理脚本'
        },
        {
            'pattern': 'compare_*.py',
            'target_dir': 'debug_files',
            'description': '比较脚本'
        },
        {
            'pattern': 'update_*.py',
            'target_dir': 'temp_scripts',
            'description': '更新脚本'
        },
        {
            'pattern': 'verify_*.py',
            'target_dir': 'debug_files',
            'description': '验证脚本'
        },
        {
            'pattern': 'simple_*.py',
            'target_dir': 'debug_files',
            'description': '简单脚本'
        },
        
        # 临时文档
        {
            'pattern': '*.md',
            'target_dir': 'docs_temp',
            'description': 'Markdown文档'
        },
        
        # JSON备份文件
        {
            'pattern': '*.json',
            'target_dir': 'json_backups',
            'description': 'JSON配置文件'
        },
        
        # 输出文件
        {
            'pattern': '*.txt',
            'target_dir': 'debug_files',
            'description': '输出文件'
        }
    ]
    
    moved_files = []
    skipped_files = []
    
    for rule in move_rules:
        pattern = rule['pattern']
        target_dir = rule['target_dir']
        description = rule['description']
        
        # 查找匹配的文件
        matching_files = glob.glob(pattern)
        
        for file_path in matching_files:
            # 跳过一些重要文件
            if file_path in ['README.md', 'requirements.txt', 'manage.py']:
                skipped_files.append(f"{file_path} (重要文件，跳过)")
                continue
                
            # 跳过目录
            if os.path.isdir(file_path):
                continue
                
            # 构建目标路径
            target_path = os.path.join(target_dir, file_path)
            
            # 如果目标文件已存在，添加时间戳
            if os.path.exists(target_path):
                name, ext = os.path.splitext(file_path)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_name = f"{name}_{timestamp}{ext}"
                target_path = os.path.join(target_dir, new_name)
            
            try:
                shutil.move(file_path, target_path)
                moved_files.append(f"{file_path} -> {target_path}")
                print(f"📁 移动 {description}: {file_path} -> {target_path}")
            except Exception as e:
                print(f"❌ 移动失败 {file_path}: {e}")
    
    return moved_files, skipped_files

def create_readme_files():
    """为整理后的目录创建README文件"""
    
    readme_content = {
        'temp_scripts': """# 临时脚本目录

这个目录包含在开发过程中创建的临时脚本文件。

## 文件说明
- test_*.py: 测试脚本
- fix_*.py: 修复脚本  
- extract_*.py: 数据提取脚本
- suggest_*.py: 建议生成脚本
- cleanup_*.py: 清理脚本

## 注意事项
- 这些文件是临时性的，可能包含过时的代码
- 在删除前请确认不再需要
- 重要的修复脚本建议保存到版本控制系统
""",
        
        'debug_files': """# 调试文件目录

这个目录包含调试和分析过程中创建的文件。

## 文件说明
- debug_*.py: 调试脚本
- check_*.py: 检查脚本
- analyze_*.py: 分析脚本
- compare_*.py: 比较脚本
- verify_*.py: 验证脚本
- simple_*.py: 简单测试脚本
- *.txt: 输出文件

## 注意事项
- 这些文件主要用于问题诊断和调试
- 可以安全删除，但建议保留一段时间以防需要重新分析
""",
        
        'docs_temp': """# 临时文档目录

这个目录包含开发过程中创建的临时文档。

## 文件说明
- *.md: Markdown格式的文档
- 包含技术说明、问题分析、改进建议等

## 注意事项
- 重要的技术文档建议整理后保存到docs目录
- 临时性的分析文档可以定期清理
""",
        
        'json_backups': """# JSON备份目录

这个目录包含MSFG配置文件的备份。

## 文件说明
- *.json: MSFG配置文件
- 包含不同版本的配置备份

## 注意事项
- 重要的配置文件建议保存到版本控制系统
- 可以定期清理过时的备份文件
"""
    }
    
    for dir_name, content in readme_content.items():
        if os.path.exists(dir_name):
            readme_path = os.path.join(dir_name, 'README.md')
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"📝 创建README: {readme_path}")

def main():
    """主函数"""
    print("🧹 开始整理主路径文件")
    print("=" * 50)
    
    # 移动文件
    moved_files, skipped_files = move_files_by_pattern()
    
    # 创建README文件
    create_readme_files()
    
    # 输出结果
    print(f"\n📊 整理结果:")
    print(f"   移动文件: {len(moved_files)} 个")
    print(f"   跳过文件: {len(skipped_files)} 个")
    
    if moved_files:
        print(f"\n📁 移动的文件:")
        for file_info in moved_files:
            print(f"   {file_info}")
    
    if skipped_files:
        print(f"\n⏭️ 跳过的文件:")
        for file_info in skipped_files:
            print(f"   {file_info}")
    
    print(f"\n✅ 文件整理完成！")
    print(f"📁 整理后的目录结构:")
    
    for dir_name in ['temp_scripts', 'debug_files', 'docs_temp', 'json_backups']:
        if os.path.exists(dir_name):
            file_count = len([f for f in os.listdir(dir_name) if os.path.isfile(os.path.join(dir_name, f))])
            print(f"   {dir_name}/ ({file_count} 个文件)")

if __name__ == "__main__":
    main()
