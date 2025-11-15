
#!/usr/bin/env python3
"""
测试laozhang.ai中转API的独立脚本
用于验证API key和base_url配置是否正常工作
"""
import os
from openai import OpenAI
import httpx

def test_laozhang_api():
    """测试laozhang.ai中转API"""
    print("=" * 60)
    print("开始测试 laozhang.ai 中转API")
    print("=" * 60)
    
    # 从环境变量获取API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ 错误：未找到环境变量 OPENAI_API_KEY")
        return False
    
    print(f"✅ API Key 已找到: {api_key[:20]}...")
    print(f"✅ Base URL: https://api.laozhang.ai/v1")
    
    try:
        # 创建客户端
        print("\n📡 创建OpenAI客户端...")
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.laozhang.ai/v1",
            timeout=httpx.Timeout(60.0, connect=30.0)
        )
        print("✅ 客户端创建成功")
        
        # 发送简单测试请求
        print("\n🚀 发送测试请求到API...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "你是一个测试助手"},
                {"role": "user", "content": "请简单回复：API测试成功"}
            ],
            temperature=0.7,
            max_tokens=100
        )
        
        # 解析响应
        if response and response.choices:
            content = response.choices[0].message.content
            print("\n" + "=" * 60)
            print("✅ API调用成功！")
            print("=" * 60)
            print(f"📝 API响应内容: {content}")
            print(f"📊 使用模型: {response.model}")
            print(f"🔢 Token使用: {response.usage.total_tokens if response.usage else 'N/A'}")
            print("=" * 60)
            return True
        else:
            print("❌ API返回了空响应")
            return False
            
    except httpx.ConnectError as e:
        print("\n" + "=" * 60)
        print("❌ 网络连接错误")
        print("=" * 60)
        print(f"错误详情: {str(e)}")
        print("可能原因:")
        print("  1. 中转API地址不可达")
        print("  2. 网络防火墙阻止")
        print("  3. DNS解析问题")
        return False
        
    except httpx.TimeoutException as e:
        print("\n" + "=" * 60)
        print("❌ 请求超时")
        print("=" * 60)
        print(f"错误详情: {str(e)}")
        print("可能原因:")
        print("  1. API响应太慢")
        print("  2. 网络不稳定")
        return False
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ 其他错误")
        print("=" * 60)
        print(f"错误类型: {type(e).__name__}")
        print(f"错误详情: {str(e)}")
        
        # 检查是否是认证错误
        if "401" in str(e) or "authentication" in str(e).lower():
            print("\n⚠️  这可能是API Key认证问题")
            print(f"当前使用的API Key: {api_key[:20]}...")
        
        return False

if __name__ == "__main__":
    success = test_laozhang_api()
    
    if success:
        print("\n🎉 测试通过！中转API工作正常")
        exit(0)
    else:
        print("\n❌ 测试失败！请检查配置")
        exit(1)
