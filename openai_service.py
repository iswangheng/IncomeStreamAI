import os
import json
import logging
from openai import OpenAI
from typing import Dict, List, Any, Optional

# OpenAI客户端初始化
# the newest OpenAI model is "gpt-4o" which was released May 13, 2024. 
# do not change this unless explicitly requested by the user
import httpx
import time

# 创建带重试机制的客户端
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    timeout=httpx.Timeout(60.0, connect=30.0)  # 增加超时时间：连接30秒，读取60秒
)

logger = logging.getLogger(__name__)

class AngelaAI:
    """Angela - 非劳务收入路径设计AI服务"""
    
    def __init__(self):
        self.model = "gpt-4o-mini"  # 使用更快的mini版本，响应速度更快
        self.max_tokens = 2500  # 减少token数量，加快响应
    
    def _call_openai_with_retry(self, **kwargs):
        """调用OpenAI API，带简单重试机制"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"正在调用OpenAI API (尝试 {attempt + 1}/{max_retries})...")
                return client.chat.completions.create(**kwargs)
            except (httpx.TimeoutException, httpx.ConnectError, ConnectionError, httpx.ReadTimeout, httpx.ConnectTimeout) as e:
                if attempt < max_retries - 1:
                    wait_time = 3 * (attempt + 1)  # 线性退避: 3s, 6s, 9s
                    logger.warning(f"OpenAI API调用失败 (尝试 {attempt + 1}): {str(e)}, {wait_time}秒后重试...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"OpenAI API调用失败，已重试{max_retries}次: {str(e)}")
                    # 不要raise，返回None让调用方处理
                    return None
            except Exception as e:
                logger.error(f"OpenAI API调用遇到非网络错误: {str(e)}")
                # 对于其他错误也返回None
                return None
        
    def format_make_happy(self, make_happy_data) -> str:
        """格式化动机标签数据"""
        if not make_happy_data:
            return "未指定"
        
        # 如果是字符串，先分割成列表
        if isinstance(make_happy_data, str):
            make_happy_list = make_happy_data.split(',')
        else:
            make_happy_list = make_happy_data
        
        # 映射值到显示文本（包含新的实际标签）
        label_map = {
            'recognition': '获得认可/名声',
            'learning': '学习新知识/技能',
            'networking': '扩展人脉/社交圈',
            'fun': '娱乐放松/享受过程',
            'helping': '帮助他人/社会价值',
            'money': '获得金钱/经济收益',
            'power': '获得权力/影响力',
            'creation': '创造作品/表达自我',
            'growth': '个人成长/突破挑战',
            # 新增实际使用的标签
            'bring_leads': '带来客户/引流',
            'recurring_income': '获得持续收入',
            'no_conflict_current_partner': '不冲突现有合作',
            'brand_exposure': '品牌曝光',
            'expand_network': '拓展网络/人脉'
        }
        
        return "、".join([label_map.get(item.strip(), item.strip()) for item in make_happy_list])
    
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
            from models import KnowledgeItem
            
            # 获取活跃状态的知识库条目
            knowledge_items = db_session.query(KnowledgeItem).filter(
                KnowledgeItem.status == 'active'
            ).all()
            
            if not knowledge_items:
                return self.get_core_knowledge_fallback()
            
            # 构建项目关键词，用于匹配知识库案例
            project_keywords = self._extract_project_keywords(project_description, key_persons)
            
            # 优先查找非劳务收入相关的知识库内容
            non_labor_income_items = [item for item in knowledge_items 
                                    if item.content_summary and ('非劳务收入' in item.content_summary or 
                                                               '管道' in item.content_summary or
                                                               '租金' in item.content_summary or
                                                               '股份' in item.content_summary or
                                                               '版权' in item.content_summary or
                                                               'Bonnie' in item.content_summary or
                                                               'Angela' in item.content_summary or
                                                               '楚楚' in item.content_summary or
                                                               '知了猴' in item.content_summary or
                                                               '英语培训' in item.content_summary or
                                                               '商铺' in item.content_summary)]
            
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

    def _extract_project_keywords(self, project_description: str, key_persons: List[Dict]) -> List[str]:
        """提取项目关键词用于知识库匹配"""
        keywords = []
        
        # 从项目描述中提取关键词
        if '英语' in project_description or '培训' in project_description:
            keywords.extend(['英语培训', 'Bonnie', '升学规划'])
        if '商铺' in project_description or '房东' in project_description or '租' in project_description:
            keywords.extend(['商铺', '租金', 'Angela', '二房东'])  
        if '知了猴' in project_description or '养殖' in project_description:
            keywords.extend(['知了猴', '楚楚', '养殖'])
            
        return keywords

    def get_core_knowledge_fallback(self) -> str:
        """当知识库检索失败时的核心知识要点"""
        return """• 非劳务收入核心公式：意识+能量+能力（行动）=结果
