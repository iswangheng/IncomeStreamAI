#!/usr/bin/env python3
"""
测试默认管理员账号登录
"""

import requests

def test_admin_login():
    """测试默认管理员账号"""
    base_url = "http://0.0.0.0:5000"
    session = requests.Session()
    
    print("🔐 测试默认管理员账号登录")
    
    # 从app.py中看到的默认管理员账号
    admin_credentials = {
        "phone": "18302196515",
        "password": "aibenzong9264"
    }
    
    print(f"   账号: {admin_credentials['phone']}")
    print(f"   密码: {admin_credentials['password']}")
    
    # 清理session
    session.cookies.clear()
    
    # 尝试登录
    response = session.post(f"{base_url}/login", data=admin_credentials, allow_redirects=False)
    
    print(f"\n📊 登录结果:")
    print(f"   状态码: {response.status_code}")
    print(f"   Location: {response.headers.get('Location', 'None')}")
    
    cookies = response.headers.get('Set-Cookie', 'None')
    print(f"   Set-Cookie: {cookies}")
    
    # 分析结果
    if response.status_code == 302:
        location = response.headers.get('Location', '')
        if 'login' not in location:
            print("   🟢 登录成功 - 重定向到应用页面")
            success = True
        else:
            print("   🔴 登录失败 - 重定向回登录页面")
            success = False
    elif 'session=' in cookies and 'Expires=Thu, 01 Jan 1970' not in cookies:
        print("   🟢 Session已设置 - 可能登录成功")
        success = True
    else:
        print("   🔴 登录失败")
        success = False
    
    # 验证登录状态
    print(f"\n🔍 验证登录状态:")
    home_response = session.get(f"{base_url}/", allow_redirects=False)
    print(f"   访问主页状态: {home_response.status_code}")
    
    if home_response.status_code == 200:
        print("   ✅ 确认登录成功 - 可以访问需要登录的页面")
        return True
    elif home_response.status_code == 302:
        print("   ❌ 登录失败 - 仍被重定向到登录页")
        return False
    else:
        print(f"   ❓ 未知状态: {home_response.status_code}")
        return False

if __name__ == "__main__":
    test_admin_login()