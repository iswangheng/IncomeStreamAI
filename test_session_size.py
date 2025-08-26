#!/usr/bin/env python3
"""测试session大小，找出占用空间最大的数据"""

import json
import sys

# 模拟一个session字典
sample_session = {
    '_fresh': False,
    '_permanent': True,
    '_user_id': '1',
    'analysis_form_data': {
        'keyPersons': [
            {
                'make_happy': ['获得持续收入', '不冲突现有合作', '品牌曝光', '获得认可/名声'], 
                'name': '升学规划师Lisa', 
                'resources': ['1000+精准家长客户', '教育咨询品牌信任度', '家长微信群3个', '升学规划专业认证'], 
                'role': 'enterprise_owner'
            },
            {
                'make_happy': ['获得稳定客源', '获得持续收入', '获得认可/名声'],
                'name': '英语外教Kevin', 
                'resources': ['TESOL认证', '5年教学经验', '线上教学设备', '标准美式发音', '课程设计能力'],
                'role': 'service_provider'
            },
            {
                'make_happy': ['控制成本开支', '获得稳定供应', '获得优质产品'],
                'name': '程序员家长王先生',
                'resources': ['教育支付预算年5万', '对在线教育接受度高', '注重教学效果', '愿意分享好的教育产品'],
                'role': 'store_owner'
            }
        ],
        'projectDescription': '我通过朋友圈发现，升学规划师朋友经常有家长询问英语培训推荐，而我认识的外教群体因为疫情线下课减少正在找线上机会。我设计了"1对1外教口语陪练"产品：标准化课程包（30分钟/节，8节一期），统一定价288元/期，我负责获客和质量监督，外教获得稳定学员，升学规划师获得推荐费。这样形成三方共赢的收入管道。',
        'projectName': '在线口语陪练连接平台'
    },
    'analysis_progress': 0,
    'analysis_result': None,
    'analysis_result_id': None,
    'analysis_stage': '准备开始分析...',
    'analysis_started': False,
    'analysis_status': 'not_started'
}

def analyze_session_size(session_data):
    """分析session中各个字段的大小"""
    total_size = len(json.dumps(session_data, ensure_ascii=False))
    print(f"Total session size: {total_size} bytes")
    
    if total_size > 4093:
        print(f"⚠️ WARNING: Session size exceeds 4093 bytes limit by {total_size - 4093} bytes!")
    else:
        print(f"✓ Session size is within limit (under 4093 bytes)")
    
    print("\nSize breakdown by key:")
    print("-" * 50)
    
    # 分析每个键的大小
    sizes = []
    for key, value in session_data.items():
        key_size = len(json.dumps({key: value}, ensure_ascii=False))
        sizes.append((key, key_size))
    
    # 按大小排序
    sizes.sort(key=lambda x: x[1], reverse=True)
    
    for key, size in sizes:
        percentage = (size / total_size) * 100
        print(f"{key:30s}: {size:6d} bytes ({percentage:5.1f}%)")
    
    return total_size

def test_minimal_session():
    """测试最小session配置"""
    minimal_session = {
        '_fresh': False,
        '_permanent': True,
        '_user_id': '1',
        'analysis_project_name': '在线口语陪练连接平台',
        'analysis_form_id': '0f0e3bda-2e6a-48e0-b7a0-267baecd51ca',
        'analysis_result_id': '0f0e3bda-2e6a-48e0-b7a0-267baecd51ca',
        'analysis_status': 'completed',
        'analysis_progress': 100,
        'analysis_stage': '分析完成！'
    }
    
    print("\n" + "=" * 50)
    print("Testing minimal session configuration:")
    print("=" * 50)
    
    size = analyze_session_size(minimal_session)
    return size

# 运行测试
print("=" * 50)
print("Analyzing current session with form_data:")
print("=" * 50)
current_size = analyze_session_size(sample_session)

minimal_size = test_minimal_session()

print("\n" + "=" * 50)
print("SUMMARY:")
print("=" * 50)
print(f"Current session size: {current_size} bytes")
print(f"Minimal session size: {minimal_size} bytes")
print(f"Reduction: {current_size - minimal_size} bytes ({((current_size - minimal_size) / current_size * 100):.1f}%)")

if current_size > 4093:
    print(f"\n⚠️ Need to reduce by at least {current_size - 4093} bytes to meet limit")
if minimal_size < 4093:
    print(f"✓ Minimal configuration is within limit with {4093 - minimal_size} bytes to spare")