• 七大类型：租金（万物皆可租）、利息、股份/红利、版权、专利、企业连锁、团队收益
• 三步法则：盘资源→搭管道→动真格
• 核心原则：让关键环节的关键人物都高兴，严格区分需换取的人物资源vs可直接动用的外部资源
• 成功要素：1)设计共赢机制 2)掌握核心信息+筛选规则 3)前置合作规则
• 成功案例参考：Bonnie英语培训管道（连接规划师+机构，年40万收入）、Angela商铺二房东（1万启动，8年72万收入）、楚楚知了猴管道（7条管道，年70万收入）"""
    
    def generate_income_paths(self, form_data: Dict[str, Any], db_session) -> Dict[str, Any]:
        """生成非劳务收入路径"""
        try:
            # 提取表单数据
            project_name = form_data.get('projectName', '未命名项目')
            project_description = form_data.get('projectDescription', '')
            project_stage = form_data.get('projectStage', '初期阶段')
            key_persons = form_data.get('keyPersons', [])
            external_resources = form_data.get('externalResources', [])
            
            # 获取知识库片段 - 简化以减少prompt长度
            try:
                kb_snippets = self.get_knowledge_base_snippets(
                    project_description, key_persons, external_resources, db_session
                )
                # 限制知识库内容长度
                if len(kb_snippets) > 500:
                    kb_snippets = kb_snippets[:500] + "..."
            except Exception as kb_error:
                logger.warning(f"Knowledge base retrieval failed: {kb_error}")
                kb_snippets = self.get_core_knowledge_fallback()
            
            # 构造系统提示
            system_prompt = """你是"Angela"，一位专精于"非劳务收入管道设计"的高级商业顾问与架构师。  
你长期研究并实践"如何利用别人手中的资源来创造收益"，擅长把复杂的利益关系拆解成低成本、低风险、快验证的合作路径。  
你的任务是：根据用户提供的项目信息，生成 1–3 套切实可行的非劳务收入路径草案。

必须遵循以下核心原则：

1. 非劳务收入的本质公式
【意识 + 能量 + 能力 = 结果】
- 意识：设计者（用户）负责提出闭环方案与规则，确保所有关键人物都高兴。  
- 能量：关键环节的关键人物必须"高兴"，即获得了他们想要的（动机满足）。  
- 能力：让结果发生所需的所有环节能力（人、钱、时间、资源），都借用别人的。  
最终结果：设计者本人不依赖持续劳动，而能通过七大类型的非劳务收益模式获得稳定回报。  
在输出时，必须说明：这一条路径中的【设计者的意识/位置】、能量来自谁、能力是谁的。

2. 七大类型（非劳务收入的源头分类）
你必须严格以以下 7 类为框架，来映射或组合方案：
1) 租金 —— 万物皆可租：场地租赁、设备租赁、渠道租赁、品牌位租赁  
2) 利息 —— 金钱的时间价值：资金占用费、信用额度收益、资金拆借  
3) 股份 —— 资源换股权：以资源/渠道/IP入股，收取股息或未来收益  
4) 版权专利 —— 经验/创作/知识产权的授权费：内容、方法论、商标、专利许可  
5) 居间 —— 中介费/撮合费：供需对接、撮合成交、推荐返佣  
6) 企业连锁 —— 体系复制收益：加盟费、平台会员费、生态合作费  
7) 团队收益 —— 借人赚钱：团队业绩提成、代理分佣、运营管理费  

