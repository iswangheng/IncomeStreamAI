
#!/bin/bash

# 测试laozhang.ai中转API的shell脚本
echo "======================================"
echo "测试 laozhang.ai 中转API"
echo "======================================"

# 从环境变量获取API key
API_KEY="${OPENAI_API_KEY}"

if [ -z "$API_KEY" ]; then
    echo "❌ 错误: 环境变量 OPENAI_API_KEY 未设置"
    exit 1
fi

echo "✅ API Key 已找到: ${API_KEY:0:20}..."
echo "✅ Base URL: https://api.laozhang.ai/v1"
echo ""
echo "🚀 发送测试请求..."
echo ""

# 发送curl请求并保存响应
response=$(curl -s -w "\n%{http_code}" https://api.laozhang.ai/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": "gpt-4o",
    "messages": [
      {"role": "user", "content": "请简单回复：API测试成功"}
    ]
  }')

# 分离响应体和状态码
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

echo "======================================"
echo "📊 HTTP状态码: $http_code"
echo "======================================"

if [ "$http_code" -eq 200 ]; then
    echo "✅ API调用成功！"
    echo ""
    echo "📝 响应内容:"
    echo "$body" | python3 -m json.tool
    echo ""
    echo "======================================"
    echo "🎉 测试通过！中转API工作正常"
    echo "======================================"
    exit 0
else
    echo "❌ API调用失败"
    echo ""
    echo "错误响应:"
    echo "$body"
    echo ""
    
    if [ "$http_code" -eq 401 ]; then
        echo "⚠️  认证失败 - 请检查API Key是否正确"
    elif [ "$http_code" -eq 0 ]; then
        echo "⚠️  网络连接失败 - 无法连接到API服务器"
    fi
    
    echo "======================================"
    exit 1
fi
