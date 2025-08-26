#!/usr/bin/env python3
"""
测试SSL连接修复是否有效
"""
import logging
logging.basicConfig(level=logging.INFO)

from openai_service import AngelaAI

def test_simple_openai_call():
    """测试简单的OpenAI API调用"""
    try:
        ai = AngelaAI()
        
        # 创建简单测试数据
        test_data = {
            'projectName': 'SSL连接测试项目', 
            'projectDescription': '这是一个用来测试SSL连接稳定性的测试项目',
            'keyPersons': [{
                'name': '测试人员',
                'role': 'service_provider',
                'resources': ['测试技能'],
                'make_happy': ['money']
            }],
            'externalResources': []
        }
        
        print("🚀 开始测试OpenAI API调用...")
        result = ai.generate_income_paths(test_data, None)
        
        if result and 'error' not in result:
            print("✅ SSL连接修复成功！API调用正常")
            print(f"结果类型: {type(result)}")
            if isinstance(result, dict) and 'result' in result:
                print("✅ 返回了正确的结构化数据")
            return True
        else:
            print("❌ API调用失败")
            print(f"错误结果: {result}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

if __name__ == '__main__':
    test_simple_openai_call()