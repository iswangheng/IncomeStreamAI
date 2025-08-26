#!/usr/bin/env python3
"""专门测试认证问题的调试工具"""

import sys
import os
import requests
import json
sys.path.append('.')

def test_auth_workflow():
    """测试真实的认证工作流程"""
    base_url = "http://localhost:5000"
    
    print("🔐 测试认证工作流程...")
    
    # 使用持久session
    session = requests.Session()
    
    try:
        # 1. 获取登录页面看session是否正常
        print("1️⃣ 获取登录页面...")
        login_page = session.get(f"{base_url}/login")
        print(f"   状态码: {login_page.status_code}")
        print(f"   响应类型: {login_page.headers.get('content-type', 'unknown')}")
        
        # 检查是否有测试用户 
        print("2️⃣ 尝试登录测试账户...")
        login_data = {
            "phone": "13800000000",
            "password": "testpass123"
        }
        
        # 使用正确的表单提交方式
        login_response = session.post(
            f"{base_url}/login", 
            data=login_data,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            allow_redirects=False  # 不自动跳转，看重定向
        )
        
        print(f"   登录状态码: {login_response.status_code}")
        print(f"   响应头: {dict(login_response.headers)}")
        
        if login_response.status_code in [302, 303]:
            redirect_url = login_response.headers.get('Location', '未知')
            print(f"   🔄 重定向到: {redirect_url}")
            
            # 如果重定向到主页，说明登录成功
            if redirect_url.endswith('/'):
                print("   ✅ 登录成功！")
                
                # 3. 现在测试需要认证的端点
                print("3️⃣ 测试认证状态...")
                
                # 访问thinking页面看是否认证
                thinking_response = session.get(f"{base_url}/thinking")
                print(f"   thinking页面状态码: {thinking_response.status_code}")
                
                if thinking_response.status_code == 200:
                    if '<!DOCTYPE html>' in thinking_response.text:
                        print("   ✅ 成功访问thinking页面")
                        
                        # 4. 测试AJAX请求
                        print("4️⃣ 测试AJAX认证...")
                        ajax_response = session.post(
                            f"{base_url}/start_analysis",
                            headers={
                                'Content-Type': 'application/json',
                                'X-Requested-With': 'XMLHttpRequest'
                            }
                        )
                        
                        print(f"   AJAX状态码: {ajax_response.status_code}")
                        print(f"   AJAX响应类型: {ajax_response.headers.get('content-type', 'unknown')}")
                        
                        # 检查响应内容
                        response_preview = ajax_response.text[:200]
                        print(f"   AJAX响应预览: {response_preview}")
                        
                        if ajax_response.headers.get('content-type', '').startswith('application/json'):
                            print("   ✅ 收到JSON响应")
                            try:
                                data = ajax_response.json()
                                print(f"   响应数据: {data}")
                                return True
                            except:
                                print("   ❌ JSON解析失败")
                                return False
                        else:
                            print("   ❌ 没收到JSON，可能被重定向了")
                            return False
                    else:
                        print("   ❌ thinking页面不是HTML")
                        return False
                else:
                    print(f"   ❌ thinking页面访问失败: {thinking_response.status_code}")
                    return False
            else:
                print(f"   ❌ 登录失败，重定向到: {redirect_url}")
                return False
        else:
            print(f"   ❌ 登录请求异常: {login_response.status_code}")
            print(f"   响应内容: {login_response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ 认证测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_create_test_user():
    """尝试创建测试用户"""
    print("👤 创建测试用户...")
    
    try:
        from app import app, db
        from models import User
        from werkzeug.security import generate_password_hash
        
        with app.app_context():
            # 检查是否已有测试用户
            existing_user = User.query.filter_by(phone="13800000000").first()
            if existing_user:
                print("   ✅ 测试用户已存在")
                return True
            
            # 创建测试用户
            test_user = User()
            test_user.phone = "13800000000"
            test_user.username = "testuser"
            test_user.password_hash = generate_password_hash("testpass123")
            
            db.session.add(test_user)
            db.session.commit()
            
            print("   ✅ 测试用户创建成功")
            return True
            
    except Exception as e:
        print(f"   ❌ 创建测试用户失败: {e}")
        return False

def test_direct_session_setup():
    """直接在app context中设置session测试"""
    print("🧪 直接session测试...")
    
    try:
        from app import app
        
        with app.test_client() as client:
            with client.session_transaction() as sess:
                # 模拟已登录状态
                sess['user_id'] = 1  # 假设用户ID为1
                sess['_user_id'] = '1'
                sess['_fresh'] = True
                
            # 测试需要登录的端点
            response = client.post('/start_analysis')
            print(f"   状态码: {response.status_code}")
            print(f"   响应类型: {response.headers.get('content-type', 'unknown')}")
            
            if response.status_code == 200:
                print("   ✅ 认证通过")
                return True
            else:
                print(f"   ❌ 认证失败: {response.data.decode()[:200]}")
                return False
                
    except Exception as e:
        print(f"❌ 直接session测试失败: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🔐 认证问题专项调试")
    print("=" * 60)
    
    # 1. 创建测试用户
    test_create_test_user()
    print()
    
    # 2. 测试认证工作流程
    print("=" * 50)
    auth_success = test_auth_workflow()
    print()
    
    # 3. 直接session测试
    print("=" * 50)
    direct_success = test_direct_session_setup()
    print()
    
    # 总结
    print("=" * 60)
    print("🎯 认证调试结果")
    print("=" * 60)
    print(f"   完整认证流程: {'✅ 成功' if auth_success else '❌ 失败'}")
    print(f"   直接session测试: {'✅ 成功' if direct_success else '❌ 失败'}")
    
    if not auth_success and not direct_success:
        print("\n💡 可能的问题:")
        print("   1. Flask-Login配置问题")
        print("   2. Session配置问题") 
        print("   3. CSRF保护问题")
        print("   4. 数据库用户数据问题")
        print("\n🔧 建议:")
        print("   1. 检查@login_required装饰器")
        print("   2. 检查session secret key")
        print("   3. 检查用户加载函数")
    elif auth_success:
        print("\n🎉 认证系统工作正常！")
        print("前端SSL问题可能是其他原因，比如:")
        print("   1. 表单数据缺失")
        print("   2. OpenAI API调用中的网络问题")
        print("   3. 会话数据过大导致的问题")