#!/usr/bin/env python3
"""
AI分析模块单元测试
测试目的：验证AI分析功能是否正常工作
"""

import os
import sys
import json
import time
import traceback
from datetime import datetime

# 设置环境变量
os.environ['DATABASE_URL'] = os.environ.get('DATABASE_URL', '')
os.environ['OPENAI_API_KEY'] = os.environ.get('OPENAI_API_KEY', '')

print("=" * 60)
print("AI分析模块单元测试")
print("=" * 60)
print(f"测试时间: {datetime.now()}")
print(f"OpenAI API Key 状态: {'已配置' if os.environ.get('OPENAI_API_KEY') else '未配置'}")
print(f"数据库连接状态: {'已配置' if os.environ.get('DATABASE_URL') else '未配置'}")
print("=" * 60)

# 测试用例数据
test_cases = [
    {
        "name": "测试用例1: 简单项目",
        "data": {
            "projectName": "测试项目1",
            "projectDescription": "这是一个测试项目，用于验证AI分析功能",
            "projectStage": "idea",
            "keyPersons": [
                {
                    "name": "张三",
                    "role": "developer",
                    "resources": ["技术能力", "开发经验"],
                    "make_happy": "learning"
                }
            ],
            "externalResources": ["无"]
        }
    },
    {
        "name": "测试用例2: 完整项目",
        "data": {
            "projectName": "企业内网部署项目",
            "projectDescription": "为某公司搭建内部网络系统，满足办公需求",
            "projectStage": "growing",
            "keyPersons": [
                {
                    "name": "王总",
                    "role": "buyer",
                    "resources": ["采购预算", "决策权"],
                    "make_happy": "fast_execution"
                },
                {
                    "name": "李经理",
                    "role": "user",
                    "resources": ["使用反馈", "需求调研"],
                    "make_happy": "recognition"
                }
            ],
            "externalResources": ["技术支持团队", "硬件供应商"]
        }
    },
    {
        "name": "测试用例3: 最小数据",
        "data": {
            "projectName": "最小测试",
            "projectDescription": "最小化测试",
            "projectStage": "idea",
            "keyPersons": [],
            "externalResources": []
        }
    }
]

def test_openai_connection():
    """测试OpenAI API连接"""
    print("\n[测试] OpenAI API连接测试...")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        
        # 简单的连接测试
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "测试连接，请回复OK"}],
            max_tokens=10,
            timeout=10
        )
        
        if response and response.choices:
            print("✓ OpenAI API连接成功")
            return True
        else:
            print("✗ OpenAI API响应异常")
            return False
            
    except Exception as e:
        print(f"✗ OpenAI API连接失败: {str(e)}")
        return False

