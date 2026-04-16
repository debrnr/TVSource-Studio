# Test Scripts - 测试脚本目录

## 📁 说明

本目录存放所有**测试脚本**和**临时诊断工具**，用于开发调试和问题排查。

---

## 📋 当前脚本清单

### 1. diagnose_tvbox_issue.py
**用途**：TVBox数据显示问题诊断工具

**功能**：
- 检查API响应结构完整性
- 验证必需字段（class、page、total等）
- 检查数据类型兼容性
- 输出详细诊断报告

**使用方法**：
```powershell
.\venv\Scripts\python.exe test/diagnose_tvbox_issue.py
```

**适用场景**：
- TVBox只显示少量数据
- 分类导航不显示
- API响应异常排查

---

### 2. quick_test.py
**用途**：快速验证API响应

**功能**：
- 简化版诊断，快速检查关键字段
- 验证class字段是否存在
- 确认分页字段类型

**使用方法**：
```powershell
.\venv\Scripts\python.exe test/quick_test.py
```

**适用场景**：
- 代码修改后快速验证
- 日常健康检查

---

## 🔧 添加新测试脚本规范

### 命名规范
- 使用小写字母和下划线
- 以功能描述命名，如 `test_xxx.py` 或 `diagnose_xxx.py`
- 示例：
  - `test_api_response.py`
  - `diagnose_cache_issue.py`
  - `check_k1k_adapter.py`

### 脚本要求
1. **自包含**：脚本应能独立运行，无需额外参数
2. **清晰输出**：使用emoji和分隔线提高可读性
3. **错误处理**：包含try-except捕获异常
4. **中文注释**：关键步骤添加中文说明

### 模板示例
```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试脚本描述"""

import requests
import json

print("="*80)
print("测试标题")
print("="*80)

try:
    # 测试逻辑
    response = requests.get("http://127.0.0.1:8080/api/xxx", timeout=10)
    data = response.json()
    
    print(f"\n✅ 测试结果: {data['status']}")
    
except Exception as e:
    print(f"\n❌ 测试失败: {e}")
```

---

## ⚠️ 注意事项

### Git管理
- ✅ **可以提交**：有长期价值的诊断工具（如 `diagnose_tvbox_issue.py`）
- ❌ **不应提交**：一次性临时测试脚本

**判断标准**：
- 如果脚本可能在未来重复使用 → 提交到Git
- 如果只是临时调试用 → 添加到 `.gitignore`

### 清理策略
- 定期清理不再使用的临时脚本
- 保留有价值的诊断工具
- 更新本文档中的脚本清单

---

## 📊 历史脚本归档

以下脚本已完成使命，已删除或归档：

### 已删除的测试脚本
- `analyze_k1k.py` - k1k数据分析（功能已整合到正式代码）
- `analyze_k1k_detail.py` - k1k详细分析
- `check_data_composition.py` - 数据构成检查
- `test_api_sources.py` - API源测试v1
- `test_api_sources_2026.py` - API源测试v2
- `test_k1k_complete.py` - k1k完整测试
- `test_k1k_fix.py` - k1k修复测试
- `test_k1k_quick.py` - k1k快速测试
- `test_multiple_sites.py` - 多站点测试
- `test_new_sources.py` - 新源测试
- `verify_api_data.py` - API数据验证
- `verify_categories.py` - 分类验证
- `verify_flags.py` - 标志验证
- `extract_type1_sites.py` - Type1站点提取
- `evaluate_websites.py` - 网站评估（结果保存在 `data/results/`）

**原因**：这些是开发过程中的临时测试脚本，功能已整合到正式代码或不再需要。

---

## 🎯 最佳实践

### 1. 优先使用正式工具
- API健康检查 → `tools/health_check_api_sources.py`
- k1k适配器测试 → 直接调用 `tools/k1k_adapter.py`

### 2. 测试脚本仅用于调试
- 不要将业务逻辑写在测试脚本中
- 测试脚本应保持简洁、专注单一功能

### 3. 及时清理
- 问题解决后立即删除临时脚本
- 保留有价值的诊断工具并更新文档

---

## 📝 更新日志

### 2026-04-15
- ✅ 创建 test/ 目录
- ✅ 移动 diagnose_tvbox_issue.py
- ✅ 移动 quick_test.py
- ✅ 更新 .gitignore 忽略测试脚本
- ✅ 创建本文档