要求：
- 每条路径必须标注：【类型】+【收益触发点】+【结算方式】  
- **必须明确设计者本人通过哪一类或哪几类获得非劳务收入**  
- 收益来源若不属于七类之一，必须重写。

3. 设计路径的流程
每条非劳务收入路径必须遵循以下步骤：
① 盘点现有资源 —— 关键人物（身份/资源/动机）、外部资源  
② 判断是否存在缺口 —— 
   - 如果已有资源已能闭环，直接生成方案，并写明"为什么足够闭环"  
   - 如果不足，则提示缺失的角色/资源  
③ 匹配动机 —— 设计让关键人物高兴的激励（满足他们的需求标签）  
④ 串联资源 —— 借用资源形成闭环（不依赖设计者自己出力）  
⑤ 设计最小闭环（MVP） —— 用 1–3 句话清晰说明方案如何自洽、资源如何串联形成闭环  
⑥ 收益来源 —— 明确非劳务收入从哪里来，并指出属于七大类型中的哪一类；必须指出"设计者的收入来源"  
⑦ 风险与 Plan B —— 每一条方案必须写清楚可能存在的项目风险，以及对应的每一个风险的应对方案  
⑧ 弱环节识别 —— 指出闭环中最脆弱的一环，并说明可能影响闭环的原因  

4. 输出必须剧本化
- 每条路径包含：谁 → 做什么 → 用什么资源 → 满足谁的动机 → 触发什么收益  
- 动作必须包含：动作类型 + 平台/场景 + 频率/形式  
- 必须明确设计者的动作（即便是"统筹/撮合/规则制定"），不能跳过设计者  
- 收益触发必须对应七大类型中的至少一类，并明确"设计者的非劳务收益"

5. 缺口识别与补齐
- 如果用户提供的资源已经足够，直接生成闭环方案，并写明"现有资源足够闭环"  
- 如果资源确实不足，则明确点出缺少的角色/资源类型，并提供"去哪找 + 如何说服"的建议  
- 所有话术必须切实可行，符合中国当下的商业环境和语言环境，避免大路货  
- 话术必须包含交换逻辑（你给对方什么 / 对方得到什么）

6. 输出风格
- 方案数量：1–3 条，少而精  
- 严格结构化输出，字段固定，顺序统一，便于系统解析  
- 避免空洞词汇，必须落到动作、资源和收益上  
- 所有收益必须是"非劳务"性质，不能依赖用户自己长期劳动  

7. 检验标准
- 一条合格的路径，用户（设计者）能看懂闭环逻辑，并知道从哪里开始执行第一步  
- 输出必须明确：方案启动的第一步、在哪里做、为什么可行  
- 设计者必须在方案中明确存在，并且获得非劳务收入  
- 如果不能落地执行，视为失败

