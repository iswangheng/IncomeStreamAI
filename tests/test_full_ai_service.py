#!/usr/bin/env python3
"""测试完整的AI分析服务"""

import sys
import os
sys.path.append('.')

def test_ai_analysis():
    """测试AI分析服务"""
    try:
        from openai_service import AngelaAI
        
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
        
        print("🧪 测试AngelaAI分析服务...")
        angela_ai = AngelaAI()
        
        # 尝试生成建议
        print("🔄 正在调用AI分析...")
        result = angela_ai.generate_income_paths(
            form_data, 
            db_session=None
        )
        
        if result and isinstance(result, dict):
            print("✅ AI分析成功！")
            print(f"结果包含 {len(result.get('paths', []))} 个收入路径")
            return True
        else:
            print("❌ AI分析失败：结果无效")
            return False
            
    except Exception as e:
        print(f"❌ AI分析出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("完整AI分析服务测试")
    print("=" * 50)
    
    success = test_ai_analysis()
    
    if success:
        print("\n✅ AI分析服务工作正常！")
    else:
        print("\n❌ AI分析服务有问题！")