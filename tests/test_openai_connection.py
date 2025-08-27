#!/usr/bin/env python3
"""测试OpenAI API连接"""

import os
import sys
from openai import OpenAI

def test_openai_connection():
    """测试OpenAI API连接"""
    try:
        # 检查API密钥
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("❌ 错误：未找到OPENAI_API_KEY环境变量")
            return False
        
        print(f"✓ API密钥已配置 (长度: {len(api_key)})")
        
        # 创建客户端
        client = OpenAI(api_key=api_key)
        print("✓ OpenAI客户端创建成功")
        
        # 测试简单调用
        print("🧪 测试API调用...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # 使用便宜的模型测试
            messages=[
                {"role": "user", "content": "Hello! Just testing the connection. Please respond with 'Connection OK'."}
            ],
            max_tokens=20,
            timeout=10
        )
        
        if response and response.choices:
            content = response.choices[0].message.content
            print(f"✅ API调用成功！响应: {content}")
            return True
        else:
            print("❌ API调用失败：无有效响应")
            return False
            
    except Exception as e:
        print(f"❌ API调用出错: {str(e)}")
        print(f"错误类型: {type(e).__name__}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("OpenAI API 连接测试")
    print("=" * 50)
    
    success = test_openai_connection()
    
    if success:
        print("\n✅ 连接测试成功！OpenAI API工作正常")
        sys.exit(0)
    else:
        print("\n❌ 连接测试失败！")
        sys.exit(1)