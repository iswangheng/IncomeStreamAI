#!/usr/bin/env python3
"""
测试 OpenAI API 连接的独立脚本
用于诊断 OpenAI API 调用问题
"""
import os
import json
from openai import OpenAI
import httpx
import logging

# 设置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_openai_connection():
    """测试 OpenAI API 连接"""
    try:
        # 检查 API key
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("❌ 没有找到 OPENAI_API_KEY 环境变量")
            return False
        
        print(f"✅ 找到 API Key (前10字符): {api_key[:10]}...")
        
        # 创建客户端
        client = OpenAI(
            api_key=api_key,
            timeout=httpx.Timeout(30.0, connect=15.0)
        )
        
        print("🔄 测试简单的 API 调用...")
        
        # 简单的测试请求
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "请简单回答：你是谁？"}
            ],
            max_tokens=50,
            temperature=0.7
        )
        
        print("✅ OpenAI API 调用成功!")
        print(f"📝 响应: {response.choices[0].message.content}")
        
        return True
        
    except httpx.TimeoutException as e:
        print(f"⏰ 网络超时错误: {str(e)}")
        return False
    except httpx.ConnectError as e:
        print(f"🌐 网络连接错误: {str(e)}")
        return False
    except Exception as e:
        print(f"💥 其他错误: {str(e)}")
        print(f"💥 错误类型: {type(e).__name__}")
        import traceback
        print(f"💥 完整堆栈: {traceback.format_exc()}")
        return False

def test_complex_prompt():
    """测试复杂的提示词（类似真实场景）"""
    try:
        api_key = os.environ.get("OPENAI_API_KEY")
        client = OpenAI(api_key=api_key)
        
        print("🔄 测试复杂的分析请求...")
        
        system_prompt = """你是Angela，专业的非劳务收入管道设计师。
根据用户的项目信息，设计非劳务收入方案。

要求：
- 输出JSON格式
- 包含overview和pipelines字段
"""
        
        user_prompt = """【项目】测试项目
【描述】这是一个测试项目，用于验证API连接"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=1000,
            temperature=0.7
        )
        
        result_text = response.choices[0].message.content
        print("✅ 复杂请求成功!")
        print(f"📝 响应长度: {len(result_text)} 字符")
        
        # 尝试解析JSON
        try:
            result = json.loads(result_text)
            print("✅ JSON解析成功!")
            print(f"📋 顶级字段: {list(result.keys())}")
        except json.JSONDecodeError as json_error:
            print(f"❌ JSON解析失败: {json_error}")
            print(f"📝 原始响应: {result_text[:500]}...")
        
        return True
        
    except Exception as e:
        print(f"💥 复杂请求失败: {str(e)}")
        import traceback
        print(f"💥 完整堆栈: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🧪 开始 OpenAI API 诊断测试\n")
    
    # 基础连接测试
    print("=" * 50)
    print("测试 1: 基础连接测试")
    print("=" * 50)
    basic_success = test_openai_connection()
    
    if basic_success:
        print("\n" + "=" * 50)
        print("测试 2: 复杂提示词测试")
        print("=" * 50)
        complex_success = test_complex_prompt()
    else:
        complex_success = False
    
    print("\n" + "=" * 50)
    print("🏁 测试结果汇总")
    print("=" * 50)
    print(f"基础连接: {'✅ 成功' if basic_success else '❌ 失败'}")
    print(f"复杂请求: {'✅ 成功' if complex_success else '❌ 失败'}")
    
    if basic_success and complex_success:
        print("\n🎉 OpenAI API 工作正常！问题可能在于应用代码的其他部分。")
    elif basic_success and not complex_success:
        print("\n⚠️ 基础连接正常，但复杂请求失败。可能是提示词或参数问题。")
    else:
        print("\n🚨 OpenAI API 连接有问题，需要检查网络和API key。")