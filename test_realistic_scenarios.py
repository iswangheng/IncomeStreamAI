#!/usr/bin/env python3
"""测试真实场景下的分析流程 - 模拟前端完整请求"""

import sys
import os
import requests
import time
import json
import threading
sys.path.append('.')

def test_full_frontend_flow():
    """测试完整的前端流程"""
    base_url = "http://localhost:5000"
    
    print("🧪 测试完整前端流程...")
    
    try:
        # 1. 先登录获取session
        print("1️⃣ 模拟用户登录...")
        session = requests.Session()
        
        # 获取登录页面
        login_page = session.get(f"{base_url}/login")
        print(f"   登录页面状态码: {login_page.status_code}")
        
        # 模拟登录 (这里假设已经有测试用户)
        login_data = {
            "phone": "13800000000",  # 测试手机号
            "password": "testpass123"
        }
        
        login_response = session.post(f"{base_url}/login", data=login_data)
        print(f"   登录响应状态码: {login_response.status_code}")
        
        # 2. 提交表单数据
        print("2️⃣ 模拟表单提交...")
        form_data = {
            "projectName": "SSL测试项目",
            "projectDescription": "专门用于测试SSL连接问题的项目",
            "keyPersons": json.dumps([
                {
                    "name": "测试人员A",
                    "role": "service_provider",
                    "resources": ["测试资源1", "测试资源2"],
                    "make_happy": ["获得持续收入", "获得认可/名声"]
                },
                {
                    "name": "测试人员B", 
                    "role": "enterprise_owner",
                    "resources": ["预算支持", "渠道资源"],
                    "make_happy": ["控制成本开支", "获得优质产品"]
                }
            ])
        }
        
        generate_response = session.post(f"{base_url}/generate", data=form_data)
        print(f"   表单提交状态码: {generate_response.status_code}")
        
        # 3. 访问thinking页面
        print("3️⃣ 访问thinking页面...")
        thinking_response = session.get(f"{base_url}/thinking")
        print(f"   Thinking页面状态码: {thinking_response.status_code}")
        
        # 4. 启动分析 (这里最容易出SSL问题)
        print("4️⃣ 启动分析...")
        start_time = time.time()
        
        start_analysis_response = session.post(f"{base_url}/start_analysis", 
                                             headers={'Content-Type': 'application/json'})
        elapsed = time.time() - start_time
        
        print(f"   启动分析响应时间: {elapsed:.2f}秒")
        print(f"   启动分析状态码: {start_analysis_response.status_code}")
        
        if start_analysis_response.status_code == 200:
            try:
                response_data = start_analysis_response.json()
                print(f"   响应内容: {response_data}")
                return True
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON解析失败: {e}")
                print(f"   原始响应: {start_analysis_response.text[:200]}")
                return False
        else:
            print(f"   ❌ HTTP错误: {start_analysis_response.status_code}")
            print(f"   错误内容: {start_analysis_response.text[:200]}")
            return False
            
    except requests.exceptions.SSLError as ssl_error:
        print(f"❌ SSL错误 (这就是问题所在!): {ssl_error}")
        return False
    except requests.exceptions.ConnectionError as conn_error:
        print(f"❌ 连接错误: {conn_error}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_concurrent_requests():
    """测试并发请求是否会造成SSL问题"""
    print("🧪 测试并发请求...")
    
    def make_request(thread_id):
        try:
            response = requests.post("http://localhost:5000/start_analysis", 
                                   headers={'Content-Type': 'application/json'},
                                   timeout=10)
            print(f"   线程{thread_id}: 状态码 {response.status_code}")
            return True
        except Exception as e:
            print(f"   线程{thread_id}: 错误 {str(e)}")
            return False
    
    # 创建5个并发请求
    threads = []
    for i in range(5):
        thread = threading.Thread(target=make_request, args=(i,))
        threads.append(thread)
        thread.start()
    
    # 等待所有线程完成
    for thread in threads:
        thread.join()

def test_openai_api_stress():
    """压力测试OpenAI API调用"""
    print("🧪 压力测试OpenAI API...")
    
    try:
        from openai_service import AngelaAI
        angela_ai = AngelaAI()
        
        # 连续调用多次，看是否出现SSL问题
        for i in range(3):
            print(f"   第{i+1}次调用...")
            start_time = time.time()
            
            try:
                result = angela_ai.generate_income_paths({
                    "projectName": f"压力测试{i+1}",
                    "projectDescription": "压力测试项目",
                    "keyPersons": [
                        {
                            "name": "测试用户",
                            "role": "service_provider",
                            "resources": ["测试"],
                            "make_happy": ["测试"]
                        }
                    ]
                }, db_session=None)
                
                elapsed = time.time() - start_time
                print(f"   ✅ 成功，耗时: {elapsed:.2f}秒")
                
            except Exception as e:
                print(f"   ❌ 失败: {str(e)}")
                return False
                
            # 短暂休息避免过快请求
            time.sleep(2)
            
        return True
        
    except Exception as e:
        print(f"❌ 压力测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_session_and_database():
    """测试session和数据库操作"""
    print("🧪 测试session和数据库操作...")
    
    try:
        from app import app
        from models import User, AnalysisResult
        
        with app.test_client() as client:
            with app.app_context():
                # 检查数据库连接
                user_count = User.query.count()
                result_count = AnalysisResult.query.count()
                print(f"   数据库连接正常: 用户{user_count}个, 分析结果{result_count}个")
                
                # 测试session操作
                with client.session_transaction() as sess:
                    sess['test_key'] = 'test_value'
                    
                print("   ✅ Session操作正常")
                return True
                
    except Exception as e:
        print(f"❌ Session/数据库测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🔍 真实场景SSL问题诊断测试")
    print("=" * 60)
    
    # 检查服务是否运行
    try:
        response = requests.get("http://localhost:5000", timeout=5)
        print(f"✅ 服务运行正常，状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ 服务无法访问: {e}")
        print("请确保应用正在运行")
        sys.exit(1)
    
    print("\n" + "="*50)
    
    # 运行各种测试
    tests = [
        ("完整前端流程测试", test_full_frontend_flow),
        ("并发请求测试", test_concurrent_requests), 
        ("OpenAI API压力测试", test_openai_api_stress),
        ("Session和数据库测试", test_session_and_database)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        print("-" * 40)
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            results[test_name] = False
        print()
    
    # 总结
    print("=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")
    
    # 如果有失败的测试，给出建议
    failed_tests = [name for name, result in results.items() if not result]
    if failed_tests:
        print(f"\n⚠️  失败的测试: {', '.join(failed_tests)}")
        print("\n💡 建议排查方向:")
        print("   1. 检查OpenAI API密钥和网络连接")
        print("   2. 检查SSL证书配置")
        print("   3. 检查请求频率限制")
        print("   4. 检查session和认证问题")
    else:
        print("\n🎉 所有测试通过！")