#!/usr/bin/env python3
"""
简化的端到端测试 - 查看完整流程
"""

import requests
import json

def test_complete_flow():
    """测试完整流程"""
    base_url = "http://0.0.0.0:5000"
    session = requests.Session()
    
    print("🚀 开始完整流程测试")
    
    # 1. 登录
    print("\n1️⃣ 测试登录...")
    response = session.post(f"{base_url}/login", data={
        "phone": "13800138000", 
        "password": "123456"
    })
    print(f"   登录响应状态: {response.status_code}")
    
    # 2. 访问主页
    print("\n2️⃣ 访问主页...")
    response = session.get(f"{base_url}/")
    print(f"   主页状态: {response.status_code}")
    
    # 3. 提交表单
    print("\n3️⃣ 提交表单 - 社区生活服务集合店...")
    form_data = {
        "projectName": "社区生活服务集合店",
        "projectDescription": "在居民区开设综合性生活服务店，集成超市、洗衣、快递、维修、家政等多种日常服务，为社区居民提供一站式便民服务。",
        "keyPersons": json.dumps([
            {
                "name": "张经理",
                "role": "店长", 
                "skills": "零售管理, 客户服务, 团队领导",
                "experience": "8年超市连锁店管理经验",
                "education": "工商管理大专",
                "resources": "本地客户关系网络, 供应商资源"
            }
        ], ensure_ascii=False)
    }
    
    response = session.post(f"{base_url}/generate", data=form_data)
    print(f"   表单提交状态: {response.status_code}")
    if response.status_code == 302:
        print(f"   重定向到: {response.headers.get('Location', 'N/A')}")
    
    # 4. 访问thinking页面
    print("\n4️⃣ 访问thinking页面...")
    response = session.get(f"{base_url}/thinking")
    print(f"   thinking页面状态: {response.status_code}")
    
    # 5. 检查分析状态
    print("\n5️⃣ 检查分析状态...")
    response = session.get(f"{base_url}/check_analysis_status")
    print(f"   分析状态API: {response.status_code}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"   状态: {data.get('status', 'Unknown')}")
            print(f"   项目名: {data.get('project_name', 'Unknown')}")
            print(f"   消息: {data.get('message', 'No message')}")
        except:
            print(f"   响应内容: {response.text[:200]}")
    
    print("\n✅ 完整流程测试结束")

if __name__ == "__main__":
    test_complete_flow()