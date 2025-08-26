#!/usr/bin/env python3
"""
调试真实的分析流程
模拟真实用户数据进行完整的 Angela AI 分析
"""
import os
import sys
import json
import logging

# 确保能找到应用模块
sys.path.append('.')

# 设置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_real_analysis():
    """使用真实的 AngelaAI 进行分析测试"""
    try:
        # 导入应用模块
        from openai_service import AngelaAI
        from app import app, db
        
        print("🔄 正在初始化 AngelaAI...")
        angela_ai = AngelaAI()
        
        # 构造测试数据（模拟真实用户输入）
        test_form_data = {
            'projectName': '调试测试项目',
            'projectDescription': '我发现有一个英语培训的机会，想要设计一个非劳务收入管道',
            'keyPersons': [
                {
                    'name': '张老师',
                    'role': 'service_provider',
                    'resources': ['英语教学经验', '外教资源'],
                    'make_happy': ['获得稳定客源', '提升收入'],
                    'notes': '资深英语培训师'
                },
                {
                    'name': '李家长',
                    'role': 'enterprise_owner',
                    'resources': ['培训预算', '家长群体'],
                    'make_happy': ['孩子英语提升', '性价比高'],
                    'notes': '有培训需求的家长'
                }
            ],
            'externalResources': ['在线教学平台', '市场推广渠道']
        }
        
        print(f"📋 测试数据准备完成:")
        print(f"   项目名: {test_form_data['projectName']}")
        print(f"   关键人物数: {len(test_form_data['keyPersons'])}")
        print(f"   外部资源数: {len(test_form_data['externalResources'])}")
        
        # 在应用上下文中执行分析
        with app.app_context():
            print("🧠 开始执行 Angela AI 分析...")
            
            # 调用真实的分析方法
            result = angela_ai.generate_income_paths(test_form_data, db.session)
            
            print("✅ 分析执行完成!")
            print(f"📊 结果类型: {type(result)}")
            print(f"📏 结果大小: {len(str(result))} 字符")
            
            # 检查是否是真实AI结果还是备用方案
            if isinstance(result, dict):
                overview = result.get('overview', {})
                situation = overview.get('situation', '')
                
                if '基于【意识+能量+能力=结果】公式分析' in situation and '设计者作为统筹方整合现有关键人物资源' in situation:
                    print("⚠️ 警告: 这是备用方案，不是真实的AI分析结果!")
                    print("💡 这意味着在 generate_income_paths() 方法中出现了异常")
                else:
                    print("🎉 确认: 这是真实的AI分析结果!")
                
                # 显示结果的关键信息
                print(f"📝 Overview situation: {situation[:100]}...")
                
                pipelines = result.get('pipelines', [])
                print(f"🔧 管道数量: {len(pipelines)}")
                
                if pipelines:
                    first_pipeline = pipelines[0]
                    print(f"🎯 第一个管道名称: {first_pipeline.get('name', 'N/A')}")
                    print(f"💰 收入机制: {first_pipeline.get('income_mechanism', {}).get('type', 'N/A')}")
            
            return result
            
    except Exception as e:
        import traceback
        print(f"💥 调试测试失败: {str(e)}")
        print(f"💥 错误类型: {type(e).__name__}")
        print(f"💥 完整堆栈: {traceback.format_exc()}")
        return None

if __name__ == "__main__":
    print("🔍 开始调试真实的分析流程\n")
    
    result = test_real_analysis()
    
    print("\n" + "=" * 60)
    print("🏁 调试测试总结")
    print("=" * 60)
    
    if result:
        print("✅ 分析流程执行成功")
        
        # 保存结果到文件以便检查
        with open('debug_analysis_result.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print("📄 结果已保存到 debug_analysis_result.json")
        
    else:
        print("❌ 分析流程执行失败")
        print("💡 请检查上面的错误信息以定位问题")