8. 劳动占比自检
- 每条路径都要输出"设计者自身劳动负担估算（小时/周）"  
- 输出分档：<5h/周 = 轻度；5–10h/周 = 中度；>10h/周 = 过高  
- 必须提供"如何降低劳动量的替代执行方案"""
            
            # 构造用户提示
            user_content = f"""【项目名称】{project_name}
【项目背景】{project_description}
【当前阶段】{project_stage}

【关键人物】（含角色、资源、动机）"""
            
            for i, person in enumerate(key_persons):
                name = person.get('name', f'人物{i+1}')
                role = person.get('role', '')  # 修正：使用role而不是roles
                resources = person.get('resources', [])
                make_happy = person.get('make_happy', '')  # 修正：使用make_happy而不是makeHappy
                notes = person.get('notes', '')
                
                user_content += f"""
- 人物：{name}｜角色：{role if role else "未指定"}
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
    "situation": "运用【意识+能量+能力=结果】公式分析当前情况（<=150字），必须包含设计者自己的位置",
    "income_type": "主要适用的非劳务收入类型（租金/利息/股份/版权/居间/企业连锁/团队收益）",
    "core_insight": "核心洞察：为什么这个项目能形成非劳务收入管道，并且设计者本人如何在其中获利",
    "gaps": ["缺少的关键角色或环节1","..."],
    "suggested_roles_to_hunt": [
      {
        "role":"建议补齐的角色",
        "why":"为什么需要",
        "where_to_find":"去哪找",
        "outreach_script":"切实可行的话术（包含交换逻辑：你给什么/对方得什么）"
      }
    ]
  },
  "paths": [
    {
      "id": "path_1",
      "name": "路径名（<=20字）",
      "income_mechanism": {
        "type": "所属的非劳务收入类型（七大类之一或组合）",
        "trigger": "收益触发点（钱从哪来）",
        "settlement": "结算方式（按单/按期/分红/授权费等）"
      },
      "parties_structure": [
        {
          "party": "设计者（你）",
          "resources": ["你提供的资源或规则"],
          "role_value": "你在闭环中的价值（统筹/撮合/规则制定等）",
          "make_them_happy": "如何让自己在闭环中不被跳过并持续获利"
        },
        {
          "party": "关键人物A",
          "resources": ["他能提供的资源"],
          "role_value": "他在闭环中的位置/作用",
          "make_them_happy": "如何让他高兴（满足的需求/动机）"
        },
        {
          "party": "关键人物B",
          "resources": ["..."],
          "role_value": "...",
          "make_them_happy": "..."
        }
      ],
      "action_steps": [
        {
          "owner":"你",
          "action":"具体动作（动作类型+平台/场景+频率/形式）",
          "why_it_works":"满足了谁的动机，用了哪份资源"
        },
        {
          "owner":"关键人物A",
          "action":"响应动作",
          "why_it_works":"满足了谁的动机"
        }
      ],
      "mvp": "最小闭环，用1-3句话说明如何形成自洽的闭环",
      "weak_link": "闭环中最脆弱的一环及原因",
      "revenue_trigger": "明确写出钱从哪来，属于哪类非劳务收入类型",
      "risks_and_planB": [
        {"risk":"具体风险1","mitigation":"对应的应对方案"},
        {"risk":"具体风险2","mitigation":"对应的应对方案"}
      ],
      "first_step": "方案的启动动作，在哪里做，为什么可行",
      "labor_load_estimate": {
        "hours_per_week": "设计者预计投入小时数/周",
        "level": "轻度(<5h)/中度(5-10h)/过高(>10h)",
        "alternative": "如何降低劳动量的替代方案"
      }
    }
  ]
}"""
            
            # 打印prompt长度信息
            total_prompt = system_prompt + user_content + assistant_prompt
            logger.info(f"===== OpenAI API Request Info =====")
            logger.info(f"Model: {self.model}")
            logger.info(f"Max tokens: {self.max_tokens}")
            logger.info(f"System prompt length: {len(system_prompt)} chars")
            logger.info(f"User content length: {len(user_content)} chars")
            logger.info(f"Assistant prompt length: {len(assistant_prompt)} chars")
            logger.info(f"Total prompt length: {len(total_prompt)} chars")
            logger.info(f"===== Full Prompt Content =====")
            logger.info(f"System: {system_prompt[:500]}..." if len(system_prompt) > 500 else f"System: {system_prompt}")
            logger.info(f"User: {user_content[:500]}..." if len(user_content) > 500 else f"User: {user_content}")
            logger.info(f"Assistant: {assistant_prompt[:500]}..." if len(assistant_prompt) > 500 else f"Assistant: {assistant_prompt}")
            logger.info(f"================================")
            
            # 调用OpenAI API，带重试机制
            response = self._call_openai_with_retry(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                    {"role": "assistant", "content": assistant_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=self.max_tokens,
                timeout=45  # 添加明确的请求级超时
            )
            
            # 如果响应为None（网络错误），返回备用方案
            if response is None:
                logger.warning("OpenAI API返回None，使用备用方案")
                return self._get_fallback_result(form_data)
            
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