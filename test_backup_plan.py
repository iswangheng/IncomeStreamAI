#!/usr/bin/env python3
"""测试备用方案生成是否正常工作"""

import sys
import os
sys.path.append('.')

def test_backup_generation():
    """测试备用方案生成"""
    try:
        from app import generate_fallback_result
        
        # 模拟表单数据
        form_data = {
            "projectName": "测试项目", 
            "projectDescription": "这是一个测试项目描述",
            "keyPersons": [
                {
                    "name": "测试人员A",
                    "role": "service_provider", 
                    "resources": ["测试资源1", "测试资源2"],
                    "make_happy": ["获得持续收入", "获得认可/名声"]
                }
            ]
        }
        
        print("🧪 测试备用方案生成...")
        result = generate_fallback_result(form_data, "网络连接问题测试")
        
        if result and isinstance(result, dict):
            print("✅ 备用方案生成成功！")
            print(f"包含overview: {'overview' in result}")
            print(f"包含paths: {'paths' in result}")
            if 'paths' in result:
                print(f"路径数量: {len(result['paths'])}")
            return True
        else:
            print("❌ 备用方案生成失败：结果无效")
            return False
            
    except Exception as e:
        print(f"❌ 备用方案生成出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("备用方案生成测试")
    print("=" * 50)
    
    success = test_backup_generation()
    
    if success:
        print("\n✅ 备用方案工作正常！")
    else:
        print("\n❌ 备用方案有问题！")