"""
快速启用JS爬虫工具

帮助用户快速启用已导入的JS爬虫数据源
"""

import json
from pathlib import Path


def enable_js_sources(config_file: str = "data/sources/source_config.json", 
                      source_types: list = None):
    """
    批量启用指定类型的数据源
    
    Args:
        config_file: 配置文件路径
        source_types: 要启用的数据类型列表 [0, 2, 3]
                     0=MacCMS API, 2=XBPQ规则, 3=DRPY2脚本
    """
    if source_types is None:
        source_types = [2, 3]  # 默认启用XBPQ和DRPY2
    
    # 读取配置
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    sources = config.get('sources', [])
    
    print("\n" + "="*60)
    print("📋 当前数据源状态:")
    print("="*60)
    
    enabled_count = 0
    for source in sources:
        name = source['name']
        stype = source.get('type', 0)
        was_enabled = source.get('enabled', False)
        
        type_name = {0: 'MacCMS', 2: 'XBPQ', 3: 'DRPY2'}.get(stype, f'Type{stype}')
        status = "✓ 已启用" if was_enabled else "✗ 已禁用"
        
        print(f"  [{status}] {name:20} ({type_name})")
        
        # 如果是指定类型且当前未启用,则启用
        if stype in source_types and not was_enabled:
            source['enabled'] = True
            enabled_count += 1
            print(f"         → 已启用 ✓")
    
    # 保存配置
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*60)
    print(f"✅ 操作完成!")
    print(f"   新启用数据源: {enabled_count} 个")
    print("="*60)
    
    if enabled_count > 0:
        print("\n💡 下一步:")
        print("   1. 重启服务以应用更改")
        print("      python src/app.py")
        print("   2. 访问管理后台查看状态")
        print("      http://localhost:8080/admin/")
    else:
        print("\nℹ️  没有新的数据源被启用")
    
    return config


if __name__ == "__main__":
    import sys
    
    print("\n" + "🔧 TVSource Studio - 快速启用JS爬虫".center(60))
    print("=" * 60)
    
    # 解析命令行参数
    if len(sys.argv) > 1:
        types_to_enable = []
        for arg in sys.argv[1:]:
            if arg.lower() in ['maccms', 'api', '0']:
                types_to_enable.append(0)
            elif arg.lower() in ['xbpq', 'rule', '2']:
                types_to_enable.append(2)
            elif arg.lower() in ['drpy2', 'js', '3']:
                types_to_enable.append(3)
        
        if not types_to_enable:
            print("\n❌ 无效的参数")
            print("\n用法:")
            print("  python scripts/enable_js_sources.py xbpq drpy2")
            print("  python scripts/enable_js_sources.py all  # 启用所有")
            sys.exit(1)
    else:
        # 默认启用XBPQ和DRPY2
        types_to_enable = [2, 3]
        print("\n💡 提示: 将启用所有XBPQ规则和DRPY2脚本")
        print("   如需自定义,请使用参数: xbpq drpy2 maccms all")
    
    if 'all' in [arg.lower() for arg in sys.argv[1:]] if len(sys.argv) > 1 else False:
        types_to_enable = [0, 2, 3]
    
    # 执行启用操作
    enable_js_sources(source_types=types_to_enable)
