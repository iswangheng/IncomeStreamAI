#!/usr/bin/env python3
"""
测试简化prompt的OpenAI调用
"""

import os
import json
import openai
from openai import OpenAI

def test_simplified_prompt():
    """测试简化的prompt是否能生成个性化结果"""
    
    # 简化的系统prompt
    system_prompt = """你是Angela，专业的非劳务收入管道设计师。

## 任务
根据用户的具体项目特点，设计个性化的非劳务收入管道方案。

## 核心原则
- 非劳务收入类型：租金、利息、股份、版权、居间、企业连锁、团队收益
- 设计者通过整合资源获得收益，而非依赖持续劳动
- 让所有参与方获益，设计者控制关键环节

## 要求
- 深入分析项目特点，提供针对性建议
- 避免通用模板，体现项目独特性  
- 说明具体的收益机制和第一步行动

## 分析要点
针对这个具体项目，请分析：
1. 项目的独特机会点在哪里？
2. 现有资源如何形成收益闭环？  
3. 设计者可以通过什么方式获得非劳务收入？
4. 第一步应该如何行动？"""

    # 用户内容（出书项目）
    user_content = """【项目名称】老师想要出书
【项目背景】听说Angela老师想要出书，感觉有机会搭建非劳务收入管道了

【关键人物】（含角色、资源、动机）
- 人物：Angela｜角色：品牌经理（需求方）
  资源：决策权, 签约权限, 品牌授权
  动机标签（如何让TA高兴）：项目尽快落地, 打造个人标签/专家身份, 曝光到目标圈层, 有品牌露出（线上线下）
  备注：无

【外部资源（可直接使用的资源池）】
无可用外部资源

【知识库要点】（只给要点，避免冗长）
非劳务收入核心要点：
• 核心公式：意识+能量+能力=结果
• 七大类型：租金、利息、股份、版权、居间、企业连锁、团队收益
• 三步法则：盘资源→搭管道→动真格
• 核心原则：让关键环节的关键人物都高兴"""

    # 简化的assistant prompt
    assistant_prompt = """请根据这个具体的出书项目，生成个性化的非劳务收入管道建议。

要求：
1. 必须体现"出书"这个项目的特点
2. 管道名称要反映项目特色，不能是通用的"资源整合撮合管道"
3. 针对出书行业的具体痛点和机会
4. 说明如何利用Angela的品牌和决策权资源

请返回JSON格式：
{
  "overview": {
    "situation": "项目分析（针对出书项目的具体情况）",
    "income_type": "适用的非劳务收入类型",
    "core_insight": "核心洞察（出书项目的独特机会）",
    "gaps": ["缺少的关键角色"],
    "suggested_roles_to_hunt": []
  },
  "pipelines": [
    {
      "id": "pipeline_1", 
      "name": "针对出书项目的具体管道名称",
      "income_mechanism": {
        "type": "收入类型",
        "trigger": "收益触发点",
        "settlement": "结算方式"
      },
      "mvp": "针对出书项目的最小验证方案",
      "first_step": "出书项目的具体第一步行动"
    }
  ]
}"""

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-2024-11-20",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}, 
                {"role": "assistant", "content": assistant_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=2000
        )
        
        result_text = response.choices[0].message.content
        result = json.loads(result_text)
        
        print("🎯 简化prompt测试结果:")
        print(f"管道名称: {result['pipelines'][0]['name']}")
        print(f"收入类型: {result['pipelines'][0]['income_mechanism']['type']}")
        print(f"MVP: {result['pipelines'][0]['mvp']}")
        print(f"第一步: {result['pipelines'][0]['first_step']}")
        
        return result
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return None

if __name__ == "__main__":
    test_simplified_prompt()