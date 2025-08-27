#!/usr/bin/env python3
"""
OpenAI API 测试脚本
用于检查API密钥是否有效、余额是否充足
"""

import os
import sys
from openai import OpenAI
import httpx

def test_openai_api():
    """测试OpenAI API连接"""
    print("🔍 正在测试OpenAI API...")
    
    # 检查API密钥
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ 错误: 未找到OPENAI_API_KEY环境变量")
        return False
    
    print(f"✅ API密钥已找到: {api_key[:10]}...{api_key[-4:]}")
    
    try:
        # 创建客户端，设置较短的超时时间用于测试
        client = OpenAI(
            api_key=api_key,
            timeout=httpx.Timeout(10.0)
        )
        
        print("🚀 正在发送测试请求...")
        
        # 发送简单的测试请求
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # 使用较便宜的模型进行测试
            messages=[
                {"role": "user", "content": "请回复'API测试成功'"}
            ],
            max_tokens=10,
            temperature=0
        )
        
        result = response.choices[0].message.content
        print(f"✅ API测试成功! 响应: {result}")
        
        # 显示使用信息
        if hasattr(response, 'usage'):
            usage = response.usage
            print(f"📊 Token使用: {usage.prompt_tokens} + {usage.completion_tokens} = {usage.total_tokens}")
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ API测试失败: {error_msg}")
        
        # 检查常见错误类型
        if "insufficient_quota" in error_msg.lower():
            print("💰 可能的原因: OpenAI账户余额不足")
            print("📝 建议: 请检查您的OpenAI账户余额并充值")
        elif "invalid_api_key" in error_msg.lower():
            print("🔑 可能的原因: API密钥无效或已过期")
            print("📝 建议: 请检查您的API密钥是否正确")
        elif "rate_limit" in error_msg.lower():
            print("⏰ 可能的原因: API请求频率限制")
            print("📝 建议: 请稍后再试")
        elif "timeout" in error_msg.lower():
            print("🌐 可能的原因: 网络连接超时")
            print("📝 建议: 请检查网络连接")
        else:
            print("🔍 其他错误，请检查API密钥和网络连接")
        
        return False

def test_billing_info():
    """尝试获取账单信息（如果API支持）"""
    print("\n💰 正在检查账单信息...")
    
    try:
        api_key = os.environ.get("OPENAI_API_KEY")
        client = OpenAI(api_key=api_key)
        
        # 注意：OpenAI已经移除了直接的余额查询API
        # 这里只是尝试一个简单的模型列表请求来验证权限
        models = client.models.list()
        available_models = [model.id for model in models.data if 'gpt' in model.id]
        print(f"✅ 可用的GPT模型: {', '.join(available_models[:5])}...")
        
    except Exception as e:
        print(f"⚠️ 无法获取详细账单信息: {str(e)}")

if __name__ == "__main__":
    print("=" * 50)
    print("OpenAI API 连接测试")
    print("=" * 50)
    
    success = test_openai_api()
    test_billing_info()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 测试完成: API连接正常")
    else:
        print("💥 测试完成: API连接存在问题")
        sys.exit(1)