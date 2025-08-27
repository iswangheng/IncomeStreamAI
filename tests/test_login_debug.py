#!/usr/bin/env python3
"""
登录问题诊断测试
"""

import requests
import json

def test_login_debug():
    """诊断登录问题"""
    base_url = "http://0.0.0.0:5000"
    session = requests.Session()
    
    print("🔍 开始登录诊断测试")
    
    # 1. 获取登录页面
    print("\n1️⃣ 获取登录页面...")
    response = session.get(f"{base_url}/login")
    print(f"   状态码: {response.status_code}")
    print(f"   Set-Cookie: {response.headers.get('Set-Cookie', 'None')}")
    
    # 2. 尝试登录
    print("\n2️⃣ 尝试登录...")
    login_data = {
        "phone": "13800138000",
        "password": "123456"
    }
    
    response = session.post(f"{base_url}/login", data=login_data, allow_redirects=False)
    print(f"   状态码: {response.status_code}")
    print(f"   Location: {response.headers.get('Location', 'None')}")
    print(f"   Set-Cookie: {response.headers.get('Set-Cookie', 'None')}")
    
    # 3. 检查登录后的session
    print("\n3️⃣ 检查session状态...")
    print(f"   Session cookies: {dict(session.cookies)}")
    
    # 4. 测试访问需要登录的页面
    print("\n4️⃣ 测试访问主页...")
    response = session.get(f"{base_url}/", allow_redirects=False)
    print(f"   状态码: {response.status_code}")
    print(f"   Location: {response.headers.get('Location', 'None')}")
    
    # 5. 如果重定向，跟随重定向
    if response.status_code == 302:
        print("\n5️⃣ 跟随重定向...")
        response = session.get(f"{base_url}/", allow_redirects=True)
        print(f"   最终状态码: {response.status_code}")
        print(f"   最终URL检查: {'login' in response.url}")
    
    # 6. 手动检查用户是否已登录
    print("\n6️⃣ 检查登录状态...")
    # 尝试访问一个明确需要登录的页面
    response = session.get(f"{base_url}/profile", allow_redirects=False)
    print(f"   访问profile页面状态: {response.status_code}")
    if response.status_code == 302:
        print("   ❌ 用户未登录（被重定向）")
    elif response.status_code == 200:
        print("   ✅ 用户已登录")
    else:
        print(f"   ❓ 未知状态: {response.status_code}")

if __name__ == "__main__":
    test_login_debug()