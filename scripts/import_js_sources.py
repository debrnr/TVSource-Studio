"""
JS爬虫批量导入工具

将demo目录中的XBPQ JSON规则和DRPY2 JS脚本自动转换为TVSource Studio配置
支持:
1. XBPQ规则 (Type 2) - JSON配置文件
2. DRPY2脚本 (Type 3) - JavaScript文件
3. 自动分类和验证
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)


class JSSourceImporter:
    """JS爬虫导入器"""
    
    def __init__(self, demo_base: str):
        """
        初始化导入器
        
        Args:
            demo_base: DEMO基础目录或直接是rules目录
        """
        self.demo_base = Path(demo_base)
        
        # 检查是否是扁平结构(直接包含json和js子目录)
        if (self.demo_base / "xbpq").exists() and (self.demo_base / "drpy2").exists():
            # 新的扁平结构: data/rules/xbpq 和 data/rules/drpy2
            self.json_dir = self.demo_base / "xbpq"
            self.js_dir = self.demo_base / "drpy2"
            logger.info(f"使用扁平规则目录结构")
        else:
            # 旧的嵌套结构: demo/Box系列/本地包/奇奇，20260414/tvboxqq/南风
            self.nanfeng_base = self.demo_base / "奇奇，20260414" / "tvboxqq" / "南风"
            self.js_dir = self.nanfeng_base / "js"
            self.json_dir = self.nanfeng_base / "json"
            logger.info(f"使用嵌套DEMO目录结构")
    
    def scan_xbpq_rules(self) -> List[Dict]:
        """
        扫描XBPQ JSON规则文件
        
        Returns:
            规则列表
        """
        rules = []
        
        if not self.json_dir.exists():
            logger.warning(f"JSON规则目录不存在: {self.json_dir}")
            return rules
        
        for json_file in self.json_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    rule_data = json.load(f)
                
                # 提取关键信息
                rule_name = rule_data.get('规则名', json_file.stem)
                
                # 构建数据源配置 - 使用绝对路径
                import os
                abs_json_path = str(json_file.resolve())  # 转换为绝对路径
                
                source_config = {
                    "name": rule_name,
                    "type": 2,  # XBPQ规则引擎
                    "api": "",  # XBPQ不需要API地址
                    "ext": abs_json_path,  # 使用绝对路径
                    "timeout": 15,
                    "enabled": False,  # 默认禁用,需手动启用
                    "metadata": {
                        "author": rule_data.get('规则作者', ''),
                        "home_url": rule_data.get('首页推荐链接', ''),
                        "categories": rule_data.get('分类名称', '').split('&') if rule_data.get('分类名称') else []
                    }
                }
                
                rules.append(source_config)
                logger.info(f"✓ 发现XBPQ规则: {rule_name}")
                
            except Exception as e:
                logger.error(f"✗ 解析规则文件失败 [{json_file.name}]: {e}")
        
        return rules
    
    def scan_drpy2_scripts(self) -> List[Dict]:
        """
        扫描DRPY2 JS脚本文件
        
        Returns:
            脚本列表
        """
        scripts = []
        
        if not self.js_dir.exists():
            logger.warning(f"JS脚本目录不存在: {self.js_dir}")
            return scripts
        
        for js_file in self.js_dir.glob("*.js"):
            try:
                # 读取JS文件前500字节,检测类型
                with open(js_file, 'r', encoding='utf-8', errors='ignore') as f:
                    preview = f.read(500)
                
                # 判断是否为MacCMS API聚合器
                is_aggregator = 'maccms' in preview.lower() or 'api.php' in preview
                
                script_name = js_file.stem
                
                # 使用绝对路径
                import os
                abs_js_path = str(js_file.resolve())
                
                source_config = {
                    "name": f"{script_name}(DRPY2)",
                    "type": 3,  # DRPY2 JS运行时
                    "api": abs_js_path,  # 使用绝对路径
                    "timeout": 20,
                    "enabled": False,  # 默认禁用
                    "metadata": {
                        "is_aggregator": is_aggregator,
                        "file_size_kb": round(js_file.stat().st_size / 1024, 2)
                    }
                }
                
                scripts.append(source_config)
                
                script_type = "聚合器" if is_aggregator else "爬虫"
                logger.info(f"✓ 发现DRPY2{script_type}: {script_name}")
                
            except Exception as e:
                logger.error(f"✗ 解析JS脚本失败 [{js_file.name}]: {e}")
        
        return scripts
    
    def generate_config(self, output_path: str = "data/sources/js_sources.json"):
        """
        生成TVSource Studio配置文件
        
        Args:
            output_path: 输出配置文件路径
        """
        logger.info("="*60)
        logger.info("开始扫描JS爬虫资源...")
        logger.info("="*60)
        
        # 扫描所有资源
        xbpq_rules = self.scan_xbpq_rules()
        drpy2_scripts = self.scan_drpy2_scripts()
        
        all_sources = xbpq_rules + drpy2_scripts
        
        if not all_sources:
            logger.warning("未发现任何JS爬虫资源!")
            return
        
        # 构建配置文件
        config = {
            "version": "1.0",
            "description": "从demo目录自动导入的JS爬虫配置",
            "imported_at": str(__import__('datetime').datetime.now()),
            "sources": all_sources
        }
        
        # 确保输出目录存在
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入配置文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        logger.info("="*60)
        logger.info(f"✓ 配置文件生成成功: {output_file}")
        logger.info(f"  - XBPQ规则: {len(xbpq_rules)} 个")
        logger.info(f"  - DRPY2脚本: {len(drpy2_scripts)} 个")
        logger.info(f"  - 总计: {len(all_sources)} 个数据源")
        logger.info("="*60)
        
        # 打印摘要
        print("\n📋 导入摘要:")
        print("-" * 60)
        
        if xbpq_rules:
            print("\n🎯 XBPQ规则引擎:")
            for rule in xbpq_rules:
                categories = rule['metadata'].get('categories', [])
                cat_preview = ', '.join(categories[:3]) + ('...' if len(categories) > 3 else '')
                print(f"  • {rule['name']}")
                print(f"    分类: {cat_preview}")
                print(f"    状态: {'✓ 已启用' if rule['enabled'] else '✗ 已禁用'}")
        
        if drpy2_scripts:
            print("\n⚙️  DRPY2脚本:")
            for script in drpy2_scripts:
                script_type = "聚合器" if script['metadata']['is_aggregator'] else "爬虫"
                print(f"  • {script['name']}")
                print(f"    类型: {script_type}")
                print(f"    大小: {script['metadata']['file_size_kb']} KB")
                print(f"    状态: {'✓ 已启用' if script['enabled'] else '✗ 已禁用'}")
        
        print("\n" + "="*60)
        print("💡 下一步操作:")
        print("  1. 编辑配置文件启用需要的数据源")
        print("  2. 运行: python src/app.py 启动服务")
        print("  3. 访问管理后台查看和管理数据源")
        print("="*60 + "\n")
        
        return config


def scan_and_import_sources(base_dir: str = None):
    """
    扫描并导入JS爬虫资源
    
    Args:
        base_dir: 基础目录,默认为项目根目录下的data/rules
    """
    if base_dir is None:
        # 使用项目内部的规则目录
        import os
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        base_dir = os.path.join(project_root, "data", "rules")
    
    print("\n" + "🔧 TVSource Studio - JS爬虫导入工具".center(60))
    print("=" * 60)
    print(f"\n扫描路径: {base_dir}")
    print(f"路径存在: {Path(base_dir).exists()}")
    
    if not Path(base_dir).exists():
        print(f"\n❌ 错误: demo目录不存在!")
        print(f"   请确认路径: {base_dir}")
        return
    
    # 创建导入器
    importer = JSSourceImporter(str(base_dir))
    
    # 生成配置
    config = importer.generate_config("data/sources/js_sources.json")
    
    if config:
        print("\n✅ 导入完成!")
        print(f"\n配置文件已保存到: data/sources/js_sources.json")
        print("\n您可以:")
        print("  1. 手动编辑该文件,将需要的数据源 enabled 改为 true")
        print("  2. 或者在管理后台 (http://localhost:8080/admin/) 中启用")
    else:
        print("\n❌ 导入失败,未找到任何JS爬虫资源")


def main():
    """主函数"""
    import sys
    
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    
    # 使用项目内部的规则目录(优先)或demo目录(备选)
    rules_path = project_root / "data" / "rules"
    demo_path = project_root / "demo" / "Box系列" / "本地包"
    
    # 优先使用内部rules目录
    if rules_path.exists():
        scan_path = rules_path
        print(f"\n✅ 使用项目内部规则目录: {scan_path}")
    elif demo_path.exists():
        scan_path = demo_path
        print(f"\n⚠️  使用DEMO目录(临时): {scan_path}")
        print(f"   建议运行: python scripts/migrate_demo_to_rules.py 迁移到内部目录")
    else:
        print(f"\n❌ 错误: 规则目录不存在!")
        print(f"   期望路径: {rules_path}")
        sys.exit(1)
    
    print("\n" + "🔧 TVSource Studio - JS爬虫导入工具".center(60))
    print("=" * 60)
    print(f"\n扫描路径: {scan_path}")
    print(f"路径存在: {scan_path.exists()}")
    
    # 创建导入器
    importer = JSSourceImporter(str(scan_path))
    
    # 生成配置
    config = importer.generate_config("data/sources/js_sources.json")
    
    if config:
        print("\n✅ 导入完成!")
        print(f"\n配置文件已保存到: data/sources/js_sources.json")
        print("\n您可以:")
        print("  1. 手动编辑该文件,将需要的数据源 enabled 改为 true")
        print("  2. 或者在管理后台 (http://localhost:8080/admin/) 中启用")
    else:
        print("\n❌ 导入失败,未找到任何JS爬虫资源")
        sys.exit(1)


if __name__ == "__main__":
    main()
