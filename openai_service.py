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
        self.model = "gpt-4o-2024-11-20"  # 使用最新的稳定版本
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
                return self.get_core_knowledge_fallback()
            
            # 优先查找非劳务收入相关的知识库内容
            non_labor_income_items = [item for item in knowledge_items 
                                    if item.content_summary and ('非劳务收入' in item.content_summary or 
                                                               '管道' in item.content_summary or
                                                               '租金' in item.content_summary or
                                                               '股份' in item.content_summary or
                                                               '版权' in item.content_summary)]
            
            relevant_snippets = []
            
            # 如果找到非劳务收入相关内容，优先使用
            if non_labor_income_items:
                for item in non_labor_income_items[:2]:  # 最多2个核心条目
                    if item.content_summary:
                        # 提取更多有用信息，特别关注核心原理和案例
                        summary = item.content_summary[:800]  # 增加到800字符获取更多信息
                        relevant_snippets.append(f"• {summary}")
                        item.usage_count += 1
            
            # 补充其他相关条目
            other_items = [item for item in knowledge_items if item not in non_labor_income_items]
            for item in other_items[:2]:  # 最多再补充2个
                if item.content_summary and len(relevant_snippets) < 4:
                    summary = item.content_summary[:300]
                    relevant_snippets.append(f"• {summary}")
                    item.usage_count += 1
            
            # 如果没有找到相关内容，返回核心知识要点
            if not relevant_snippets:
                return self.get_core_knowledge_fallback()
            
            return "\n".join(relevant_snippets)
            
        except Exception as e:
            logger.error(f"Knowledge base retrieval error: {e}")
            return self.get_core_knowledge_fallback()

    def get_core_knowledge_fallback(self) -> str:
        """当知识库检索失败时的核心知识要点"""
        return """• 非劳务收入核心公式：意识+能量+能力（行动）=结果
• 七大类型：租金（万物皆可租）、利息、股份/红利、版权、专利、企业连锁、团队收益
• 三步法则：盘资源→搭管道→动真格
• 核心原则：让关键环节的关键人物都高兴，严格区分需换取的人物资源vs可直接动用的外部资源
• 成功要素：1)设计共赢机制 2)掌握核心信息+筛选规则 3)前置合作规则"""
    
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
            system_prompt = """你是"Angela"，专精"非劳务收入管道设计"的高级策略顾问，掌握成熟的造物法则。

【核心公式】意识+能量+能力（行动）=结果
- 意识：设计让所有关键人物都高兴的方案/规则（不用自己出能力）
- 能量：关键环节的关键人物都得高兴，为什么高兴？因为获得了他们想要的
- 能力：让结果发生的所有关键环节能力（人、钱、时间、资源等，借用别人的）

【非劳务收入七大类型】租金、利息、股份/红利、版权、专利、企业连锁、团队收益
重点关注：租金（万物皆可租）、版权（经验变现）、股份（资源换股权）

【三步成功法则】
1. 盘资源：识别可互相连接的各方，找出能互相连接的几方
2. 搭管道：设计清晰闭环，让三方及以上形成稳定合作
3. 动真格：站稳中间人位置，让每方都离不开你

【设计管道的核心要素】
- 让关键环节关键人物都高兴：设计共赢机制，每方都有明确收获
- 掌握核心信息+筛选规则：不让各方直接对接，保持中心位置
- 前置合作规则：事前谈清楚协议、抽成、流程、职责，确保可复制

【输出原则】
- 只输出可执行方案，每条都能立刻行动，明确"谁先动、动什么、怎么动"
- 严格区分【关键人物资源（需换取/打动）】与【外部资源（可直接动用）】
- 必须设计三方及以上的闭环结构，确保自己在管道中心不被跳过
- 提供最小可验证原型（MVP），一天内就能开始测试
- 发现信息缺口时，明确建议补齐的关键角色类型和获取路径"""
            
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
            
            assistant_prompt = """请严格按照非劳务收入管道设计原理，输出以下JSON格式：
{
  "overview": {
    "situation": "运用【意识+能量+能力=结果】公式分析当前情况（<=150字）",
    "income_type": "主要适用的收入类型（租金/版权/股份/其他）",
    "core_insight": "核心洞察：为什么这个项目能形成非劳务收入管道",
    "gaps": ["缺少的关键角色或环节1","..."],
    "suggested_roles_to_hunt": [
      {"role":"具体角色（如：本地餐饮老板/内容创作者）","why":"为什么需要这个角色","where_to_find":"具体去哪找（如：本地商会/小红书私信）","outreach_script":"开场话术（<=80字）"}
    ]
  },
  "paths": [
    {
      "id": "path_1",
      "name": "路径名（<=20字）",
      "income_mechanism": "收入机制（如：中介费分成/授权费/股权分红）",
      "three_parties_structure": {
        "party_a": "甲方名称和需求",
        "party_b": "乙方名称和能提供的",
        "your_role": "你的中间人价值和不可替代性"
      },
      "scene": "操作场景/媒介（如：微信群直播/线下沙龙/公众号合作）",
      "who_moves_first": "首先行动者和具体动作",
      "action_steps": [
        {"owner":"你","step":"第1步具体动作（平台/形式/频率）","make_who_happy":"让谁高兴？为什么高兴？"},
        {"owner":"关键人物A","step":"对方的响应动作","make_who_happy":"满足了谁的需求"},
        {"owner":"你","step":"第2步跟进动作","make_who_happy":"进一步巩固哪方关系"},
        {"owner":"关键人物B/外部资源","step":"第3步扩展动作","make_who_happy":"形成多赢局面"}
      ],
      "use_key_person_resources": ["明确引用谁的什么具体资源"],
      "use_external_resources": ["直接动用的外部资源"],
      "revenue_trigger": "非劳务收益触发条件和机制（具体金额/比例）",
      "mvp": "24小时内最小验证动作（含成功标准，如：3个意向客户确认/获得1个试点机会）",
      "avoid_being_bypassed": "如何确保不被跳过的3个措施",
      "risks": ["风险1","风险2"],
      "plan_b": "主要风险的具体应对方案",
      "scaling_potential": "规模化潜力（如：可复制到多少个区域/品类）"
    }
  ],
  "implementation_priority": "建议实施顺序和理由",
  "notes": "基于知识库案例的额外建议"
}

【设计要求】
- 必须设计三方及以上闭环，确保你在管道中心位置
- 每个路径都要有明确的非劳务收入触发机制（不能是你亲自干活赚钱）
- action_steps要体现"让关键人物都高兴"的原则
- MVP必须在24小时内可验证，有明确成功判据
- 优先使用项目现有资源，巧妙串联各方需求
- 参考知识库中的成功案例模式（如租金差价/授权分成/资源整合等）"""
            
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