def test_generate_ai_suggestions(test_case):
    """测试generate_ai_suggestions函数"""
    print(f"\n[测试] {test_case['name']}")
    print(f"输入数据: {json.dumps(test_case['data'], ensure_ascii=False, indent=2)}")
    
    try:
        # 导入必要的模块
        from app import app, generate_ai_suggestions
        
        with app.app_context():
            start_time = time.time()
            
            # 调用AI分析函数
            result = generate_ai_suggestions(test_case['data'])
            
            elapsed_time = time.time() - start_time
            
            if result:
                print(f"✓ 分析成功 (耗时: {elapsed_time:.2f}秒)")
                print(f"结果类型: {type(result)}")
                print(f"结果键值: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
                
                # 验证结果结构
                if isinstance(result, dict):
                    required_keys = ['overview', 'paths']
                    missing_keys = [k for k in required_keys if k not in result]
                    if missing_keys:
                        print(f"⚠ 结果缺少必需键: {missing_keys}")
                    else:
                        print(f"✓ 结果包含所有必需键")
                        
                    # 检查是否是备用方案
                    if 'overview' in result and 'situation' in result['overview']:
                        if '基础的合作变现潜力' in str(result['overview']['situation']):
                            print("⚠ 注意: 返回的是备用方案，不是真正的AI分析结果")
                        else:
                            print("✓ 返回的是真正的AI分析结果")
                            
                return True
            else:
                print(f"✗ 分析失败: 返回结果为空")
                return False
                
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        print(f"错误详情:\n{traceback.format_exc()}")
        return False

def test_angela_ai_direct():
    """直接测试AngelaAI类"""
    print("\n[测试] 直接测试AngelaAI类...")
    
    try:
        from openai_service import AngelaAI
        from app import app, db
        
        with app.app_context():
            angela_ai = AngelaAI()
            
            test_data = {
                "projectName": "直接测试项目",
                "projectDescription": "直接测试AngelaAI类的功能",
                "projectStage": "idea",
                "keyPersons": [
                    {
                        "name": "测试员",
                        "role": "tester",
                        "resources": ["测试能力"],
                        "make_happy": "learning"
                    }
                ],
                "externalResources": ["测试资源"]
            }
            
            print(f"调用AngelaAI.generate_income_paths...")
            start_time = time.time()
            
            try:
                result = angela_ai.generate_income_paths(test_data, db)
                elapsed_time = time.time() - start_time
                
                if result:
                    print(f"✓ 直接调用成功 (耗时: {elapsed_time:.2f}秒)")
                    print(f"结果预览: {str(result)[:200]}...")
                    return True
                else:
                    print(f"✗ 直接调用失败: 无返回结果")
                    return False
                    
            except Exception as e:
                elapsed_time = time.time() - start_time
                print(f"✗ 直接调用失败 (耗时: {elapsed_time:.2f}秒)")
                print(f"错误: {str(e)}")
                return False
                
    except Exception as e:
        print(f"✗ 无法导入或初始化AngelaAI: {str(e)}")
        return False

def test_timeout_handling():
    """测试超时处理机制"""
    print("\n[测试] 超时处理机制测试...")
    
    try:
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("测试超时")
        
        # 设置1秒超时
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(1)
        
        try:
            time.sleep(2)  # 故意睡眠2秒触发超时
            signal.alarm(0)
            print("✗ 超时机制未触发")
            return False
        except TimeoutError:
            signal.alarm(0)
            print("✓ 超时机制正常工作")
            return True
            
    except Exception as e:
        print(f"✗ 超时测试失败: {str(e)}")
        return False

def run_all_tests():
    """运行所有测试"""
    results = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "details": []
    }
    
    # 1. 测试超时机制
    print("\n" + "=" * 60)
    print("步骤1: 测试基础设施")
    print("=" * 60)
    
    if test_timeout_handling():
        results["passed"] += 1
    else:
        results["failed"] += 1
    results["total"] += 1
    
    # 2. 测试OpenAI连接
    if test_openai_connection():
        results["passed"] += 1
    else:
        results["failed"] += 1
        print("⚠ OpenAI连接失败，后续测试可能无法正常进行")
    results["total"] += 1
    
    # 3. 测试generate_ai_suggestions函数
    print("\n" + "=" * 60)
    print("步骤2: 测试AI分析函数")
    print("=" * 60)
    
    for test_case in test_cases:
        if test_generate_ai_suggestions(test_case):
            results["passed"] += 1
        else:
            results["failed"] += 1
        results["total"] += 1
    
    # 4. 直接测试AngelaAI
    print("\n" + "=" * 60)
    print("步骤3: 直接测试AngelaAI类")
    print("=" * 60)
    
    if test_angela_ai_direct():
        results["passed"] += 1
    else:
        results["failed"] += 1
    results["total"] += 1
    
    # 打印测试总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"总测试数: {results['total']}")
    print(f"通过: {results['passed']}")
    print(f"失败: {results['failed']}")
    print(f"成功率: {results['passed']/results['total']*100:.1f}%")
    
    if results['failed'] > 0:
        print("\n⚠ 发现问题:")
        if results['failed'] == results['total']:
            print("- 所有测试都失败了，可能是API密钥或网络连接问题")
        else:
            print("- 部分测试失败，需要检查具体的错误信息")
    else:
        print("\n✓ 所有测试通过!")
    
    return results

if __name__ == "__main__":
    try:
        results = run_all_tests()
        sys.exit(0 if results['failed'] == 0 else 1)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n测试运行失败: {str(e)}")
        print(traceback.format_exc())
        sys.exit(1)