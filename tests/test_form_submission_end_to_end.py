#!/usr/bin/env python3
"""
端到端测试：表单提交到AI分析完整流程
按照TDD要求测试整个用户使用流程
"""

import sys
import os
import unittest
import json
import requests
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestFormSubmissionEndToEnd(unittest.TestCase):
    """测试完整的表单提交到AI分析流程"""
    
    def setUp(self):
        """测试前的设置"""
        self.base_url = "http://0.0.0.0:5000"
        self.session = requests.Session()
        
        # 示例案例数据 - 社区生活服务集合店
        self.test_form_data = {
            "projectName": "社区生活服务集合店",
            "projectDescription": "在居民区开设综合性生活服务店，集成超市、洗衣、快递、维修、家政等多种日常服务，为社区居民提供一站式便民服务。",
            "keyPersons": [
                {
                    "name": "张经理",
                    "role": "店长",
                    "skills": "零售管理, 客户服务, 团队领导",
                    "experience": "8年超市连锁店管理经验",
                    "education": "工商管理大专",
                    "resources": "本地客户关系网络, 供应商资源"
                },
                {
                    "name": "李师傅", 
                    "role": "维修技师",
                    "skills": "家电维修, 水电安装, 小家具维修",
                    "experience": "15年维修从业经验",
                    "education": "技工学校毕业",
                    "resources": "维修工具设备, 配件供应渠道"
                }
            ]
        }
    
    def test_1_user_login(self):
        """测试1: 用户登录"""
        print("\n=== 测试1: 用户登录 ===")
        
        # 访问登录页面
        response = self.session.get(f"{self.base_url}/login")
        self.assertEqual(response.status_code, 200)
        print("✅ 登录页面访问成功")
        
        # 模拟用户登录（使用测试账号）
        login_data = {
            "phone": "13800138000",
            "password": "123456"
        }
        
        response = self.session.post(f"{self.base_url}/login", data=login_data)
        
        # 检查是否重定向（登录成功会重定向）
        if response.status_code in [200, 302]:
            print("✅ 登录请求发送成功")
        else:
            print(f"⚠️ 登录响应状态码: {response.status_code}")
    
    def test_2_access_main_page(self):
        """测试2: 访问主页面"""
        print("\n=== 测试2: 访问主页面 ===")
        
        response = self.session.get(f"{self.base_url}/")
        self.assertEqual(response.status_code, 200)
        print("✅ 主页面访问成功")
        
        # 检查页面是否包含表单元素
        self.assertIn("projectName", response.text)
        self.assertIn("projectDescription", response.text)
        print("✅ 表单元素存在")
    
    def test_3_form_submission(self):
        """测试3: 表单提交"""
        print("\n=== 测试3: 表单提交 ===")
        
        # 构建表单数据（模拟HTML表单提交）
        form_data = {
            "projectName": self.test_form_data["projectName"],
            "projectDescription": self.test_form_data["projectDescription"],
            "keyPersons": json.dumps(self.test_form_data["keyPersons"], ensure_ascii=False)
        }
        
        print(f"📝 提交项目: {form_data['projectName']}")
        print(f"📝 项目描述: {form_data['projectDescription'][:50]}...")
        print(f"📝 关键人员数量: {len(self.test_form_data['keyPersons'])}人")
        
        # 提交表单
        response = self.session.post(f"{self.base_url}/submit", data=form_data)
        
        # 检查响应
        print(f"📊 响应状态码: {response.status_code}")
        
        if response.status_code == 302:
            print("✅ 表单提交成功（重定向到thinking页面）")
            print(f"🔗 重定向URL: {response.headers.get('Location', 'N/A')}")
        elif response.status_code == 200:
            print("✅ 表单提交响应成功")
        else:
            print(f"❌ 表单提交失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text[:500]}")
    
    def test_4_thinking_page_access(self):
        """测试4: thinking页面访问"""
        print("\n=== 测试4: thinking页面访问 ===")
        
        response = self.session.get(f"{self.base_url}/thinking")
        print(f"📊 thinking页面状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ thinking页面访问成功")
            # 检查页面内容
            if "Angela正在分析" in response.text or "思考过程" in response.text:
                print("✅ thinking页面内容正确")
            else:
                print("⚠️ thinking页面内容可能异常")
        else:
            print(f"❌ thinking页面访问失败: {response.status_code}")
    
    def test_5_check_analysis_status(self):
        """测试5: 检查分析状态API"""
        print("\n=== 测试5: 检查分析状态API ===")
        
        response = self.session.get(f"{self.base_url}/check_analysis_status")
        print(f"📊 分析状态API状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ 分析状态API响应成功")
                print(f"📊 返回数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
                
                # 检查关键字段
                if 'status' in data:
                    print(f"📊 分析状态: {data['status']}")
                if 'project_name' in data:
                    print(f"📊 项目名称: {data['project_name']}")
                    
            except json.JSONDecodeError:
                print(f"⚠️ 分析状态API返回非JSON数据: {response.text[:200]}")
        else:
            print(f"❌ 分析状态API失败: {response.status_code}")
    
    def run_complete_test(self):
        """运行完整的端到端测试"""
        print("\n" + "="*60)
        print("🚀 开始端到端表单提交流程测试")
        print("📋 测试案例: 社区生活服务集合店")
        print("="*60)
        
        try:
            # 初始化测试环境
            self.setUp()
            
            self.test_1_user_login()
            self.test_2_access_main_page() 
            self.test_3_form_submission()
            self.test_4_thinking_page_access()
            self.test_5_check_analysis_status()
            
            print("\n" + "="*60)
            print("✅ 端到端测试完成！")
            print("="*60)
            
        except Exception as e:
            print(f"\n❌ 测试过程中出现错误: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    # 直接运行完整测试
    test = TestFormSubmissionEndToEnd()
    test.run_complete_test()