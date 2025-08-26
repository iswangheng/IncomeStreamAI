#!/usr/bin/env python3
"""
Angela AI服务 - 简化版，专注个性化分析
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from openai import OpenAI
from tenacity import retry, wait_exponential, stop_after_attempt

# 配置日志
logger = logging.getLogger(__name__)


class AngelaAIService:
    """Angela AI服务类"""

    def __init__(self):
        # 初始化OpenAI客户端
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def get_model_config(self, config_type='main_analysis'):
        """获取模型配置"""
        configs = {
            'main_analysis': {
                'model': 'gpt-4o-2024-11-20',
                'temperature': 0.7,
                'max_tokens': 3000,
                'timeout': 60
            }
        }
        return configs.get(config_type, configs['main_analysis'])

    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
    def _call_openai_with_retry(self, **kwargs):
        """带重试的OpenAI API调用"""
        try:
            response = self.client.chat.completions.create(**kwargs)
            return response
        except Exception as e:
            logger.error(f"OpenAI API调用失败: {e}")
            raise

    def format_role_to_chinese(self, role_identifier: str) -> str:
        """将角色标识符转换为中文"""
        role_mapping = {
            'brand_manager': '品牌经理',
            'teacher': '教师',
            'content_creator': '内容创作者',
            'business_owner': '商业负责人',
            'project_manager': '项目经理',
            'technical_lead': '技术负责人'
        }
        return role_mapping.get(role_identifier, role_identifier)

    def get_role_type_by_identifier(self, role_identifier: str) -> str:
        """根据角色标识符获取角色类型"""
        type_mapping = {
            'brand_manager': '需求方',
            'teacher': '交付方',
            'content_creator': '交付方',
            'business_owner': '统筹方',
            'project_manager': '统筹方',
            'technical_lead': '交付方'
        }
        return type_mapping.get(role_identifier, '其他方')

    def format_make_happy(self, make_happy_data) -> str:
        """格式化动机标签"""
        if isinstance(make_happy_data, list):
            return ", ".join(make_happy_data)
        elif isinstance(make_happy_data, str):
            return make_happy_data
        return "未指定"

    def format_external_resources(self, external_resources: List[Dict]) -> str:
        """格式化外部资源"""
        if not external_resources:
            return "无可用外部资源"
        
        formatted = []
        for resource in external_resources:
            name = resource.get('name', '未命名资源')
            desc = resource.get('description', '无描述')
            formatted.append(f"- {name}: {desc}")
        
        return "\n".join(formatted)

    def get_core_knowledge_fallback(self) -> str:
        """核心知识备用方案"""
        return """非劳务收入核心要点：
• 核心公式：意识+能量+能力=结果
• 七大类型：租金、利息、股份、版权、居间、企业连锁、团队收益
• 三步法则：盘资源→搭管道→动真格
• 核心原则：让关键环节的关键人物都高兴"""

    def get_knowledge_base_snippets(self, project_description, key_persons, external_resources, db_session):
        """获取知识库片段（简化版）"""
        try:
            # 这里可以实现更复杂的知识库检索逻辑
            return self.get_core_knowledge_fallback()
        except Exception as e:
            logger.warning(f"知识库检索失败: {e}")
            return self.get_core_knowledge_fallback()

    def generate_income_paths(self, form_data: Dict[str, Any], db_session) -> Dict[str, Any]:
        """生成非劳务收入路径 - 简化版"""
        logger.info("=== Angela AI generate_income_paths方法开始 ===")
        logger.info(f"输入数据: {json.dumps(form_data, ensure_ascii=False)}")
        
        try:
            # 提取表单数据
            project_name = form_data.get('projectName', '未命名项目')
            project_description = form_data.get('projectDescription', '')
            key_persons = form_data.get('keyPersons', [])
            external_resources = form_data.get('externalResources', [])

            # 获取知识库片段
            try:
                kb_snippets = self.get_knowledge_base_snippets(
                    project_description, key_persons, external_resources, db_session)
                # 限制知识库内容长度
                if len(kb_snippets) > 500:
                    kb_snippets = kb_snippets[:500] + "..."
            except Exception as kb_error:
                logger.warning(f"Knowledge base retrieval failed: {kb_error}")
                kb_snippets = self.get_core_knowledge_fallback()

            # 简化系统提示 - 专注于个性化分析  
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

            # 构造用户提示
            user_content = f"""【项目名称】{project_name}
【项目背景】{project_description}

