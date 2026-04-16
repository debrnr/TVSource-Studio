"""
临时禁用XBPQ规则(因为适配器尚未完全实现)
"""
import json

config_file = "data/sources/source_config.json"

with open(config_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

disabled_count = 0
for source in data['sources']:
    if source['type'] == 2 and source.get('enabled', False):
        source['enabled'] = False
        disabled_count += 1
        print(f"✗ 禁用: {source['name']}")

with open(config_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\n✅ 已禁用 {disabled_count} 个XBPQ规则")
print(f"当前启用的数据源: {len([s for s in data['sources'] if s['enabled']])} 个")
print("\n提示: XBPQ适配器核心方法(get_categories/get_vod_list)尚未实现")
print("      待完善后再启用这些规则")
