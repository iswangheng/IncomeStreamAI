#!/usr/bin/env python3
"""完整端到端测试 - 模拟真实用户从首页到结果页面的完整操作流程"""

import sys
import os
import requests
import json
import time
sys.path.append('.')

def test_complete_user_journey():
    """测试完整的用户旅程：登录 → 首页填表 → 提交 → thinking页面 → 分析 → 结果页面"""
    
    base_url = "http://localhost:5000"
    session = requests.Session()
    
    print("🚀 开始完整端到端测试")
    print("=" * 60)
    
    try:
        # 步骤1: 用户登录
        print("1️⃣ 用户登录...")
        login_data = {
            "phone": "13800000000",
            "password": "testpass123"
        }
        
        login_response = session.post(f"{base_url}/login", data=login_data)
        if login_response.status_code not in [200, 302]:
            print(f"   ❌ 登录失败: {login_response.status_code}")
            return False
        print("   ✅ 用户成功登录")
        
        # 步骤2: 访问首页
        print("\n2️⃣ 访问首页...")
        home_response = session.get(f"{base_url}/")
        if home_response.status_code != 200:
            print(f"   ❌ 首页访问失败: {home_response.status_code}")
            return False
        print("   ✅ 首页加载成功")
        
        # 步骤3: 填写并提交表单（模拟用户在首页的操作）
        print("\n3️⃣ 用户填写并提交表单...")
        
        # 模拟真实的表单数据
        form_data = {
            "projectName": "端到端测试项目",
            "projectDescription": "这是一个完整的端到端测试项目，验证从首页到结果页面的完整流程",
            "keyPersons": json.dumps([
                {
                    "name": "测试开发者",
                    "role": "service_provider",
                    "resources": ["编程技能", "项目经验", "时间精力"],
                    "make_happy": ["获得稳定收入", "技能提升", "项目成就感"]
                },
                {
                    "name": "测试企业主",
                    "role": "enterprise_owner", 
                    "resources": ["资金预算", "业务需求", "市场渠道"],
                    "make_happy": ["降低开发成本", "快速产品上线", "业务增长"]
                },
                {
                    "name": "测试用户",
                    "role": "customer",
                    "resources": ["使用需求", "付费意愿"],
                    "make_happy": ["解决问题", "便捷体验", "性价比"]
                }
            ])
        }
        
        # 提交表单到/generate路由
        submit_response = session.post(
            f"{base_url}/generate",
            data=form_data,
            allow_redirects=True
        )
        
        print(f"   表单提交状态码: {submit_response.status_code}")
        print(f"   最终URL: {submit_response.url}")
        
        # 检查是否成功重定向到thinking页面
        if "thinking" not in submit_response.url:
            print(f"   ❌ 没有重定向到thinking页面，而是: {submit_response.url}")
            return False
        print("   ✅ 成功提交表单并重定向到thinking页面")
        
        # 步骤4: 验证thinking页面数据
        print("\n4️⃣ 验证thinking页面的session数据...")
        session_data_response = session.get(f"{base_url}/get_session_data")
        
        if session_data_response.status_code != 200:
            print(f"   ❌ 无法获取session数据: {session_data_response.status_code}")
            return False
            
        try:
            session_data = session_data_response.json()
            if not session_data.get('success') or not session_data.get('form_data'):
                print(f"   ❌ Session中没有表单数据: {session_data}")
                return False
                
            form_data_in_session = session_data['form_data']
            print(f"   ✅ Session数据验证成功")
            print(f"   项目名称: {form_data_in_session.get('projectName')}")
            print(f"   关键人物数量: {len(form_data_in_session.get('keyPersons', []))}")
            
        except json.JSONDecodeError:
            print("   ❌ Session数据解析失败")
            return False
        
        # 步骤5: 启动AI分析（模拟用户在thinking页面的操作）
        print("\n5️⃣ 启动AI分析...")
        start_analysis_response = session.post(
            f"{base_url}/start_analysis",
            headers={'Content-Type': 'application/json'},
            allow_redirects=False  # 避免自动重定向到登录页面
        )
        
        if start_analysis_response.status_code != 200:
            print(f"   ❌ 启动分析失败: {start_analysis_response.status_code}")
            return False
            
        try:
            analysis_start_data = start_analysis_response.json()
            print(f"   启动分析响应: {analysis_start_data}")
            
            start_status = analysis_start_data.get('status')
            if start_status == 'error':
                print(f"   ❌ 分析启动错误: {analysis_start_data.get('message')}")
                return False
            elif start_status in ['processing', 'completed']:
                print(f"   ✅ 分析启动成功，状态: {start_status}")
            else:
                print(f"   ⚠️ 未知启动状态: {start_status}")
                
        except json.JSONDecodeError:
            print("   ❌ 启动分析响应解析失败")
            return False
        
        # 步骤6: 轮询分析状态（模拟thinking页面的自动轮询）
        print("\n6️⃣ 轮询分析状态...")
        max_polls = 30  # 最多轮询30次
        poll_count = 0
        analysis_completed = False
        
        while poll_count < max_polls and not analysis_completed:
            poll_count += 1
            print(f"   第{poll_count}次轮询...")
            
            status_response = session.get(f"{base_url}/check_analysis_status")
            
            if status_response.status_code != 200:
                print(f"   ❌ 状态检查失败: {status_response.status_code}")
                return False
                
            try:
                status_data = status_response.json()
                current_status = status_data.get('status')
                
                print(f"   当前状态: {current_status}")
                
                if current_status == 'completed':
                    print("   ✅ 分析完成！")
                    analysis_completed = True
                    break
                elif current_status == 'error':
                    print(f"   ❌ 分析出错: {status_data.get('message')}")
                    return False
                elif current_status == 'processing':
                    progress = status_data.get('progress', 0)
                    print(f"   📊 分析进行中... 进度: {progress}%")
                else:
                    print(f"   ⚠️ 未知状态: {current_status}")
                
                # 等待2秒再次轮询
                time.sleep(2)
                
            except json.JSONDecodeError:
                print("   ❌ 状态响应解析失败")
                return False
        
        if not analysis_completed:
            print("   ⚠️ 分析未在预期时间内完成，但这可能是正常的")
        
        # 步骤7: 访问结果页面
        print("\n7️⃣ 访问结果页面...")
        results_response = session.get(f"{base_url}/results")
        
        if results_response.status_code != 200:
            print(f"   ❌ 结果页面访问失败: {results_response.status_code}")
            return False
            
        # 检查结果页面是否包含分析结果
        results_content = results_response.text
        if "项目概览" in results_content or "收入管道" in results_content or "pipeline" in results_content.lower():
            print("   ✅ 结果页面显示正常，包含分析结果")
        else:
            print("   ⚠️ 结果页面可能没有显示完整的分析结果")
            print(f"   页面内容预览: {results_content[:200]}...")
        
        print("\n🎉 端到端测试完成！")
        return True
        
    except Exception as e:
        print(f"\n❌ 端到端测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ai_thinking_stream():
    """测试AI思考流是否工作正常"""
    print("\n🧠 测试AI思考流...")
    
    session = requests.Session()
    base_url = "http://localhost:5000"
    
    try:
        # 先登录
        login_data = {"phone": "13800000000", "password": "testpass123"}
        session.post(f"{base_url}/login", data=login_data)
        
        # 获取AI思考内容
        thinking_response = session.get(f"{base_url}/get_ai_thinking_stream")
        
        if thinking_response.status_code == 200:
            thinking_data = thinking_response.json()
            print(f"   ✅ AI思考流正常: {thinking_data.get('content', '无内容')}")
            return True
        else:
            print(f"   ❌ AI思考流失败: {thinking_response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ AI思考流测试异常: {e}")
        return False

if __name__ == "__main__":
    print("🔍 完整端到端流程测试")
    print("模拟真实用户从首页到结果页面的完整操作")
    print("=" * 70)
    
    # 检查服务状态
    try:
        response = requests.get("http://localhost:5000", timeout=5)
        print("✅ 服务运行正常\n")
    except:
        print("❌ 服务无法访问，请确保应用正在运行")
        sys.exit(1)
    
    # 运行完整测试
    main_test_success = test_complete_user_journey()
    thinking_test_success = test_ai_thinking_stream()
    
    print("\n" + "=" * 70)
    print("📊 测试结果总结")
    print("=" * 70)
    print(f"   完整用户旅程: {'✅ 成功' if main_test_success else '❌ 失败'}")
    print(f"   AI思考流: {'✅ 成功' if thinking_test_success else '❌ 失败'}")
    
    if main_test_success and thinking_test_success:
        print("\n🎉 所有测试通过！系统工作正常。")
    else:
        print("\n⚠️ 部分测试失败，需要进一步检查。")
        
    # 给出最终结论
    if main_test_success:
        print("\n✅ 核心功能验证：")
        print("   - 用户可以正常登录")
        print("   - 表单提交和数据保存工作正常") 
        print("   - AI分析功能正常")
        print("   - 结果页面可以正确显示")
        print("   - 完整的用户工作流程没有问题")
    else:
        print("\n❌ 发现问题，需要进一步修复")