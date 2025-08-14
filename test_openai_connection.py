import os
import httpx
from openai import OpenAI
import time

print("Testing OpenAI API connection...")
print(f"API Key exists: {bool(os.environ.get('OPENAI_API_KEY'))}")

# 测试基础连接
try:
    # 使用更短的超时测试
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
        timeout=httpx.Timeout(10.0, connect=5.0)
    )
    
    start = time.time()
    print("Sending test request to OpenAI...")
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # 使用更快的模型测试
        messages=[{"role": "user", "content": "Say 'test ok' in 2 words"}],
        max_tokens=10
    )
    
    elapsed = time.time() - start
    print(f"✓ Success! Response in {elapsed:.2f}s: {response.choices[0].message.content}")
    
except httpx.TimeoutException as e:
    print(f"✗ Timeout error: {e}")
except httpx.ConnectError as e:
    print(f"✗ Connection error: {e}")
except Exception as e:
    print(f"✗ Other error: {type(e).__name__}: {e}")
