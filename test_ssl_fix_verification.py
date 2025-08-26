#!/usr/bin/env python3
"""验证SSL和连接问题修复效果的专项测试"""

import sys
import os
import requests
import json
import time
import threading
sys.path.append('.')

def test_ssl_fix_verification():
    """验证SSL修复是否有效"""
    
    base_url = "http://localhost:5000"
    session = requests.Session()
    
    print("🔧 SSL修复验证测试")
    print("=" * 50)
    
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
        
        # 步骤2: 提交表单
        print("\n2️⃣ 提交表单...")
        form_data = {
            "projectName": "SSL修复验证项目",
            "projectDescription": "验证SSL连接问题是否已完全修复",
            "keyPersons": json.dumps([
                {
                    "name": "技术专家",
                    "role": "service_provider",
                    "resources": ["SSL调试经验", "网络连接优化"],
                    "make_happy": ["系统稳定运行", "用户体验良好"]
                },
                {
                    "name": "项目经理",
                    "role": "enterprise_owner", 
                    "resources": ["项目管理经验", "质量把控"],
                    "make_happy": ["按时交付", "用户满意"]
                }
            ])
        }
        
        generate_response = session.post(f"{base_url}/generate", data=form_data, allow_redirects=True)
        if "thinking" not in generate_response.url:
            print(f"   ❌ 表单提交失败: {generate_response.url}")
            return False
        print("   ✅ 表单提交成功")
        
        # 步骤3: 连续测试分析启动（模拟用户多次尝试）
        print("\n3️⃣ 连续测试分析启动...")
        success_count = 0
        total_tests = 5
        
        for i in range(total_tests):
            print(f"   第{i+1}次尝试启动分析...")
            start_time = time.time()
            
            try:
                analysis_response = session.post(
                    f"{base_url}/start_analysis",
                    headers={'Content-Type': 'application/json'},
                    timeout=60  # 60秒超时
                )
                
                elapsed = time.time() - start_time
                
                if analysis_response.status_code == 200:
                    try:
                        response_data = analysis_response.json()
                        status = response_data.get('status', 'unknown')
                        print(f"   ✅ 第{i+1}次成功，状态: {status}, 耗时: {elapsed:.1f}秒")
                        success_count += 1
                    except json.JSONDecodeError:
                        print(f"   ⚠️ 第{i+1}次响应格式异常，耗时: {elapsed:.1f}秒")
                else:
                    print(f"   ❌ 第{i+1}次失败，状态码: {analysis_response.status_code}, 耗时: {elapsed:.1f}秒")
                    
            except requests.exceptions.Timeout:
                print(f"   ⏰ 第{i+1}次超时")
            except requests.exceptions.ConnectionError:
                print(f"   🔌 第{i+1}次连接错误")
            except Exception as e:
                print(f"   ❌ 第{i+1}次异常: {str(e)}")
                
            # 重新提交表单为下次测试做准备
            if i < total_tests - 1:
                session.post(f"{base_url}/generate", data=form_data, allow_redirects=True)
                time.sleep(1)  # 短暂等待
        
        success_rate = (success_count / total_tests) * 100
        print(f"\n📊 测试结果: {success_count}/{total_tests} 成功，成功率: {success_rate:.1f}%")
        
        # 步骤4: 并发测试
        print("\n4️⃣ 并发分析测试...")
        concurrent_results = []
        
        def concurrent_analysis_test(test_id):
            """并发分析测试函数"""
            test_session = requests.Session()
            # 重新登录
            test_session.post(f"{base_url}/login", data=login_data)
            # 提交表单
            test_session.post(f"{base_url}/generate", data=form_data, allow_redirects=True)
            
            try:
                start_time = time.time()
                response = test_session.post(
                    f"{base_url}/start_analysis",
                    headers={'Content-Type': 'application/json'},
                    timeout=60
                )
                elapsed = time.time() - start_time
                
                result = {
                    'test_id': test_id,
                    'success': response.status_code == 200,
                    'status_code': response.status_code,
                    'elapsed': elapsed
                }
                concurrent_results.append(result)
                print(f"   线程{test_id}: 状态码{response.status_code}, 耗时{elapsed:.1f}秒")
                
            except Exception as e:
                result = {
                    'test_id': test_id,
                    'success': False,
                    'error': str(e),
                    'elapsed': time.time() - start_time
                }
                concurrent_results.append(result)
                print(f"   线程{test_id}: 异常 {str(e)}")
        
        # 启动3个并发线程
        threads = []
        for i in range(3):
            thread = threading.Thread(target=concurrent_analysis_test, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        concurrent_success = sum(1 for r in concurrent_results if r['success'])
        concurrent_rate = (concurrent_success / len(concurrent_results)) * 100
        print(f"   并发测试结果: {concurrent_success}/{len(concurrent_results)} 成功，成功率: {concurrent_rate:.1f}%")
        
        # 步骤5: 评估修复效果
        print("\n5️⃣ 修复效果评估...")
        overall_success_rate = (success_rate + concurrent_rate) / 2
        
        if overall_success_rate >= 80:
            print(f"   ✅ 修复效果优秀，综合成功率: {overall_success_rate:.1f}%")
            print("   SSL连接问题已基本解决")
            return True
        elif overall_success_rate >= 60:
            print(f"   ⚠️ 修复效果一般，综合成功率: {overall_success_rate:.1f}%")
            print("   仍需进一步优化")
            return False
        else:
            print(f"   ❌ 修复效果不佳，综合成功率: {overall_success_rate:.1f}%")
            print("   需要深入排查")
            return False
            
    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
        return False

def test_fallback_mechanism():
    """测试备用机制是否正常工作"""
    print("\n🛡️ 备用机制测试")
    print("-" * 30)
    
    # 这里可以通过模拟网络错误来测试备用机制
    # 但由于真实环境限制，我们主要验证机制是否就位
    
    base_url = "http://localhost:5000"
    session = requests.Session()
    
    try:
        # 登录
        login_data = {"phone": "13800000000", "password": "testpass123"}
        session.post(f"{base_url}/login", data=login_data)
        
        # 检查备用方案生成是否可用
        fallback_test_response = session.get(f"{base_url}/get_ai_thinking_stream")
        
        if fallback_test_response.status_code == 200:
            print("   ✅ 备用机制接口正常")
            return True
        else:
            print(f"   ⚠️ 备用机制接口异常: {fallback_test_response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ 备用机制测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🔍 SSL修复验证测试套件")
    print("验证网络连接问题是否已彻底解决")
    print("=" * 60)
    
    # 检查服务状态
    try:
        response = requests.get("http://localhost:5000", timeout=5)
        print("✅ 服务运行正常\n")
    except:
        print("❌ 服务无法访问，请确保应用正在运行")
        sys.exit(1)
    
    # 运行测试
    ssl_test_success = test_ssl_fix_verification()
    fallback_test_success = test_fallback_mechanism()
    
    print("\n" + "=" * 60)
    print("📊 总体测试结果")
    print("=" * 60)
    print(f"   SSL修复验证: {'✅ 通过' if ssl_test_success else '❌ 失败'}")
    print(f"   备用机制验证: {'✅ 通过' if fallback_test_success else '❌ 失败'}")
    
    if ssl_test_success and fallback_test_success:
        print("\n🎉 所有测试通过！SSL问题已解决，系统稳定可靠。")
    elif ssl_test_success:
        print("\n✅ SSL主要问题已解决，备用机制需要调整。")
    else:
        print("\n⚠️ 仍需进一步优化SSL连接稳定性。")
        
    print("\n💡 建议:")
    if not ssl_test_success:
        print("   1. 检查网络环境和OpenAI API密钥")
        print("   2. 考虑增加连接池大小")
        print("   3. 优化超时设置")
    if not fallback_test_success:
        print("   1. 检查备用方案生成逻辑")
        print("   2. 确保错误处理覆盖全面")