import os
import sys
import json
import time

# 添加项目路径
sys.path.insert(0, '/home/runner/workspace')

from openai_service import AngelaAI
from app import db

print("Testing full AI service with actual project data...")

# 测试数据 - 商铺租赁案例
test_data = {
    "projectName": "Angela临街商铺二房东管道",
    "projectDescription": "我打了20多个电话调研发现一个房东有临街双层商铺，挂了两三个月都租不出去",
    "keyPersons": [
        {
            "name": "社恐房东",
            "role": "investor",
            "resources": ["临街双层商铺", "5年长期租约意愿"],
            "make_happy": "recurring_income,no_money_no_liability"
        }
    ],
    "externalResources": ["暂无明确外部资源"]
}

try:
    angela_ai = AngelaAI()
    print(f"Using model: {angela_ai.model}")
    print(f"Max tokens: {angela_ai.max_tokens}")
    
    start_time = time.time()
    print("\nGenerating income paths...")
    
    # 使用实际的数据库session
    with db.app.app_context():
        result = angela_ai.generate_income_paths(test_data, db.session)
    
    elapsed = time.time() - start_time
    
    if result:
        print(f"\n✓ Success! Generated in {elapsed:.2f} seconds")
        print(f"Result keys: {list(result.keys())}")
        
        if 'overview' in result:
            print(f"Income type: {result['overview'].get('income_type', 'N/A')}")
        if 'income_paths' in result and len(result['income_paths']) > 0:
            print(f"Generated {len(result['income_paths'])} paths")
            print(f"First path title: {result['income_paths'][0].get('title', 'N/A')}")
    else:
        print(f"\n✗ Failed: AI returned None after {elapsed:.2f} seconds")
        
except Exception as e:
    print(f"\n✗ Error: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