【关键人物】（含角色、资源、动机）"""

            for i, person in enumerate(key_persons):
                name = person.get('name', f'人物{i+1}')
                role = person.get('role', '')
                resources = person.get('resources', [])
                make_happy = person.get('make_happy', '')
                notes = person.get('notes', '')

                # 将英文角色标识符转换为中文显示名称
                role_chinese = self.format_role_to_chinese(role) if role else "未指定"
                role_type = self.get_role_type_by_identifier(role) if role else "其他方"

                user_content += f"""
- 人物：{name}｜角色：{role_chinese}（{role_type}）
  资源：{", ".join(resources) if resources else "无"}
  动机标签（如何让TA高兴）：{self.format_make_happy(make_happy)}
  备注：{notes if notes else "无"}"""

            user_content += f"""

【外部资源（可直接使用的资源池）】
{self.format_external_resources(external_resources)}

【知识库要点】（只给要点，避免冗长）
{kb_snippets}"""

            # 简化assistant prompt - 专注于个性化生成
            assistant_prompt = f"""请根据这个具体项目，生成个性化的非劳务收入管道建议。

要求：
1. 必须体现项目的独特特点
2. 管道名称要反映项目特色，避免通用模板
3. 针对项目的具体痛点和机会
4. 说明如何利用现有资源

请返回JSON格式：
{{
  "overview": {{
    "situation": "项目分析（针对具体项目情况）",
    "income_type": "适用的非劳务收入类型",
    "core_insight": "核心洞察（项目的独特机会）",
    "gaps": ["缺少的关键角色"],
    "suggested_roles_to_hunt": []
  }},
  "pipelines": [
    {{
      "id": "pipeline_1", 
      "name": "针对项目的具体管道名称",
      "income_mechanism": {{
        "type": "收入类型",
        "trigger": "收益触发点",
        "settlement": "结算方式"
      }},
      "parties_structure": [
        {{
          "party": "参与方名称",
          "role_type": "需求方/交付方/资金方/统筹方",
          "role_value": "该参与方的价值",
          "resources": ["资源1", "资源2"],
          "motivation": "参与动机"
        }}
      ],
      "mvp": "针对项目的最小验证方案",
      "first_step": "项目的具体第一步行动",
      "risks_and_plan_b": [
        {{
          "risk": "风险点",
          "plan_b": "应对方案"
        }}
      ]
    }}
  ]
}}"""

            logger.info(f"系统提示长度: {len(system_prompt)} 字符")
            logger.info(f"用户内容长度: {len(user_content)} 字符")  
            logger.info(f"助手提示长度: {len(assistant_prompt)} 字符")

            # OpenAI API调用
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-2024-11-20",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                        {"role": "assistant", "content": assistant_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.7,
                    max_tokens=3000
                )
                
                result_text = response.choices[0].message.content
                logger.info(f"AI原始响应: {result_text[:500]}...")
                
                # 解析JSON
                result = json.loads(result_text)
                logger.info("✅ JSON解析成功")
                
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {e}")
                logger.error(f"原始响应: {result_text}")
                return self.get_fallback_response()
                
            except Exception as e:
                logger.error(f"OpenAI API调用失败: {e}")
                return self.get_fallback_response()

        except Exception as e:
            logger.error(f"生成非劳务收入路径时发生错误: {e}")
            return self.get_fallback_response()

    def get_fallback_response(self):
        """返回备用响应"""
        return {
            "overview": {
                "situation": "由于技术问题，暂时无法生成个性化分析",
                "income_type": "居间", 
                "core_insight": "请重试或联系技术支持",
                "gaps": [],
                "suggested_roles_to_hunt": []
            },
            "pipelines": [{
                "id": "pipeline_1",
                "name": "暂时无法生成",
                "income_mechanism": {
                    "type": "居间",
                    "trigger": "暂时无法生成",
                    "settlement": "暂时无法生成"
                },
                "parties_structure": [],
                "mvp": "请重试",
                "first_step": "请重试",
                "risks_and_plan_b": []
            }]
        }

    def refine_path(self, pipeline_data: Dict[str, Any], db_session) -> Dict[str, Any]:
        """精化路径（简化版）"""
        logger.info("refine_path方法被调用")
        # 这里可以实现路径精化逻辑
        return pipeline_data

    def _validate_result_structure(self, result: Dict[str, Any]) -> bool:
        """验证结果结构"""
        required_keys = ['overview', 'pipelines']
        return all(key in result for key in required_keys)

    def _get_fallback_result(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """获取备用结果"""
        return self.get_fallback_response()