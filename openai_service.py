import os
import json
import logging
from openai import OpenAI
from typing import Dict, List, Any, Optional

# OpenAI客户端初始化
# the newest OpenAI model is "gpt-4o" which was released May 13, 2024. 
# do not change this unless explicitly requested by the user
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

logger = logging.getLogger(__name__)

class AngelaAI:
    """Angela - 非劳务收入路径设计AI服务"""
    
    def __init__(self):
        self.model = "gpt-4o"
        self.max_tokens = 4000
        
    def format_make_happy(self, make_happy_data: List[str]) -> str:
        """格式化动机标签数据"""
        if not make_happy_data:
            return "未指定"
        
        # 映射值到显示文本
        label_map = {
            'recognition': '获得认可/名声',
            'learning': '学习新知识/技能',
            'networking': '扩展人脉/社交圈',
            'fun': '娱乐放松/享受过程',
            'helping': '帮助他人/社会价值',
            'money': '获得金钱/经济收益',
            'power': '获得权力/影响力',
            'creation': '创造作品/表达自我',
            'growth': '个人成长/突破挑战'
        }
        
        return "、".join([label_map.get(item, item) for item in make_happy_data])
    
    def format_external_resources(self, resources_data: List[str]) -> str:
        """格式化外部资源数据"""
        if not resources_data:
            return "无可用外部资源"
            
        # 按资源类型分组
        categories = {
            '资金支持': [],
            '市场渠道': [],
            '执行能力': [],
            '战略合作': []
        }
        
        # 根据资源内容分类（简化版，可以扩展）
        for resource in resources_data:
            if any(keyword in resource for keyword in ['资金', '投资', '预算', '赞助']):
                categories['资金支持'].append(resource)
            elif any(keyword in resource for keyword in ['渠道', '平台', '媒体', '社群']):
                categories['市场渠道'].append(resource)
            elif any(keyword in resource for keyword in ['技术', '团队', '设备', '工具']):
                categories['执行能力'].append(resource)
            else:
                categories['战略合作'].append(resource)
        
        result = []
        for category, items in categories.items():
            if items:
                result.append(f"{category}: {', '.join(items)}")
        
        return "; ".join(result) if result else "通用外部资源可用"
    
    def get_knowledge_base_snippets(self, project_description: str, key_persons: List[Dict], 
                                  external_resources: List[str], db_session) -> str:
        """从知识库中检索相关片段"""
        try:
            from app import KnowledgeItem
            
            # 获取活跃状态的知识库条目
            knowledge_items = db_session.query(KnowledgeItem).filter(
                KnowledgeItem.status == 'active'
            ).all()
            
            if not knowledge_items:
                return "知识库暂无可用内容"
            
            # 提取关键词进行匹配（简化版）
            keywords = []
            if project_description:
                keywords.extend(project_description.split()[:10])  # 项目描述前10个词
            
            for person in key_persons:
                if person.get('roles'):
                    keywords.extend(person['roles'])
                if person.get('resources'):
                    keywords.extend(person['resources'][:3])  # 每人前3个资源
            
            keywords.extend(external_resources[:5])  # 前5个外部资源
            
            # 从知识库条目中选择最相关的内容摘要
            relevant_snippets = []
            for item in knowledge_items[:6]:  # 最多选择6个条目
                if item.content_summary and len(relevant_snippets) < 3:
                    # 简化的相关性检查
                    summary = item.content_summary[:200]  # 前200字符
                    relevant_snippets.append(f"• {summary}")
                    
                    # 更新使用次数
                    item.usage_count += 1
            
            return "\n".join(relevant_snippets) if relevant_snippets else "知识库内容暂不相关"
            
        except Exception as e:
            logger.error(f"Knowledge base retrieval error: {e}")
            return "知识库检索异常，使用默认策略"
    
    def generate_income_paths(self, form_data: Dict[str, Any], db_session) -> Dict[str, Any]:
        """生成非劳务收入路径"""
        try:
            # 提取表单数据
            project_name = form_data.get('projectName', '未命名项目')
            project_description = form_data.get('projectDescription', '')
            project_stage = form_data.get('projectStage', '初期阶段')
            key_persons = form_data.get('keyPersons', [])
            external_resources = form_data.get('externalResources', [])
            
            # 获取知识库片段
            kb_snippets = self.get_knowledge_base_snippets(
                project_description, key_persons, external_resources, db_session
            )
            
            # 构造系统提示
            system_prompt = """你是"Angela"，专精"非劳务收入路径设计"的高级策略顾问。
原则：
- 只输出可执行的方案，不空话。每条方案都要能立刻行动。
- 明确"谁先动、动什么、怎么动"，提供最小可验证原型（MVP）。
- 严格区分【关键人物资源（需换取/打动）】与【外部资源（可直接动用）】的用法。
- 发现信息缺口时，提出【建议补齐的关键角色类型】与可行获取路径（去哪找、用什么话术）。
- 输出结构固定，字段齐全，便于前端渲染。"""
            
            # 构造用户提示
            user_content = f"""【项目名称】{project_name}
【项目背景】{project_description}
【当前阶段】{project_stage}

【关键人物】（含角色、资源、动机）"""
            
            for i, person in enumerate(key_persons):
                name = person.get('name', f'人物{i+1}')
                roles = person.get('roles', [])
                resources = person.get('resources', [])
                make_happy = person.get('makeHappy', [])
                notes = person.get('notes', '')
                
                user_content += f"""
- 人物：{name}｜角色：{", ".join(roles) if roles else "未指定"}
  资源：{", ".join(resources) if resources else "无"}
  动机标签（如何让TA高兴）：{self.format_make_happy(make_happy)}
  备注：{notes if notes else "无"}"""
            
            user_content += f"""

【外部资源（可直接使用的资源池）】
{self.format_external_resources(external_resources)}

【知识库要点】（只给要点，避免冗长）
{kb_snippets}"""
            
            assistant_prompt = """请输出 JSON，字段与格式严格如下：
{
  "overview": {
    "situation": "当前已掌握资源与限制的总结（<=120字）",
    "gaps": ["缺少的关键角色或环节1","..."],
    "suggested_roles_to_hunt": [
      {"role":"渠道方/推广方","why":"理由","where_to_find":"去哪里找","outreach_script":"简短话术（<=80字）"}
    ]
  },
  "paths": [
    {
      "id": "path_1",
      "name": "路径名（<=16字）",
      "scene": "在哪个场景/媒介下操作（如：微信群直播/线下小沙龙/联名推文）",
      "who_moves_first": "由谁先出手（如：你先约KOL/先找品牌运营）",
      "action_steps": [
        {"owner":"你","step":"做什么动作（具体到渠道/频次/形式）","why_it_works":"满足谁的动机/资源如何串联"},
        {"owner":"关键人物A","step":"做什么","why_it_works":"..."}
      ],
      "use_key_person_resources": ["引用到的人与其具体资源清单..."],
      "use_external_resources": ["直接动用的外部资源..."],
      "revenue_trigger": "非劳务收益触发点（如分成/倒流/授权/转介绍）",
      "mvp": "一天内可完成的最小验证动作（含成功判据，如报名数≥30/转化≥2%）",
      "risks": ["风险点1","风险点2"],
      "plan_b": "最关键风险的替代方案（具体）",
      "kpis": ["行动KPI1","KPI2（含口径）"]
    }
  ],
  "notes": "补充建议（可为空）"
}
注意：
- 最多返回3条路径，少而精。
- 每个 action_steps 至少3步，尽量具体到"在哪个平台、用什么形式、频率多少"。
- 用项目现有资源优先，其次才建议补齐角色。"""
            
            # 调用OpenAI API
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                    {"role": "assistant", "content": assistant_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=self.max_tokens
            )
            
            # 解析响应
            result_text = response.choices[0].message.content
            if not result_text:
                raise ValueError("AI返回内容为空")
            result = json.loads(result_text)
            
            # 验证结果结构
            if not self._validate_result_structure(result):
                raise ValueError("AI返回结构不完整")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return self._get_fallback_result(form_data)
        except Exception as e:
            logger.error(f"AI generation error: {e}")
            return self._get_fallback_result(form_data)
    
    def refine_path(self, path_data: Dict[str, Any], refinement_data: Dict[str, Any], 
                   db_session) -> Dict[str, Any]:
        """细化指定路径"""
        try:
            selected_path_id = refinement_data.get('selected_path_id')
            add_personas = refinement_data.get('add_personas', [])
            constraints = refinement_data.get('constraints', '')
            tweaks = refinement_data.get('tweaks', '')
            
            # 构造细化提示
            system_prompt = """你是"Angela"，正在细化一条非劳务收入路径。根据用户的补充信息和约束条件，优化现有路径。"""
            
            user_content = f"""【当前路径】
{json.dumps(path_data, ensure_ascii=False, indent=2)}

【补充人物】
{json.dumps(add_personas, ensure_ascii=False, indent=2)}

【约束条件】
{constraints}

【调整要求】
{tweaks}

请优化这条路径，保持相同的ID，但调整action_steps、resources使用、MVP等内容。"""
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"},
                temperature=0.6,
                max_tokens=2000
            )
            
            result_text = response.choices[0].message.content
            if not result_text:
                return path_data
            result = json.loads(result_text)
            return result
            
        except Exception as e:
            logger.error(f"Path refinement error: {e}")
            # 返回原路径作为后备
            return path_data
    
    def _validate_result_structure(self, result: Dict[str, Any]) -> bool:
        """验证返回结果的结构完整性"""
        required_keys = ['overview', 'paths']
        if not all(key in result for key in required_keys):
            return False
            
        overview = result.get('overview', {})
        if not all(key in overview for key in ['situation', 'gaps']):
            return False
            
        paths = result.get('paths', [])
        if not paths:
            return False
            
        for path in paths:
            required_path_keys = ['id', 'name', 'scene', 'action_steps', 'mvp']
            if not all(key in path for key in required_path_keys):
                return False
                
        return True
    
    def _get_fallback_result(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """降级返回结果（当AI调用失败时）"""
        project_name = form_data.get('projectName', '项目')
        key_persons = form_data.get('keyPersons', [])
        
        return {
            "overview": {
                "situation": f"{project_name}处于初期阶段，需要整合现有资源并寻找收益化路径。",
                "gaps": ["明确收益模式", "扩展合作渠道", "制定执行计划"],
                "suggested_roles_to_hunt": [
                    {
                        "role": "渠道合作方",
                        "why": "需要流量入口和变现渠道",
                        "where_to_find": "行业群组、专业论坛、商业活动",
                        "outreach_script": "我们有优质内容和用户基础，寻求互利合作机会，可先小规模试点。"
                    }
                ]
            },
            "paths": [
                {
                    "id": "path_1",
                    "name": "资源整合变现",
                    "scene": "线上协作平台",
                    "who_moves_first": "你先梳理现有资源清单",
                    "action_steps": [
                        {"owner": "你", "step": "整理现有资源和人脉清单", "why_it_works": "明确可用资产"},
                        {"owner": "你", "step": "寻找1-2个初步合作伙伴", "why_it_works": "测试合作可能性"},
                        {"owner": "合作方", "step": "提供渠道或资源支持", "why_it_works": "实现资源互补"}
                    ],
                    "use_key_person_resources": [f"{p.get('name', '关键人物')}: {', '.join(p.get('resources', ['待确定']))}" for p in key_persons[:2]],
                    "use_external_resources": ["现有网络资源", "行业关系"],
                    "revenue_trigger": "合作分成或资源置换",
                    "mvp": "完成一次小规模合作测试，验证合作模式可行性",
                    "risks": ["合作方不积极", "资源对接困难"],
                    "plan_b": "转为自主开发，寻求其他渠道支持",
                    "kpis": ["合作洽谈成功率", "初步收益金额"]
                }
            ],
            "notes": "系统降级生成，建议手动优化各环节细节。"
        }

# 创建全局实例
angela_ai = AngelaAI()