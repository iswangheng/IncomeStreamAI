#!/usr/bin/env python3
"""测试完整的用户工作流程 - 从首页提交到thinking页面"""

import sys
import os
import requests
import json
import time
sys.path.append('.')

def test_complete_user_workflow():
    """测试完整的用户操作流程"""
    base_url = "http://localhost:5000"
    
    print("🔄 测试完整用户工作流程...")
    print("   模拟真实用户：首页填表 → 提交 → thinking页面 → 启动分析")
    
    # 使用持久session模拟真实用户
    session = requests.Session()
    
    try:
        # 步骤1: 登录
        print("\n1️⃣ 用户登录...")
        login_data = {
            "phone": "13800000000",
            "password": "testpass123"
        }
        
        login_response = session.post(f"{base_url}/login", data=login_data)
        if login_response.status_code not in [200, 302]:
            print(f"   ❌ 登录失败: {login_response.status_code}")
            return False
        print("   ✅ 登录成功")
        
        # 步骤2: 访问首页，获取表单
        print("\n2️⃣ 用户访问首页...")
        home_response = session.get(f"{base_url}/")
        if home_response.status_code != 200:
            print(f"   ❌ 首页访问失败: {home_response.status_code}")
            return False
        print("   ✅ 首页加载成功")
        
        # 步骤3: 用户填写并提交表单 (这是关键步骤!)
        print("\n3️⃣ 用户提交表单数据...")
        
        form_data = {
            "projectName": "完整测试项目",
            "projectDescription": "这是一个完整的工作流程测试项目，用于验证数据传递",
            "keyPersons": json.dumps([
                {
                    "name": "张三",
                    "role": "service_provider",
                    "resources": ["技术能力", "开发经验"],
                    "make_happy": ["获得持续收入", "技术成长"]
                },
                {
                    "name": "李四",
                    "role": "enterprise_owner", 
                    "resources": ["资金预算", "市场渠道"],
                    "make_happy": ["控制成本", "快速上线"]
                }
            ])
        }
        
        # 提交表单 (应该保存到session并重定向到thinking页面)
        generate_response = session.post(
            f"{base_url}/generate", 
            data=form_data,
            allow_redirects=True  # 允许跟随重定向
        )
        
        print(f"   提交响应状态码: {generate_response.status_code}")
        print(f"   最终URL: {generate_response.url}")
        
        # 检查是否重定向到了thinking页面
        if "thinking" in generate_response.url:
            print("   ✅ 成功重定向到thinking页面")
        else:
            print(f"   ⚠️  重定向到了: {generate_response.url}")
        
        # 步骤4: 检查thinking页面的session数据
        print("\n4️⃣ 检查thinking页面的session数据...")
        
        session_data_response = session.get(f"{base_url}/get_session_data")
        print(f"   Session数据API状态码: {session_data_response.status_code}")
        
        if session_data_response.status_code == 200:
            try:
                session_data = session_data_response.json()
                print(f"   Session数据: {session_data}")
                
                if session_data.get('success') and session_data.get('form_data'):
                    print("   ✅ Session中有表单数据")
                    form_data_in_session = session_data['form_data']
                    print(f"   项目名称: {form_data_in_session.get('projectName')}")
                    print(f"   关键人物数量: {len(form_data_in_session.get('keyPersons', []))}")
                else:
                    print("   ❌ Session中没有表单数据")
                    return False
            except:
                print("   ❌ Session数据解析失败")
                return False
        else:
            print(f"   ❌ 无法获取session数据: {session_data_response.status_code}")
            return False
        
        # 步骤5: 现在启动分析 (应该能找到表单数据)
        print("\n5️⃣ 启动AI分析...")
        
        start_analysis_response = session.post(
            f"{base_url}/start_analysis",
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"   启动分析状态码: {start_analysis_response.status_code}")
        
        if start_analysis_response.status_code == 200:
            try:
                analysis_data = start_analysis_response.json()
                print(f"   分析响应: {analysis_data}")
                
                status = analysis_data.get('status')
                if status == 'processing':
                    print("   ✅ 分析开始处理")
                    return True
                elif status == 'completed':
                    print("   ✅ 分析已完成")
                    return True
                elif status == 'error':
                    error_code = analysis_data.get('error_code', 'UNKNOWN')
                    message = analysis_data.get('message', '未知错误')
                    print(f"   ❌ 分析错误: {error_code} - {message}")
                    
                    if error_code == 'NO_FORM_DATA':
                        print("   ⚠️  这就是用户遇到的问题：表单数据丢失了！")
                    
                    return False
                else:
                    print(f"   ❌ 未知状态: {status}")
                    return False
                    
            except Exception as parse_error:
                print(f"   ❌ 响应解析失败: {parse_error}")
                print(f"   原始响应: {start_analysis_response.text[:200]}")
                return False
        else:
            print(f"   ❌ 启动分析HTTP错误: {start_analysis_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 完整工作流程测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_manual_form_submission():
    """手动测试表单提交逻辑"""
    print("\n🧪 手动测试表单提交逻辑...")
    
    try:
        from app import app, db
        from models import FormSubmission
        from flask import session
        import json
        
        # 测试数据
        test_form_data = {
            "projectName": "手动测试项目",
            "projectDescription": "手动测试项目描述",
            "keyPersons": [
                {
                    "name": "测试人员",
                    "role": "service_provider",
                    "resources": ["测试资源"],
                    "make_happy": ["测试目标"]
                }
            ]
        }
        
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = 1  # 假设用户ID为1
                sess['_user_id'] = '1'
                sess['_fresh'] = True
            
            # 直接调用表单提交端点
            response = client.post('/generate', data={
                'projectName': test_form_data['projectName'],
                'projectDescription': test_form_data['projectDescription'],
                'keyPersons': json.dumps(test_form_data['keyPersons'])
            })
            
            print(f"   表单提交状态码: {response.status_code}")
            
            if response.status_code in [302, 303]:
                print("   ✅ 表单提交成功，有重定向")
                
                # 检查数据库中是否保存了数据
                with app.app_context():
                    recent_submission = FormSubmission.query.filter_by(user_id=1).order_by(FormSubmission.created_at.desc()).first()
                    if recent_submission:
                        print(f"   ✅ 数据库中找到提交记录: {recent_submission.project_name}")
                        return True
                    else:
                        print("   ❌ 数据库中没有找到提交记录")
                        return False
            else:
                print(f"   ❌ 表单提交失败: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ 手动表单测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("🔍 完整用户工作流程诊断")
    print("=" * 70)
    print("目标：找出为什么用户从前端操作时会丢失表单数据")
    
    # 检查服务运行状态
    try:
        response = requests.get("http://localhost:5000", timeout=5)
        print(f"✅ 服务运行正常")
    except:
        print("❌ 服务无法访问，请确保应用正在运行")
        sys.exit(1)
    
    print("\n" + "="*60)
    
    # 测试1: 完整用户工作流程
    workflow_success = test_complete_user_workflow()
    
    print("\n" + "="*60)
    
    # 测试2: 手动表单提交
    manual_success = test_manual_form_submission()
    
    print("\n" + "="*70)
    print("🎯 诊断结果")
    print("="*70)
    
    print(f"   完整工作流程: {'✅ 成功' if workflow_success else '❌ 失败'}")
    print(f"   手动表单提交: {'✅ 成功' if manual_success else '❌ 失败'}")
    
    if not workflow_success:
        print("\n💡 问题诊断:")
        print("   用户从前端操作时表单数据确实会丢失")
        print("   可能的原因:")
        print("   1. /generate路由的数据保存逻辑有问题")
        print("   2. session配置或大小限制")
        print("   3. 数据库保存和检索逻辑不匹配")
        print("   4. 重定向过程中session数据丢失")
        
        print("\n🔧 建议修复:")
        print("   1. 检查/generate路由的实现")
        print("   2. 确保数据正确保存到FormSubmission表")
        print("   3. 确保get_form_data_from_db()能正确检索数据")
        print("   4. 增加详细的日志追踪数据流")
    else:
        print("\n🎉 工作流程正常！问题可能在其他地方。")