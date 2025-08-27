#!/usr/bin/env python3
"""
使用数据库中的真实form_submissions数据测试OpenAI API调用
"""
import logging
import json
logging.basicConfig(level=logging.INFO)

# 设置数据库
from app import db
from models import FormSubmission
from openai_service import AngelaAI

def test_with_database_data():
    """使用数据库中的实际数据测试OpenAI API"""
    try:
        # 获取最新的表单提交数据
        latest_form = FormSubmission.query.order_by(FormSubmission.created_at.desc()).first()
        
        if not latest_form:
            print("❌ 数据库中没有找到表单数据")
            return False
            
        print(f"📊 找到表单数据: {latest_form.project_name}")
        print(f"📅 创建时间: {latest_form.created_at}")
        
        # 解析关键人物数据
        key_persons_data = json.loads(latest_form.key_persons_data)
        
        # 构建测试数据格式
        test_data = {
            'projectName': latest_form.project_name,
            'projectDescription': latest_form.project_description, 
            'keyPersons': key_persons_data,
            'externalResources': []  # 这个项目没有外部资源数据
        }
        
        print("🚀 使用真实数据测试OpenAI API调用...")
        print(f"项目名称: {test_data['projectName']}")
        print(f"关键人物数量: {len(test_data['keyPersons'])}")
        
        # 调用AI服务
        ai = AngelaAI()
        result = ai.generate_income_paths(test_data, db.session)
        
        # 检查结果
        if result and isinstance(result, dict):
            if 'error' in result:
                print(f"❌ API调用返回错误: {result['error']}")
                return False
            elif 'result' in result:
                print("✅ OpenAI API调用成功！")
                print("✅ 返回了结构化的分析结果")
                
                # 显示结果的基本信息
                analysis_result = result['result']
                if isinstance(analysis_result, dict):
                    # 检查是否包含预期的字段
                    if 'overview' in analysis_result:
                        overview = analysis_result['overview']
                        print(f"📈 情况分析: {overview.get('situation', 'N/A')[:100]}...")
                        print(f"💰 收入类型: {overview.get('income_type', 'N/A')}")
                    
                    if 'pipelines' in analysis_result and analysis_result['pipelines']:
                        pipeline = analysis_result['pipelines'][0]
                        print(f"🔧 管道名称: {pipeline.get('name', 'N/A')}")
                        
                        # 检查参与方结构
                        if 'parties_structure' in pipeline:
                            parties = pipeline['parties_structure']
                            print(f"👥 参与方数量: {len(parties)}")
                            for party in parties[:3]:  # 显示前3个
                                print(f"   - {party.get('party', 'N/A')} ({party.get('role_type', 'N/A')})")
                else:
                    print("⚠️ 返回的分析结果不是预期的字典格式")
                    print(f"结果类型: {type(analysis_result)}")
                
                return True
            else:
                print(f"⚠️ API调用成功但结果格式异常: {result}")
                return False
        else:
            print(f"❌ API调用失败，返回结果: {result}")
            return False
            
    except Exception as e:
        import traceback
        print(f"❌ 测试过程中出现异常: {str(e)}")
        print(f"完整错误信息: {traceback.format_exc()}")
        return False

if __name__ == '__main__':
    from app import app
    with app.app_context():
        success = test_with_database_data()
        if success:
            print("\n🎉 测试完全成功！OpenAI API集成工作正常！")
        else:
            print("\n💔 测试失败，需要进一步排查问题")