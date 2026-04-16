"""
配置合并工具

将多个数据源配置文件合并为一个统一配置
"""

import json
from pathlib import Path
from typing import List


def merge_configs(config_files: List[str], output_file: str = "data/sources/source_config.json"):
    """
    合并多个配置文件
    
    Args:
        config_files: 配置文件路径列表
        output_file: 输出文件路径
    """
    all_sources = []
    
    for config_file in config_files:
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            sources = config.get('sources', [])
            all_sources.extend(sources)
            
            print(f"✓ 加载 {config_file}: {len(sources)} 个数据源")
            
        except Exception as e:
            print(f"✗ 加载失败 [{config_file}]: {e}")
    
    # 去重(按名称) - 优先保留有metadata的版本
    seen_names = {}
    unique_sources = []

    for source in all_sources:
        name = source['name']
        
        if name not in seen_names:
            # 第一次出现,直接添加
            seen_names[name] = len(unique_sources)
            unique_sources.append(source)
        else:
            # 已存在,比较哪个版本更好(有metadata的优先)
            existing_idx = seen_names[name]
            existing_source = unique_sources[existing_idx]
            
            # 如果新源有metadata而旧源没有,替换
            if 'metadata' in source and 'metadata' not in existing_source:
                unique_sources[existing_idx] = source
                print(f"⚠ 更新数据源 {name}: 使用更完整的版本")
            else:
                print(f"⚠ 跳过重复数据源: {name}")
    
    # 构建最终配置
    merged_config = {
        "version": "1.0",
        "description": "TVSource Studio 统一数据源配置(已合并JS爬虫)",
        "total_sources": len(unique_sources),
        "sources": unique_sources
    }
    
    # 写入文件
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged_config, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*60)
    print(f"✅ 配置合并完成!")
    print(f"   输出文件: {output_file}")
    print(f"   总数据源: {len(unique_sources)} 个")
    print("="*60)
    
    # 统计信息
    type_stats = {}
    for source in unique_sources:
        source_type = source.get('type', 0)
        type_name = {0: 'MacCMS API', 2: 'XBPQ规则', 3: 'DRPY2脚本'}.get(source_type, f'Type {source_type}')
        type_stats[type_name] = type_stats.get(type_name, 0) + 1
    
    print("\n📊 类型分布:")
    for type_name, count in type_stats.items():
        print(f"   • {type_name}: {count} 个")
    
    return merged_config


if __name__ == "__main__":
    print("\n" + "🔧 TVSource Studio - 配置合并工具".center(60))
    print("=" * 60)
    
    # 要合并的配置文件
    configs_to_merge = [
        "data/sources/source_config.json",  # 原有配置
        "data/sources/js_sources.json"       # JS爬虫配置
    ]
    
    # 检查文件是否存在
    existing_configs = [f for f in configs_to_merge if Path(f).exists()]
    
    if not existing_configs:
        print("\n❌ 错误: 没有找到任何配置文件!")
        exit(1)
    
    print(f"\n发现 {len(existing_configs)} 个配置文件:")
    for config in existing_configs:
        print(f"   • {config}")
    
    # 执行合并
    merge_configs(existing_configs)
    
    print("\n💡 提示:")
    print("   重启服务以应用新配置: python src/app.py")
