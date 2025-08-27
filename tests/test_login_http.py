#!/usr/bin/env python3
"""
通过HTTP直接测试登录功能
"""

import requests
import json

def test_login_with_logging():
    """通过HTTP测试登录，获取服务器日志信息"""
    base_url = "http://0.0.0.0:5000"
    session = requests.Session()
    
    print("🔍 HTTP登录测试")
    
    # 测试各种密码组合
    test_cases = [
        {"phone": "13800138000", "password": "123456", "desc": "测试用户 - 常用密码"},
        {"phone": "13800138000", "password": "password", "desc": "测试用户 - 默认密码"},
        {"phone": "13800138000", "password": "admin", "desc": "测试用户 - 管理员密码"},
        {"phone": "18302196515", "password": "123456", "desc": "管理员用户 - 常用密码"},
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}️⃣ 测试: {case['desc']}")
        print(f"   手机号: {case['phone']}")
        print(f"   密码: {case['password']}")
        
        # 清理session
        session.cookies.clear()
        
        # 尝试登录
        response = session.post(f"{base_url}/login", data={
            "phone": case['phone'],
            "password": case['password']
        }, allow_redirects=False)
        
        print(f"   状态码: {response.status_code}")
        print(f"   Location: {response.headers.get('Location', 'None')}")
        
        cookies = response.headers.get('Set-Cookie', 'None')
        print(f"   Set-Cookie: {cookies}")
        
        # 分析cookie
        if 'session=' in cookies and 'Expires=Thu, 01 Jan 1970' in cookies:
            print("   🔴 Session被立即清空 - 登录失败")
        elif 'session=' in cookies:
            print("   🟢 Session已设置 - 可能登录成功")
        else:
            print("   🟡 没有设置Session")
        
        # 测试访问主页确认登录状态
        home_response = session.get(f"{base_url}/", allow_redirects=False)
        if home_response.status_code == 200:
            print("   ✅ 登录成功 - 可以访问主页")
            break
        elif home_response.status_code == 302:
            print("   ❌ 登录失败 - 被重定向到登录页")
        else:
            print(f"   ❓ 未知状态: {home_response.status_code}")
    
    print("\n📊 测试总结：")
    print("   如果所有测试都失败，可能的原因：")
    print("   1. 密码哈希验证问题")
    print("   2. Flask-Login配置问题") 
    print("   3. Session配置问题")
    print("   4. 用户账号状态问题")

if __name__ == "__main__":
    test_login_with_logging()