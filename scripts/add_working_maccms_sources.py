"""
添加可用的MacCMS API源
"""
import json

config_file = "data/sources/source_config.json"

# 已知的可用MacCMS API源列表
working_sources = [
    {
        "name": "红牛资源",
        "type": 0,
        "api": "https://www.hongniuzy2.com/api.php/provide/vod/",
        "timeout": 10,
        "enabled": True,
        "metadata": {"category": "综合"}
    },
    {
        "name": "飞速资源",
        "type": 0,
        "api": "https://www.feisuzyapi.com/api.php/provide/vod/",
        "timeout": 10,
        "enabled": True,
        "metadata": {"category": "综合"}
    },
    {
        "name": "量子资源",
        "type": 0,
        "api": "https://cj.lziapi.com/api.php/provide/vod/",
        "timeout": 10,
        "enabled": True,
        "metadata": {"category": "综合"}
    },
    {
        "name": "非凡资源",
        "type": 0,
        "api": "http://cj.ffzyapi.com/api.php/provide/vod/",
        "timeout": 10,
        "enabled": True,
        "metadata": {"category": "综合"}
    },
    {
        "name": "卧龙资源",
        "type": 0,
        "api": "https://collect.wolongzyw.com/api.php/provide/vod/",
        "timeout": 10,
        "enabled": True,
        "metadata": {"category": "综合"}
    }
]

with open(config_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 添加新源(避免重复)
existing_apis = {s['api'] for s in data['sources'] if s.get('api')}
added_count = 0

for new_source in working_sources:
    if new_source['api'] not in existing_apis:
        data['sources'].append(new_source)
        added_count += 1
        print(f"✓ 添加: {new_source['name']}")
    else:
        print(f"- 跳过(已存在): {new_source['name']}")

with open(config_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\n✅ 成功添加 {added_count} 个MacCMS API源")
print(f"当前总数据源: {len(data['sources'])} 个")
print(f"启用的数据源: {len([s for s in data['sources'] if s.get('enabled', False)])} 个")
